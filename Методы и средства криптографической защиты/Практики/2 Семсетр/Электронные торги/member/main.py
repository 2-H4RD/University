# member/main.py
# GUI участника торгов:
# - Подготовка: ввод ID, генерация RSA и ГОСТ-ключей;
# - Аутентификация: подключение к серверу, запуск/завершение аутентификации;
# - Торги: ввод ставки, хэширование и подпись заявки по ГОСТ 34.10-94,
#          отправка на сервер через AuctionMemberClient.

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from common.num_generator import (
    generate_gost_pq,
    generate_gost_a,
    secure_random_int,
)
from common.rsa_utils import generate_rsa_keys
from common.gost_hash_3411 import gost3411_94_full

# сетевой клиент
from client_network import AuctionMemberClient, RSAKeys, GostKeys


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

        # RSA-ключи участника (для аутентификации по RSA)
        self.rsa_n = None
        self.rsa_e = None
        self.rsa_d = None
        self.rsa_keys_obj: RSAKeys | None = None

        # ГОСТ-параметры и ключи
        self.gost_p = None
        self.gost_q = None
        self.gost_a = None
        self.gost_x = None  # закрытый
        self.gost_y = None  # открытый
        self.gost_keys_obj: GostKeys | None = None

        # Публичный ключ организатора торгов
        self.server_rsa_n: int | None = None
        self.server_rsa_e: int | None = None

        # Сетевое/протокольное состояние
        self.client: AuctionMemberClient | None = None
        self.connected_to_server = False
        self.auth_window_active = False   # логический флаг, когда мы пытаемся аутентифицироваться
        self.auth_completed = False
        self.trade_phase_open = False

        self._build_ui()

    # ------------------------------------------------------------------
    # Построение интерфейса
    # ------------------------------------------------------------------
    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab_prep = ttk.Frame(notebook)
        self.tab_auth = ttk.Frame(notebook)
        self.tab_trade = ttk.Frame(notebook)

        notebook.add(self.tab_prep, text="Подготовка")
        notebook.add(self.tab_auth, text="Аутентификация")
        notebook.add(self.tab_trade, text="Торги")

        self._build_tab_prep()
        self._build_tab_auth()
        self._build_tab_trade()

    # ------------------------------------------------------------------
    # Вкладка "Подготовка"
    # ------------------------------------------------------------------
    def _build_tab_prep(self):
        frame_top = ttk.Frame(self.tab_prep)
        frame_top.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_top, text="Идентификатор участника:").pack(side="left")
        self.entry_member_id = ttk.Entry(frame_top, width=30)
        self.entry_member_id.pack(side="left", padx=5)

        btn_gen_keys = ttk.Button(
            frame_top, text="Сгенерировать ключи (RSA + ГОСТ)",
            command=self.on_generate_keys_clicked
        )
        btn_gen_keys.pack(side="left", padx=10)

        # Раздел RSA
        rsa_frame = ttk.LabelFrame(self.tab_prep, text="Ключи для аутентификации (RSA)")
        rsa_frame.pack(fill="both", expand=True, padx=10, pady=5)

        rsa_pub_frame = ttk.LabelFrame(rsa_frame, text="Открытый ключ (e, n)")
        rsa_pub_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        rsa_priv_frame = ttk.LabelFrame(rsa_frame, text="Закрытый ключ (d, n)")
        rsa_priv_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.txt_rsa_pub = scrolledtext.ScrolledText(rsa_pub_frame, height=8)
        self.txt_rsa_pub.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_rsa_priv = scrolledtext.ScrolledText(rsa_priv_frame, height=8)
        self.txt_rsa_priv.pack(fill="both", expand=True, padx=5, pady=5)

        # Раздел ГОСТ
        gost_frame = ttk.LabelFrame(self.tab_prep, text="Ключи для подписи (ГОСТ Р 34.10-94)")
        gost_frame.pack(fill="both", expand=True, padx=10, pady=5)

        gost_pub_frame = ttk.LabelFrame(gost_frame, text="Параметры и открытый ключ (p, q, a, y)")
        gost_pub_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        gost_priv_frame = ttk.LabelFrame(gost_frame, text="Закрытый ключ (x)")
        gost_priv_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.txt_gost_pub = scrolledtext.ScrolledText(gost_pub_frame, height=10)
        self.txt_gost_pub.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_gost_priv = scrolledtext.ScrolledText(gost_priv_frame, height=10)
        self.txt_gost_priv.pack(fill="both", expand=True, padx=5, pady=5)

    # ------------------------------------------------------------------
    # Вкладка "Аутентификация"
    # ------------------------------------------------------------------
    def _build_tab_auth(self):
        top_frame = ttk.Frame(self.tab_auth)
        top_frame.pack(fill="x", padx=10, pady=10)

        btn_connect = ttk.Button(
            top_frame, text="Подключиться к серверу", command=self.on_connect_to_server
        )
        btn_connect.pack(side="left", padx=5)

        btn_start_auth = ttk.Button(
            top_frame, text="Начать аутентификацию", command=self.on_start_auth_window
        )
        btn_start_auth.pack(side="left", padx=5)

        btn_end_auth = ttk.Button(
            top_frame, text="Завершить аутентификацию", command=self.on_end_auth_window
        )
        btn_end_auth.pack(side="left", padx=5)

        status_frame = ttk.LabelFrame(self.tab_auth, text="Состояние")
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.lbl_conn_status = ttk.Label(status_frame, text="Соединение с сервером: НЕТ")
        self.lbl_conn_status.pack(anchor="w", padx=5, pady=2)

        self.lbl_auth_window_status = ttk.Label(status_frame, text="Окно аутентификации: ЗАКРЫТО")
        self.lbl_auth_window_status.pack(anchor="w", padx=5, pady=2)

        self.lbl_auth_status = ttk.Label(status_frame, text="Статус участника: НЕ АУТЕНТИФИЦИРОВАН")
        self.lbl_auth_status.pack(anchor="w", padx=5, pady=2)

        info = (
            "Примечания:\n"
            " - Аутентификация возможна только при активном окне аутентификации на сервере;\n"
            " - Участник должен иметь сгенерированные RSA-ключи и ID;\n"
            " - После успешной аутентификации участник допускается к торгам."
        )
        ttk.Label(status_frame, text=info, wraplength=900, foreground="gray").pack(
            anchor="w", padx=5, pady=5
        )

    # ------------------------------------------------------------------
    # Вкладка "Торги"
    # ------------------------------------------------------------------
    def _build_tab_trade(self):
        top_frame = ttk.Frame(self.tab_trade)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Ваша ставка (целое число):").pack(side="left")
        self.entry_bid = ttk.Entry(top_frame, width=20)
        self.entry_bid.pack(side="left", padx=5)

        btn_send_bid = ttk.Button(
            top_frame, text="Подписать и отправить заявку", command=self.on_send_bid
        )
        btn_send_bid.pack(side="left", padx=10)

        status_frame = ttk.LabelFrame(self.tab_trade, text="Заявка и подпись")
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

        info = (
            "Примечания:\n"
            " - Сервер публикует параметры своей RSA-схемы (в упрощённой версии можно\n"
            "   использовать открытый ключ сервера, известный заранее);\n"
            " - Участник шифрует ставку открытым ключом сервера и подписывает\n"
            "   хэш заявки по ГОСТ Р 34.10-94;\n"
            " - Ниже реализовано вычисление хэша и подписи, а также отправка заявки\n"
            "   на сервер через AuctionMemberClient."
        )
        ttk.Label(status_frame, text=info, wraplength=900, foreground="gray").pack(
            anchor="w", padx=5, pady=5
        )

    # ==================================================================
    # Обработчики вкладки "Подготовка"
    # ==================================================================
    def on_generate_keys_clicked(self):
        member_id = self.entry_member_id.get().strip()
        if not member_id:
            messagebox.showerror("Ошибка", "Сначала введите идентификатор участника.")
            return

        self.participant_id = member_id
        print(f"[CLIENT GUI] Генерация ключей для участника '{member_id}'...")

        # --- Генерация RSA-ключей (для аутентификации по RSA) ---
        try:
            n, e, d, p1, p2 = generate_rsa_keys(bits_p=512)
        except Exception as ex:
            messagebox.showerror("Ошибка RSA", f"Не удалось сгенерировать RSA-ключи: {ex}")
            return

        self.rsa_n = n
        self.rsa_e = e
        self.rsa_d = d
        self.rsa_keys_obj = RSAKeys(n=n, e=e, d=d)

        self.txt_rsa_pub.delete("1.0", "end")
        self.txt_rsa_pub.insert(
            "end",
            f"e = {e}\n"
            f"n = {n}\n\n"
            f"(простые множители p1, p2 скрыты для участника в этом интерфейсе)"
        )

        self.txt_rsa_priv.delete("1.0", "end")
        self.txt_rsa_priv.insert(
            "end",
            f"d = {d}\n"
            f"n = {n}\n"
            f"p1 (внутренний) = {p1}\n"
            f"p2 (внутренний) = {p2}\n"
        )

        # --- Генерация ГОСТ-параметров (p, q, a) и ключей (x, y) ---
        try:
            gost_p, gost_q = generate_gost_pq(bits_p=512)
            gost_a = generate_gost_a(gost_p, gost_q)
            gost_x = secure_random_int(1, gost_q - 1)
            gost_y = pow(gost_a, gost_x, gost_p)
        except Exception as ex:
            messagebox.showerror("Ошибка ГОСТ", f"Не удалось сгенерировать ГОСТ-параметры: {ex}")
            return

        self.gost_p = gost_p
        self.gost_q = gost_q
        self.gost_a = gost_a
        self.gost_x = gost_x
        self.gost_y = gost_y
        self.gost_keys_obj = GostKeys(p=gost_p, q=gost_q, a=gost_a, x=gost_x, y=gost_y)

        self.txt_gost_pub.delete("1.0", "end")
        self.txt_gost_pub.insert(
            "end",
            f"p = {gost_p}\n\n"
            f"q = {gost_q}\n\n"
            f"a = {gost_a}\n\n"
            f"Открытый ключ y = {gost_y}\n"
        )

        self.txt_gost_priv.delete("1.0", "end")
        self.txt_gost_priv.insert(
            "end",
            f"Закрытый ключ x = {gost_x}\n"
        )

        print("[CLIENT GUI] Ключи RSA и ГОСТ успешно сгенерированы.")

    # ==================================================================
    # Обработчики вкладки "Аутентификация"
    # ==================================================================
    def on_connect_to_server(self):
        """
        Подключение к серверу через AuctionMemberClient:
          1) discovery + TCP connect;
          2) HELLO;
          3) REGISTER_KEYS (отправка открытых ключей).
        """
        if not self.participant_id:
            messagebox.showerror("Ошибка", "Сначала введите идентификатор участника на вкладке 'Подготовка'.")
            return
        if not self.rsa_keys_obj or not self.gost_keys_obj:
            messagebox.showerror("Ошибка", "Сначала сгенерируйте ключи RSA и ГОСТ на вкладке 'Подготовка'.")
            return

        # Если уже есть клиент и подключение — сначала закрываем.
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self.connected_to_server = False

        print("[CLIENT GUI] Запуск discovery и подключение к серверу...")
        client = AuctionMemberClient(
            participant_id=self.participant_id,
            rsa_keys=self.rsa_keys_obj,
            gost_keys=self.gost_keys_obj,
        )

        if not client.discover_and_connect():
            messagebox.showerror("Ошибка", "Не удалось найти или подключиться к серверу.")
            self.lbl_conn_status.config(text="Соединение с сервером: НЕТ", foreground="red")
            return

        # HELLO
        if not client.hello():
            messagebox.showerror("Ошибка", "Сервер отклонил HELLO.")
            client.close()
            self.lbl_conn_status.config(text="Соединение с сервером: НЕТ", foreground="red")
            return

        # REGISTER_KEYS
        if not client.register_keys():
            messagebox.showerror("Ошибка", "Сервер отклонил регистрацию ключей.")
            client.close()
            self.lbl_conn_status.config(text="Соединение с сервером: НЕТ", foreground="red")
            return

        # Всё ок — сохраняем клиента
        self.client = client
        self.connected_to_server = True
        self.lbl_conn_status.config(text="Соединение с сервером: УСТАНОВЛЕНО", foreground="green")
        print("[CLIENT GUI] Подключение и регистрация ключей на сервере завершены успешно.")

    def on_start_auth_window(self):
        """
        Запуск процедуры аутентификации по RSA через AuctionMemberClient.
        По сути — вызов client.authenticate().
        """
        if not self.connected_to_server or not self.client:
            messagebox.showerror("Ошибка", "Сначала подключитесь к серверу.")
            return

        if not self.rsa_keys_obj:
            messagebox.showerror("Ошибка", "Нет RSA-ключей. Сгенерируйте их на вкладке 'Подготовка'.")
            return

        if not self.participant_id:
            messagebox.showerror("Ошибка", "Сначала укажите идентификатор участника.")
            return

        print("[CLIENT GUI] Запуск аутентификации по RSA через сеть...")
        self.auth_window_active = True
        self.lbl_auth_window_status.config(
            text="Окно аутентификации: АКТИВНО (запрос к серверу)", foreground="green"
        )
        self.lbl_auth_status.config(
            text="Статус участника: В ПРОЦЕССЕ АУТЕНТИФИКАЦИИ", foreground="orange"
        )

        ok = self.client.authenticate()
        if not ok:
            messagebox.showerror(
                "Ошибка аутентификации",
                "Сервер отклонил аутентификацию или окно аутентификации не активно."
            )
            self.auth_completed = False
            self.lbl_auth_status.config(
                text="Статус участника: НЕ АУТЕНТИФИЦИРОВАН", foreground="red"
            )
            return

        # Успех
        self.auth_completed = True
        self.lbl_auth_status.config(
            text="Статус участника: АУТЕНТИФИЦИРОВАН", foreground="green"
        )
        print("[CLIENT GUI] Аутентификация успешно пройдена.")

    def on_end_auth_window(self):
        """
        Локальное завершение "окна аутентификации" с точки зрения GUI.
        На сети ничего не отправляется — реальное закрытие окна управляется сервером.
        """
        if not self.auth_window_active:
            messagebox.showinfo("Информация", "Окно аутентификации уже закрыто.")
            return

        print("[CLIENT GUI] Завершение окна аутентификации (локальное).")
        self.auth_window_active = False
        self.lbl_auth_window_status.config(
            text="Окно аутентификации: ЗАКРЫТО (GUI)", foreground="red"
        )

        if self.auth_completed:
            self.trade_phase_open = True
            self.lbl_trade_status.config(
                text="Статус: участник допущен к торгам", foreground="green"
            )
        else:
            self.trade_phase_open = False
            self.lbl_trade_status.config(
                text="Статус: участник НЕ допущен к торгам (нет аутентификации)", foreground="red"
            )

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
                "Сначала подключитесь к серверу (вкладка «Аутентификация»)."
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


# ======================================================================
# Точка входа
# ======================================================================

def main():
    root = tk.Tk()
    app = MemberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
