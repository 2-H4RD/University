# server/server_network.py
# Сетевое ядро сервера электронных торгов.
#
# Функциональность:
#   - UDP discovery: поиск сервера клиентами в LAN;
#   - TCP-сервер: приём подключений участников;
#   - Простейший текстовый протокол JSON по строкам;
#   - Обработка:
#       HELLO           / WELCOME
#       REGISTER_KEYS   / REGISTER_RESULT
#       AUTH_REQUEST    / AUTH_CHALLENGE
#       AUTH_RESPONSE   / AUTH_RESULT
#       BID             / BID_RESULT
#
# Вся логика максимально «болтлива» — подробные print(...) для трассировки.
#
# Дальнейшая интеграция с GUI:
#   - GUI создаёт объект AuctionServerCore,
#   - настраивает список допущенных идентификаторов,
#   - включает/выключает окна аутентификации и торгов,
#   - подписывается на колбэки on_log, on_auth_update, on_bid_received.


import socket
import threading
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Tuple, List
from common.gost_hash_3411 import gost3411_94_full


# Те же константы, что и у клиента
DISCOVERY_PORT = 50050
DISCOVERY_MAGIC = "AUCTION_DISCOVER"
DISCOVERY_RESPONSE_MAGIC = "AUCTION_HERE"

DEFAULT_TCP_PORT = 50051

# Типы колбэков для интеграции с GUI
LogCallback = Callable[[str], None]
AuthUpdateCallback = Callable[[str, bool], None]      # (participant_id, authenticated)
BidReceivedCallback = Callable[[str, int, int, int, int, int], None]
# (participant_id, bid_value, y, h, r, s)


@dataclass
class ParticipantInfo:
    """Информация о конкретном участнике торгов на сервере."""
    participant_id: str
    rsa_n: Optional[int] = None
    rsa_e: Optional[int] = None
    gost_p: Optional[int] = None
    gost_q: Optional[int] = None
    gost_a: Optional[int] = None
    gost_y: Optional[int] = None

    registered: bool = False          # прошёл REGISTER_KEYS
    authenticated: bool = False       # прошёл аутентификацию
    last_challenge: Optional[int] = None  # r от сервера для RSA-аутентификации
    send_fn: Optional[Callable[[dict], None]] = None


@dataclass
class AuctionServerCore:
    """
    Ядро сервера торгов.

    Основные публичные методы:
      - start() / stop()
      - set_allowed_ids(list[str])
      - set_auth_window_open(bool)
      - set_bidding_open(bool)
      - get_current_bids() -> List[...]
    """

    host: str = "0.0.0.0"
    tcp_port: int = DEFAULT_TCP_PORT

    # --- RSA-ключи организатора торгов (сервер) ---
    rsa_n: Optional[int] = None
    rsa_e: Optional[int] = None
    rsa_d: Optional[int] = None

    # --- Управляющие флаги (GUI может менять) ---
    allowed_ids: List[str] = field(default_factory=list)  # список ID из опубликованного реестра
    auth_window_open: bool = False                        # окно аутентификации открыто?
    bidding_open: bool = False                            # окно подачи заявок открыто?
    stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    # --- Колбэки для GUI (опциональные) ---
    on_log: Optional[LogCallback] = None
    on_auth_update: Optional[AuthUpdateCallback] = None
    on_bid_received: Optional[BidReceivedCallback] = None


    # --- Внутреннее состояние ---
    _participants: Dict[str, ParticipantInfo] = field(default_factory=dict, init=False)
    _bids: List[dict] = field(default_factory=list, init=False)

    _udp_thread: Optional[threading.Thread] = field(default=None, init=False)
    _tcp_thread: Optional[threading.Thread] = field(default=None, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    _tcp_sock: Optional[socket.socket] = field(default=None, init=False)

    # ------------------- Вспомогательные методы логирования ------------------- #

    def _log(self, msg: str):
        print(msg)
        if self.on_log:
            try:
                self.on_log(msg)
            except Exception:
                # Не даём GUI-колбэку уронить сервер
                pass

    def run_blocking(self):
        """
        Запускает сетевые потоки (TCP/UDP) и блокируется, пока не вызван stop().
        Используется GUI, который запускает это в отдельном потоке.
        """
        # Запускаем сервер (создаёт и стартует tcp_thread/udp_thread)
        self.start()
        self._log("[SERVER] AuctionServerCore.run_blocking(): сервер запущен, ждём stop_event...")

        try:
            # Блокирующий цикл — пока stop_event не установлен
            while not self.stop_event.is_set():
                time.sleep(0.1)
        finally:
            self._log("[SERVER] AuctionServerCore.run_blocking(): завершение работы.")

    # ------------------- Управляющие методы для GUI ------------------- #

    def set_allowed_ids(self, ids: List[str]):
        """Установить список идентификаторов, допущенных к участию в торгах."""
        self.allowed_ids = list(ids)
        self._log(f"[SERVER] Обновлён список разрешённых ID: {self.allowed_ids}")

    def set_auth_window_open(self, is_open: bool):
        self.auth_window_open = is_open
        self._log(f"[SERVER] Окно аутентификации: {'ОТКРЫТО' if is_open else 'ЗАКРЫТО'}")

    def set_bidding_open(self, is_open: bool):
        self.bidding_open = is_open
        self._log(f"[SERVER] Окно приёма заявок: {'ОТКРЫТО' if is_open else 'ЗАКРЫТО'}")

    def get_current_bids(self) -> List[dict]:
        """Вернуть копию списка всех принятых заявок."""
        return list(self._bids)

    # ------------------- Жизненный цикл сервера ------------------- #

    def start(self):
        """Запуск UDP discovery и TCP-сервера в фоновых потоках."""
        self._stop_event.clear()
        self._log("[SERVER] === ЗАПУСК СЕТЕВОГО СЕРВЕРА ТОРГОВ ===")

        # UDP discovery
        self._udp_thread = threading.Thread(target=self._udp_discovery_loop, daemon=True)
        self._udp_thread.start()

        # TCP listener
        self._tcp_thread = threading.Thread(target=self._tcp_listen_loop, daemon=True)
        self._tcp_thread.start()

    def stop(self):
        """Остановка всех потоков и закрытие сокетов."""
        self._log("[SERVER] === ОСТАНОВКА СЕРВЕРА ===")
        self._stop_event.set()

        try:
            if self._tcp_sock:
                self._tcp_sock.close()
        except Exception:
            pass

        # Потоки помечены daemon=True, так что при завершении процесса они умрут.
        # Можно дополнительно join'ить их, если нужно аккуратное завершение.

    # ------------------- UDP discovery ------------------- #

    def _udp_discovery_loop(self):
        """
        Слушает broadcast-пакеты на DISCOVERY_PORT.
        На 'AUCTION_DISCOVER' отвечает 'AUCTION_HERE <tcp_port>'.
        """
        self._log(f"[SERVER][UDP] Старт discovery loop на порту {DISCOVERY_PORT}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", DISCOVERY_PORT))
        except Exception as ex:
            self._log(f"[SERVER][UDP][ERROR] Не удалось привязать сокет: {ex}")
            sock.close()
            return

        sock.settimeout(1.0)

        while not self._stop_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                continue
            except Exception as ex:
                self._log(f"[SERVER][UDP][ERROR] recvfrom: {ex}")
                break

            try:
                text = data.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue

            self._log(f"[SERVER][UDP] Получено '{text}' от {addr}")

            if text == DISCOVERY_MAGIC:
                resp = f"{DISCOVERY_RESPONSE_MAGIC} {self.tcp_port}"
                try:
                    sock.sendto(resp.encode("utf-8"), addr)
                    self._log(f"[SERVER][UDP] Отправлен ответ discovery '{resp}' -> {addr}")
                except Exception as ex:
                    self._log(f"[SERVER][UDP][ERROR] sendto: {ex}")

        sock.close()
        self._log("[SERVER][UDP] Discovery loop завершён.")

    # ------------------- TCP-сервер ------------------- #

    def _tcp_listen_loop(self):
        """
        Поднимает TCP-сервер, принимает подключения и для каждого
        запускает отдельный поток.
        """
        self._log(f"[SERVER][TCP] Старт listen loop на порту {self.tcp_port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_sock = sock
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.tcp_port))
            sock.listen(5)
        except Exception as ex:
            self._log(f"[SERVER][TCP][ERROR] Не удалось запустить сервер: {ex}")
            try:
                sock.close()
            except Exception:
                pass
            self._tcp_sock = None
            return

        sock.settimeout(1.0)

        while not self._stop_event.is_set():
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            except Exception as ex:
                self._log(f"[SERVER][TCP][ERROR] accept: {ex}")
                break

            self._log(f"[SERVER][TCP] Новое подключение от {addr}")
            th = threading.Thread(target=self._client_handler, args=(conn, addr), daemon=True)
            th.start()

        try:
            sock.close()
        except Exception:
            pass
        self._tcp_sock = None
        self._log("[SERVER][TCP] Listen loop завершён.")

    # ------------------- Работа с одним клиентом ------------------- #

    def _client_handler(self, conn: socket.socket, addr: Tuple[str, int]):
        """
        Обработчик одного TCP-клиента.
        Читает строки JSON, обрабатывает, отправляет ответы.
        """
        file_r = conn.makefile("r", encoding="utf-8", newline="\n")
        file_w = conn.makefile("w", encoding="utf-8", newline="\n")

        participant_id: Optional[str] = None

        def send_json(obj: dict):
            try:
                line = json.dumps(obj, ensure_ascii=False)
                file_w.write(line + "\n")
                file_w.flush()
                self._log(f"[SERVER -> {addr}] {line}")
            except Exception as ex:
                self._log(f"[SERVER][ERROR] Отправка в {addr}: {ex}")

        try:
            while not self._stop_event.is_set():
                line = file_r.readline()
                if not line:
                    self._log(f"[SERVER][TCP] Клиент {addr} закрыл соединение.")
                    break

                line = line.strip()
                if not line:
                    continue

                self._log(f"[{addr} -> SERVER] {line}")

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError as ex:
                    self._log(f"[SERVER][ERROR] Некорректный JSON от {addr}: {ex}")
                    continue

                mtype = msg.get("type")

                # --- HELLO ---
                if mtype == "HELLO":
                    role = msg.get("role")
                    participant_id = msg.get("id")
                    self._handle_hello(send_json, role, participant_id)

                # --- REGISTER_KEYS ---
                elif mtype == "REGISTER_KEYS":
                    pid = msg.get("id")
                    rsa = msg.get("rsa") or {}
                    gost = msg.get("gost") or {}
                    self._handle_register_keys(send_json, pid, rsa, gost)

                # --- AUTH_REQUEST ---
                elif mtype == "AUTH_REQUEST":
                    pid = msg.get("id")
                    self._handle_auth_request(send_json, pid)

                # --- AUTH_RESPONSE ---
                elif mtype == "AUTH_RESPONSE":
                    pid = msg.get("id")
                    s_val = msg.get("s")
                    self._handle_auth_response(send_json, pid, s_val)

                # --- BID ---
                elif mtype == "BID":
                    pid = msg.get("id")
                    bid_value = msg.get("bid_value")
                    y_val = msg.get("y")
                    h_val = msg.get("h")
                    r_val = msg.get("r")
                    s_val = msg.get("s")
                    self._handle_bid(send_json, pid, bid_value, y_val, h_val, r_val, s_val)

                else:
                    self._log(f"[SERVER][WARN] Неизвестный тип сообщения от {addr}: {mtype}")

        except Exception as ex:
            self._log(f"[SERVER][ERROR] Исключение в обработчике клиента {addr}: {ex}")
        finally:
            try:
                file_r.close()
            except Exception:
                pass
            try:
                file_w.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            self._log(f"[SERVER][TCP] Соединение с {addr} закрыто.")

    def _gost_hash_to_int_q(message: bytes, q: int) -> int:
        H_be = gost3411_94_full(message)
        h = int.from_bytes(H_be[::-1], "big") % q
        return h or 1

    # ------------------- Обработчики сообщений протокола ------------------- #

    def _get_or_create_participant(self, participant_id: str) -> ParticipantInfo:
        if participant_id not in self._participants:
            self._participants[participant_id] = ParticipantInfo(participant_id=participant_id)
        return self._participants[participant_id]

    def _is_id_allowed(self, participant_id: str) -> bool:
        """Проверка, есть ли ID в опубликованном реестре (allowed_ids)."""
        if not self.allowed_ids:
            # если список пуст, для отладки можно пока разрешить всех
            return True
        return participant_id in self.allowed_ids

    # --- HELLO --- #
    def _handle_hello(self, send_json, role: str, participant_id: Optional[str]):
        if role != "member" or not participant_id:
            self._log(f"[SERVER][HELLO] Неверные параметры: role={role}, id={participant_id}")
            send_json({
                "type": "WELCOME",
                "ok": False,
                "message": "Некорректный HELLO."
            })
            return

        self._log(f"[SERVER][HELLO] Подключился участник id='{participant_id}', role='{role}'")

        # Проверка на соответствие реестру
        if not self._is_id_allowed(participant_id):
            self._log(f"[SERVER][HELLO] Участник '{participant_id}' не в опубликованном реестре.")
            send_json({
                "type": "WELCOME",
                "ok": False,
                "message": "Ваш идентификатор отсутствует в опубликованном реестре."
            })
            return

        # Создаём/обновляем запись участника
        info = self._get_or_create_participant(participant_id)
        info.send_fn = send_json
        self._log(f"[SERVER][HELLO] Участник '{participant_id}' принят, можно регистрировать ключи.")

        # Добавим открытый ключ сервера, чтобы клиент мог шифровать ставки
        welcome_payload = {
            "type": "WELCOME",
            "ok": True,
            "message": "HELLO принят. Ожидается регистрация ключей.",
        }
        if self.rsa_n and self.rsa_e:
            welcome_payload["server_rsa_n"] = self.rsa_n
            welcome_payload["server_rsa_e"] = self.rsa_e
        else:
            # если ключи не заданы, клиент увидит, что ставки шифровать пока нечем
            welcome_payload["server_rsa_n"] = None
            welcome_payload["server_rsa_e"] = None

        send_json(welcome_payload)

    # --- REGISTER_KEYS --- #
    def _handle_register_keys(self, send_json, pid: str, rsa: dict, gost: dict):
        if not pid:
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": "Нет id участника."})
            return

        if not self._is_id_allowed(pid):
            reason = "Идентификатор не в опубликованном реестре."
            self._log(f"[SERVER][REGISTER_KEYS] {pid}: {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return

        info = self._get_or_create_participant(pid)

        try:
            info.rsa_n = int(rsa.get("n"))
            info.rsa_e = int(rsa.get("e"))
            info.gost_p = int(gost.get("p"))
            info.gost_q = int(gost.get("q"))
            info.gost_a = int(gost.get("a"))
            info.gost_y = int(gost.get("y"))
        except Exception as ex:
            reason = f"Ошибка при разборе ключей: {ex}"
            self._log(f"[SERVER][REGISTER_KEYS] {pid}: {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return

        # Простая проверка на заполненность
        if not info.rsa_n or not info.rsa_e:
            reason = "Некорректные RSA-ключи."
            self._log(f"[SERVER][REGISTER_KEYS] {pid}: {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return
        if not info.gost_p or not info.gost_q or not info.gost_a or not info.gost_y:
            reason = "Некорректные ГОСТ-ключи."
            self._log(f"[SERVER][REGISTER_KEYS] {pid}: {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return

        info.registered = True
        self._log(f"[SERVER][REGISTER_KEYS] Участник '{pid}' зарегистрировал ключи.")
        send_json({"type": "REGISTER_RESULT", "ok": True, "reason": ""})

    # --- AUTH_REQUEST --- #
    def _handle_auth_request(self, send_json, pid: str):
        if not pid:
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": "Нет id участника."})
            return

        if not self.auth_window_open:
            reason = "Окно аутентификации закрыто."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            # В примере нам нужно, чтобы клиент видел это явно
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if not self._is_id_allowed(pid):
            reason = "Идентификатор не в опубликованном реестре."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        info = self._get_or_create_participant(pid)
        if not info.registered or not info.rsa_n or not info.rsa_e:
            reason = "Участник не зарегистрировал ключи."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        # Выбираем случайный r: 1 < r < n (для простоты — псевдо-r)
        # В production лучше использовать криптогенератор.
        n = info.rsa_n
        import random
        r = random.randrange(2, n - 1)
        info.last_challenge = r

        self._log(f"[SERVER][AUTH_REQUEST] {pid}: выдаём челлендж r={r}")
        send_json({
            "type": "AUTH_CHALLENGE",
            "id": pid,
            "r": r
        })

    # --- AUTH_RESPONSE --- #
    def _handle_auth_response(self, send_json, pid: str, s_val):
        if not pid:
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": "Нет id участника."})
            return

        info = self._participants.get(pid)
        if not info:
            reason = "Участник не известен серверу."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if not info.registered or not info.rsa_n or not info.rsa_e:
            reason = "Участник не зарегистрировал ключи."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if info.last_challenge is None:
            reason = "Сервер не выдавал челлендж этому участнику."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if not isinstance(s_val, int):
            reason = "Некорректный формат ответа s."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        # Проверяем, что s^e mod n == r
        n = info.rsa_n
        e = info.rsa_e
        r = info.last_challenge

        self._log(f"[SERVER][AUTH_RESPONSE] {pid}: проверяем s^e mod n == r ...")
        try:
            r_check = pow(s_val, e, n)
        except Exception as ex:
            reason = f"Ошибка при вычислении pow(s,e,n): {ex}"
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if r_check != r:
            reason = "Аутентификация не пройдена (s^e mod n != r)."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        info.authenticated = True
        info.last_challenge = None
        self._log(f"[SERVER][AUTH_RESPONSE] {pid}: Аутентификация УСПЕШНА.")
        send_json({"type": "AUTH_RESULT", "ok": True, "reason": ""})

        if self.on_auth_update:
            try:
                self.on_auth_update(pid, True)
            except Exception:
                pass

    # --- BID --- #
    def _handle_bid(self, send_json, pid: str,
                    bid_value, y_val, h_val, r_val, s_val):
        if not pid:
            send_json({"type": "BID_RESULT", "ok": False, "reason": "Нет id участника."})
            return

        if not self.bidding_open:
            reason = "Окно приёма заявок закрыто."
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        info = self._participants.get(pid)
        if not info:
            reason = "Участник не известен серверу."
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        if not info.authenticated:
            reason = "Участник не прошёл аутентификацию."
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        # --- Приводим поля к int ---
        try:
            x_int = int(bid_value) if bid_value is not None else None
            y_int = int(y_val)
            h_int = int(h_val)
            r_int = int(r_val)
            s_int = int(s_val)
        except Exception as ex:
            reason = f"Некорректные числовые поля BID: {ex}"
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        if x_int is None:
            reason = "Сервер не получил исходное значение ставки bid_value."
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        # --- Проверка хэша h ---
        msg_bytes = f"bid={x_int}".encode("utf-8")
        h_check = _gost_hash_to_int_q(msg_bytes, info.gost_q)

        if h_check != h_int:
            reason = "Хэш заявки не совпадает с переданным h (возможна подмена)."
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        # --- Проверка ГОСТ-подписи ---
        p = info.gost_p
        q = info.gost_q
        a = info.gost_a
        y_pub = info.gost_y

        try:
            # Стандартная проверка:
            # v = a^s * y^{-r} (mod p), r' = v mod q, должно быть r' == r
            v1 = pow(a, s_int, p)
            # y^{-r} mod p = y^{(p-1-r) mod (p-1)}, но удобнее использовать q:
            y_inv = pow(y_pub, q - 1 - r_int, p)
            v = (v1 * y_inv) % p
            r_check = v % q
        except Exception as ex:
            reason = f"Ошибка при проверке ГОСТ-подписи: {ex}"
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        if r_check != r_int:
            reason = "ГОСТ-подпись заявки неверна."
            self._log(f"[SERVER][BID] {pid}: {reason}")
            send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            return

        # --- Если мы здесь — заявка корректна и подписана ---
        self._log(f"[SERVER][BID] {pid}: заявка принята (подпись корректна).")

        self._bids.append(
            {
                "id": pid,
                "bid_value": x_int,
                "y": y_int,
                "h": h_int,
                "r": r_int,
                "s": s_int,
            }
        )

        # Уведомить GUI
        if self.on_bid_received:
            try:
                self.on_bid_received(pid, x_int, y_int, h_int, r_int, s_int)
            except Exception:
                pass

        send_json({"type": "BID_RESULT", "ok": True, "reason": ""})

    def start_auth(self):
        self.set_auth_window_open(True)

    def stop_auth(self):
        self.set_auth_window_open(False)

    def set_authentication_active(self, flag: bool):
        self.set_auth_window_open(flag)

    def set_bidding_active(self, flag: bool):
        self.set_bidding_open(flag)

    def shutdown(self):
        self.stop()
        self.stop_event.set()

    def decrypt_and_choose_winner(self):
        results = []
        winner_id = None
        max_bid = -1

        for bid in self._bids:
            pid = bid["id"]
            y = bid["y"]
            s = bid["s"]

            # RSA-расшифровка
            try:
                x = pow(y, self.rsa_d, self.rsa_n)
            except Exception:
                x = None

            rec = {"id": pid, "y": y, "s": s, "x": x, "winner": False}
            results.append(rec)

            if x is not None and x > max_bid:
                max_bid = x
                winner_id = pid

        # помечаем победителя
        for rec in results:
            if rec["id"] == winner_id:
                rec["winner"] = True

        return results

    def broadcast_encrypted_bids(self):
        """
        Отправить всем участникам список зашифрованных заявок:
        [{id, y, s}, ...]
        """
        payload = []
        for bid in self._bids:
            payload.append({
                "id": bid["id"],
                "y": bid["y"],
                "s": bid["s"],
            })

        self._log(f"[SERVER] Публикуем зашифрованные заявки ({len(payload)} шт.) всем участникам")

        for info in self._participants.values():
            if info.send_fn is None:
                continue
            try:
                info.send_fn({
                    "type": "BIDS_PUBLISHED",
                    "bids": payload,
                })
            except Exception as ex:
                self._log(f"[SERVER][BIDS_PUBLISHED][ERROR] отправка участнику {info.participant_id}: {ex}")

    def broadcast_results(self, results: List[dict]):
        """
        Публикация расшифрованных результатов:
        [{id, x}, ...] всем участникам.
        """
        payload = []
        for rec in results:
            payload.append({
                "id": rec.get("id"),
                "x": rec.get("x"),
            })

        self._log(f"[SERVER] Публикуем расшифрованные результаты ({len(payload)} шт.) всем участникам")

        for info in self._participants.values():
            if info.send_fn is None:
                continue
            try:
                info.send_fn({
                    "type": "RESULTS_PUBLISHED",
                    "results": payload,
                })
            except Exception as ex:
                self._log(f"[SERVER][RESULTS_PUBLISHED][ERROR] отправка участнику {info.participant_id}: {ex}")



# ------------------- Пример standalone-запуска ------------------- #

if __name__ == "__main__":
    # Небольшой тест без GUI: сервер слушает discovery+TCP,
    # допускает все ID, окно аутентификации и торгов открыты.
    server = AuctionServerCore()
    server.set_allowed_ids([])            # [] => разрешаем всех для отладки
    server.set_auth_window_open(True)
    server.set_bidding_open(True)
    server.start()

    print("Сервер запущен. Нажмите Ctrl+C для выхода.")
    try:
        while True:
            # Просто ждём; сервер работает в фоновых потоках.
            threading.Event().wait(1.0)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: остановка сервера...")
        server.stop()
