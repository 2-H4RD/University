# server/member_main(1).py
# GUI организатора торгов + интеграция с AuctionServerCore

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from common.rsa_utils import generate_rsa_keys
from server.server_network import AuctionServerCore


class AuctionServerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Организатор торгов (сервер)")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # --- состояние сервера / протокола ---
        self.registry_published = False
        self.allowed_ids = []               # список допустимых идентификаторов
        self.id_set = set()                 # для проверки уникальности

        self.server_core: AuctionServerCore | None = None
        self.server_thread: threading.Thread | None = None
        self.server_running = False

        self.auth_window_open = False       # «окно аутентификации» открыто/закрыто
        self.bidding_open = False           # «окно подачи заявок» открыто/закрыто

        # RSA ключи сервера (для аутентификации / шифрования заявок)
        self.n = None
        self.e = None
        self.d = None

        # подготовим UI
        self._build_ui()

        self.server_core: AuctionServerCore | None = None

    # -------------------------------------------------------------------------
    #  Построение интерфейса
    # -------------------------------------------------------------------------
    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.tab_prepare = ttk.Frame(notebook)
        self.tab_auth = ttk.Frame(notebook)
        self.tab_bidding = ttk.Frame(notebook)

        notebook.add(self.tab_prepare, text="Подготовка")
        notebook.add(self.tab_auth, text="Аутентификация")
        notebook.add(self.tab_bidding, text="Торги")

        self._build_prepare_tab()
        self._build_auth_tab()
        self._build_bidding_tab()
        self._build_status_bar()

    # -------------------------------------------------------------------------
    #  Вкладка "Подготовка"
    # -------------------------------------------------------------------------
    def _build_prepare_tab(self):
        frame_top = ttk.LabelFrame(self.tab_prepare, text="Условия и реестр участников")
        frame_top.pack(fill="both", expand=True, padx=10, pady=10)

        # Левая часть — список идентификаторов и управление
        left = ttk.Frame(frame_top)
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ttk.Label(left, text="Правило торгов: побеждает участник с максимальной ставкой.",
                  foreground="blue").pack(anchor="w", pady=(0, 10))

        # Строка для ввода ID
        entry_frame = ttk.Frame(left)
        entry_frame.pack(fill="x", pady=5)

        ttk.Label(entry_frame, text="Идентификатор участника:").pack(side="left")
        self.entry_participant_id = ttk.Entry(entry_frame, width=30)
        self.entry_participant_id.pack(side="left", padx=5)

        btn_add_id = ttk.Button(entry_frame, text="Добавить", command=self._add_participant_id)
        btn_add_id.pack(side="left", padx=5)

        # Список идентификаторов
        list_frame = ttk.Frame(left)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.listbox_ids = tk.Listbox(list_frame, height=10)
        self.listbox_ids.pack(side="left", fill="both", expand=True)

        scrollbar_ids = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox_ids.yview)
        scrollbar_ids.pack(side="right", fill="y")
        self.listbox_ids.config(yscrollcommand=scrollbar_ids.set)

        btn_del_id = ttk.Button(left, text="Удалить выбранный", command=self._delete_selected_id)
        btn_del_id.pack(anchor="w", pady=5)

        # Статус публикации реестра
        self.label_registry_status = ttk.Label(
            left,
            text="Статус реестра: НЕ ОПУБЛИКОВАН",
            foreground="red"
        )
        self.label_registry_status.pack(anchor="w", pady=(5, 5))

        btn_publish = ttk.Button(left, text="Опубликовать реестр", command=self._publish_registry)
        btn_publish.pack(anchor="w")

        # Правая часть — ключи сервера
        right = ttk.LabelFrame(frame_top, text="Ключи сервера (RSA)")
        right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        btn_gen_keys = ttk.Button(right, text="Сгенерировать RSA-ключи сервера",
                                  command=self._generate_rsa_keys_clicked)
        btn_gen_keys.pack(anchor="w", pady=(0, 8))

        # Публичный ключ
        pub_frame = ttk.LabelFrame(right, text="Открытый ключ (публикуется)")
        pub_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.text_pub_key = tk.Text(pub_frame, height=4, wrap="word")
        self.text_pub_key.pack(fill="both", expand=True)

        # Закрытый ключ — визуально отделить
        priv_frame = ttk.LabelFrame(right, text="Закрытый ключ (НЕ публикуется)")
        priv_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.text_priv_key = tk.Text(priv_frame, height=4, wrap="word", foreground="darkred")
        self.text_priv_key.pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    #  Вкладка "Аутентификация"
    # -------------------------------------------------------------------------
    def _build_auth_tab(self):
        frame = ttk.Frame(self.tab_auth)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_controls = ttk.Frame(frame)
        top_controls.pack(fill="x", pady=(0, 10))

        self.btn_start_server = ttk.Button(top_controls, text="Запустить сервер",
                                           command=self._start_server_clicked)
        self.btn_start_server.pack(side="left", padx=5)

        self.btn_stop_server = ttk.Button(top_controls, text="Остановить сервер",
                                          command=self._stop_server_clicked, state="disabled")
        self.btn_stop_server.pack(side="left", padx=5)

        self.btn_auth_open = ttk.Button(top_controls, text="Начать аутентификацию",
                                        command=self._open_auth_window_clicked, state="disabled")
        self.btn_auth_open.pack(side="left", padx=5)

        self.btn_auth_close = ttk.Button(top_controls, text="Завершить аутентификацию",
                                         command=self._close_auth_window_clicked, state="disabled")
        self.btn_auth_close.pack(side="left", padx=5)

        self.label_server_status = ttk.Label(frame, text="Сервер: не запущен", foreground="red")
        self.label_server_status.pack(anchor="w", pady=(0, 10))

        # Таблица статусов участников
        table_frame = ttk.LabelFrame(frame, text="Участники и статус аутентификации")
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "status")
        self.tree_auth = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree_auth.heading("id", text="ID участника")
        self.tree_auth.heading("status", text="Статус")
        self.tree_auth.column("id", width=150, anchor="center")
        self.tree_auth.column("status", width=200, anchor="center")
        self.tree_auth.pack(side="left", fill="both", expand=True)

        scrollbar_auth = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_auth.yview)
        scrollbar_auth.pack(side="right", fill="y")
        self.tree_auth.configure(yscrollcommand=scrollbar_auth.set)

    # -------------------------------------------------------------------------
    #  Вкладка "Торги"
    # -------------------------------------------------------------------------
    def _build_bidding_tab(self):
        frame = ttk.Frame(self.tab_bidding)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_controls = ttk.Frame(frame)
        top_controls.pack(fill="x", pady=(0, 10))



        self.btn_bidding_open = ttk.Button(
            top_controls, text="Открыть приём заявок",
            command=self._open_bidding_window_clicked, state="disabled"
        )
        self.btn_bidding_open.pack(side="left", padx=5)

        self.btn_bidding_close = ttk.Button(
            top_controls, text="Завершить приём заявок",
            command=self._close_bidding_window_clicked, state="disabled"
        )
        self.btn_bidding_close.pack(side="left", padx=5)

        self.btn_publish_encrypted = ttk.Button(
            top_controls,
            text="Опубликовать зашифрованные заявки",
            command=self._publish_encrypted_bids_clicked,
            state="disabled"
        )
        self.btn_publish_encrypted.pack(side="left", padx=5)


        self.btn_decrypt_and_choose = ttk.Button(
            top_controls, text="Опубликовать итог",
            command=self._decrypt_and_choose_clicked, state="disabled"
        )
        self.btn_decrypt_and_choose.pack(side="left", padx=5)

        self.label_bidding_status = ttk.Label(frame, text="Приём заявок: закрыт", foreground="red")
        self.label_bidding_status.pack(anchor="w", pady=(0, 10))

        # Таблица заявок
        bids_frame = ttk.LabelFrame(frame, text="Полученные заявки")
        bids_frame.pack(fill="both", expand=True)

        columns = ("id", "y", "s", "x")
        self.tree_bids = ttk.Treeview(bids_frame, columns=columns, show="headings", height=12)
        self.tree_bids.heading("id", text="ID участника")
        self.tree_bids.heading("y", text="Зашифр. заявка y")
        self.tree_bids.heading("s", text="Подпись s")
        self.tree_bids.heading("x", text="Расшифр. ставка x")
        self.tree_bids.column("id", width=120, anchor="center")
        self.tree_bids.column("y", width=220, anchor="center")
        self.tree_bids.column("s", width=220, anchor="center")
        self.tree_bids.column("x", width=150, anchor="center")
        self.tree_bids.pack(side="left", fill="both", expand=True)

        scrollbar_bids = ttk.Scrollbar(bids_frame, orient="vertical", command=self.tree_bids.yview)
        scrollbar_bids.pack(side="right", fill="y")
        self.tree_bids.configure(yscrollcommand=scrollbar_bids.set)

        # Информация о победителе
        winner_frame = ttk.LabelFrame(frame, text="Результат торгов")
        winner_frame.pack(fill="x", pady=10)

        self.label_winner = ttk.Label(
            winner_frame,
            text="Победитель: пока не определён",
            font=("TkDefaultFont", 11, "bold")
        )
        self.label_winner.pack(anchor="w", padx=5, pady=5)

    def _publish_encrypted_bids_clicked(self):
        if self.server_core is None:
            messagebox.showwarning("Торги", "Ядро сервера не инициализировано.")
            return
        try:
            self.server_core.broadcast_encrypted_bids()
            self._set_status("Зашифрованные заявки опубликованы участникам.")
        except AttributeError:
            messagebox.showerror(
                "Торги",
                "В AuctionServerCore не реализован метод broadcast_encrypted_bids()."
            )
        except Exception as ex:
            messagebox.showerror("Торги", f"Ошибка при публикации зашифрованных заявок:\n{ex}")


    # -------------------------------------------------------------------------
    #  Статус-бар
    # -------------------------------------------------------------------------
    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Готово.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def _set_status(self, text: str):
        self.status_var.set(text)
        # заставим Tk обновить строку статуса
        self.update_idletasks()

    # -------------------------------------------------------------------------
    #  Логика вкладки "Подготовка"
    # -------------------------------------------------------------------------
    def _add_participant_id(self):
        pid = self.entry_participant_id.get().strip()
        if not pid:
            messagebox.showwarning("Ввод идентификатора", "Введите идентификатор участника.")
            return
        if pid in self.id_set:
            messagebox.showwarning("Идентификатор уже есть", f"ID '{pid}' уже добавлен.")
            return

        self.id_set.add(pid)
        self.allowed_ids.append(pid)
        self.listbox_ids.insert(tk.END, pid)
        self.entry_participant_id.delete(0, tk.END)

        self._registry_changed()
        self._refresh_auth_table()

    def _delete_selected_id(self):
        selection = self.listbox_ids.curselection()
        if not selection:
            return
        index = selection[0]
        pid = self.listbox_ids.get(index)

        self.listbox_ids.delete(index)
        if pid in self.id_set:
            self.id_set.remove(pid)
        if pid in self.allowed_ids:
            self.allowed_ids.remove(pid)

        self._registry_changed()
        self._refresh_auth_table()

    def _registry_changed(self):
        # любое изменение реестра => статус «не опубликован»
        if self.registry_published:
            self.registry_published = False
            self.label_registry_status.config(text="Статус реестра: НЕ ОПУБЛИКОВАН", foreground="red")
            self._set_status("Реестр участников изменён: необходимо перепубликовать.")

        # обновим список разрешённых ID в core (если сервер уже создан)
        if self.server_core is not None:
            try:
                self.server_core.set_allowed_ids(self.allowed_ids)
            except AttributeError:
                # если в AuctionServerCore пока нет такого метода — просто игнорируем
                pass

    def _publish_registry(self):
        if not self.allowed_ids:
            messagebox.showwarning("Публикация реестра", "Список участников пуст. Добавьте хотя бы один ID.")
            return
        self.registry_published = True
        self.label_registry_status.config(text="Статус реестра: ОПУБЛИКОВАН", foreground="green")
        self._set_status("Реестр участников опубликован.")

        # после публикации — передадим список разрешённых ID в ядро сервера
        if self.server_core is not None:
            try:
                self.server_core.set_allowed_ids(self.allowed_ids)
            except AttributeError:
                pass

    def _generate_rsa_keys_clicked(self):
        self._set_status("Генерация RSA-ключей сервера...")
        self.update_idletasks()

        try:
            n, e, d, p, q = generate_rsa_keys(bits_p=512)
        except Exception as ex:
            messagebox.showerror("Ошибка генерации ключей", f"Не удалось сгенерировать ключи:\n{ex}")
            self._set_status("Ошибка генерации RSA-ключей.")
            return

        self.server_rsa_n = n
        self.server_rsa_e = e
        self.server_rsa_d = d

        self.text_pub_key.delete("1.0", tk.END)
        self.text_pub_key.insert(tk.END, f"e = {e}\n")
        self.text_pub_key.insert(tk.END, f"n = {n}\n")

        self.text_priv_key.delete("1.0", tk.END)
        self.text_priv_key.insert(tk.END, f"d = {d}\n")
        self.text_priv_key.insert(tk.END, f"n = {n}\n")

        self._set_status("RSA-ключи сервера сгенерированы.")

    # -------------------------------------------------------------------------
    #  Логика вкладки "Аутентификация"
    # -------------------------------------------------------------------------
    def _refresh_auth_table(self):
        """Перестроить таблицу участников (ID + статус) на основе allowed_ids."""
        # очистить
        for item in self.tree_auth.get_children():
            self.tree_auth.delete(item)

        for pid in self.allowed_ids:
            self.tree_auth.insert("", tk.END, values=(pid, "не допущен"))

    def _start_server_clicked(self):
        if self.server_core is not None:
            messagebox.showinfo("Информация", "Сервер уже запущен")
            return

        if not hasattr(self, "server_rsa_n"):
            messagebox.showerror("Ошибка", "Сначала сгенерируйте ключи RSA")
            return

        print("[SERVER GUI] Запуск серверного ядра AuctionServerCore...")

        self.server_core = AuctionServerCore(
            allowed_ids=list(self.allowed_ids),
            rsa_n=self.server_rsa_n,
            rsa_e=self.server_rsa_e,
            rsa_d=self.server_rsa_d,
            on_log=self._on_core_log,
            on_auth_update=self._on_member_authenticated,
            on_bid_received=self._on_bid_received
        )

        # Запускаем сервер в отдельном потоке
        t = threading.Thread(target=self.server_core.run_blocking, daemon=True)
        t.start()
        self.server_thread = t  # чтобы хранить ссылку на поток

        print("[SERVER GUI] Сервер запущен и слушает клиентов.")
        self.label_server_status.config(text="Статус сервера: запущен", foreground="green")

        self.server_running = True
        self.label_server_status.config(text="Сервер: запущен", foreground="green")
        self._set_status("Сервер запущен, ожидание подключений участников.")

        self.btn_start_server.config(state="disabled")
        self.btn_stop_server.config(state="normal")
        self.btn_auth_open.config(state="normal")

        # после запуска сервера можно открыть окно торгов, но пока не разрешаем приём заявок
        self.btn_bidding_open.config(state="normal")

    def _stop_server_clicked(self):
        if not self.server_running:
            return
        if self.server_core is not None:
            try:
                self.server_core.shutdown()
            except AttributeError:
                pass

        self.server_running = False
        self.label_server_status.config(text="Сервер: остановлен", foreground="red")
        self._set_status("Сервер остановлен.")

        self.btn_start_server.config(state="normal")
        self.btn_stop_server.config(state="disabled")
        self.btn_auth_open.config(state="disabled")
        self.btn_auth_close.config(state="disabled")
        self.btn_bidding_open.config(state="disabled")
        self.btn_bidding_close.config(state="disabled")
        self.btn_decrypt_and_choose.config(state="disabled")

        self.server_core = None
        self.server_thread = None

    def _open_auth_window_clicked(self):
        if self.server_core is None:
            messagebox.showerror("Ошибка", "Сервер не запущен!")
            return
        if not self.server_running:
            messagebox.showwarning("Аутентификация", "Сервер ещё не запущен.")
            return
        if not self.registry_published:
            messagebox.showwarning("Аутентификация", "Реестр участников не опубликован.")
            return
        self.server_core.start_auth()
        print("[SERVER GUI] Сервер открыл окно аутентификации")
        self.auth_window_open = True
        self._set_status("Окно аутентификации открыто. Участники могут проходить аутентификацию.")
        self.btn_auth_open.config(state="disabled")
        self.btn_auth_close.config(state="normal")

        if self.server_core is not None:
            try:
                self.server_core.set_authentication_active(True)
            except AttributeError:
                pass

    def _close_auth_window_clicked(self):
        self.auth_window_open = False
        self._set_status("Окно аутентификации закрыто.")
        self.btn_auth_open.config(state="normal")
        self.btn_auth_close.config(state="disabled")

        if self.server_core is not None:
            try:
                self.server_core.set_authentication_active(False)
            except AttributeError:
                pass
        if self.server_core:
            self.server_core.stop_auth()
            print("[SERVER GUI] Сервер закрыл окно аутентификации")

    # -------------------------------------------------------------------------
    #  Логика вкладки "Торги"
    # -------------------------------------------------------------------------
    def _open_bidding_window_clicked(self):
        if not self.server_running:
            messagebox.showwarning("Торги", "Сервер ещё не запущен.")
            return

        self.bidding_open = True
        self.label_bidding_status.config(text="Приём заявок: открыт", foreground="green")
        self._set_status("Окно приёма заявок открыто.")
        self.btn_bidding_open.config(state="disabled")
        self.btn_bidding_close.config(state="normal")
        self.btn_decrypt_and_choose.config(state="disabled")
        self.btn_publish_encrypted.config(state="disabled")

        if self.server_core is not None:
            try:
                self.server_core.set_bidding_active(True)
            except AttributeError:
                pass

    def _close_bidding_window_clicked(self):
        self.bidding_open = False
        self.label_bidding_status.config(text="Приём заявок: закрыт", foreground="red")
        self._set_status("Окно приёма заявок закрыто.")
        self.btn_bidding_open.config(state="normal")
        self.btn_bidding_close.config(state="disabled")
        self.btn_decrypt_and_choose.config(state="normal")
        self.btn_publish_encrypted.config(state="normal")

        if self.server_core is not None:
            try:
                self.server_core.set_bidding_active(False)
                # Автоматически публикуем зашифрованные заявки после закрытия окна торгов
                self._set_status("Зашифрованные заявки автоматически опубликованы участникам.")
            except AttributeError:
                pass
            except Exception as ex:
                messagebox.showerror("Торги", f"Ошибка при публикации зашифрованных заявок:\n{ex}")

    def _decrypt_and_choose_clicked(self):
        """
        Кнопка «Расшифровать и выбрать победителя».
        Предполагается, что AuctionServerCore внутри хранит заявки и умеет:
          - расшифровать их с помощью RSA-ключа сервера;
          - выбрать max ставку.
        Здесь мы просто запросим у core список (id, x, y, s, is_winner).
        """
        if self.server_core is None:
            messagebox.showwarning("Торги", "Ядро сервера не инициализировано.")
            return

        try:
            results = self.server_core.decrypt_and_choose_winner()
        except AttributeError:
            messagebox.showerror(
                "Торги",
                "В AuctionServerCore не реализован метод decrypt_and_choose_winner()."
            )
            return
        except Exception as ex:
            messagebox.showerror("Торги", f"Ошибка при расшифровке и выборе победителя:\n{ex}")
            return

        # очистим таблицу и покажем расшифрованные ставки
        for item in self.tree_bids.get_children():
            self.tree_bids.delete(item)

        winner_id = None
        winner_bid = None

        for rec in results:
            pid = rec.get("id")
            decrypted_x = rec.get("x")  # расшифрованная ставка
            encrypted_y = rec.get("y")  # зашифрованная заявка
            s = rec.get("s")
            is_winner = rec.get("winner", False)

            # >>> ВАЖНО: порядок колонок (id, y, s, x) <<<
            self.tree_bids.insert(
                "", tk.END,
                values=(pid, str(encrypted_y), str(s), str(decrypted_x))
            )

            if is_winner:
                winner_id = pid
                winner_bid = decrypted_x

        if winner_id is not None:
            self.label_winner.config(
                text=f"Победитель: {winner_id} со ставкой {winner_bid}",
                foreground="green"
            )
            self._set_status(f"Определён победитель: {winner_id} (ставка {winner_bid}).")
            if self.server_core is not None:
                try:
                    self.server_core.broadcast_results(results)
                    self._set_status("Итоговые результаты опубликованы участникам.")
                except AttributeError:
                    # на случай, если метод ещё не реализован
                    pass
                except Exception as ex:
                    messagebox.showerror("Торги", f"Ошибка при публикации итога:\n{ex}")

        else:
            self.label_winner.config(
                text="Победитель: не найден (возможно, нет заявок).",
                foreground="red"
            )
            self._set_status("Победитель не найден.")

    # -------------------------------------------------------------------------
    #  Callback’и от AuctionServerCore
    # -------------------------------------------------------------------------
    def _on_core_log(self, msg: str):
        """
        Общий лог от ядра сервера — выводим в консоль и в статус-бар.
        """
        print("[SERVER CORE]", msg)
        self._set_status(msg)

    def _on_member_authenticated(self, participant_id: str, authenticated: bool):
        """
        Ядро сервера сообщает, что участник успешно аутентифицирован (или, в будущем, отозван).
        Обновляем статус в таблице.
        """
        for item in self.tree_auth.get_children():
            pid, status = self.tree_auth.item(item, "values")
            if pid == participant_id:
                new_status = "допущен" if authenticated else "не допущен"
                self.tree_auth.item(item, values=(pid, new_status))
                break

    def _on_bid_received(self, participant_id: str,
                         bid_value: int, y: int, h: int, r: int, s: int):
        encrypted_y = y
        signature_s = s

        for item in self.tree_bids.get_children():
            pid, _, _, _ = self.tree_bids.item(item, "values")
            if pid == participant_id:
                self.tree_bids.item(
                    item,
                    values=(pid, str(encrypted_y), str(signature_s), "")
                )
                return

        self.tree_bids.insert(
            "", tk.END,
            values=(participant_id, str(encrypted_y), str(signature_s), "")
        )

    def _on_bidding_finished(self):
        """
        Если ядро сервера само решит, что приём заявок завершён — можем обновить GUI.
        """
        self.bidding_open = False
        self.label_bidding_status.config(text="Приём заявок: закрыт", foreground="red")
        self.btn_bidding_open.config(state="normal")
        self.btn_bidding_close.config(state="disabled")
        self.btn_decrypt_and_choose.config(state="normal")
        self._set_status("Приём заявок завершён ядром сервера.")

    # -------------------------------------------------------------------------
    #  Закрытие приложения
    # -------------------------------------------------------------------------
    def on_close(self):
        if self.server_running and self.server_core is not None:
            try:
                self.server_core.shutdown()
            except AttributeError:
                pass
        self.destroy()


if __name__ == "__main__":
    app = AuctionServerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
