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
from gost_hash_3411 import gost3411_94_full
from num_generator import secure_random_int
from rsa_utils import (
    ffs_generate_secret_and_public,
    ffs_commit,
    ffs_respond,
    ffs_verify,
)


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
    _on_bidding_status = None
    _on_push_log = None

    participant_id: str
    rsa_keys: Optional[RSAKeys] = None
    gost_keys: Optional[GostKeys] = None

    server_addr: Optional[Tuple[str, int]] = None
    tcp_sock: Optional[socket.socket] = field(default=None, init=False)
    tcp_file_r: Optional[object] = field(default=None, init=False)
    tcp_file_w: Optional[object] = field(default=None, init=False)

    server_rsa_n: Optional[int] = None
    server_rsa_e: Optional[int] = None
    server_gost_p: Optional[int] = None
    server_gost_q: Optional[int] = None
    server_gost_a: Optional[int] = None
    server_schnorr_y: Optional[int] = None

    # --- FFS public key of server (n is reused from server RSA) ---
    server_ffs_n: Optional[int] = None
    server_ffs_v: Optional[int] = None

    # --- FFS keys of client (secret s + public v) ---
    ffs_s: Optional[int] = None
    ffs_v: Optional[int] = None

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

        # Разделяем reader/writer для удобства.
        # Важно: reader-thread НЕ стартуем здесь, чтобы не было гонки за первые ответы протокола (WELCOME/REGISTER_RESULT
        # и т.п.). Синхронные ответы читаются напрямую через _recv_json_direct().
        self.tcp_file_r = sock.makefile("r", encoding="utf-8", newline="\n")
        self.tcp_file_w = sock.makefile("w", encoding="utf-8", newline="\n")


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
        """
        Получение JSON-ответа.
        Если reader-thread уже запущен — читаем из очереди (_inbox).
        Если reader-thread ещё не запущен (этап HELLO/REGISTER и т.п.) — читаем напрямую из TCP.
        """
        if self._reader_thread is None or not self._reader_thread.is_alive():
            return self._recv_json_direct(timeout=timeout)
        try:
            return self._inbox.get(timeout=timeout)
        except queue.Empty:
            print("[CLIENT][ERROR] _recv_json: таймаут ожидания ответа от сервера.")
            return None
    def _recv_json_direct(self, timeout: float = 10.0) -> Optional[dict]:
        """
        Синхронное чтение JSON по строкам из TCP.
        Используется ДО запуска reader-thread, чтобы исключить гонки за первый ответ WELCOME.
        """
        if not self.tcp_sock or not self.tcp_file_r:
            print("[CLIENT][ERROR] _recv_json_direct: нет TCP-подключения.")
            return None
        prev_timeout = None
        try:
            prev_timeout = self.tcp_sock.gettimeout()
        except Exception:
            prev_timeout = None

        try:
            # Временно выставляем таймаут на чтение.
            try:
                self.tcp_sock.settimeout(timeout)
            except Exception:
                pass
            while True:
                line = self.tcp_file_r.readline()
                if not line:
                    print("[CLIENT][ERROR] _recv_json_direct: сервер закрыл соединение (EOF).")
                    return None
                line = line.strip()
                if not line:
                    continue
                try:
                    return json.loads(line)
                except json.JSONDecodeError as ex:
                    print(f"[CLIENT][WARN] _recv_json_direct: некорректный JSON ({ex}), строка пропущена.")
                    continue
        except socket.timeout:
            print("[CLIENT][ERROR] _recv_json_direct: таймаут ожидания ответа от сервера.")
            return None
        except Exception as ex:
            print(f"[CLIENT][ERROR] _recv_json_direct: {ex}")
            return None
        finally:
            # Возвращаем исходный таймаут.
            try:
                self.tcp_sock.settimeout(prev_timeout)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Локальное логирование (в т.ч. в GUI)
    # ------------------------------------------------------------------

    def _log(self, msg: str):
        """Лог в консоль и (если подключено) в GUI-виджет клиента."""
        print(msg)
        if self._on_push_log:
            try:
                self._on_push_log(msg)
            except Exception:
                pass

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
        ВАЖНО: на Windows makefile().readline() в другом потоке может зависать,
        поэтому сначала делаем shutdown сокета, чтобы гарантированно разбудить reader-thread.
        """
        print("[CLIENT] Закрытие TCP-соединения.")
        self.running = False

        # 1) останавливаем reader-loop
        try:
            self._reader_stop.set()
        except Exception:
            pass

        # 2) жёстко "будим" поток чтения: shutdown сокета
        try:
            if self.tcp_sock:
                try:
                    self.tcp_sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
        except Exception:
            pass

        # 3) закрываем файловые обёртки (после shutdown)
        try:
            if self.tcp_file_r:
                self.tcp_file_r.close()
        except Exception:
            pass

        try:
            if self.tcp_file_w:
                self.tcp_file_w.close()
        except Exception:
            pass

        # 4) закрываем сокет
        try:
            if self.tcp_sock:
                self.tcp_sock.close()
        except Exception:
            pass

        # 5) НЕ делаем blocking-join в GUI потоке (или делаем микро-таймаут)
        try:
            if self._reader_thread and self._reader_thread.is_alive():
                self._reader_thread.join(timeout=0.2)
        except Exception:
            pass

        self.tcp_sock = None
        self.tcp_file_r = None
        self.tcp_file_w = None
        self.running = False

    def _start_reader_thread(self):
        if self._reader_thread and self._reader_thread.is_alive():
            return
        # Для reader-thread нужен блокирующий режим, иначе socket.timeout может преждевременно рвать чтение.
        try:
            if self.tcp_sock:
                self.tcp_sock.settimeout(None)
        except Exception:
            pass

        self._reader_stop.clear()

        def _safe_push_log(text: str):
            """
            Никогда не даём reader-thread упасть из-за лог-колбэка (особенно из-за Tkinter).
            """
            try:
                if self._on_push_log:
                    self._on_push_log(text)
                else:
                    # если GUI-колбэка нет — хотя бы в консоль
                    print(text)
            except Exception as ex:
                # важная диагностика: видно, почему умирает поток чтения
                print(f"[CLIENT][WARN] on_push_log callback failed: {ex!r}. msg={text!r}")

        def _loop():
            _safe_push_log("[CLIENT] Reader-thread стартовал.")
            while not self._reader_stop.is_set():
                try:
                    line = self.tcp_file_r.readline()
                    if not line:
                        _safe_push_log("[CLIENT] Reader-thread: EOF от сервера (readline вернул пусто).")
                        break
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        msg = json.loads(line)
                    except Exception as ex:
                        _safe_push_log(f"[CLIENT] Reader-thread: JSON parse error: {ex!r}. line={line!r}")
                        continue

                    mtype = msg.get("type", "")

                    # PUSH сообщения
                    if mtype == "BIDS_PUBLISHED":
                        bids = msg.get("bids", [])
                        _safe_push_log(f"[CLIENT] PUSH: BIDS_PUBLISHED ({len(bids)} записей)")
                        if self._on_bids_published:
                            try:
                                self._on_bids_published(bids)
                            except Exception as cb_ex:
                                _safe_push_log(f"[CLIENT] on_bids_published error: {cb_ex!r}")
                        continue

                    if mtype == "RESULTS_PUBLISHED":
                        results = msg.get("results", [])
                        winner_id = msg.get("winner_id", None)
                        _safe_push_log(f"[CLIENT] PUSH: RESULTS_PUBLISHED ({len(results)} записей), winner={winner_id!r}")
                        if self._on_results_published:
                            try:
                                self._on_results_published(results, winner_id)
                            except Exception as cb_ex:
                                _safe_push_log(f"[CLIENT] on_results_published error: {cb_ex!r}")
                        continue

                    if mtype == "BIDDING_STATUS":
                        is_open = bool(msg.get("open", False))
                        _safe_push_log(f"[CLIENT] PUSH: BIDDING_STATUS open={is_open}")
                        if self._on_bidding_status:
                            try:
                                self._on_bidding_status(is_open)
                            except Exception as cb_ex:
                                _safe_push_log(f"[CLIENT] on_bidding_status error: {cb_ex!r}")
                        continue

                    # Обычные ответы — в очередь
                    self._inbox.put(msg)

                except Exception as ex:
                    _safe_push_log(f"[CLIENT] Reader-thread exception: {ex!r}")
                    break

            _safe_push_log("[CLIENT] Reader-thread остановлен.")

        self._reader_thread = threading.Thread(target=_loop, daemon=True)
        self._reader_thread.start()

    # ------------------------------------------------------------------
    # Высокоуровневые операции протокола
    # ------------------------------------------------------------------
    def hello(self) -> tuple[bool, str | None]:
        """
        HELLO — представление клиента серверу.
        ВАЖНО: метод НИКОГДА не закрывает соединение сам.
        """
        msg = {
            "type": "HELLO",
            "role": "member",
            "id": self.participant_id,
        }

        if not self._send_json(msg):
            return False, "Не удалось отправить HELLO серверу."

        resp = self._recv_json(timeout=5.0)
        if not resp:
            return False, "Сервер не ответил на HELLO."

        if resp.get("type") != "WELCOME":
            return False, "Некорректный ответ сервера на HELLO."

        if not resp.get("ok", False):
            reason = resp.get("message", "Сервер отклонил подключение.")
            return False, reason

        # Сохраняем открытый ключ сервера
        self.server_rsa_n = resp.get("server_rsa_n")
        self.server_rsa_e = resp.get("server_rsa_e")
        self.server_gost_p = resp.get("gost_p")
        self.server_gost_q = resp.get("gost_q")
        self.server_gost_a = resp.get("gost_a")
        self.server_schnorr_y = resp.get("server_schnorr_y")
        self.server_ffs_n = resp.get("server_ffs_n")
        self.server_ffs_v = resp.get("server_ffs_v")

        return True, None

    def register_keys(self) -> bool:
        """
        Регистрация открытых ключей на сервере.

        Отправляем:
          - ГОСТ: y (публичный ключ подписи)
          - FFS:  v (публичный ключ идентификации; модуль n общий — n сервера)

        RSA-ключи участника оставлены как опциональные и могут не отправляться.
        """
        if not self.gost_keys:
            self._log("[CLIENT][ERROR] register_keys: нет gost_keys (x/y). Сначала получите p,q,a и сгенерируйте ключи ГОСТ.")
            return False

        if self.server_rsa_n is None:
            self._log("[CLIENT][ERROR] register_keys: сервер не передал server_rsa_n (n требуется как модуль для FFS).")
            return False

        # Генерируем FFS-ключи клиента (s, v) на модуле n сервера (в учебном протоколе n общий).
        if not self._ensure_ffs_keys():
            return False

        msg = {
            "type": "REGISTER_KEYS",
            "id": self.participant_id,
            "gost": {"y": self.gost_keys.y},
            "ffs": {"v": int(self.ffs_v)},
        }
        if self.rsa_keys is not None:
            msg["rsa"] = {"n": self.rsa_keys.n, "e": self.rsa_keys.e}

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

    def _ensure_ffs_keys(self) -> bool:
        """Убедиться, что у клиента есть FFS-ключи (s, v).

        Используем модуль n сервера (тот же, что используется для RSA-шифрования заявок).
        """
        if self.ffs_s is not None and self.ffs_v is not None:
            return True
        if self.server_rsa_n is None:
            return False
        try:
            s, v = ffs_generate_secret_and_public(int(self.server_rsa_n))
            self.ffs_s = int(s)
            self.ffs_v = int(v)
            self._log(f"[CLIENT][FFS] Сгенерированы FFS-ключи клиента: v={self.ffs_v} (s скрыт)")
            return True
        except Exception as ex:
            self._log(f"[CLIENT][ERROR] Не удалось сгенерировать FFS-ключи клиента: {ex}")
            return False

    def authenticate(self) -> bool:
        """
        Двухсторонняя аутентификация по схеме Фейге–Фиата–Шамира (FFS, single-bit).

        ВАЖНО: используем многократное повторение (k=16 раундов).
        Вероятность подделки без секрета ~ 2^-k.
        """
        ROUNDS = 16

        if self.server_rsa_n is None:
            self._log("[CLIENT][ERROR] authenticate: сервер не передал server_rsa_n.")
            return False

        if self.server_ffs_v is None:
            self._log(
                "[CLIENT][ERROR] authenticate: сервер не передал server_ffs_v (взаимная аутентификация невозможна).")
            return False

        if not self._ensure_ffs_keys():
            return False

        n = int(self.server_rsa_n)
        s = int(self.ffs_s)
        v = int(self.ffs_v)

        # -------------------- Фаза A: клиент доказывает серверу --------------------
        self._log(f"[CLIENT][AUTH] === FFS: фаза A (клиент -> сервер), раундов: {ROUNDS} ===")

        for i in range(1, ROUNDS + 1):
            r, z = ffs_commit(n)
            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: выбрано r ∈ [1,n-1]. r = {r}")
            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: commitment z = r^2 mod n = {z}")

            if not self._send_json({
                "type": "AUTH_REQUEST",
                "id": self.participant_id,
                "z": z,
                "round": i,
                "rounds": ROUNDS,
            }):
                return False

            resp = self._recv_json(timeout=10.0)
            if not resp:
                return False

            # сервер может ответить отказом сразу
            if resp.get("type") == "AUTH_RESULT" and not resp.get("ok", False):
                self._log(
                    f"[CLIENT][ERROR] authenticate: сервер отказал на шаге AUTH_REQUEST (раунд {i}): {resp.get('reason')}")
                return False

            if resp.get("type") != "AUTH_CHALLENGE":
                self._log(f"[CLIENT][ERROR] authenticate: ожидался 'AUTH_CHALLENGE' (раунд {i}).")
                return False

            b = resp.get("b")
            srv_round = resp.get("round")
            if srv_round is not None and srv_round != i:
                self._log(f"[CLIENT][ERROR] authenticate: сервер вернул round={srv_round}, ожидался {i}.")
                return False

            if not isinstance(b, int) or b not in (0, 1):
                self._log(f"[CLIENT][ERROR] authenticate: 'b' должен быть битом 0/1 (раунд {i}).")
                return False

            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: получен challenge b = {b}")
            resp_val = ffs_respond(r=r, s=s, b=b, n=n)
            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: ответ resp = {resp_val}")

            if not self._send_json({
                "type": "AUTH_RESPONSE",
                "id": self.participant_id,
                "resp": resp_val,
                "round": i,
            }):
                return False

            resp2 = self._recv_json(timeout=10.0)
            if not resp2:
                return False

            if resp2.get("type") != "AUTH_RESULT":
                self._log(f"[CLIENT][ERROR] authenticate: ожидался 'AUTH_RESULT' (раунд {i}).")
                return False

            res_round = resp2.get("round")
            if res_round is not None and res_round != i:
                self._log(f"[CLIENT][ERROR] authenticate: сервер вернул AUTH_RESULT round={res_round}, ожидался {i}.")
                return False

            if not resp2.get("ok", False):
                self._log(
                    f"[CLIENT][ERROR] authenticate: сервер отклонил аутентификацию (раунд {i}): {resp2.get('reason')}")
                return False

            done = resp2.get("done", None)
            if i < ROUNDS:
                self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: OK (done={done})")
            else:
                self._log("[CLIENT][AUTH] Фаза A: все раунды пройдены, сервер подтвердил подлинность клиента.")

        # -------------------- Фаза B: сервер доказывает клиенту --------------------
        self._log(f"[CLIENT][AUTH] === FFS: фаза B (сервер -> клиент), раундов: {ROUNDS} ===")
        v_srv = int(self.server_ffs_v)

        for i in range(1, ROUNDS + 1):
            if not self._send_json({
                "type": "SERVER_AUTH_REQUEST",
                "id": self.participant_id,
                "round": i,
                "rounds": ROUNDS,
            }):
                return False

            resp3 = self._recv_json(timeout=10.0)
            if not resp3:
                return False

            if resp3.get("type") != "SERVER_AUTH_COMMIT":
                self._log(f"[CLIENT][ERROR] authenticate: ожидался 'SERVER_AUTH_COMMIT' (раунд {i}).")
                return False

            if not resp3.get("ok", False):
                self._log(
                    f"[CLIENT][ERROR] authenticate: сервер отказал в server-auth (раунд {i}): {resp3.get('reason')}")
                return False

            z_srv = resp3.get("z")
            srv_round = resp3.get("round")
            if srv_round is not None and srv_round != i:
                self._log(f"[CLIENT][ERROR] authenticate: server-auth commit round={srv_round}, ожидался {i}.")
                return False

            if not isinstance(z_srv, int) or z_srv <= 0 or z_srv >= n:
                self._log(f"[CLIENT][ERROR] authenticate: z_srv некорректен (раунд {i}).")
                return False

            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: получен commitment сервера z_srv = {z_srv}")
            b_srv = secure_random_int(0, 1)
            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: сформирован challenge серверу b_srv = {b_srv}")

            if not self._send_json({
                "type": "SERVER_AUTH_CHALLENGE",
                "id": self.participant_id,
                "b": b_srv,
                "round": i,
            }):
                return False

            resp4 = self._recv_json(timeout=10.0)
            if not resp4:
                return False

            if resp4.get("type") != "SERVER_AUTH_RESPONSE":
                self._log(f"[CLIENT][ERROR] authenticate: ожидался 'SERVER_AUTH_RESPONSE' (раунд {i}).")
                return False

            if not resp4.get("ok", False):
                self._log(
                    f"[CLIENT][ERROR] authenticate: сервер вернул ошибку на server-auth (раунд {i}): {resp4.get('reason')}")
                return False

            resp_srv = resp4.get("resp")
            srv_round2 = resp4.get("round")
            if srv_round2 is not None and srv_round2 != i:
                self._log(f"[CLIENT][ERROR] authenticate: server-auth response round={srv_round2}, ожидался {i}.")
                return False

            if not isinstance(resp_srv, int) or resp_srv <= 0 or resp_srv >= n:
                self._log(f"[CLIENT][ERROR] authenticate: resp_srv некорректен (раунд {i}).")
                return False

            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: получен ответ сервера resp_srv = {resp_srv}")

            ok_srv = ffs_verify(z=int(z_srv), resp=int(resp_srv), b=int(b_srv), v=v_srv, n=n)
            self._log(f"[CLIENT][AUTH] Раунд {i}/{ROUNDS}: проверка server-auth (FFS) = {ok_srv}")

            if not ok_srv:
                self._log(
                    f"[CLIENT][ERROR] authenticate: server-auth FFS verify failed (раунд {i}). Сервер НЕ аутентичен.")
                self._send_json({
                    "type": "MUTUAL_AUTH_CONFIRM",
                    "id": self.participant_id,
                    "ok": False,
                    "reason": f"FFS verify failed at round {i}"
                })
                return False

        # подтверждаем серверу, что все раунды проверки сервера успешны
        if not self._send_json({
            "type": "MUTUAL_AUTH_CONFIRM",
            "id": self.participant_id,
            "ok": True,
            "reason": "",
            "rounds": ROUNDS,
        }):
            return False

        resp5 = self._recv_json(timeout=10.0)
        if not resp5:
            return False

        if resp5.get("type") == "MUTUAL_AUTH_RESULT" and not resp5.get("ok", False):
            self._log(
                f"[CLIENT][ERROR] authenticate: сервер не принял подтверждение взаимной аутентификации: {resp5.get('reason')}")
            return False

        self._log("[CLIENT][AUTH] Фаза B: сервер успешно проверен. Взаимная аутентификация завершена.")
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
        msg_bytes = f"y={y}".encode("utf-8")
        r, s, h = self._gost_sign_message(
            msg_bytes,
            self.gost_keys.p,
            self.gost_keys.q,
            self.gost_keys.a,
            self.gost_keys.x
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

    def send_fake_bid(self, bid_value: int, fake_signed_value: int = 1000):
        """
        Атака 3 (ДЕМО):
        - y считается от bid_value
        - подпись считается от ДРУГОГО y (fake_signed_value)
        Сервер ОБЯЗАН отклонить заявку.
        """

        if not self.running:
            return None

        # --- Реальный y (то, что видит сервер как заявку) ---
        y_real = pow(int(bid_value), self.server_rsa_e, self.server_rsa_n)

        # --- Фейковый y, от которого считаем подпись ---
        y_fake = pow(int(fake_signed_value), self.server_rsa_e, self.server_rsa_n)

        # <<< ПОДПИСЫВАЕМ НЕ ТО >>>
        msg_bytes = f"y={y_fake}".encode("utf-8")

        r, s, h = self._gost_sign_message(
            msg_bytes,
            self.gost_keys.p,
            self.gost_keys.q,
            self.gost_keys.a,
            self.gost_keys.x
        )

        payload = {
            "type": "BID",
            "id": self.participant_id,

            # <<< ВАЖНО: bid_value и y ОТ РЕАЛЬНОЙ СТАВКИ >>>
            "bid_value": int(bid_value),
            "y": int(y_real),

            # <<< А h,r,s ОТ ДРУГОГО y >>>
            "h": int(h),
            "r": int(r),
            "s": int(s),
        }

        if not self._send_json(payload):
            return None

        return self._recv_json(timeout=5.0)

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

    def start_push_listener(self, on_bids_published=None, on_results_published=None, on_bidding_status=None,
                            on_log=None):
        self._on_bids_published = on_bids_published
        self._on_results_published = on_results_published
        self._on_bidding_status = on_bidding_status
        self._on_push_log = on_log
        # Reader-thread поднимаем только после завершения "handshake" (HELLO/REGISTER/AUTH),
        # чтобы исключить гонки за синхронные ответы протокола.
        if self.running and (self._reader_thread is None or not self._reader_thread.is_alive()):
            self._start_reader_thread()
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
