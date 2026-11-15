# Матрица требований и проверок

Основание: страницы 1–3 «Семестровое задание №1.pdf» и презентации
«7 8 - угрозы Python.pptx», «9 10 - безопасный FileManager практика.pptx»
в родительской папке.

| Требование / мера | Реализация | Проверка |
|---|---|---|
| Информация о дисках | Application.disks, psutil | test_import_export_locations |
| Создание, чтение, изменение, удаление | Application, Storage, PostgreSQL | test_crud_versions_metadata_and_audit |
| JSON | formats/worker.py | test_documents_roundtrip, test_malicious_json |
| XML | defusedxml, структурные ограничения | test_xxe_dtd_and_xml_bombs, test_xml_xinclude_depth_and_input_limit |
| Создание/извлечение ZIP | archives/zipops.py | test_zip_and_aes_roundtrip |
| Метаданные в PostgreSQL | files, users, migrations | test_crud_versions_metadata_and_audit |
| Внешние ключи и ограничения | migrations/versions | test_foreign_keys_constraints |
| Подготовленные/параметризованные запросы | SQLAlchemy + psycopg | test_auth_password_hash_and_sql_injection, Semgrep |
| Хранимая функция | fm.append_event | test_real_postgresql_restricted_role |
| Регистрация и вход | Auth | test_auth_password_hash_and_sql_injection |
| Хеширование с солью | Argon2id | test_salts_and_registration_failures |
| Проверка пароля через библиотеку | argon2-cffi, dummy-хеш | test_auth_password_hash_and_sql_injection |
| Защита от перебора | auth_attempts, общая блокировка | test_login_rate_limit |
| Сессии и отзыв | Auth.require, auth_version | test_sessions_and_admin_access, test_password_change_revokes_other_sessions |
| Роли и владение файлами | авторизация в сервисах | test_foreign_file_access, test_disable_revokes_existing_session |
| Least privilege в БД | отдельные роли и GRANT/REVOKE | test_real_postgresql_restricted_role |
| Аудит действий в БД | Journal, operations | test_crud_versions_metadata_and_audit |
| Аудит отклонённых операций | отдельная транзакция | test_failure_audit_survives_main_rollback |
| Защита аудита HMAC | цепочка, head, внешний checkpoint | test_audit_tampering_detected |
| Path traversal, ADS, Windows-имена | security/names.py, UUID-хранилище | test_windows_path_attacks |
| Junction, reparse points, hardlinks | storage/safeio.py | test_windows_junction_and_hardlink_rejected |
| TOCTOU | закреплённые handles, CREATE_NEW | test_windows_junction_and_hardlink_rejected |
| ZipSlip и коллизии | полная проверка имён до извлечения | test_zipslip_windows_paths, test_zip_symlink_and_duplicates |
| ZIP-бомбы и повреждённые архивы | лимиты + фактический подсчёт | test_zip_limits_corruption_and_no_partial_files |
| Вложенные архивы | запрет автоматической рекурсии | test_nested_archives_not_recursively_extracted |
| Атомарное добавление группы | одна транзакция метаданных и аудита | test_atomic_zip_batch_when_one_document_is_bad |
| Шифрование ZIP AES-256 | pyzipper | test_zip_and_aes_roundtrip |
| Race conditions / lost update | advisory locks, FOR UPDATE, version | test_concurrent_updates_across_instances |
| Конкурирующее создание | блокировка, уникальность | test_concurrent_name_and_quota |
| Квоты и лимиты файлов | конфигурация + проверки под блокировкой | test_quota_and_size |
| Восстановление после сбоя | неизменяемые объекты, очистка сирот | test_recovery_after_transaction_abort |
| Реальная смерть процесса | тестовый дочерний процесс, os._exit | test_abrupt_process_death_and_startup_recovery |
| Предел памяти и времени | Windows Job Object, отдельный процесс | test_worker_os_limits_and_timeout |
| Контроль содержимого | SHA-256 относительно метаданных | test_content_integrity |
| Секреты на exFAT без ACL | Windows DPAPI | test_dpapi_confidentiality_and_tampering |
| Конфиденциальность внутренних файлов | AES-256-GCM с UUID в AAD | test_encrypted_objects_and_uuid_binding |
| Проверки handle на exFAT | Win32 handle validation | test_opened_handle_validation_even_on_exfat, test_pinned_directory_cannot_be_renamed |
| Квота экспорта и количества файлов | лимиты и общая блокировка | test_export_quota_and_file_count, test_concurrent_distinct_names_cannot_exceed_quota |
| Отсутствующий checkpoint | отказ при непустом журнале | test_checkpoint_missing_fails_closed |
| Разделение HMAC-протоколов | domain prefixes | test_hmac_protocols_are_domain_separated |
| Отказ обязательного аудита | откат метаданных | test_audit_failure_rolls_back_metadata |
| Защита терминала | terminal_safe | test_terminal_escapes |
| Статический анализ | Bandit + локальные правила Semgrep | reports/bandit.json, reports/semgrep.json |
| Аудит зависимостей | pip-audit | reports/pip-audit.json |

Триггеры автоматического аудита из презентации заменены явным вызовом защищённой
функции в той же транзакции: так сохраняются пользователь, результат и смысл
операции, включая чтение, ошибки входа и отказы доступа. Проверяется фактическое
сохранение событий, а не только наличие триггера.

Веб-cookie, CSRF и HTTPS-сессии не относятся к выбранному консольному интерфейсу.
Точные параметры лимитов являются проектными решениями и описаны в README.
Нативное создание hardlink/junction проверяется только на NTFS; на фактическом
exFAT это один явно пропущенный тест. Отказ по признакам открытого handle
проверяется независимо от наличия этих функций в файловой системе.

