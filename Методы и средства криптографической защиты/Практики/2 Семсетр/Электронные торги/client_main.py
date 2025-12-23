# member/client_main.py
# GUI участника торгов:
# - Подготовка: ввод ID, генерация RSA и ГОСТ-ключей;
# - Аутентификация: подключение к серверу, запуск/завершение аутентификации;
# - Торги: ввод ставки, хэширование и подпись заявки по ГОСТ 34.10-94,
#          отправка на сервер через AuctionMemberClient.
# - Подготовка: ввод ID, подключение к серверу, регистрация открытых ключей,
#               взаимная аутентификация Фейге–Фиата–Шамира (FFS), отображение шагов протокола;
# - Торги: ввод ставки, ГОСТ-подпись заявки, отправка на сервер через AuctionMemberClient.

import tkinter as tk
import threading
from tkinter import ttk, messagebox, scrolledtext

from num_generator import (
    generate_gost_pq,
    generate_gost_a,
    secure_random_int,
)
from num_generator import secure_random_int
from gost_hash_3411 import gost3411_94_full

# сетевой клиент
from client_network import AuctionMemberClient, GostKeys


# ======================================================================
# Вспомогательные функции: ГОСТ-подпись (R 34.10-94)
# ======================================================================

def gost_hash_to_int_q(message: bytes, q: int) -> int:
    """
    Преобразование хэша ГОСТ 34.11-94 сообщения в целое по модулю q.
    Используем H_be (MSB-first), затем трактуем LE-байты, чтобы
    быть согласованными с предыдущей реализацией.
    """
    H_be = gost3411_94_full(message)      # 32 байта, MSB-first
    # В "печатном" виде мы использовали H_be[::-1].hex().
    # Для математики удобно взять LE-представление:
    h = int.from_bytes(H_be[::-1], "big")
    h = h % q
    if h == 0:
        h = 1
    return h


def gost_sign_message(message: bytes, p: int, q: int, a: int, x: int):
    """
    Подпись сообщения по ГОСТ Р 34.10-94.
    Возвращает (r, s, h), где h — хэш по модулю q.
    """
    h = gost_hash_to_int_q(message, q)

    while True:
        k = secure_random_int(1, q - 1)
        # r = (a^k mod p) mod q
        r = pow(a, k, p) % q
        if r == 0:
            continue
        s = (k * h + x * r) % q
        if s == 0:
            continue
        return r, s, h

# ------------------------------------------------------------------
# Класс scrollable GUI
# ------------------------------------------------------------------
class ScrollableTab(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._vbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._hbar = ttk.Scrollbar(self, orient="horizontal", command=self._canvas.xview)

        self._canvas.configure(yscrollcommand=self._vbar.set, xscrollcommand=self._hbar.set)

        self._vbar.pack(side="right", fill="y")
        self._hbar.pack(side="bottom", fill="x")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self._canvas)
        self._win_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        # update scrollregion when inner size changes
        self.inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # mouse wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows
        self._canvas.bind_all("<Shift-MouseWheel>", self._on_shiftwheel)

    def _on_inner_configure(self, _event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # stretch inner width to canvas width
        self._canvas.itemconfigure(self._win_id, width=event.width)

    def _on_mousewheel(self, event):
        # Windows: event.delta is multiple of 120
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shiftwheel(self, event):
        self._canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

# ======================================================================
# Класс GUI участника торгов
# ======================================================================

class MemberApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Участник торгов (клиент)")
        self.root.geometry("1000x700")

        # Состояние участника
        self.participant_id: str | None = None


        # Параметры ГОСТ (p,q,a) выдаёт сервер при HELLO; аутентификация выполняется по FFS на модуле n (RSA сервера).
        self.gost_p: int | None = None
        self.gost_q: int | None = None
        self.gost_a: int | None = None
        self.gost_x: int | None = None  # закрытый (используется для подписи по ГОСТ 34.10-94)
        self.gost_y: int | None = None  # открытый y = g^x mod p
        self.gost_keys_obj: GostKeys | None = None

        # Публичный ключ организатора торгов
        self.server_rsa_n: int | None = None
        self.server_rsa_e: int | None = None

        # Сетевое/протокольное состояние
        self.client: AuctionMemberClient | None = None
        self.connected_to_server = False
        self.auth_completed = False
        self.trade_phase_open = False

        # --- Данные для вкладки "Проверка" ---
        self.published_bids = {}     # {id: {"y": int, "s": int}}
        self.published_results = {}  # {id: int}
        self.winner_id = None

        self._build_ui()

    # ------------------------------------------------------------------
    # Построение интерфейса
    # ------------------------------------------------------------------
    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab_prep = ScrollableTab(notebook)
        self.tab_trade = ScrollableTab(notebook)
        self.tab_verify = ScrollableTab(notebook)

        notebook.add(self.tab_prep, text="Подготовка")
        notebook.add(self.tab_trade, text="Торги")
        notebook.add(self.tab_verify, text="Проверка")

        self._build_tab_prep()
        self._build_tab_trade()
        self._build_tab_verify()

    # ------------------------------------------------------------------
    # Вкладка "Подготовка"
    # ------------------------------------------------------------------
    def _build_tab_prep(self):
        frame_top = ttk.Frame(self.tab_prep.inner)
        frame_top.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_top, text="Идентификатор участника:").pack(side="left")
        self.entry_member_id = ttk.Entry(frame_top, width=30)
        self.entry_member_id.pack(side="left", padx=5)

        self.btn_connect = ttk.Button(
            frame_top,
            text = "Подключиться к серверу",
            command = self.on_connect_to_server
        )
        self.btn_connect.pack(side="left", padx=10)

        self.btn_authenticate = ttk.Button(
            frame_top,
            text = "Пройти взаимную аутентификацию (FFS)",
            command = self.on_start_auth_window,
            state = "disabled",
        )
        self.btn_authenticate.pack(side="left", padx=5)
        status_frame = ttk.LabelFrame(self.tab_prep.inner, text="Состояние")
        status_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_conn_status = ttk.Label(status_frame, text="Соединение с сервером: НЕТ", foreground="red")
        self.lbl_conn_status.pack(anchor="w", padx=5, pady=2)

        self.lbl_auth_status = ttk.Label(status_frame, text="Статус аутентификации: НЕ ПРОЙДЕНА", foreground="red")
        self.lbl_auth_status.pack(anchor="w", padx=5, pady=2)

        # --- Открытые ключи RSA сервера (получаем при HELLO) ---
        server_rsa_frame = ttk.LabelFrame(self.tab_prep.inner, text="Открытые ключи RSA сервера (e, n)")
        server_rsa_frame.pack(fill="both", expand=False, padx=10, pady=5)
        self.txt_server_rsa_pub = scrolledtext.ScrolledText(server_rsa_frame, height=6)
        self.txt_server_rsa_pub.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_server_rsa_pub.insert(
            "end",
            "Нет данных. Подключитесь к серверу — ключи RSA (e,n) будут получены при HELLO.\n"
        )

        # Раздел ГОСТ (подпись) + FFS (аутентификация)
        gost_frame = ttk.LabelFrame(self.tab_prep.inner,
                                    text="ГОСТ 34.10-94 (подпись) + FFS (Feige–Fiat–Shamir, аутентификация)")
        gost_frame.pack(fill="both", expand=True, padx=10, pady=5)

        gost_pub_frame = ttk.LabelFrame(gost_frame, text="Параметры (p, q, a) и открытый ключ y (ГОСТ)")
        gost_pub_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        gost_priv_frame = ttk.LabelFrame(gost_frame, text="Секретный ключ x (ГОСТ)")
        gost_priv_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.txt_gost_pub = scrolledtext.ScrolledText(gost_pub_frame, height=10)
        self.txt_gost_pub.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_gost_priv = scrolledtext.ScrolledText(gost_priv_frame, height=10)
        self.txt_gost_priv.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_gost_pub.insert(
            "end",
            "Параметры ГОСТ p,q,a будут получены от сервера после подключения.\n"
        )

        # --- FFS (Feige–Fiat–Shamir) параметры аутентификации ---
        # Требуемое расположение: под блоком ГОСТ, но над логами аутентификации.
        ffs_frame = ttk.LabelFrame(self.tab_prep.inner, text="FFS (аутентификация): параметры и ключи")
        ffs_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.txt_ffs_info = scrolledtext.ScrolledText(ffs_frame, height=6)
        self.txt_ffs_info.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_ffs_info.insert(
            "end",
            "Нет данных. Подключитесь к серверу — параметры FFS будут получены при HELLO/REGISTER.\n"
        )

        # Лог аутентификации (локально на клиенте)
        log_frame = ttk.LabelFrame(self.tab_prep.inner, text="Логи прохождения аутентификации (клиент)")
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.txt_auth_log = scrolledtext.ScrolledText(log_frame, height=10)
        self.txt_auth_log.pack(fill="both", expand=True, padx=5, pady=5)
    # ------------------------------------------------------------------
    # Вкладка "Торги"
    # ------------------------------------------------------------------
    def _build_tab_trade(self):
        top_frame = ttk.Frame(self.tab_trade.inner)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Ваша ставка (целое число):").pack(side="left")
        self.entry_bid = ttk.Entry(top_frame, width=20)
        self.entry_bid.pack(side="left", padx=5)

        btn_send_bid = ttk.Button(
            top_frame, text="Подписать и отправить заявку", command=self.on_send_bid
        )
        btn_send_bid.pack(side="left", padx=10)

        btn_send_fake = ttk.Button(
            top_frame, text="Отправить фиктивную заявку", command=self.on_send_fake_bid
        )
        btn_send_fake.pack(side="left", padx=10)


        status_frame = ttk.LabelFrame(self.tab_trade.inner, text="Заявка и подпись")
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)

        inner = ttk.Frame(status_frame)
        inner.pack(fill="both", expand=True, padx=5, pady=5)

        left = ttk.Frame(inner)
        left.pack(side="left", fill="both", expand=True, padx=5)

        right = ttk.Frame(inner)
        right.pack(side="left", fill="both", expand=True, padx=5)

        # Слева: зашифрованная ставка и хэш
        ttk.Label(left, text="Зашифрованная ставка y:").pack(anchor="w")
        self.txt_enc_bid = scrolledtext.ScrolledText(left, height=5)
        self.txt_enc_bid.pack(fill="both", expand=True, pady=3)

        ttk.Label(left, text="Хэш заявки (ГОСТ 34.11-94, mod q):").pack(anchor="w")
        self.txt_hash = scrolledtext.ScrolledText(left, height=4)
        self.txt_hash.pack(fill="both", expand=True, pady=3)

        # Справа: подпись (r, s)
        ttk.Label(right, text="Подпись заявки (r, s):").pack(anchor="w")
        self.txt_signature = scrolledtext.ScrolledText(right, height=9)
        self.txt_signature.pack(fill="both", expand=True, pady=3)

        # Общий статус по торгам
        self.lbl_trade_status = ttk.Label(
            status_frame, text="Статус: торги пока не начаты (демо-состояние)"
        )
        self.lbl_trade_status.pack(anchor="w", padx=5, pady=5)

    # ==================================================================
    # Обработчики вкладки "Подготовка"
    # ==================================================================
    def _append_auth_log(self, line: str):
        if not hasattr(self, "txt_auth_log"):
            return
        def _write():
            self.txt_auth_log.insert("end", str(line) + "\n")
            self.txt_auth_log.see("end")
        if threading.current_thread() is threading.main_thread():
            _write()
        else:
            self.root.after(0, _write)

    # ==================================================================
    # Обработчики вкладки "Аутентификация"
    # ==================================================================
    def on_connect_to_server(self):
        # RSA-ключи участника не требуются для аутентификации; используется FFS-секрет s (публикуется v).
        # Если RSA-ключи сгенерированы — они будут отправлены на сервер в REGISTER_KEYS для совместимости.
        participant_id = self.entry_member_id.get().strip()
        if not participant_id:
            messagebox.showerror("Ошибка", "Введите идентификатор участника.")
            return

        self.participant_id = participant_id
        if hasattr(self, "txt_auth_log"):
            self.txt_auth_log.delete("1.0", "end")

        print("[CLIENT GUI] Запуск discovery и подключение к серверу...")

        client = AuctionMemberClient(
            participant_id=participant_id,
            gost_keys=None  # будет установлено после HELLO
        )
        try:
            client._on_push_log = self._append_auth_log
        except Exception:
            pass

        # 1) Поиск сервера + TCP connect (как у вас устроено)
        ok = client.discover_and_connect()
        if not ok:
            messagebox.showerror("Ошибка", "Не удалось найти сервер (discovery) или подключиться по TCP.")
            return

        # 2) HELLO — получаем RSA сервера и ГОСТ p,q,a
        ok, reason = client.hello()
        if not ok:
            messagebox.showerror("Подключение отклонено", reason or "Сервер отклонил подключение.")
            try:
                client.close()
            except Exception:
                pass
            return
        #3) Сохраняем и отображаем открытые ключи RSA сервера (e, n)
        self.server_rsa_n = getattr(client, "server_rsa_n", None)
        self.server_rsa_e = getattr(client, "server_rsa_e", None)
        try:
            if hasattr(self, "txt_server_rsa_pub") and self.txt_server_rsa_pub:
                self.txt_server_rsa_pub.delete("1.0", "end")
                if self.server_rsa_n and self.server_rsa_e:
                    self.txt_server_rsa_pub.insert(
                        "end",
                        "Получено от сервера при HELLO:\n"
                        f"e = {self.server_rsa_e}\n\n"
                        f"n = {self.server_rsa_n}\n"
                    )
                else:
                    self.txt_server_rsa_pub.insert("end", "Сервер не передал RSA-ключи (e,n).\n")
        except Exception:
            pass
        # Обновить информацию по FFS (n берём из RSA, v сервера — из server_ffs_v)
        try:
            if hasattr(self, "txt_ffs_info") and self.txt_ffs_info:
                self.txt_ffs_info.delete("1.0", "end")
                ffs_n = getattr(client, "server_ffs_n", None) or getattr(client, "server_rsa_n", None)
                ffs_v_srv = getattr(client, "server_ffs_v", None)
                ffs_v_cli = getattr(client, "ffs_v", None)
                ffs_s_cli = getattr(client, "ffs_s", None)  # <-- ДОБАВЛЕНО

                self.txt_ffs_info.insert(
                    "end",
                    f"n (модуль) = {ffs_n}\n"
                    f"v сервера = {ffs_v_srv}\n"
                    f"v клиента  = {ffs_v_cli}\n"
                    f"s клиента  = {ffs_s_cli}\n\n"
                    "Примечание: s — секретный параметр FFS, он НЕ должен передаваться на сервер.\n"
                )
        except Exception:
            pass


        # 3) Получить p,q,a от сервера и отобразить на вкладке "Подготовка"
        p = getattr(client, "server_gost_p", None)
        q = getattr(client, "server_gost_q", None)
        a = getattr(client, "server_gost_a", None)

        if not p or not q or not a:
            messagebox.showerror("ГОСТ", "Сервер не передал параметры ГОСТ (p,q,a).")
            try:
                client.close()
            except Exception:
                pass
            return

        # 4) Сгенерировать x и вычислить y на клиенте (после получения q)
        try:
            # secure_random_int должен быть доступен (если у вас он импортирован как-то иначе — подставьте вашу функцию)
            gost_x = secure_random_int(1, int(q) - 1)
            gost_y = pow(int(a), int(gost_x), int(p))
        except Exception as ex:
            messagebox.showerror("ГОСТ", f"Не удалось сгенерировать (x,y):\n{ex}")
            try:
                client.close()
            except Exception:
                pass
            return

        self.gost_p, self.gost_q, self.gost_a = int(p), int(q), int(a)
        self.gost_x, self.gost_y = int(gost_x), int(gost_y)
        self.gost_keys_obj = GostKeys(p=self.gost_p, q=self.gost_q, a=self.gost_a, x=self.gost_x, y=self.gost_y)

        # Показываем p,q,a и y (публичное) + x (приватное)
        self.txt_gost_pub.delete("1.0", "end")
        self.txt_gost_pub.insert(
            "end",
            f"Получено от сервера:\n"
            f"p = {self.gost_p}\n\nq = {self.gost_q}\n\na = {self.gost_a}\n\n"
            f"Открытый ключ участника y = {self.gost_y}\n"
        )

        self.txt_gost_priv.delete("1.0", "end")
        self.txt_gost_priv.insert("end", f"Закрытый ключ участника x = {self.gost_x}\n")

        # 5) Установить gost_keys в клиент и зарегистрировать ключи на сервере
        client.gost_keys = self.gost_keys_obj

        if not client.register_keys():
            messagebox.showerror("Ошибка", "Сервер отклонил регистрацию ключей.")
            try:
                client.close()
            except Exception:
                pass
            return

        # Обновить отображение FFS после регистрации ключей (v клиента может быть сгенерирован в register_keys)
        try:
            if hasattr(self, "txt_ffs_info") and self.txt_ffs_info:
                ffs_n = getattr(client, "server_ffs_n", None) or getattr(client, "server_rsa_n", None)
                ffs_v_srv = getattr(client, "server_ffs_v", None)
                ffs_v_cli = getattr(client, "ffs_v", None)
                ffs_s_cli = getattr(client, "ffs_s", None)  # <-- ДОБАВЛЕНО

                self.txt_ffs_info.delete("1.0", "end")
                self.txt_ffs_info.insert(
                    "end",
                    f"n (модуль) = {ffs_n}\n"
                    f"v сервера = {ffs_v_srv}\n"
                    f"v клиента  = {ffs_v_cli}\n"
                    f"s клиента  = {ffs_s_cli}\n\n"
                )


        except Exception:
            pass

        # 6) Подключение успешно — сохранить client и обновить статус GUI
        self.client = client
        self.connected_to_server = True

        if hasattr(self, "btn_authenticate"):
            self.btn_authenticate.config(state="normal")

        self.lbl_conn_status.config(text="Соединение с сервером: ДА", foreground="green")
        messagebox.showinfo("Подключение", "Подключение установлено и ключи зарегистрированы.")

        # 7) Регистрация push callbacks (если у вас так принято)
        try:
            client.start_push_listener(
                on_bids_published=self.on_bids_published,
                on_results_published=self.on_results_published,
                on_bidding_status=self.on_bidding_status_changed,
                on_log=self._append_auth_log
            )

        except Exception:
            pass

    def on_start_auth_window(self):
        """
        Запуск процедуры взаимной аутентификации по схеме FFS (Feige–Fiat–Shamir) через AuctionMemberClient.
        По сути — вызов client.authenticate().
        """
        if self.auth_completed:
            messagebox.showinfo("Аутентификация", "Вы уже прошли аутентификацию. Повторная не требуется.")
            return

        if not self.connected_to_server or not self.client:
            messagebox.showerror("Ошибка", "Сначала подключитесь к серверу.")
            return

        # RSA-ключи участника для аутентификации больше не нужны.
        if not self.participant_id:
            messagebox.showerror("Ошибка", "Сначала укажите идентификатор участника.")
            return

        self._append_auth_log("[CLIENT GUI] Запуск взаимной аутентификации (FFS)...")
        self.lbl_auth_status.config(
            text="Статус аутентификации: В ПРОЦЕССЕ", foreground="orange"
        )

        ok = self.client.authenticate()
        if not ok:
            messagebox.showerror(
                "Ошибка аутентификации",
                "Сервер отклонил аутентификацию или окно аутентификации не активно."
            )
            # НЕ сбрасываем, если ранее уже было успешно
            if not self.auth_completed:
                self.auth_completed = False
            self.lbl_auth_status.config(
                text="Статус аутентификации: НЕ ПРОЙДЕНА", foreground="red"
            )
            return

        # Успех
        self.auth_completed = True
        self.trade_phase_open = True
        self.lbl_auth_status.config(
            text="Статус аутентификации: ПРОЙДЕНА", foreground="green"
        )
        self._append_auth_log("[CLIENT GUI] Аутентификация успешно пройдена.")

    # ==================================================================
    # Обработчики вкладки "Торги"
    # ==================================================================
    def on_send_bid(self):
        """
        Обработчик кнопки «Отправить заявку».

        Шаги:
          1) считываем x (ставку) из поля;
          2) шифруем её RSA-ключом сервера: y = x^e_c mod n_c;
          3) подписываем y по ГОСТ 34.10-94 -> (h, r, s);
          4) показываем y, h, r, s в GUI;
          5) отправляем (x, y, h, r, s) на сервер.
        """
        # --- 0. Проверка подключения к серверу ---
        if self.client is None or not getattr(self.client, "running", False):
            messagebox.showwarning(
                "Нет соединения",
                "Сначала подключитесь к серверу (вкладка «Подготовка»)."
            )
            return

        # --- 0.1. Проверка статуса аутентификации ---
        if not self.auth_completed:
            messagebox.showwarning(
                "Нет доступа",
                "Сначала пройдите аутентификацию, затем отправляйте заявки."
            )
            return

        # --- 1. Читаем и проверяем ставку x ---
        bid_str = self.entry_bid.get().strip()
        if not bid_str:
            messagebox.showwarning(
                "Пустая ставка",
                "Введите размер ставки перед отправкой."
            )
            return

        try:
            bid_value = int(bid_str)
        except ValueError:
            messagebox.showerror(
                "Неверный формат",
                "Ставка должна быть целым числом."
            )
            return

        if bid_value <= 0:
            messagebox.showerror(
                "Неверное значение",
                "Ставка должна быть положительным числом."
            )
            return

        # --- 2. Запрос у сетевого клиента на шифрование, подпись и отправку ---
        try:
            result = self.client.send_bid(bid_value=bid_value)
        except Exception as ex:
            messagebox.showerror(
                "Ошибка отправки",
                f"Не удалось отправить заявку на сервер:\n{ex}"
            )
            return

        if not result:
            messagebox.showerror(
                "Ошибка отправки",
                "Не удалось отправить заявку (нет соединения или ключей сервера)."
            )
            return

        # Если сервер отклонил заявку — показываем причину и выходим
        if isinstance(result, dict) and not result.get("ok", True):
            reason = result.get("reason", "") or "Заявка отклонена сервером."
            messagebox.showerror("Заявка отклонена", reason)
            return

        # --- 3. Обновляем GUI: показываем y, h, r, s ---
        y_enc = result["y"]
        h_hex = hex(result["h"])[2:].upper()
        r = result["r"]
        s = result["s"]

        self.txt_enc_bid.delete("1.0", "end")
        self.txt_enc_bid.insert("end", str(y_enc))

        self.txt_hash.delete("1.0", "end")
        self.txt_hash.insert("end", h_hex)

        self.txt_signature.delete("1.0", "end")
        self.txt_signature.insert("end", f"r = {r}\ns = {s}")

        messagebox.showinfo(
            "Заявка отправлена",
            "Ваша зашифрованная и подписанная заявка успешно отправлена на сервер."
        )

    def on_send_fake_bid(self):
        if self.client is None or not getattr(self.client, "running", False):
            messagebox.showwarning("Нет соединения", "Сначала подключитесь к серверу.")
            return
        if not self.auth_completed:
            messagebox.showwarning("Нет доступа", "Сначала пройдите аутентификацию.")
            return

        bid_str = self.entry_bid.get().strip()
        if not bid_str:
            messagebox.showwarning("Пустая ставка", "Введите ставку (например 10000).")
            return

        try:
            bid_value = int(bid_str)
        except ValueError:
            messagebox.showerror("Неверный формат", "Ставка должна быть целым числом.")
            return

        # ВАЖНО: для атаки подпись считается НЕ на тот y, который отправляется серверу.
        # Поэтому fake_signed_value должен отличаться от bid_value.
        fake_signed_value = 1000
        if bid_value == fake_signed_value:
            # чтобы атака гарантированно была "фиктивной"
            fake_signed_value = bid_value + 1

        try:
            # В client_network.py метод должен принимать параметры:
            # send_fake_bid(bid_value: int, fake_signed_value: int = 1000)
            resp = self.client.send_fake_bid(bid_value=bid_value, fake_signed_value=fake_signed_value)
        except TypeError:
            # если у тебя пока старое имя параметра в client_network.py
            resp = self.client.send_fake_bid(bid_value=bid_value, signed_value=fake_signed_value)
            if isinstance(resp, dict) and resp.get("type") == "BID_RESULT" and not resp.get("ok", True):
                messagebox.showerror("Заявка отклонена", resp.get("reason", "") or "Заявка отклонена сервером.")
                return
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось отправить фиктивную заявку:\n{ex}")
            return

        if not resp:
            messagebox.showerror("Ошибка", "Нет ответа от сервера.")
            return

        ok = resp.get("ok", False)
        reason = resp.get("reason", "")

        if not ok:
            messagebox.showinfo(
                "Фиктивная заявка отклонена",
                f"Сервер отклонил заявку:\n\n{reason}"
            )
        else:
            messagebox.showwarning(
                "Фиктивная заявка принята",
                "Неожиданно: сервер принял фиктивную заявку. Проверьте, что сервер сравнивает Hash(y) с h из подписи."
            )

    # ------------------------------------------------------------------
    # Вкладка "Проверка"
    # ------------------------------------------------------------------
    def _build_tab_verify(self):
        frame = ttk.Frame(self.tab_verify.inner)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        top = ttk.Frame(frame)
        top.pack(fill="x", pady=(0, 10))

        self.lbl_verify_winner = ttk.Label(top, text="Победитель: Не определен", foreground="blue")
        self.lbl_verify_winner.pack(side="left")

        btn_check = ttk.Button(top, text="Проверить результаты", command=self.on_verify_results_clicked)
        btn_check.pack(side="right")

        # Таблица 1: опубликованные зашифрованные заявки
        bids_frame = ttk.LabelFrame(frame, text="Опубликованные зашифрованные заявки")
        bids_frame.pack(fill="both", expand=True, pady=(0, 10))

        cols1 = ("id", "y", "r","s")
        self.tree_verify_bids = ttk.Treeview(bids_frame, columns=cols1, show="headings", height=10)
        self.tree_verify_bids.heading("id", text="ID участника")
        self.tree_verify_bids.heading("y", text="Зашифрованная ставка (y)")
        self.tree_verify_bids.heading("r", text="Часть подписи r")
        self.tree_verify_bids.heading("s", text="Часть подписи s")
        self.tree_verify_bids.column("id", width=140, anchor="center")
        self.tree_verify_bids.column("y", width=320, anchor="center")
        self.tree_verify_bids.column("r", width=320, anchor="center")
        self.tree_verify_bids.column("s", width=320, anchor="center")
        self.tree_verify_bids.pack(side="left", fill="both", expand=True)

        sb1 = ttk.Scrollbar(bids_frame, orient="vertical", command=self.tree_verify_bids.yview)
        sb1.pack(side="right", fill="y")
        self.tree_verify_bids.configure(yscrollcommand=sb1.set)

        # Таблица 2: опубликованные открытые результаты
        res_frame = ttk.LabelFrame(frame, text="Опубликованные открытые результаты")
        res_frame.pack(fill="both", expand=True)

        cols2 = ("id", "x")
        self.tree_verify_results = ttk.Treeview(res_frame, columns=cols2, show="headings", height=10)
        self.tree_verify_results.heading("id", text="ID участника")
        self.tree_verify_results.heading("x", text="Ставка (x)")
        self.tree_verify_results.column("id", width=140, anchor="center")
        self.tree_verify_results.column("x", width=200, anchor="center")
        self.tree_verify_results.pack(side="left", fill="both", expand=True)

        sb2 = ttk.Scrollbar(res_frame, orient="vertical", command=self.tree_verify_results.yview)
        sb2.pack(side="right", fill="y")
        self.tree_verify_results.configure(yscrollcommand=sb2.set)

    def on_bidding_status_changed(self, is_open: bool):
        self.trade_phase_open = bool(is_open)

        if self.trade_phase_open:
            self.lbl_trade_status.config(text="Статус: приём заявок ОТКРЫТ", foreground="green")
        else:
            self.lbl_trade_status.config(text="Статус: приём заявок ЗАКРЫТ", foreground="red")

    def on_bids_published(self, bids: list[dict]):
        # bids: [{id, y, s}, ...]
        self.published_bids.clear()
        for item in self.tree_verify_bids.get_children():
            self.tree_verify_bids.delete(item)

        for rec in bids:
            pid = rec.get("id")
            y = rec.get("y")
            r= rec.get("r")
            s = rec.get("s")
            if pid is None:
                continue
            try:
                y = int(y)
                r = int(r)
                s = int(s)
            except Exception:
                continue

            self.published_bids[pid] = {"y": y, "r": r, "s": s}
            self.tree_verify_bids.insert("", "end", values=(pid, str(y), str(r), str(s)))

    def on_results_published(self, results: list[dict], winner_id):
        # results: [{id, x}, ...]
        self.published_results.clear()
        for item in self.tree_verify_results.get_children():
            self.tree_verify_results.delete(item)

        for rec in results:
            pid = rec.get("id")
            x = rec.get("x")
            if pid is None:
                continue
            try:
                x = int(x) if x is not None else None
            except Exception:
                x = None

            self.published_results[pid] = x
            self.tree_verify_results.insert("", "end", values=(pid, "" if x is None else str(x)))

        self.winner_id = winner_id
        if winner_id:
            self.lbl_verify_winner.config(text=f"Победитель: {winner_id}", foreground="green")
        else:
            self.lbl_verify_winner.config(text="Победитель: Не определен", foreground="blue")

    def on_verify_results_clicked(self):
        def build_verify_report(mismatches: list[dict], checked: int) -> str:
            def _short_int(v, head: int = 18, tail: int = 18) -> str:
                if v is None:
                    return "None"
                s = str(v)
                if len(s) <= head + tail + 3:
                    return s
                return s[:head] + "..." + s[-tail:]

            lines = []
            lines.append(f"Проверено записей: {checked}")
            lines.append(f"Несоответствий: {len(mismatches)}")
            lines.append("")

            for i, m in enumerate(mismatches[:20], start=1):
                pid = m.get("id")
                x = m.get("x")
                y_pub = m.get("y_pub")
                y_calc = m.get("y_calc")
                reason = m.get("reason", "")

                lines.append(f"{i}) Участник ID={pid}")
                if reason:
                    lines.append(f"   Причина: {reason}")
                if x is not None:
                    lines.append(f"   Опубликованная открытая ставка x: {_short_int(x)}")
                lines.append(f"   Опубликованная зашифрованная заявка y: {_short_int(y_pub)}")
                if y_calc is not None:
                    lines.append(f"   Enc(x), вычисленная клиентом:         {_short_int(y_calc)}")
                lines.append("")

            if len(mismatches) > 20:
                lines.append(f"... и ещё {len(mismatches) - 20} несоответствий (не показаны).")

            return "\n".join(lines)
        # bids: [{id, y, r, s}, ...]
        if not self.client or not self.connected_to_server:
            messagebox.showwarning("Проверка", "Нет подключения к серверу.")
            return
        # Нужны и зашифрованные заявки, и открытые результаты
        if not self.published_bids:
            messagebox.showwarning("Проверка", "Нет опубликованных зашифрованных заявок.")
            return
        if not self.published_results:
            messagebox.showwarning("Проверка", "Нет опубликованных открытых результатов.")
            return

        # Нужен открытый ключ сервера
        n = getattr(self.client, "server_rsa_n", None)
        e = getattr(self.client, "server_rsa_e", None)
        if not n or not e:
            messagebox.showerror("Проверка", "Неизвестен открытый ключ сервера (n,e).")
            return

        mismatches: list[dict] = []
        checked = 0

        for pid, x in self.published_results.items():
            if pid not in self.published_bids:
                continue

            y_pub = self.published_bids[pid].get("y")

            if x is None:
                mismatches.append({
                    "id": pid,
                    "x": None,
                    "y_pub": y_pub,
                    "y_calc": None,
                    "reason": "Сервер опубликовал результат без ставки x (x=None)."
                })
                continue

            try:
                x_int = int(x)
                y_pub_int = int(y_pub)
            except Exception:
                mismatches.append({
                    "id": pid,
                    "x": x,
                    "y_pub": y_pub,
                    "y_calc": None,
                    "reason": "Некорректный формат данных (x или y не приводятся к int)."
                })
                continue

            y_calc = pow(x_int, int(e), int(n))
            checked += 1

            if y_calc != y_pub_int:
                mismatches.append({
                    "id": pid,
                    "x": x_int,
                    "y_pub": y_pub_int,
                    "y_calc": y_calc,
                    "reason": "Enc(x) не совпадает с опубликованным y."
                })

        if checked == 0:
            messagebox.showwarning("Проверка", "Нет пересечения между опубликованными заявками и результатами.")
            return

        if not mismatches:
            messagebox.showinfo(
                "Проверка честности пройдена",
                "Несоответствий не обнаружено.\n\n"
                f"Проверено записей: {checked}\n\n"
                "Организатор торгов не подменил заявки"
            )
        else:
            report = build_verify_report(mismatches, checked)
            messagebox.showerror("Проверка честности НЕ пройдена", report)


# ======================================================================
# Точка входа
# ======================================================================

def main():
    root = tk.Tk()
    app = MemberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
