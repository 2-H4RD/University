# ServiceApp · практика 4

**Требование:** Музыкальный Service, старт/стоп, работа после Home, уведомление с собственным названием.

Разрешите уведомления. Запустите сервис, нажмите Home, откройте шторку: название трека должно быть «Сигнал безопасного канала». PlayerService объявлен с foregroundServiceType=mediaPlayback, а манифест содержит FOREGROUND_SERVICE и FOREGROUND_SERVICE_MEDIA_PLAYBACK. ContextCompat.startForegroundService создаёт компонент; onCreate создаёт NotificationChannel, immutable PendingIntent и Notification, затем немедленно вызывает startForeground(5,...). player хранит MediaPlayer. onStartCommand запускает звук и возвращает START_NOT_STICKY; повторный старт не создаёт второй player. Service сам по себе не является новым потоком: асинхронное аудио обслуживает MediaPlayer. После stopService либо окончания трека onDestroy делает release и убирает уведомление. Отказ POST_NOTIFICATIONS не даёт права скрывать foreground service: Android сохраняет системный контроль активных приложений.

[Полный разбор кода](../РАЗБОР_КОДА.md) · [Защита](../ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) · [Фактические проверки](../ОТЧЁТ_О_ПРОВЕРКАХ.md)
