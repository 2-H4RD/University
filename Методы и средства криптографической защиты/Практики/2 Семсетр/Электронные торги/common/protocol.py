# common/protocol.py

import json
import socket

ENCODING = "utf-8"
BUFFER_SIZE = 4096


def send_json(sock: socket.socket, obj: dict, who: str = "UNKNOWN"):
    """
    Отправка JSON-объекта по TCP-соединению.
    Используем протокол "одна строка = одно сообщение" (разделитель '\n').

    who - строка для трассировки: "SERVER" или "CLIENT".
    """
    try:
        msg = json.dumps(obj, ensure_ascii=False)
    except Exception as e:
        print(f"[{who}][ERROR] Не удалось сериализовать JSON: {e}, объект={obj!r}")
        raise

    data = (msg + "\n").encode(ENCODING)
    try:
        sock.sendall(data)
        print(f"[{who}] >>> отправлено: {msg}")
    except Exception as e:
        print(f"[{who}][ERROR] Ошибка при отправке данных: {e}")
        raise


def recv_json(sock: socket.socket, who: str = "UNKNOWN") -> dict | None:
    """
    Приём одного JSON-сообщения по TCP.
    Читаем до '\n'. Возвращаем dict или None, если соединение закрыто.

    who - строка для трассировки.
    """
    buf = b""
    try:
        while True:
            chunk = sock.recv(BUFFER_SIZE)
            if not chunk:
                # Соединение закрыто
                if buf:
                    print(f"[{who}][WARN] Соединение закрыто, но в буфере остались данные: {buf!r}")
                else:
                    print(f"[{who}] Соединение закрыто удалённой стороной.")
                return None

            buf += chunk
            if b"\n" in buf:
                line, rest = buf.split(b"\n", 1)
                # rest можно сохранить, но для простоты мы его не используем
                try:
                    text = line.decode(ENCODING)
                except Exception as e:
                    print(f"[{who}][ERROR] Не удалось декодировать строку: {e}, raw={line!r}")
                    return None

                print(f"[{who}] <<< получено: {text}")
                try:
                    obj = json.loads(text)
                except Exception as e:
                    print(f"[{who}][ERROR] Не удалось распарсить JSON: {e}, text={text!r}")
                    return None
                return obj
    except Exception as e:
        print(f"[{who}][ERROR] Ошибка при приёме данных: {e}")
        return None
