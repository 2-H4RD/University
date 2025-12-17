# server/member_main(1).py

import socket
import threading
import os
import sys
from typing import Dict, Any

# Добавляем project_root в sys.path, чтобы можно было импортировать common.*
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.protocol import send_json, recv_json
from common.rsa_utils import generate_rsa_keys
from common.num_generator import secure_random_int
from common.discovery import server_broadcast_loop

HOST = "0.0.0.0"   # слушаем все интерфейсы
PORT = 5000
EXPECTED_CLIENTS = 3  # для отладки: ожидаем 3 участника; можешь поменять

clients_lock = threading.Lock()
clients: Dict[int, Dict[str, Any]] = {}
next_client_id = 1

center_public_key = None
center_private_key = None


def handle_client(conn: socket.socket, addr):
    global next_client_id

    print(f"[SERVER] Новое соединение от {addr}")

    # Назначаем ID клиента
    with clients_lock:
        client_id = next_client_id
        next_client_id += 1

        clients[client_id] = {
            "socket": conn,
            "addr": addr,
            "public_e": None,
            "public_n": None,
            "authenticated": False,
        }

    send_json(conn, {"type": "hello", "message": "Добро пожаловать на торги", "client_id": client_id}, who="SERVER")

    # Ожидаем от клиента его открытый ключ
    msg = recv_json(conn, who="SERVER")
    if msg is None:
        print(f"[SERVER][client {client_id}] Соединение закрыто до отправки ключа.")
        conn.close()
        return

    if msg.get("type") != "register_public_key":
        print(f"[SERVER][client {client_id}][ERROR] Ожидали register_public_key, получили: {msg}")
        conn.close()
        return

    try:
        e_v = int(msg["e"])
        n_v = int(msg["n"])
    except Exception as e:
        print(f"[SERVER][client {client_id}][ERROR] Не удалось прочитать e/n: {e}, msg={msg}")
        conn.close()
        return

    with clients_lock:
        clients[client_id]["public_e"] = e_v
        clients[client_id]["public_n"] = n_v

    print(f"[SERVER][client {client_id}] Получен открытый ключ участника: e={e_v}, n(bitlen)={n_v.bit_length()}")

    # === АУТЕНТИФИКАЦИЯ УЧАСТНИКА ПО RSA ===
    # Выбираем случайное r: 1 < r < n_v
    r = secure_random_int(2, n_v - 1)
    print(f"[SERVER][client {client_id}] Сгенерирован challenge r={r}")

    send_json(conn, {"type": "auth_challenge", "r": str(r)}, who="SERVER")

    resp = recv_json(conn, who="SERVER")
    if resp is None:
        print(f"[SERVER][client {client_id}] Соединение закрыто во время аутентификации.")
        conn.close()
        return

    if resp.get("type") != "auth_response":
        print(f"[SERVER][client {client_id}][ERROR] Ожидали auth_response, получили: {resp}")
        conn.close()
        return

    try:
        s = int(resp["s"])
    except Exception as e:
        print(f"[SERVER][client {client_id}][ERROR] Не удалось прочитать s: {e}, msg={resp}")
        conn.close()
        return

    print(f"[SERVER][client {client_id}] Получен ответ подписи s={s}")

    # Проверяем: r' = s^{e_v} mod n_v == r ?
    r_prime = pow(s, e_v, n_v)
    print(f"[SERVER][client {client_id}] Вычислено r'={r_prime}, ожидаем r={r}")

    authenticated = (r_prime == r)
    with clients_lock:
        clients[client_id]["authenticated"] = authenticated

    send_json(conn, {"type": "auth_result", "ok": authenticated}, who="SERVER")

    if authenticated:
        print(f"[SERVER][client {client_id}] Аутентификация УСПЕШНА.")
    else:
        print(f"[SERVER][client {client_id}] Аутентификация НЕ ПРОЙДЕНА. Закрываем соединение.")
        conn.close()
        return

    # TODO: здесь дальше будет этап подачи заявок, подпись по ГОСТ, защита от атак и т.д.
    print(f"[SERVER][client {client_id}] Готов к этапу торгов (логика ещё не реализована).")


def main():
    print("[SERVER] === ЗАПУСК СЕРВЕРА ОРГАНИЗАТОРА ТОРГОВ ===")

    # Генерация RSA-ключей организатора торгов
    print("[SERVER] Генерируем RSA-ключи центра...")
    n_c, e_c, d_c, p_c, q_c = generate_rsa_keys()
    print("[SERVER] Ключи центра готовы.")
    print(f"[SERVER] Открытый ключ центра: (e_c={e_c}, n_c(bitlen)={n_c.bit_length()})")

    global center_public_key, center_private_key
    center_public_key = (e_c, n_c)
    center_private_key = (d_c, n_c)

    # Поток broadcast-объявления сервера
    stop_broadcast = threading.Event()
    broadcast_thread = threading.Thread(
        target=server_broadcast_loop,
        args=(PORT, stop_broadcast),
        daemon=True
    )
    broadcast_thread.start()

    # Запускаем TCP-сервер
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print(f"[SERVER] Слушаю {HOST}:{PORT}, ожидаю до {EXPECTED_CLIENTS} участников...")

        threads = []

        try:
            while True:
                conn, addr = s.accept()
                print(f"[SERVER] Принято соединение от {addr}")

                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()
                threads.append(t)

                with clients_lock:
                    auth_count = sum(1 for c in clients.values() if c["authenticated"])
                    total_count = len(clients)

                print(f"[SERVER] Сейчас подключено {total_count} клиентов, аутентифицировано {auth_count}.")

                # Для простоты: если все ожидаемые клиенты аутентифицированы — можно завершить сервер (для отладки)
                if auth_count >= EXPECTED_CLIENTS:
                    print("[SERVER] Достигнуто требуемое количество аутентифицированных участников. "
                          "Для учебных целей завершаем сервер.")
                    break

        except KeyboardInterrupt:
            print("\n[SERVER] Остановка по Ctrl+C")

        print("[SERVER] Ожидаем завершения потоков клиентов...")
        for t in threads:
            t.join(timeout=1.0)

    # Останавливаем broadcast-поток
    stop_broadcast.set()
    broadcast_thread.join(timeout=2.0)

    print("[SERVER] Сервер завершил работу.")


if __name__ == "__main__":
    main()
