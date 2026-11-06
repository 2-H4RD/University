# WorkManager · практика 4

**Требование:** Worker и критерии запуска (интернет, по выбору зарядка).

Введите abc: SHA-256 должен быть ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad. manager — singleton WorkManager; Constraints требуют CONNECTED и, если отмечено, зарядку. text записывается в Data входа, UploadWorker получает его через getInputData. doWork хеширует UTF-8 байты, переводит каждый байт в два шестнадцатеричных знака и возвращает Result.success с digest. WorkInfo LiveData показывает ENQUEUED/RUNNING/SUCCEEDED/CANCELLED и outputData. unique name lesson4-audit с REPLACE заменяет предыдущую задачу. Проверка digest не отправляет данные в сеть: интернет здесь условие планирования. Отмена адресуется тому же unique name. Покажите ожидание при отключённой зарядке; после проверки восстановите состояние батареи AVD.

[Полный разбор кода](../РАЗБОР_КОДА.md) · [Защита](../ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) · [Фактические проверки](../ОТЧЁТ_О_ПРОВЕРКАХ.md)
