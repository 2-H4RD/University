import argparse
import getpass
import json
import multiprocessing
import shlex
import sys
from dataclasses import asdict

from sqlalchemy.exc import SQLAlchemyError

from filemanager.config import Settings
from filemanager.errors import FMError
from filemanager.repositories.db import execute
from filemanager.security.names import terminal_safe
from filemanager.services.application import Application

HELP = """
register                       Регистрация (логин и пароль запрашиваются)
login                          Вход
logout                         Выход из учётной записи
passwd                         Смена пароля с отзывом всех сессий
whoami                         Текущий пользователь
disks                          Диски и свободное место
locations                      Ваши каталоги импорта и экспорта
list                           Ваши файлы, ID и версии
new "имя" text|json|xml         Создать файл, содержимое запрашивается одной строкой
read ID                        Показать содержимое (до 64 КиБ)
write ID ВЕРСИЯ                Заменить содержимое с проверкой версии
delete ID ВЕРСИЯ               Удалить файл с проверкой версии
import "имя_в_inbox" ФОРМАТ     Импорт из вашего inbox
export ID "имя_в_outbox"        Экспорт без перезаписи существующего файла
zip "архив.zip" ID [ID...]      Создать ZIP
zip-aes "архив.zip" ID [ID...]  Создать AES-256 ZIP; пароль вводится скрыто
unzip ID "префикс"             Безопасно извлечь в логический каталог
unzip-aes ID "префикс"         Извлечь AES ZIP; пароль вводится скрыто
audit [КОЛИЧЕСТВО]             Просмотр аудита (администратор)
verify-audit                   Проверка HMAC-цепочки (администратор)
recover                        Очистка незавершённых объектов (администратор)
disable-user ЛОГИН             Отключить пользователя (администратор)
help                           Справка
exit                           Завершить программу
""".strip()


def prompt(message):
    print(message, end="", flush=True)
    value = sys.stdin.readline(65538)
    if not value:
        raise EOFError
    if len(value) > 65536:
        # Drop the remainder; never interpret it as another command.
        while value and not value.endswith("\n"):
            value = sys.stdin.readline(65538)
        raise FMError("INPUT_TOO_LONG")
    return value.rstrip("\r\n")


def show(value):
    if isinstance(value, bytes):
        limited = value[:65536]
        try:
            output = limited.decode("utf-8", errors="strict")
        except UnicodeError:
            output = f"<binary: {len(value)} bytes; use export>"
        print(terminal_safe(output))
        if len(value) > 65536:
            print("[Вывод ограничен; используйте export]")
    else:
        def encode(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return asdict(obj)
            return str(obj)
        print(json.dumps(value, ensure_ascii=True, indent=2, default=encode))


def dispatch(app, args):
    command, *rest = args
    match command, rest:
        case "help", []:
            print(HELP)
        case "register", []:
            user = app.auth.register(prompt("Логин: "), getpass.getpass("Пароль (15–128 символов): "))
            show({"registered": user.username})
        case "login", []:
            show(app.auth.login(prompt("Логин: "), getpass.getpass("Пароль: ")))
        case "logout", []:
            app.auth.logout()
            print("Сессия завершена.")
        case "passwd", []:
            old = getpass.getpass("Текущий пароль: ")
            new = getpass.getpass("Новый пароль: ")
            if new != getpass.getpass("Повтор нового пароля: "):
                raise FMError("PASSWORDS_DIFFER")
            app.auth.change_password(old, new)
            print("Пароль изменён. Войдите снова.")
        case "whoami", []:
            show(app.auth.require())
        case "disks", []:
            show(app.disks())
        case "locations", []:
            show(app.locations())
        case "list", []:
            show(app.list_files())
        case "new", [name, fmt] if fmt in {"text", "json", "xml"}:
            show(app.create(name, prompt("Содержимое: ").encode("utf-8"), fmt))
        case "read", [identifier]:
            show(app.read(identifier))
        case "write", [identifier, version]:
            show(app.update(identifier, prompt("Новое содержимое: ").encode("utf-8"), int(version)))
        case "delete", [identifier, version]:
            app.delete(identifier, int(version))
            print("Файл удалён.")
        case "import", [name, fmt]:
            show(app.import_file(name, format=fmt))
        case "export", [identifier, name]:
            show(app.export_file(identifier, name))
        case ("zip" | "zip-aes"), [name, *identifiers] if identifiers:
            password = getpass.getpass("Пароль ZIP: ") if command == "zip-aes" else None
            show(app.create_zip(name, identifiers, password=password))
        case ("unzip" | "unzip-aes"), [identifier, prefix]:
            password = getpass.getpass("Пароль ZIP: ") if command == "unzip-aes" else None
            show(app.extract_zip(identifier, prefix, password=password))
        case "audit", []:
            show(app.audit_events())
        case "audit", [limit]:
            show(app.audit_events(int(limit)))
        case "verify-audit", []:
            show({"verified_events": app.verify_audit()})
        case "recover", []:
            show({"removed_objects": app.recover()})
        case "disable-user", [username]:
            app.disable_user(username)
            print("Пользователь отключён.")
        case _:
            raise FMError("INVALID_COMMAND_USE_HELP")


def main():
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description="Безопасный файловый менеджер, Python + PostgreSQL")
    parser.add_argument("--env", default=".env", help="Файл конфигурации относительно проекта")
    parser.add_argument("--create-admin", action="store_true", help="Первый администратор, один раз")
    parser.add_argument("--check", action="store_true", help="Проверить БД, хранилище и аудит, затем выйти")
    args = parser.parse_args()
    app = None
    try:
        app = Application(Settings.load(args.env))
        if args.check:
            with app.db.transaction() as conn:
                version = execute(conn, "SHOW server_version").scalar_one()
                role = execute(conn, "SELECT current_user").scalar_one()
            show({"status": "OK", "postgresql": version, "db_role": role,
                  "audit_events": app.journal.verify()})
            return 0
        if args.create_admin:
            # Trusted local provisioning path; the interactive command set has no role selector.
            username = prompt("Логин первого администратора: ")
            password = getpass.getpass("Пароль: ")
            if password != getpass.getpass("Повтор пароля: "):
                raise FMError("PASSWORDS_DIFFER")
            show(app.auth.register(username, password, admin=True))
            return 0
        print("Безопасный файловый менеджер. Введите help для списка команд.")
        while True:
            try:
                line = prompt("fm> ")
                if not line.strip():
                    continue
                if line.strip() == "exit":
                    app.auth.logout()
                    break
                dispatch(app, shlex.split(line, posix=True))
            except EOFError:
                app.auth.logout()
                break
            except (FMError, ValueError) as exc:
                print("Ошибка: " + (exc.code if isinstance(exc, FMError) else "INVALID_ARGUMENT"))
            except (SQLAlchemyError, OSError):
                print("Ошибка: STORAGE_OR_DATABASE_UNAVAILABLE. Операция не подтверждена; "
                      "проверьте list после восстановления.")
    except KeyboardInterrupt:
        print("\nРабота прервана.")
        return 130
    except (FMError, SQLAlchemyError, OSError) as exc:
        print("Ошибка запуска: " + (exc.code if isinstance(exc, FMError)
                                   else "DATABASE_OR_STORAGE_UNAVAILABLE"), file=sys.stderr)
        return 1
    finally:
        if app:
            app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

