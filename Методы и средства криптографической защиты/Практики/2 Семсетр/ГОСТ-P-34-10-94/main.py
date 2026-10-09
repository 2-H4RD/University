# main.py
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox

# === Импорты из модулей проекта ===
from num_generator import (
    generate_gost_pq,
    generate_gost_a,
    get_entropy_sources,
    mix_entropy_with_hash,
    secure_random_int,
)

from gost_hash_3411 import gost3411_94_full


WINDOW_WIDTH = 700
WINDOW_HEIGHT = 700


def center_two_windows(sender, receiver, w=WINDOW_WIDTH, h=WINDOW_HEIGHT):
    """
    Центрирует два окна по горизонтали по середине экрана, ставя их рядом.
    sender  - главное окно (Отправитель)
    receiver - окно-получатель (Toplevel)
    """
    sender.update_idletasks()
    screen_w = sender.winfo_screenwidth()
    screen_h = sender.winfo_screenheight()

    total_width = 2 * w
    start_x = (screen_w - total_width) // 2
    start_y = (screen_h - h) // 2

    sender.geometry(f"{w}x{h}+{start_x}+{start_y}")
    receiver.geometry(f"{w}x{h}+{start_x + w}+{start_y}")


def modinv(a: int, m: int) -> int:
    """
    Обратный элемент a^{-1} по модулю m (расширенный алгоритм Евклида).
    Если обратного не существует, выбрасывает исключение.
    """
    a = a % m
    if a == 0:
        raise ValueError("Обратного элемента не существует (a ≡ 0 mod m)")

    lm, hm = 1, 0
    low, high = a, m

    while low > 1:
        r = high // low
        nm = hm - lm * r
        new = high - low * r
        hm, lm = lm, nm
        high, low = low, new

    return lm % m


class GostApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Отправитель")

        # окно получателя
        self.receiver = tk.Toplevel(self.root)
        self.receiver.title("Получатель")

        # флаги состояния
        self.keys_generated = False   # p, q, a, x, y готовы?
        self.key_transmitted = False  # публичный ключ передан получателю?

        # параметры ГОСТ
        self.p = None
        self.q = None
        self.a = None
        self.x = None  # секретный ключ
        self.y = None  # открытый ключ

        # состояние для контроля изменений и хэша
        self.last_signed_message = None      # текст, который подписывали
        self.received_hash_hex = None        # хэш, переданный отправителем (как строка hex)

        # запрет закрытия окна получателя напрямую
        self.receiver.protocol("WM_DELETE_WINDOW", self.on_receiver_close_attempt)

        # закрытие отправителя закрывает и получателя
        self.root.protocol("WM_DELETE_WINDOW", self.on_sender_close)

        # центрирование окон
        center_two_windows(self.root, self.receiver)

        # построение интерфейса
        self.build_sender_ui()
        self.build_receiver_ui()

    # ======================= Обработчики окон =======================

    def on_receiver_close_attempt(self):
        """
        Нельзя закрывать окно получателя, пока открыт отправитель.
        """
        messagebox.showinfo(
            "Нельзя закрыть окно",
            "Нельзя закрыть окно получателя, пока открыт отправитель."
        )

    def on_sender_close(self):
        """
        При закрытии окна отправителя закрываем окно получателя
        и завершаем программу.
        """
        try:
            if self.receiver is not None and self.receiver.winfo_exists():
                self.receiver.destroy()
        except Exception:
            pass
        self.root.destroy()

    # ======================= UI отправителя =======================

    def build_sender_ui(self):
        """
        Окно 'Отправитель':
        - поле ввода сообщения;
        - кнопки:
            * 'Сгенерировать ключи'
            * 'Передать ключ'
            * 'Подписать и отправить'
        - фреймы для p, q, a, y;
        - поля для хэша и подписи.
        """
        # ---------- верхний фрейм: сообщение ----------
        msg_frame = ttk.LabelFrame(self.root, text="Сообщение (отправитель)")
        msg_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        self.sender_text = tk.Text(msg_frame, height=6, wrap="word")
        self.sender_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sender_text.bind("<KeyRelease>", self.on_sender_text_changed)

        # ---------- фрейм с кнопками ----------
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.gen_button = ttk.Button(
            btn_frame,
            text="Сгенерировать ключи (p, q, a, y)",
            command=self.on_generate_keys
        )
        self.gen_button.pack(side=tk.LEFT, padx=(0, 5))

        self.send_key_button = ttk.Button(
            btn_frame,
            text="Передать ключ",
            command=self.on_send_key
        )
        self.send_key_button.pack(side=tk.LEFT, padx=(0, 5))

        self.sign_button = ttk.Button(
            btn_frame,
            text="Подписать и отправить",
            command=self.on_sign_and_send
        )
        self.sign_button.pack(side=tk.LEFT, padx=(0, 5))

        # ---------- фрейм параметров ГОСТ ----------
        params_frame = ttk.LabelFrame(self.root, text="Параметры ГОСТ (p, q, a, y)")
        params_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        # p
        p_label = ttk.Label(params_frame, text="p (≈ 512 бит):")
        p_label.pack(anchor="w", padx=5, pady=(5, 0))

        self.p_text = tk.Text(params_frame, height=3, wrap="word")
        self.p_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        # q
        q_label = ttk.Label(params_frame, text="q (≈ 256 бит):")
        q_label.pack(anchor="w", padx=5, pady=(5, 0))

        self.q_text = tk.Text(params_frame, height=2, wrap="word")
        self.q_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        # a
        a_label = ttk.Label(params_frame, text="a:")
        a_label.pack(anchor="w", padx=5, pady=(5, 0))

        self.a_text = tk.Text(params_frame, height=2, wrap="word")
        self.a_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        # y (открытый ключ)
        y_label = ttk.Label(params_frame, text="Открытый ключ y = a^x mod p:")
        y_label.pack(anchor="w", padx=5, pady=(5, 0))

        self.y_text = tk.Text(params_frame, height=2, wrap="word")
        self.y_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        # ---------- фрейм хэша и подписи ----------
        crypto_frame = ttk.LabelFrame(self.root, text="Хэш-значение и подпись")
        crypto_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # хэш
        hash_label = ttk.Label(
            crypto_frame,
            text="Хэш-значние сообщения (ГОСТ 34.11-94, hex, младшие байты первыми):"
        )
        hash_label.pack(anchor="w", padx=5, pady=(5, 0))

        self.hash_text = tk.Text(crypto_frame, height=2, wrap="word")
        self.hash_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        # подпись
        sig_label = ttk.Label(crypto_frame, text="Подпись (r, s):")
        sig_label.pack(anchor="w", padx=5, pady=(5, 0))

        self.signature_text = tk.Text(crypto_frame, height=2, wrap="word")
        self.signature_text.pack(fill=tk.X, padx=5, pady=(0, 5))

    # ======================= UI получателя =======================

    def build_receiver_ui(self):
        """
        Окно 'Получатель':
        - поле для полученного сообщения;
        - поле для открытого ключа y;
        - поле для вычисленного хэша;
        - поле для полученной подписи;
        - статус проверки хэша;
        - поля для z1, z2, u;
        - кнопки 'Вычислить хэш' и 'Проверить подпись'.
        """
        # полученное сообщение
        msg_frame = ttk.LabelFrame(self.receiver, text="Полученное сообщение (получатель)")
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.receiver_text = tk.Text(msg_frame, height=8, wrap="word")
        self.receiver_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # окно для открытого ключа
        key_frame = ttk.LabelFrame(self.receiver, text="Открытый ключ отправителя (y)")
        key_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        self.receiver_key_text = tk.Text(key_frame, height=2, wrap="word")
        self.receiver_key_text.pack(fill=tk.X, padx=5, pady=5)

        # окно для вычисленного хэша
        calc_hash_frame = ttk.LabelFrame(self.receiver, text="Вычисленное хэш-значение (hex)")
        calc_hash_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        self.receiver_hash_text = tk.Text(calc_hash_frame, height=2, wrap="word")
        self.receiver_hash_text.pack(fill=tk.X, padx=5, pady=5)

        # окно для полученной подписи
        recv_sig_frame = ttk.LabelFrame(self.receiver, text="Полученная подпись (r, s)")
        recv_sig_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        self.receiver_sig_text = tk.Text(recv_sig_frame, height=2, wrap="word")
        self.receiver_sig_text.pack(fill=tk.X, padx=5, pady=5)

        # статус проверки хэша
        status_frame = ttk.Frame(self.receiver)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.hash_status_label = ttk.Label(status_frame, text="Статус хэша-значения: не проверен")
        self.hash_status_label.pack(anchor="w", padx=5)

        # поля для z1, z2, u
        params_frame = ttk.LabelFrame(self.receiver, text="Параметры проверки подписи (z1, z2, u)")
        params_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        z1_label = ttk.Label(params_frame, text="z1:")
        z1_label.pack(anchor="w", padx=5, pady=(5, 0))
        self.z1_text = tk.Text(params_frame, height=1, wrap="word")
        self.z1_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        z2_label = ttk.Label(params_frame, text="z2:")
        z2_label.pack(anchor="w", padx=5, pady=(5, 0))
        self.z2_text = tk.Text(params_frame, height=1, wrap="word")
        self.z2_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        u_label = ttk.Label(params_frame, text="u:")
        u_label.pack(anchor="w", padx=5, pady=(5, 0))
        self.u_text = tk.Text(params_frame, height=1, wrap="word")
        self.u_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        # кнопки проверки хэша и подписи
        btn_frame = ttk.Frame(self.receiver)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        verify_hash_btn = ttk.Button(
            btn_frame,
            text="Вычислить хэш-значение",
            command=self.on_verify_hash
        )
        verify_hash_btn.pack(side=tk.LEFT, padx=(0, 5))

        verify_sig_btn = ttk.Button(
            btn_frame,
            text="Проверить подпись",
            command=self.on_verify_signature
        )
        verify_sig_btn.pack(side=tk.LEFT, padx=(0, 5))

    # ======================= Вспомогательная логика =======================

    @staticmethod
    def _set_text(widget: tk.Text, content: str):
        """
        Обновляет содержимое Text-поля.
        """
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)

    def on_sender_text_changed(self, event=None):
        """
        Вызывается при изменении текста сообщения отправителя.
        Если сообщение было уже подписано и затем изменено — при следующей
        попытке подписи будет показано предупреждение.
        """
        # Ничего специально не делаем здесь, проверка будет в on_sign_and_send
        pass

    # ======================= Генерация ключей =======================

    def on_generate_keys(self):
        """
        Обработчик кнопки 'Сгенерировать ключи (p, q, a, y)':

        - генерируем p, q по ГОСТ (Процедура A),
        - генерируем a по ГОСТ (Процедура C),
        - генерируем секретный x из энтропии (1 <= x <= q-1),
        - считаем y = a^x mod p,
        - выводим p, q, a, y в поля.
        """
        self.gen_button.config(state="disabled")
        self.root.update_idletasks()

        try:
            # Генерация p, q
            self.p, self.q = generate_gost_pq(bits_p=512, bits_q=256)

            # Генерация a
            self.a = generate_gost_a(self.p, self.q)

            # Генерация секретного ключа x из энтропии:
            entropy = get_entropy_sources()
            h_bytes = mix_entropy_with_hash(entropy, rounds=4)
            h_int = int.from_bytes(h_bytes, "big")
            self.x = (h_int % (self.q - 1)) + 1  # 1..q-1

            # Открытый ключ y = a^x mod p
            self.y = pow(self.a, self.x, self.p)

            # Выводим всё в GUI (hex)
            p_hex = hex(self.p)[2:].upper()
            q_hex = hex(self.q)[2:].upper()
            a_hex = hex(self.a)[2:].upper()
            y_hex = hex(self.y)[2:].upper()

            self._set_text(self.p_text, p_hex)
            self._set_text(self.q_text, q_hex)
            self._set_text(self.a_text, a_hex)
            self._set_text(self.y_text, y_hex)

            # флаги и состояния
            self.keys_generated = True
            self.key_transmitted = False
            self.last_signed_message = None
            self.received_hash_hex = None

            # чистим отображение у получателя
            self._set_text(self.receiver_key_text, "")
            self._set_text(self.receiver_hash_text, "")
            self._set_text(self.receiver_sig_text, "")
            self._set_text(self.receiver_text, "")
            self.hash_status_label.config(text="Статус хэша: не проверен")

            # чистим хэш и подпись у отправителя
            self._set_text(self.hash_text, "")
            self._set_text(self.signature_text, "")

            # чистим z1, z2, u
            self._set_text(self.z1_text, "")
            self._set_text(self.z2_text, "")
            self._set_text(self.u_text, "")

            messagebox.showinfo(
                "Ключи сгенерированы",
                "Параметры p, q, a и ключи x, y успешно сгенерированы."
            )
        except Exception as e:
            messagebox.showerror("Ошибка генерации ключей", f"Произошла ошибка: {e}")
        finally:
            self.gen_button.config(state="normal")

    # ======================= Передача ключа получателю =======================

    def on_send_key(self):
        """
        Обработчик кнопки 'Передать ключ':
        - если ключи не сгенерированы — сообщение,
        - иначе передаём y в окно получателя.
        """
        if not self.keys_generated or self.y is None:
            messagebox.showwarning(
                "Ключ не сгенерирован",
                "Сначала сгенерируйте ключи (p, q, a, y)."
            )
            return

        y_hex = hex(self.y)[2:].upper()
        self._set_text(self.receiver_key_text, y_hex)
        self.key_transmitted = True

        messagebox.showinfo("Ключ передан", "Открытый ключ y передан получателю.")

    # ======================= Подписать и отправить =======================

    def on_sign_and_send(self):
        """
        Обработчик кнопки 'Подписать и отправить':

        НЕ выполняем действие (и показываем сообщение), если:
        - ключи не сгенерированы;
        - ключ не передан получателю;
        - поле ввода сообщения пустое.

        Если всё в порядке:
        - считаем хэш сообщения (ГОСТ 34.11-94),
        - формируем подпись (r, s) по ГОСТ 34.10-94,
        - отображаем всё у отправителя и "передаём" данные получателю.
        """
        # 1) ключи не сгенерированы?
        if not self.keys_generated or None in (self.p, self.q, self.a, self.x, self.y):
            messagebox.showwarning(
                "Нет ключей",
                "Сначала сгенерируйте ключи (p, q, a) и открытый ключ y."
            )
            return

        # 2) ключ не передан получателю?
        if not self.key_transmitted:
            messagebox.showwarning(
                "Ключ не передан",
                "Сначала передайте открытый ключ получателю (кнопка 'Передать ключ')."
            )
            return

        # 3) сообщение пустое?
        message_str = self.sender_text.get("1.0", tk.END).strip()
        if not message_str:
            messagebox.showwarning(
                "Пустое сообщение",
                "Поле ввода сообщения пусто. Введите текст для подписи."
            )
            return

        # Если сообщение уже было подписано ранее и теперь изменилось —
        # покажем предупреждение перед повторной подписью.
        if self.last_signed_message is not None and self.last_signed_message != message_str:
            messagebox.showinfo(
                "Сообщение изменено",
                "Сообщение было изменено после предыдущей подписи.\n"
                "Будет сформирована новая подпись для нового текста."
            )

        try:
            # ---------- хэш сообщения (ГОСТ 34.11-94) ----------
            msg_bytes = message_str.encode("utf-8")
            H_be = gost3411_94_full(msg_bytes)  # 32 байта, MSB-first
            digest_hex = H_be[::-1].hex().upper()  # печатный формат (LE-байты)
            self._set_text(self.hash_text, digest_hex)

            # Превращаем хэш в число для ГОСТ 34.10-94
            h_int = int.from_bytes(H_be, "big") % self.q
            if h_int == 0:
                h_int = 1

            # ---------- генерация одноразового k ----------
            k = 0
            while k == 0:
                entropy = get_entropy_sources()
                k_bytes = mix_entropy_with_hash(entropy, rounds=2)
                k_int = int.from_bytes(k_bytes, "big")
                k = k_int % self.q
            if k == 0:
                k = secure_random_int(1, self.q - 1)

            # ---------- формирование подписи (r, s) по ГОСТ 34.10-94 ----------
            # r = (a^k mod p) mod q
            # s = (k*h + x*r) mod q
            while True:
                r = pow(self.a, k, self.p) % self.q
                if r == 0:
                    k = secure_random_int(1, self.q - 1)
                    continue

                s = (k * h_int + self.x * r) % self.q
                if s == 0:
                    k = secure_random_int(1, self.q - 1)
                    continue

                break  # корректная подпись

            r_hex = hex(r)[2:].upper()
            s_hex = hex(s)[2:].upper()
            sig_str = f"r = {r_hex}\ns = {s_hex}"
            self._set_text(self.signature_text, sig_str)

            # ---------- "передаём" данные получателю ----------
            self._set_text(self.receiver_text, message_str)
            # Хэш теперь НЕ заполняет поле получателя, а сохраняется отдельно
            self._set_text(self.receiver_hash_text, "")  # вычисленный будет позже
            self._set_text(self.receiver_sig_text, sig_str)
            self.hash_status_label.config(text="Статус хэша: не проверен")

            # Сохраняем, что именно мы подписывали и какой хэш передали
            self.last_signed_message = message_str
            self.received_hash_hex = digest_hex

            # чистим z1, z2, u
            self._set_text(self.z1_text, "")
            self._set_text(self.z2_text, "")
            self._set_text(self.u_text, "")

            messagebox.showinfo(
                "Готово",
                "Сообщение подписано.\nТекст и подпись переданы получателю.\n"
                "Получатель может вычислить хэш и сверить его с переданным."
            )

        except Exception as e:
            messagebox.showerror("Ошибка при подписи", f"Произошла ошибка: {e}")

    # ======================= Проверка/вычисление хэша у получателя =======================

    def on_verify_hash(self):
        """
        Получатель:
        - читает сообщение;
        - пересчитывает ГОСТ 34.11-94 от полученного сообщения;
        - записывает вычисленный хэш в соответствующее поле;
        - сравнивает вычисленный хэш с тем, что передал отправитель.
          (переданный хэш хранится в self.received_hash_hex)
        """
        msg_str = self.receiver_text.get("1.0", tk.END).strip()
        if not msg_str:
            messagebox.showwarning(
                "Нет сообщения",
                "Нет сообщения для вычисления хэша."
            )
            return

        if self.received_hash_hex is None:
            messagebox.showwarning(
                "Нет переданного хэша",
                "Хэш от отправителя не был передан.\nСначала отправитель должен подписать сообщение."
            )
            return

        try:
            msg_bytes = msg_str.encode("utf-8")
            H_be = gost3411_94_full(msg_bytes)
            digest_calc_hex = H_be[::-1].hex().upper()

            # Пишем вычисленный хэш в поле
            self._set_text(self.receiver_hash_text, digest_calc_hex)

            # Сравниваем вычисленный с переданным (из отправителя)
            if digest_calc_hex == self.received_hash_hex:
                self.hash_status_label.config(text="Статус хэша: совпадает")
                messagebox.showinfo("Проверка хэша", "Хэш совпадает с тем, который передал отправитель.")
            else:
                self.hash_status_label.config(text="Статус хэша: НЕ совпадает")
                messagebox.showerror(
                    "Проверка хэша",
                    "Вычисленный хэш не совпадает с хэшем отправителя.\n"
                    "Вероятно, полученное сообщение было изменено."
                )

        except Exception as e:
            messagebox.showerror("Ошибка при проверке хэша", f"Произошла ошибка: {e}")

    # ======================= Проверка подписи у получателя =======================

    def on_verify_signature(self):
        """
        Получатель:
        - читает сообщение и подпись;
        - пересчитывает ГОСТ 34.11-94 от сообщения;
        - вычисляет h, v, z1, z2, u;
        - выводит z1, z2, u в отдельные поля;
        - проверяет условие u == r и сообщает, корректна ли подпись.
        Дополнительно: если вычисленный хэш не совпадает с тем, что передал
        отправитель, показывается предупреждение о возможном изменении сообщения.
        """
        # Проверка наличия открытого ключа
        if not self.key_transmitted or self.y is None:
            messagebox.showwarning(
                "Нет ключа",
                "Открытый ключ отправителя (y) не передан."
            )
            return

        # Считываем данные
        msg_str = self.receiver_text.get("1.0", tk.END).strip()
        recv_sig_str = self.receiver_sig_text.get("1.0", tk.END).strip()

        if not msg_str or not recv_sig_str:
            messagebox.showwarning(
                "Нет данных",
                "Нет сообщения или подписи для проверки."
            )
            return

        if self.received_hash_hex is None:
            messagebox.showwarning(
                "Нет переданного хэша",
                "Отправитель ещё не подписал/не передал хэш для этого сообщения."
            )
            return

        try:
            msg_bytes = msg_str.encode("utf-8")

            # --- Пересчитываем ГОСТ 34.11-94 ---
            H_be = gost3411_94_full(msg_bytes)
            digest_calc_hex = H_be[::-1].hex().upper()

            # Проверим совпадение хэша
            if digest_calc_hex != self.received_hash_hex:
                # Обновим поле вычисленного хэша, чтобы студент видел разницу
                self._set_text(self.receiver_hash_text, digest_calc_hex)
                self.hash_status_label.config(text="Статус хэша: НЕ совпадает")
                messagebox.showerror(
                    "Несовпадение хэша",
                    "Вычисленный хэш не совпадает с хэшем отправителя.\n"
                    "Сообщение, вероятно, было изменено.\n"
                    "Проверка подписи в таких условиях может показать неверный результат."
                )
                # Можно продолжить проверку подписи, чтобы показать, что она не проходит.

            # --- Подготовка данных для проверки подписи по ГОСТ 34.10-94 ---
            h_int = int.from_bytes(H_be, "big") % self.q
            if h_int == 0:
                h_int = 1

            # Парсим подпись вида:
            # r = RRR...
            # s = SSS...
            lines = [line.strip() for line in recv_sig_str.splitlines() if line.strip()]
            r_val = None
            s_val = None
            for line in lines:
                if line.lower().startswith("r"):
                    r_hex = line.split("=", 1)[1].strip()
                    r_val = int(r_hex, 16)
                elif line.lower().startswith("s"):
                    s_hex = line.split("=", 1)[1].strip()
                    s_val = int(s_hex, 16)

            if r_val is None or s_val is None:
                messagebox.showerror("Ошибка подписи", "Не удалось разобрать значения r и s.")
                return

            r = r_val
            s = s_val

            # Проверки диапазонов:
            if not (0 < r < self.q and 0 < s < self.q):
                messagebox.showerror(
                    "Неверная подпись",
                    "r или s выходят за допустимый диапазон (0 < r,s < q)."
                )
                return

            # v = h^{-1} mod q
            v = modinv(h_int, self.q)

            # z1 = s * v mod q
            # z2 = (q - r) * v mod q
            z1 = (s * v) % self.q
            z2 = ((self.q - r) * v) % self.q

            # u = (a^{z1} * y^{z2} mod p) mod q
            u_val = (pow(self.a, z1, self.p) * pow(self.y, z2, self.p)) % self.p
            u_val = u_val % self.q

            # выводим z1, z2, u
            self._set_text(self.z1_text, hex(z1)[2:].upper())
            self._set_text(self.z2_text, hex(z2)[2:].upper())
            self._set_text(self.u_text, hex(u_val)[2:].upper())

            if u_val == r:
                messagebox.showinfo(
                    "Подпись корректна",
                    "Подпись верна.\nСообщение не изменено и действительно принадлежит отправителю."
                )
            else:
                messagebox.showerror(
                    "Неверная подпись",
                    "Подпись не прошла проверку.\n"
                    "Сообщение или подпись могли быть подделаны."
                )

        except Exception as e:
            messagebox.showerror("Ошибка при проверке подписи", f"Произошла ошибка: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GostApp(root)
    root.mainloop()
