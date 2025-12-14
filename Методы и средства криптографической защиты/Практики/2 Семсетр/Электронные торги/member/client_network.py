# member/client_network.py
# Логика сетевого взаимодействия участника торгов с сервером.
#
# Используется:
#   - UDP broadcast для поиска сервера;
#   - TCP-соединение для обмена JSON-сообщениями.
#
# Протокол (черновой, текст/JSON по строкам):
#
#  UDP:
#   Клиент -> broadcast:  "AUCTION_DISCOVER"
#   Сервер -> клиент:     "AUCTION_HERE <tcp_port>"
#
#  TCP (JSON по строкам):
#   1) Клиент после подключения:
#        {"type": "HELLO", "role": "member", "id": "<participant_id>"}
#      Сервер:
#        {"type": "WELCOME", "ok": true, "message": "..."}  или ok=false
#
#   2) Регистрация ключей участника:
#        {"type": "REGISTER_KEYS",
#         "id": "<participant_id>",
#         "rsa": {"n": <int>, "e": <int>},
#         "gost": {"p": <int>, "q": <int>, "a": <int>, "y": <int>}
#        }
#      Сервер:
#        {"type": "REGISTER_RESULT", "ok": true/false, "reason": "..."}
#
#   3) Аутентификация по RSA:
#      Клиент запрашивает начало аутентификации:
#        {"type": "AUTH_REQUEST", "id": "<participant_id>"}
#      Сервер (если участник разрешён и окно аутентификации активно):
#        {"type": "AUTH_CHALLENGE", "id": "<participant_id>", "r": <int>}
#      Клиент вычисляет:
#        s = r^d mod n
#      и отправляет:
#        {"type": "AUTH_RESPONSE", "id": "<participant_id>", "s": <int>}
#      Сервер:
#        {"type": "AUTH_RESULT", "id": "<participant_id>",
#         "ok": true/false, "reason": "..."}
#
#   4) Отправка заявки:
#        {"type": "BID",
#         "id": "<participant_id>",
#         "bid_value": <int>,  # исходная ставка (опционально)
#         "y": <int>,          # зашифрованная ставка (x^e_ot mod n_ot)
#         "h": <int>,          # хэш по модулю q
#         "r": <int>, "s": <int>  # ГОСТ-подпись
#        }
#      Сервер:
#        {"type": "BID_RESULT", "ok": true/false, "reason": "..."}
#
# Все print(...) оставлены намеренно как трассировка хода протокола.


import socket
import json
import threading
import queue
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from common.gost_hash_3411 import gost3411_94_full
from common.num_generator import secure_random_int


# Порты и «магические» строки для discovery
DISCOVERY_PORT = 50050
DISCOVERY_MAGIC = "AUCTION_DISCOVER"
DISCOVERY_RESPONSE_MAGIC = "AUCTION_HERE"

# Таймауты (секунды)
DISCOVERY_TIMEOUT = 3.0
TCP_CONNECT_TIMEOUT = 5.0
TCP_RECV_TIMEOUT = 10.0


@dataclass
class RSAKeys:
    n: int
    e: int
    d: int


@dataclass
class GostKeys:
    p: int
    q: int
    a: int
    x: int  # закрытый ключ
    y: int  # открытый ключ


@dataclass
class AuctionMemberClient:
    """
    Клиент участника торгов.

    Обычно его жизненный цикл такой:
      1) discover_and_connect() — найти сервер в LAN и подключиться;
      2) hello(...)              — представиться;
      3) register_keys(...)      — отправить открытые ключи;
      4) authenticate(...)       — пройти аутентификацию по RSA;
      5) send_bid(...)           — отправить заявку с ГОСТ-подписью.
    """
    _reader_thread: Optional[threading.Thread] = field(default=None, init=False)
    _reader_stop: threading.Event = field(default_factory=threading.Event, init=False)
    _inbox: "queue.Queue[dict]" = field(default_factory=queue.Queue, init=False)
    _send_lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    _on_bids_published = None
    _on_results_published = None
    _on_push_log = None

    participant_id: str
    rsa_keys: RSAKeys
    gost_keys: GostKeys

    server_addr: Optional[Tuple[str, int]] = None
    tcp_sock: Optional[socket.socket] = field(default=None, init=False)
    tcp_file_r: Optional[object] = field(default=None, init=False)
    tcp_file_w: Optional[object] = field(default=None, init=False)

    server_rsa_n: Optional[int] = None
    server_rsa_e: Optional[int] = None

    # индикатор активного TCP-подключения
    running: bool = field(default=False, init=False)

    def discover_and_connect(self) -> bool:
        """
        Поиск сервера через UDP broadcast и установление TCP-соединения.
        Возвращает True при успешном подключении.
        """
        print("[CLIENT] === DISCOVERY: поиск сервера через broadcast ===")
        try:
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_sock.settimeout(DISCOVERY_TIMEOUT)

            msg = DISCOVERY_MAGIC.encode("utf-8")
            udp_sock.sendto(msg, ("255.255.255.255", DISCOVERY_PORT))
            print(f"[CLIENT] Отправлен broadcast '{DISCOVERY_MAGIC}' на порт {DISCOVERY_PORT}")

            data, addr = udp_sock.recvfrom(1024)
            resp = data.decode("utf-8", errors="ignore").strip()
            print(f"[CLIENT] Ответ discovery от {addr}: '{resp}'")

            if not resp.startswith(DISCOVERY_RESPONSE_MAGIC):
                print("[CLIENT][ERROR] Неправильный формат ответа discovery.")
                return False

            parts = resp.split()
            if len(parts) != 2:
                print("[CLIENT][ERROR] Ожидался формат 'AUCTION_HERE <tcp_port>'.")
                return False

            tcp_port = int(parts[1])
            server_ip = addr[0]
            self.server_addr = (server_ip, tcp_port)
            print(f"[CLIENT] Сервер найден: {self.server_addr}")
        except socket.timeout:
            print("[CLIENT][ERROR] Discovery: таймаут поиска сервера.")
            return False
        except Exception as ex:
            print(f"[CLIENT][ERROR] Discovery: исключение {ex}")
            return False
        finally:
            try:
                udp_sock.close()
            except Exception:
                pass

        ok = self._connect_tcp()
        self.running = ok
        return ok

    def _connect_tcp(self) -> bool:
        """
        Установить TCP-соединение с self.server_addr.
        """
        if not self.server_addr:
            print("[CLIENT][ERROR] _connect_tcp: server_addr не установлен.")
            return False

        host, port = self.server_addr
        print(f"[CLIENT] === TCP CONNECT: к {host}:{port} ===")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TCP_CONNECT_TIMEOUT)
            sock.connect((host, port))
            sock.settimeout(TCP_RECV_TIMEOUT)
        except Exception as ex:
            print(f"[CLIENT][ERROR] Не удалось подключиться к серверу: {ex}")
            return False

        self.tcp_sock = sock
        # Устанавливаем таймаут в None для синхронного чтения (будет устанавливаться по необходимости)
        sock.settimeout(None)
        # Разделяем reader/writer для удобства
        self.tcp_file_r = sock.makefile("r", encoding="utf-8", newline="\n")
        self.tcp_file_w = sock.makefile("w", encoding="utf-8", newline="\n")
        # Запускаем единый поток чтения
        self._start_reader_thread()


        print("[CLIENT] TCP-соединение установлено.")
        self.running = True
        return True

    # ------------------------------------------------------------------
    # Низкоуровневые методы отправки/приёма JSON
    # ------------------------------------------------------------------
    def _send_json(self, obj: dict) -> bool:
        if not self.tcp_file_w:
            print("[CLIENT][ERROR] _send_json: нет TCP-подключения.")
            return False

        try:
            line = json.dumps(obj, ensure_ascii=False)
            with self._send_lock:
                self.tcp_file_w.write(line + "\n")
                self.tcp_file_w.flush()
            print(f"[CLIENT -> SERVER] {line}")
            return True
        except Exception as ex:
            print(f"[CLIENT][ERROR] _send_json: {ex}")
            return False

    def _recv_json(self, timeout: float = 10.0) -> Optional[dict]:
        try:
            return self._inbox.get(timeout=timeout)
        except queue.Empty:
            print("[CLIENT][ERROR] _recv_json: таймаут ожидания ответа от сервера.")
            return None

    def receive_published_bids(self, timeout: float = 10.0) -> Optional[List[dict]]:
        """
        Получить опубликованные заявки от сервера.
        Ожидает сообщение BIDS_PUBLISHED с таймаутом.
        """
        if not self.tcp_file_r:
            print("[CLIENT][ERROR] receive_published_bids: нет TCP-подключения.")
            return None
        
        try:
            # Устанавливаем таймаут для ожидания сообщения
            if self.tcp_sock:
                self.tcp_sock.settimeout(timeout)
            
            line = self.tcp_file_r.readline()
            if not line:
                print("[CLIENT][ERROR] receive_published_bids: соединение закрыто сервером.")
                return None
            
            line = line.strip()
            print(f"[CLIENT][RECEIVE] Получено: {line}")
            
            try:
                msg = json.loads(line)
                msg_type = msg.get("type")
                
                if msg_type == "BIDS_PUBLISHED":
                    bids = msg.get("bids", [])
                    print(f"[CLIENT] Получены опубликованные заявки: {len(bids)} шт.")
                    return bids
                else:
                    print(f"[CLIENT][WARN] Получено неожиданное сообщение типа '{msg_type}' вместо BIDS_PUBLISHED")
                    return None
                    
            except json.JSONDecodeError as ex:
                print(f"[CLIENT][ERROR] Ошибка парсинга JSON: {ex}")
                return None
                
        except socket.timeout:
            print(f"[CLIENT][ERROR] receive_published_bids: таймаут ожидания сообщения ({timeout} сек)")
            return None
        except Exception as ex:
            print(f"[CLIENT][ERROR] receive_published_bids: {ex}")
            return None
        finally:
            # Возвращаем таймаут в None для обычных операций
            if self.tcp_sock:
                self.tcp_sock.settimeout(None)
    
    def close(self):
        """
        Закрыть TCP-соединение.
        """
        print("[CLIENT] Закрытие TCP-соединения.")
        self.running = False

        try:
            self._reader_stop.set()
        except Exception:
            pass

        try:
            if self._reader_thread:
                self._reader_thread.join(timeout=0.5)
        except Exception:
            pass

        try:
            if self.tcp_file_w:
                self.tcp_file_w.close()
        except Exception:
            pass
        try:
            if self.tcp_file_r:
                self.tcp_file_r.close()
        except Exception:
            pass
        try:
            if self.tcp_sock:
                self.tcp_sock.close()
        except Exception:
            pass
        self.tcp_sock = None
        self.tcp_file_r = None
        self.tcp_file_w = None
        self.running = False
    def _start_reader_thread(self):
        if self._reader_thread and self._reader_thread.is_alive():
            return

        self._reader_stop.clear()

        def _loop():
            if self._on_push_log:
                self._on_push_log("[CLIENT] Reader-thread стартовал.")
            while not self._reader_stop.is_set():
                try:
                    line = self.tcp_file_r.readline()
                    if not line:
                        if self._on_push_log:
                            self._on_push_log("[CLIENT] Reader-thread: соединение закрыто сервером.")
                        break
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        msg = json.loads(line)
                    except Exception as ex:
                        if self._on_push_log:
                            self._on_push_log(f"[CLIENT] Reader-thread: JSON parse error: {ex}")
                        continue

                    mtype = msg.get("type", "")

                    # PUSH сообщения
                    if mtype == "BIDS_PUBLISHED":
                        bids = msg.get("bids", [])
                        if self._on_push_log:
                            self._on_push_log(f"[CLIENT] PUSH: BIDS_PUBLISHED ({len(bids)} записей)")
                        if self._on_bids_published:
                            try:
                                self._on_bids_published(bids)
                            except Exception as cb_ex:
                                if self._on_push_log:
                                    self._on_push_log(f"[CLIENT] on_bids_published error: {cb_ex!r}")
                        continue

                    if mtype == "RESULTS_PUBLISHED":
                        results = msg.get("results", [])
                        winner_id = msg.get("winner_id", None)
                        if self._on_push_log:
                            self._on_push_log(f"[CLIENT] PUSH: RESULTS_PUBLISHED ({len(results)} записей), winner={winner_id!r}")
                        if self._on_results_published:
                            try:
                                self._on_results_published(results, winner_id)
                            except Exception as cb_ex:
                                if self._on_push_log:
                                    self._on_push_log(f"[CLIENT] on_results_published error: {cb_ex!r}")
                        continue

                    # Обычные ответы — в очередь
                    self._inbox.put(msg)

                except Exception as ex:
                    if self._on_push_log:
                        self._on_push_log(f"[CLIENT] Reader-thread exception: {ex!r}")
                    break

            if self._on_push_log:
                self._on_push_log("[CLIENT] Reader-thread остановлен.")

        self._reader_thread = threading.Thread(target=_loop, daemon=True)
        self._reader_thread.start()

    # ------------------------------------------------------------------
    # Высокоуровневые операции протокола
    # ------------------------------------------------------------------
    def hello(self) -> bool:
        """
        Шаг: HELLO — участник представляет себя серверу.
        """
        msg = {
            "type": "HELLO",
            "role": "member",
            "id": self.participant_id,
        }
        if not self._send_json(msg):
            return False

        resp = self._recv_json()
        if not resp:
            return False

        if resp.get("type") != "WELCOME":
            print("[CLIENT][ERROR] hello: ожидался тип 'WELCOME'.")
            return False

        if not resp.get("ok", False):
            print(f"[CLIENT][ERROR] hello: сервер отказал: {resp.get('message')}")
            return False

        # Сохраняем открытый ключ сервера, если он передан
        self.server_rsa_n = resp.get("server_rsa_n")
        self.server_rsa_e = resp.get("server_rsa_e")
        if self.server_rsa_n and self.server_rsa_e:
            print(f"[CLIENT] Получен открытый ключ сервера: n={self.server_rsa_n}, e={self.server_rsa_e}")
        else:
            print("[CLIENT][WARN] Сервер не передал открытый ключ (n,e); отправка ставок может быть недоступна.")

        print("[CLIENT] HELLO успешно обработан сервером.")
        return True

    def register_keys(self) -> bool:
        """
        Регистрация открытых ключей на сервере.
        """
        msg = {
            "type": "REGISTER_KEYS",
            "id": self.participant_id,
            "rsa": {
                "n": self.rsa_keys.n,
                "e": self.rsa_keys.e,
            },
            "gost": {
                "p": self.gost_keys.p,
                "q": self.gost_keys.q,
                "a": self.gost_keys.a,
                "y": self.gost_keys.y,
            },
        }
        if not self._send_json(msg):
            return False

        resp = self._recv_json()
        if not resp:
            return False
        if resp.get("type") != "REGISTER_RESULT":
            print("[CLIENT][ERROR] register_keys: ожидался тип 'REGISTER_RESULT'.")
            return False

        if not resp.get("ok", False):
            print(f"[CLIENT][ERROR] register_keys: отказ сервера: {resp.get('reason')}")
            return False

        print("[CLIENT] Открытые ключи успешно зарегистрированы на сервере.")
        return True

    def authenticate(self) -> bool:
        """
        Аутентификация по RSA:
          - запрос окна аутентификации,
          - получение r от сервера,
          - вычисление s = r^d mod n,
          - отправка s,
          - получение результата.
        """
        msg_req = {
            "type": "AUTH_REQUEST",
            "id": self.participant_id,
        }
        if not self._send_json(msg_req):
            return False

        resp = self._recv_json()
        if not resp:
            return False
        if resp.get("type") != "AUTH_CHALLENGE":
            print("[CLIENT][ERROR] authenticate: ожидался тип 'AUTH_CHALLENGE'.")
            return False

        r = resp.get("r")
        if not isinstance(r, int):
            print("[CLIENT][ERROR] authenticate: 'r' не является целым.")
            return False

        print(f"[CLIENT] Получен челлендж r = {r}. Вычисляем s = r^d mod n...")
        s = pow(r, self.rsa_keys.d, self.rsa_keys.n)
        print(f"[CLIENT] Вычислено s = {s}")

        msg_resp = {
            "type": "AUTH_RESPONSE",
            "id": self.participant_id,
            "s": s,
        }
        if not self._send_json(msg_resp):
            return False

        resp2 = self._recv_json()
        if not resp2:
            return False
        if resp2.get("type") != "AUTH_RESULT":
            print("[CLIENT][ERROR] authenticate: ожидался тип 'AUTH_RESULT'.")
            return False

        if not resp2.get("ok", False):
            print(f"[CLIENT][ERROR] authenticate: сервер отклонил аутентификацию: {resp2.get('reason')}")
            return False

        print("[CLIENT] Аутентификация по RSA успешно пройдена.")
        return True

    def send_bid(self, bid_value: int) -> Optional[dict]:
        """
        Отправка заявки:
          - реальное RSA-шифрование x -> y = x^e_ot mod n_ot,
          - ГОСТ-подпись хэша сообщения "bid=x".
        """
        if not self.tcp_file_w:
            print("[CLIENT][ERROR] Невозможно отправить BID: нет TCP-соединения.")
            return False

        if self.server_rsa_n is None or self.server_rsa_e is None:
            print("[CLIENT][ERROR] Не известен открытый ключ сервера (n,e).")
            return None

        x = int(bid_value)

        # --- 1. Реальное шифрование заявки открытым ключом сервера ---
        y = pow(x, self.server_rsa_e, self.server_rsa_n)
        print(f"[CLIENT] BID: исходная ставка x={x}, зашифрованная y={y}")

        # --- 2. ГОСТ-подпись хэша сообщения "bid=x" ---
        msg_bytes = f"bid={x}".encode("utf-8")
        r, s, h = self._gost_sign_message(
            msg_bytes,
            self.gost_keys.p,
            self.gost_keys.q,
            self.gost_keys.a,
            self.gost_keys.x,
        )
        print(f"[CLIENT] BID: ГОСТ-подпись r={r}, s={s}, h={h}")

        # --- 3. Формируем и отправляем JSON ---
        msg = {
            "type": "BID",
            "id": self.participant_id,
            "bid_value": x,
            "y": y,
            "h": h,
            "r": r,
            "s": s,
        }

        line = json.dumps(msg, ensure_ascii=False)
        try:
            self.tcp_file_w.write(line + "\n")
            self.tcp_file_w.flush()
        except Exception as ex:
            print(f"[CLIENT][ERROR] Ошибка при отправке BID: {ex}")
            return None

        print("[CLIENT] BID отправлен серверу, ожидаем результат...")

        # Ждём BID_RESULT от сервера
        resp = self._recv_json()
        if not resp or resp.get("type") != "BID_RESULT":
            print("[CLIENT][ERROR] Не получили BID_RESULT от сервера.")
            return {"ok": False, "reason": "Нет ответа от сервера."}

        ok = resp.get("ok", False)
        reason = resp.get("reason", "")
        if not ok:
            print(f"[CLIENT][WARN] BID отклонён сервером: {reason}")
            return {"ok": False, "reason": reason or "Заявка отклонена сервером."}

        print("[CLIENT] BID принят сервером.")
        return {
            "ok": True,
            "bid_value": x,
            "y": y,
            "h": h,
            "r": r,
            "s": s,
        }

    def _gost_hash_to_int_q(self, message: bytes, q: int) -> int:
        """
        Хэш ГОСТ 34.11-94 -> целое по модулю q, как в GUI.
        """
        H_be = gost3411_94_full(message)  # 32 байта, MSB-first
        h = int.from_bytes(H_be[::-1], "big")  # LE-представление
        h = h % q
        if h == 0:
            h = 1
        return h

    def _gost_sign_message(self, message: bytes, p: int, q: int, a: int, x: int):
        """
        Подпись по ГОСТ Р 34.10-94. Возвращает (r, s, h).
        Полностью совпадает с gost_sign_message из GUI.
        """
        h = self._gost_hash_to_int_q(message, q)

        while True:
            k = secure_random_int(1, q - 1)
            r = pow(a, k, p) % q
            if r == 0:
                continue
            s = (k * h + x * r) % q
            if s == 0:
                continue
            return r, s, h

    # -------------------- PUSH LISTENER (server -> client) --------------------

    def start_push_listener(self, on_bids_published=None, on_results_published=None, on_log=None):
        self._on_bids_published = on_bids_published
        self._on_results_published = on_results_published
        self._on_push_log = on_log
        if self._on_push_log:
            self._on_push_log("[CLIENT] Push callbacks зарегистрированы (reader-thread используется общий).")

    def stop_push_listener(self):
        """Останавливает push listener (если запущен)."""
        if hasattr(self, "_push_stop") and self._push_stop:
            self._push_stop.set()



# Пример использования как standalone (для отладки без GUI):
if __name__ == "__main__":
    # ВНИМАНИЕ: это только пример, ключи нужно получить из твоих num_generator/rsa_utils,
    # здесь подставлены фиктивные значения.
    dummy_rsa = RSAKeys(n=3233, e=17, d=2753)
    dummy_gost = GostKeys(p=23, q=11, a=2, x=5, y=9)

    client = AuctionMemberClient(
        participant_id="V1",
        rsa_keys=dummy_rsa,
        gost_keys=dummy_gost,
    )

    if not client.discover_and_connect():
        print("Не удалось найти/подключиться к серверу.")
    else:
        if client.hello() and client.register_keys() and client.authenticate():
            # Фиктивные данные заявки:
            client.send_bid(bid_value=1000)

        client.close()
