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
from gost_hash_3411 import gost3411_94_full
from num_generator import secure_random_int
from rsa_utils import (
    ffs_generate_secret_and_public,
    ffs_commit,
    ffs_respond,
    ffs_verify,
)


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
    # (опционально) публичный RSA-ключ участника — больше НЕ используется для аутентификации,
    # оставляем поле только ради обратной совместимости на время миграции.
    rsa_n: Optional[int] = None
    rsa_e: Optional[int] = None

    # Параметры ГОСТ (подпись) (общие p,q,a приходят от сервера; y — публичный ключ участника)
    gost_p: Optional[int] = None
    gost_q: Optional[int] = None
    gost_a: Optional[int] = None
    gost_y: Optional[int] = None

    # --- Параметры FFS участника (публичный ключ v; модуль n общий, берём rsa_n сервера) ---
    ffs_v: Optional[int] = None

    # --- Состояние FFS-аутентификации (участник -> сервер) ---
    last_z: Optional[int] = None  # commitment z = r^2 mod n
    last_b: Optional[int] = None  # challenge bit b

    # --- Счётчики раундов FFS (участник -> сервер) ---
    ffs_rounds_total: int = 16
    ffs_round_done: int = 0
    ffs_round_pending: Optional[int] = None  # какой раунд сейчас ожидает AUTH_RESPONSE

    # --- Счётчики раундов FFS (сервер -> участник) ---
    srv_rounds_total: int = 16
    srv_round_done: int = 0
    srv_round_pending: Optional[int] = None  # какой раунд сейчас ожидает SERVER_AUTH_CHALLENGE

    # --- Состояние FFS-аутентификации (сервер -> участник) ---
    srv_r: Optional[int] = None
    srv_z: Optional[int] = None
    srv_b: Optional[int] = None

    registered: bool = False  # прошёл REGISTER_KEYS
    authenticated: bool = False  # прошёл FFS-аутентификацию (участник -> сервер)
    mutual_confirmed: bool = False  # клиент подтвердил успешную проверку сервера (сервер -> клиент)

    # --- Состояние для аутентификации Шнорра (участник -> сервер) ---
    last_t: Optional[int] = None  # commitment t = a^v mod p
    last_c: Optional[int] = None  # challenge c

    # --- Состояние для аутентификации Шнорра (сервер -> участник) ---
    srv_v: Optional[int] = None  # одноразовый секрет v (на период сеанса)
    srv_t: Optional[int] = None  # commitment t_srv
    srv_c: Optional[int] = None  # challenge, полученный от клиента

    send_fn: Optional[Callable[[dict], None]] = None

    # --- Schnorr mutual auth (server -> client) ---
    srv_auth_v: Optional[int] = None  # временный секрет v_srv
    srv_auth_t: Optional[int] = None  # commitment t_srv = g^v_srv mod p
    srv_auth_c: Optional[int] = None  # challenge c_srv (для отладки)


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

    # --- FFS-ключи организатора торгов (сервер) ---
    # Используем тот же модуль n, что и для RSA-шифрования заявок.
    ffs_s: Optional[int] = None  # секрет s (НЕ публикуется)
    ffs_v: Optional[int] = None  # публичный v

    # --- ГОСТ-ключи организатора торгов (сервер) ---
    gost_p: Optional[int] = None
    gost_q: Optional[int] = None
    gost_a: Optional[int] = None

    # --- Ключи Шнорра сервера для взаимной аутентификации ---
    schnorr_x: Optional[int] = None  # секретный ключ сервера
    schnorr_y: Optional[int] = None  # публичный ключ сервера (a^x mod p)

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

    def __post_init__(self):
        # В server_main.py параметры ГОСТ (p,q,a) часто передаются в конструктор напрямую (через поля dataclass),
        # поэтому set_gost_params() может не вызываться. В таком случае ключи Шнорра для взаимной аутентификации
        # нужно сгенерировать здесь.
        if self.gost_p and self.gost_q and self.gost_a and (self.schnorr_x is None or self.schnorr_y is None):
            # set_gost_params() помимо установки p,q,a также формирует (schnorr_x, schnorr_y).
            self.set_gost_params(int(self.gost_p), int(self.gost_q), int(self.gost_a))

        # FFS-ключи: если RSA n уже задан, генерируем (s, v) один раз на запуск.
        if self.rsa_n and (self.ffs_s is None or self.ffs_v is None):
            try:
                self.ffs_s, self.ffs_v = ffs_generate_secret_and_public(int(self.rsa_n))
                self._log('[SERVER] Сгенерированы FFS-ключи сервера (s скрыт, v публикуется в WELCOME).')
            except Exception as ex:
                self.ffs_s = None
                self.ffs_v = None
                self._log(f'[SERVER][ERROR] Не удалось сгенерировать FFS-ключи сервера: {ex}')

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
        self._broadcast_bidding_status(is_open)

    def get_current_bids(self) -> List[dict]:
        """Вернуть копию списка всех принятых заявок."""
        return list(self._bids)

    def set_gost_params(self, p: int, q: int, a: int):
        self.gost_p, self.gost_q, self.gost_a = p, q, a
        self._log(f"[SERVER] Установлены параметры ГОСТ: p(bitlen)={p.bit_length()}, q(bitlen)={q.bit_length()}")
        # Важно для учебного режима: GUI может заранее сгенерировать и «вбить» schnorr_x/schnorr_y.
        # В таком случае НЕ перегенерируем ключи, если они согласованы с (p,q,a).
        if self.schnorr_x is not None and self.schnorr_y is not None:
            try:
                expected_y = pow(a, int(self.schnorr_x), p)
                if int(self.schnorr_y) == expected_y:
                    self._log("[SERVER] Ключи Шнорра сервера уже заданы (GUI) и согласованы с текущими параметрами.")
                    return
                self._log("[SERVER][WARN] Заданные ключи Шнорра не согласованы с новыми (p,q,a). Перегенерируем.")
            except Exception:
                self._log("[SERVER][WARN] Не удалось проверить согласованность ключей Шнорра. Перегенерируем.")
                # Если ключей нет (или они не согласованы) — генерируем заново
        try:
            self.schnorr_x = secure_random_int(1, q - 1)
            self.schnorr_y = pow(a, self.schnorr_x, p)
            self._log("[SERVER] Сгенерированы ключи Шнорра сервера (x_srv скрыт, y_srv опубликован в WELCOME).")
        except Exception as ex:
            self.schnorr_x = None
            self.schnorr_y = None
            self._log(f"[SERVER][ERROR] Не удалось сгенерировать ключи Шнорра сервера: {ex}")

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
            except OSError as ex:
                # Windows: WinError 10054 может прилетать на UDP recvfrom из-за ICMP "Port unreachable"
                # Это не критично — discovery должен продолжать работать.
                if getattr(ex, "winerror", None) == 10054:
                    self._log(f"[SERVER][UDP][WARN] recvfrom WinError 10054 (игнорируем): {ex}")
                    continue
                self._log(f"[SERVER][UDP][ERROR] recvfrom: {ex}")
                continue
            except Exception as ex:
                self._log(f"[SERVER][UDP][ERROR] recvfrom: {ex}")
                continue

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
                    ffs = msg.get("ffs") or {}
                    self._handle_register_keys(send_json, pid, rsa, gost, ffs)

                # --- AUTH_REQUEST ---
                elif mtype == "AUTH_REQUEST":
                    pid = msg.get("id")
                    z_val = msg.get("z")
                    round_no = msg.get("round")
                    rounds_total = msg.get("rounds")
                    self._handle_auth_request(send_json, pid, z_val, round_no, rounds_total)

                # --- AUTH_RESPONSE ---
                elif mtype == "AUTH_RESPONSE":
                    pid = msg.get("id")
                    resp_val = msg.get("resp")
                    round_no = msg.get("round")
                    self._handle_auth_response(send_json, pid, resp_val, round_no)

                # --- SERVER_AUTH_REQUEST (взаимная аутентификация: сервер доказывает клиенту) ---
                elif mtype == "SERVER_AUTH_REQUEST":
                    pid = msg.get("id")
                    round_no = msg.get("round")
                    rounds_total = msg.get("rounds")
                    self._handle_server_auth_request(send_json, pid, round_no, rounds_total)

                # --- SERVER_AUTH_CHALLENGE ---
                elif mtype == "SERVER_AUTH_CHALLENGE":
                    pid = msg.get("id")
                    b_val = msg.get("b")
                    round_no = msg.get("round")
                    self._handle_server_auth_challenge(send_json, pid, b_val, round_no)

                # --- MUTUAL_AUTH_CONFIRM (клиент подтверждает, что проверил сервер) ---
                elif mtype == "MUTUAL_AUTH_CONFIRM":
                    pid = msg.get("id")
                    ok_val = msg.get("ok")
                    reason = msg.get("reason", "")
                    self._handle_mutual_auth_confirm(send_json, pid, ok_val, reason)

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

    def _gost_hash_to_int_q(self, message: bytes, q: int) -> int:
        H_be = gost3411_94_full(message)
        h = int.from_bytes(H_be[::-1], "big") % q
        return h or 1

    # ------------------- Обработчики сообщений протокола ------------------- #

    def _get_or_create_participant(self, participant_id: str) -> ParticipantInfo:
        if participant_id not in self._participants:
            self._participants[participant_id] = ParticipantInfo(participant_id=participant_id)
        return self._participants[participant_id]

    def _broadcast_bidding_status(self, is_open: bool):
        """PUSH всем клиентам: открыт/закрыт приём заявок."""
        payload = {"type": "BIDDING_STATUS", "open": bool(is_open)}

        sent = 0
        for info in self._participants.values():
            if info.send_fn is None:
                continue
            # Можно ограничить только аутентифицированными:
            # if not info.authenticated: continue
            try:
                info.send_fn(payload)
                sent += 1
            except Exception as ex:
                self._log(f"[SERVER][BIDDING_STATUS][ERROR] {info.participant_id}: {ex}")

        self._log(f"[SERVER] BIDDING_STATUS отправлен {sent} участникам (open={is_open}).")

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
            welcome_payload["server_ffs_n"] = self.rsa_n
            welcome_payload["server_ffs_v"] = self.ffs_v

        else:
            # если ключи не заданы, клиент увидит, что ставки шифровать пока нечем
            welcome_payload["server_rsa_n"] = None
            welcome_payload["server_rsa_e"] = None
            welcome_payload["server_ffs_n"] = None
            welcome_payload["server_ffs_v"] = None

        if not self.gost_p or not self.gost_q or not self.gost_a:
            welcome_payload["gost_p"] = None
            welcome_payload["gost_q"] = None
            welcome_payload["gost_a"] = None
            welcome_payload["server_schnorr_y"] = None

        else:
            welcome_payload["gost_p"] = self.gost_p
            welcome_payload["gost_q"] = self.gost_q
            welcome_payload["gost_a"] = self.gost_a
            welcome_payload["server_schnorr_y"] = self.schnorr_y
        send_json(welcome_payload)

    # --- REGISTER_KEYS --- #
    def _handle_register_keys(self, send_json, pid: str, rsa: dict, gost: dict, ffs: dict):
        """
        REGISTER_KEYS:
          - RSA: участник присылает свой публичный ключ (n,e)
          - ГОСТ: участник присылает ТОЛЬКО свой публичный ключ y
          - p,q,a генерируются сервером (self.gost_p/q/a) и общие для всех
        """
        # 0) Проверка ID
        if not pid:
            reason = "Пустой идентификатор участника."
            self._log(f"[SERVER][REGISTER_KEYS] {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return

        info = self._participants.get(pid)
        if info is None:
            # на всякий случай, но обычно info создаётся на HELLO
            info = ParticipantInfo(participant_id=pid)
            self._participants[pid] = info

        # 1) RSA pubkey участника (опционально; для аутентификации больше не используется)
        # Оставляем ради обратной совместимости: если клиент прислал — сохраним, если нет — это не ошибка.
        try:
            if rsa and rsa.get("n") is not None and rsa.get("e") is not None:
                rsa_n = int(rsa.get("n"))
                rsa_e = int(rsa.get("e"))
                if rsa_n <= 0 or rsa_e <= 0:
                    raise ValueError("RSA n/e должны быть положительными.")
                info.rsa_n = rsa_n
                info.rsa_e = rsa_e
            else:
                info.rsa_n = None
                info.rsa_e = None
        except Exception as ex:
            reason = f"Некорректные RSA-ключи участника: {ex}"
            self._log(f"[SERVER][REGISTER_KEYS] {pid}: {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return

# 2) ГОСТ параметры должны быть установлены на сервере
        if not self.gost_p or not self.gost_q or not self.gost_a:
            reason = "На сервере не заданы параметры ГОСТ (p,q,a)."
            self._log(f"[SERVER][REGISTER_KEYS] {pid}: {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return

        # 3) ГОСТ y участника
        try:
            y_pub = int(gost.get("y"))
            if y_pub <= 0:
                raise ValueError("ГОСТ y должен быть положительным.")
        except Exception as ex:
            reason = f"Некорректный ГОСТ-ключ участника y: {ex}"
            self._log(f"[SERVER][REGISTER_KEYS] {pid}: {reason}")
            send_json({"type": "REGISTER_RESULT", "ok": False, "reason": reason})
            return

        # сохраняем общие параметры ГОСТ в info

        # 3.1) FFS public key v участника (обязателен для новой схемы аутентификации)
        if self.rsa_n is None:
            reason = 'На сервере не задан RSA-модуль n (он же используется как модуль FFS).'
            self._log(f'[SERVER][REGISTER_KEYS] {pid}: {reason}')
            send_json({'type': 'REGISTER_RESULT', 'ok': False, 'reason': reason})
            return
        try:
            v_pub = int((ffs or {}).get('v'))
            if v_pub <= 0 or v_pub >= int(self.rsa_n):
                raise ValueError('FFS v вне диапазона (0 < v < n).')
            # v должен быть обратим по модулю n (иначе проверка невозможна)
            import math
            if math.gcd(v_pub, int(self.rsa_n)) != 1:
                raise ValueError('FFS v не взаимно просто с n (gcd(v,n) != 1).')
        except Exception as ex:
            reason = f'Некорректный публичный ключ FFS v: {ex}'
            self._log(f'[SERVER][REGISTER_KEYS] {pid}: {reason}')
            send_json({'type': 'REGISTER_RESULT', 'ok': False, 'reason': reason})
            return
        info.ffs_v = int(v_pub)
        # (можно не хранить, но у вас структура уже так устроена)
        info.gost_p = int(self.gost_p)
        info.gost_q = int(self.gost_q)
        info.gost_a = int(self.gost_a)
        info.gost_y = y_pub

        # 4) Регистрируем
        info.registered = True

        self._log(f"[SERVER][REGISTER_KEYS] Участник '{pid}' зарегистрировал ключи (ГОСТ + FFS).")
        send_json({"type": "REGISTER_RESULT", "ok": True, "reason": ""})

    # --- AUTH_REQUEST --- #
    def _handle_auth_request(self, send_json, pid: str, z_val, round_no=None, rounds_total=None):
        """
        FFS-аутентификация (участник -> сервер), раунд i из k.
        Клиент присылает commitment z = r^2 mod n.
        Сервер отвечает случайным битом b ∈ {0,1}.
        """
        if not pid:
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": "Нет id участника."})
            return

        if not self.auth_window_open:
            reason = "Окно аутентификации закрыто."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if not self._is_id_allowed(pid):
            reason = "Идентификатор не в опубликованном реестре."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if self.rsa_n is None:
            reason = "На сервере не задан модуль n (он же используется как модуль FFS)."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        info = self._get_or_create_participant(pid)

        if not info.registered or not info.gost_y or not info.gost_p or not info.gost_q or not info.gost_a:
            reason = "Участник не зарегистрировал ГОСТ-ключи."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if info.ffs_v is None:
            reason = "Участник не зарегистрировал публичный ключ FFS v."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        # раунды
        try:
            k = int(rounds_total) if rounds_total is not None else int(info.ffs_rounds_total)
            if k <= 0 or k > 1024:
                raise ValueError("rounds_total вне допустимого диапазона")
        except Exception:
            k = int(info.ffs_rounds_total) if info.ffs_rounds_total else 16

        try:
            i = int(round_no) if round_no is not None else (int(info.ffs_round_done) + 1)
        except Exception:
            i = int(info.ffs_round_done) + 1

        # если клиент начал заново с 1-го раунда — сбрасываем прогресс
        if i == 1:
            info.ffs_round_done = 0
            info.ffs_rounds_total = k
            info.ffs_round_pending = None
            info.last_z = None
            info.last_b = None
            info.authenticated = False
            info.mutual_confirmed = False

        expected = int(info.ffs_round_done) + 1
        if i != expected:
            reason = f"Неверный номер раунда: получено {i}, ожидалось {expected}."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason, "round": i})
            return

        if info.ffs_round_pending is not None or info.last_z is not None or info.last_b is not None:
            reason = "Предыдущий раунд не завершён (ожидается AUTH_RESPONSE)."
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason, "round": i})
            return

        # commitment z от клиента
        try:
            z = int(z_val)
            n = int(self.rsa_n)
            if z <= 0 or z >= n:
                raise ValueError("z вне допустимого диапазона (0 < z < n).")
        except Exception as ex:
            reason = f"Некорректный commitment z: {ex}"
            self._log(f"[SERVER][AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason, "round": i})
            return

        b = secure_random_int(0, 1)
        info.last_z = z
        info.last_b = b
        info.ffs_round_pending = i
        info.authenticated = False
        info.mutual_confirmed = False
        info.ffs_rounds_total = k

        self._log(f"[SERVER][AUTH_REQUEST] {pid}: раунд {i}/{k}: получили z={z}, выдаём challenge b={b}")
        send_json({"type": "AUTH_CHALLENGE", "id": pid, "b": b, "round": i, "rounds": k})

    # --- AUTH_RESPONSE --- #
    def _handle_auth_response(self, send_json, pid: str, resp_val, round_no=None):
        """
        FFS-аутентификация (участник -> сервер), раунд i из k.
        Клиент присылает ответ resp.
        Сервер проверяет корректность и накапливает успешные раунды.
        """
        if not pid:
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": "Нет id участника."})
            return

        info = self._participants.get(pid)
        if not info or not info.registered:
            reason = "Участник не зарегистрирован."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if self.rsa_n is None:
            reason = "На сервере не задан модуль n (он же используется как модуль FFS)."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if info.ffs_v is None:
            reason = "Нет публичного ключа FFS v участника."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        if info.last_z is None or info.last_b is None or info.ffs_round_pending is None:
            reason = "Нет активного challenge для участника (сначала AUTH_REQUEST)."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason})
            return

        i_expected = int(info.ffs_round_pending)
        if round_no is not None:
            try:
                i = int(round_no)
            except Exception:
                i = i_expected
            if i != i_expected:
                reason = f"Неверный номер раунда в AUTH_RESPONSE: получено {i}, ожидалось {i_expected}."
                self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
                send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason, "round": i})
                return
        else:
            i = i_expected

        k = int(info.ffs_rounds_total) if info.ffs_rounds_total else 16

        try:
            resp = int(resp_val)
            n = int(self.rsa_n)
            if resp <= 0 or resp >= n:
                raise ValueError("resp вне диапазона (0 < resp < n).")
        except Exception as ex:
            reason = f"Некорректный ответ resp: {ex}"
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: {reason}")
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason, "round": i})
            return

        z = int(info.last_z)
        b = int(info.last_b)
        v = int(info.ffs_v)
        n = int(self.rsa_n)

        ok = ffs_verify(z=z, resp=resp, b=b, v=v, n=n)
        if not ok:
            reason = "Аутентификация не пройдена (FFS-проверка не сошлась)."
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: раунд {i}/{k}: FAIL (b={b})")
            # сброс прогресса
            info.ffs_round_done = 0
            info.ffs_round_pending = None
            info.last_z = None
            info.last_b = None
            info.authenticated = False
            info.mutual_confirmed = False
            send_json({"type": "AUTH_RESULT", "ok": False, "reason": reason, "round": i, "rounds": k})
            return

        # раунд успешен
        info.last_z = None
        info.last_b = None
        info.ffs_round_pending = None
        info.ffs_round_done = int(info.ffs_round_done) + 1

        if info.ffs_round_done >= k:
            info.authenticated = True
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: раунд {i}/{k}: OK. ВСЕ РАУНДЫ ПРОЙДЕНЫ -> AUTHENTICATED.")
            send_json({"type": "AUTH_RESULT", "ok": True, "reason": "", "round": i, "rounds": k, "done": True})

            if self.on_auth_update:
                try:
                    self.on_auth_update(pid, True)
                except Exception:
                    pass
        else:
            next_round = int(info.ffs_round_done) + 1
            self._log(f"[SERVER][AUTH_RESPONSE] {pid}: раунд {i}/{k}: OK. Следующий раунд: {next_round}.")
            send_json({"type": "AUTH_RESULT", "ok": True, "reason": "", "round": i, "rounds": k, "done": False,
                       "next_round": next_round})

    # --- SERVER_AUTH_REQUEST / SERVER_AUTH_CHALLENGE --- #
    def _handle_server_auth_request(self, send_json, pid: str, round_no=None, rounds_total=None):
        """
        Взаимная аутентификация (сервер -> клиент) по FFS, раунд i из k.
        """
        if not pid:
            send_json({"type": "SERVER_AUTH_COMMIT", "ok": False, "reason": "Нет id участника."})
            return

        info = self._participants.get(pid)
        if not info or not info.authenticated:
            reason = "Сначала участник должен пройти аутентификацию (AUTH_*)."
            self._log(f"[SERVER][SERVER_AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "SERVER_AUTH_COMMIT", "ok": False, "reason": reason})
            return

        if self.rsa_n is None or self.ffs_s is None or self.ffs_v is None:
            reason = "На сервере не готовы FFS-ключи (n, s, v)."
            self._log(f"[SERVER][SERVER_AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "SERVER_AUTH_COMMIT", "ok": False, "reason": reason})
            return

        # раунды
        try:
            k = int(rounds_total) if rounds_total is not None else int(info.srv_rounds_total)
            if k <= 0 or k > 1024:
                raise ValueError("rounds_total вне допустимого диапазона")
        except Exception:
            k = int(info.srv_rounds_total) if info.srv_rounds_total else 16

        try:
            i = int(round_no) if round_no is not None else (int(info.srv_round_done) + 1)
        except Exception:
            i = int(info.srv_round_done) + 1

        # если клиент начал заново с 1-го раунда — сбрасываем прогресс server-auth
        if i == 1:
            info.srv_round_done = 0
            info.srv_round_pending = None
            info.srv_r = None
            info.srv_z = None
            info.srv_b = None
            info.mutual_confirmed = False
            info.srv_rounds_total = k

        expected = int(info.srv_round_done) + 1
        if i != expected:
            reason = f"Неверный номер раунда server-auth: получено {i}, ожидалось {expected}."
            self._log(f"[SERVER][SERVER_AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "SERVER_AUTH_COMMIT", "ok": False, "reason": reason, "round": i})
            return

        if info.srv_round_pending is not None or info.srv_r is not None or info.srv_z is not None:
            reason = "Предыдущий раунд server-auth не завершён (ожидается SERVER_AUTH_CHALLENGE)."
            self._log(f"[SERVER][SERVER_AUTH_REQUEST] {pid}: {reason}")
            send_json({"type": "SERVER_AUTH_COMMIT", "ok": False, "reason": reason, "round": i})
            return

        # commitment
        r_srv, z_srv = ffs_commit(int(self.rsa_n))
        info.srv_r = r_srv
        info.srv_z = z_srv
        info.srv_b = None
        info.srv_round_pending = i
        info.srv_rounds_total = k
        info.mutual_confirmed = False

        self._log(f"[SERVER][SERVER_AUTH_REQUEST] {pid}: раунд {i}/{k}: отправляем commitment z_srv={z_srv}.")
        send_json({"type": "SERVER_AUTH_COMMIT", "id": pid, "z": z_srv, "ok": True, "round": i, "rounds": k})

    def _handle_server_auth_challenge(self, send_json, pid: str, b_val, round_no=None):
        """
        Взаимная аутентификация (сервер -> клиент) по FFS, раунд i из k:
        получить бит b и отправить resp.
        """
        if not pid:
            send_json({"type": "SERVER_AUTH_RESPONSE", "ok": False, "reason": "Нет id участника."})
            return

        info = self._participants.get(pid)
        if not info or info.srv_r is None or info.srv_z is None or info.srv_round_pending is None:
            reason = "Нет активного server-auth сеанса (сначала SERVER_AUTH_REQUEST)."
            self._log(f"[SERVER][SERVER_AUTH_CHALLENGE] {pid}: {reason}")
            send_json({"type": "SERVER_AUTH_RESPONSE", "ok": False, "reason": reason})
            return

        if self.rsa_n is None or self.ffs_s is None:
            reason = "На сервере не готовы FFS-ключи."
            self._log(f"[SERVER][SERVER_AUTH_CHALLENGE] {pid}: {reason}")
            send_json({"type": "SERVER_AUTH_RESPONSE", "ok": False, "reason": reason})
            return

        i_expected = int(info.srv_round_pending)
        if round_no is not None:
            try:
                i = int(round_no)
            except Exception:
                i = i_expected
            if i != i_expected:
                reason = f"Неверный номер раунда в SERVER_AUTH_CHALLENGE: получено {i}, ожидалось {i_expected}."
                self._log(f"[SERVER][SERVER_AUTH_CHALLENGE] {pid}: {reason}")
                send_json({"type": "SERVER_AUTH_RESPONSE", "ok": False, "reason": reason, "round": i})
                return
        else:
            i = i_expected

        k = int(info.srv_rounds_total) if info.srv_rounds_total else 16

        try:
            b = int(b_val)
            if b not in (0, 1):
                raise ValueError("b must be 0 or 1")
        except Exception as ex:
            reason = f"Некорректный бит challenge b: {ex}"
            self._log(f"[SERVER][SERVER_AUTH_CHALLENGE] {pid}: {reason}")
            send_json({"type": "SERVER_AUTH_RESPONSE", "ok": False, "reason": reason, "round": i, "rounds": k})
            return

        resp = ffs_respond(r=int(info.srv_r), s=int(self.ffs_s), b=b, n=int(self.rsa_n))

        # очищаем одноразовое состояние и фиксируем прогресс
        info.srv_r = None
        info.srv_z = None
        info.srv_b = None
        info.srv_round_pending = None
        info.srv_round_done = int(info.srv_round_done) + 1

        done = (info.srv_round_done >= k)
        self._log(f"[SERVER][SERVER_AUTH_CHALLENGE] {pid}: раунд {i}/{k}: отправляем resp (b={b}), done={done}.")
        send_json({"type": "SERVER_AUTH_RESPONSE", "id": pid, "resp": resp, "ok": True, "round": i, "rounds": k,
                   "done": done})

    def _handle_mutual_auth_confirm(self, send_json, pid: str, ok_val, reason: str):
        """Клиент сообщает серверу результат проверки server-auth."""
        if not pid:
            send_json({"type": "MUTUAL_AUTH_RESULT", "ok": False, "reason": "Нет id участника."})
            return
        info = self._participants.get(pid)
        if not info or not info.authenticated:
            r = "Участник не аутентифицирован на сервере."
            self._log(f"[SERVER][MUTUAL_AUTH_CONFIRM] {pid}: {r}")
            send_json({"type": "MUTUAL_AUTH_RESULT", "ok": False, "reason": r})
            return
        # Требуем, чтобы клиент реально прошёл k раундов проверки сервера (иначе confirm преждевременен)
        k = int(info.srv_rounds_total) if info.srv_rounds_total else 16
        if int(info.srv_round_done) < k:
            r = f"Клиент подтвердил server-auth слишком рано: выполнено {info.srv_round_done}/{k} раундов."
            self._log(f"[SERVER][MUTUAL_AUTH_CONFIRM] {pid}: {r}")
            send_json({"type": "MUTUAL_AUTH_RESULT", "ok": False, "reason": r})
            return
        ok = bool(ok_val)
        if not ok:
            # Клиент не доверяет серверу — считаем сессию невалидной
            info.mutual_confirmed = False
            info.authenticated = False
            r = reason or "Клиент не подтвердил аутентичность сервера."
            self._log(f"[SERVER][MUTUAL_AUTH_CONFIRM] {pid}: FAIL: {r}")
            send_json({"type": "MUTUAL_AUTH_RESULT", "ok": False, "reason": r})
            return

        info.mutual_confirmed = True
        self._log(f"[SERVER][MUTUAL_AUTH_CONFIRM] {pid}: взаимная аутентификация подтверждена клиентом.")
        send_json({"type": "MUTUAL_AUTH_RESULT", "ok": True, "reason": ""})

    def _handle_bid(self, send_json, pid: str,
                    bid_value, y_val, h_val, r_val, s_val):
        try:
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

            if not info.mutual_confirmed:
                reason = "Нет подтверждения взаимной аутентификации (сервер не был проверен клиентом)."
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

            # Сервер хэширует зашифрованную заявку y
            msg_bytes = f"y={y_int}".encode("utf-8")
            h_check = self._gost_hash_to_int_q(msg_bytes, info.gost_q)

            if h_check != h_int:
                reason = "Хэш(зашифрованной заявки y) не совпадает с h из подписи."
                self._log(f"[SERVER][BID] {pid}: {reason}")
                send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
                return

            # --- Проверка ГОСТ-подписи (вариант ГОСТ 34.10-94) ---
            p = info.gost_p
            q = info.gost_q
            a = info.gost_a
            y_pub = info.gost_y

            # v = h^{-1} mod q (по теореме Ферма: h^{q-2} mod q)
            h_inv = pow(h_int, q - 2, q)
            z1 = (s_int * h_inv) % q
            z2 = ((q - r_int) * h_inv) % q
            v = (pow(a, z1, p) * pow(y_pub, z2, p)) % p
            r_check = v % q

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
                except Exception as cb_ex:
                    self._log(f"[SERVER][BID][WARN] on_bid_received callback error: {cb_ex}")

            send_json({"type": "BID_RESULT", "ok": True, "reason": ""})

        except Exception as ex:
            reason = f"Ошибка сервера при обработке заявки: {ex}"
            self._log(f"[SERVER][BID][ERROR] {pid}: {reason}")
            try:
                send_json({"type": "BID_RESULT", "ok": False, "reason": reason})
            except Exception:
                pass

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
        """
        Расшифровывает заявки и выбирает победителя.
        Для каждого участника берётся только последняя заявка.
        """
        # Собираем последние заявки для каждого участника
        last_bids = {}  # {participant_id: bid_dict}
        
        for bid in self._bids:
            pid = bid["id"]
            # Перезаписываем заявку для этого участника (последняя будет сохранена)
            last_bids[pid] = bid
        
        results = []
        winner_id = None
        max_bid = -1

        # Обрабатываем только последние заявки каждого участника
        for pid, bid in last_bids.items():
            y = bid["y"]
            r= bid["r"]
            s = bid["s"]

            # RSA-расшифровка
            try:
                x = pow(y, self.rsa_d, self.rsa_n)
            except Exception:
                x = None

            rec = {"id": pid, "y": y, "r": r, "s": s, "x": x, "winner": False}
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
        Отправить всем аутентифицированным участникам список зашифрованных заявок.
        Для каждого участника берётся только последняя заявка.
        Формат: [{id, y, s}, ...]
        """
        # Собираем последние заявки для каждого участника
        last_bids = {}  # {participant_id: bid_dict}
        
        for bid in self._bids:
            pid = bid["id"]
            # Перезаписываем заявку для этого участника (последняя будет сохранена)
            last_bids[pid] = bid
        
        payload = []
        for pid, bid in last_bids.items():
            payload.append({
                "id": pid,
                "y": bid["y"],
                "r": bid["r"],
                "s": bid["s"],
            })

        self._log(f"[SERVER] Публикуем зашифрованные заявки ({len(payload)} шт.) всем аутентифицированным участникам")

        # Отправляем только аутентифицированным участникам
        sent_count = 0
        for info in self._participants.values():
            if not info.authenticated or info.send_fn is None:
                continue
            try:
                info.send_fn({
                    "type": "BIDS_PUBLISHED",
                    "bids": payload,
                })
                sent_count += 1
            except Exception as ex:
                self._log(f"[SERVER][BIDS_PUBLISHED][ERROR] отправка участнику {info.participant_id}: {ex}")
        
        self._log(f"[SERVER] Зашифрованные заявки отправлены {sent_count} аутентифицированным участникам")

    def broadcast_results(self, results: List[dict]):
        """
        Публикация расшифрованных результатов:
        [{id, x}, ...] всем участникам + winner_id.
        """
        payload = []
        winner_id = None

        for rec in results:
            pid = rec.get("id")
            x = rec.get("x")
            payload.append({"id": pid, "x": x})

            if rec.get("winner", False):
                winner_id = pid

        self._log(
            f"[SERVER] Публикуем расшифрованные результаты ({len(payload)} шт.) всем участникам. winner_id={winner_id!r}")

        for info in self._participants.values():
            if info.send_fn is None:
                continue
            try:
                info.send_fn({
                    "type": "RESULTS_PUBLISHED",
                    "results": payload,
                    "winner_id": winner_id,
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
