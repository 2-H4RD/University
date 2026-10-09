# Проверка практики №3

Дата: 08.10.2026. Устройство: собственный тестовый эмулятор `emulator-5558`, Android 15 / API 35, Google Play x86_64, 1080 × 2400.

## Сборка

Оба самостоятельных проекта прошли `assembleDebug lintDebug`: **BUILD SUCCESSFUL**. Получено шесть непустых APK. Журналы: `../verification-build.log` и `../MireaProject/verification-build.log`.

| Модуль | Ошибки lint | Предупреждения lint |
|---|---:|---:|
| IntentApp | 0 | 11 |
| Sharer | 0 | 8 |
| FavoriteBook | 0 | 8 |
| SystemIntentsApp | 0 | 7 |
| SimpleFragmentApp | 0 | 15 |
| MireaProject/app | 0 | 19 |

Предупреждения сохраняются в XML/HTML lint-отчётах модулей и `lint-summary.json`. Они относятся к зафиксированным учебным версиям API/библиотек, намеренно различным элементам portrait/landscape, резервному копированию, оформлению ресурсов и JavaScript для web-страниц. 0 ошибок не означает 0 предупреждений.

## Функциональные проверки

Пройдено **52** проверок. Подробности: `checks.json`, основной сценарий: `check_lesson3.py`, дополнительные сценарии: `check_extra.py`. Журналы: `ui-test.log`, `web-final-test.log`.

- Install IntentApp
- Install Sharer
- Install FavoriteBook
- Install SystemIntentsApp
- Install SimpleFragmentApp
- Install MireaProject
- IntentApp initial
- IntentApp square 25 and timestamp
- IntentApp result survives rotation
- IntentApp displays exact sent time
- FavoriteBook initial
- FavoriteBook developer fields
- FavoriteBook rejects empty fields
- FavoriteBook returns entered data
- FavoriteBook result survives rotation
- FavoriteBook cancellation preserves result
- Sharer chooser opens
- Sharer receives shared text
- Sharer opens image picker
- Sharer picker cancellation
- ACTION_DIAL opens number
- ACTION_VIEW browser launches
- Geo handler or explicit missing-app message
- Fragment first portrait
- Fragment replace second
- Fragments both landscape
- Fragment active text survives portrait to landscape
- Selected second restored after landscape
- Fragment text survives landscape to portrait
- Fragment night theme no crash
- MireaProject data screen
- MireaProject data scrolls
- Drawer includes both destinations
- Back closes drawer
- WebView destination
- WebView default URL is MIREA
- WebView loads example.com
- WebView URL survives rotation
- WebView back history
- MireaProject dark theme
- No app fatal exception
- Sharer image picker returns content URI
- Sharer camera returns thumbnail
- Sharer camera status survives rotation
- Google Maps opens geo URI
- Final drawer opens after inset fix
- Final WebView MIREA renders
- WebView rejects cleartext URL
- Final WebView renders example.com
- Drawer Back precedes WebView history
- Final WebView history back
- Final no fatal exception

## Визуальная проверка

Скриншоты находятся в `screenshots/`: время, книга, обмен текстом, системные Intent, портретные/горизонтальные фрагменты, шторка и браузер. Проверялись доступность текста и кнопок, отступы от системных панелей, ориентации и тёмная тема.

Проверка выполнена через ADB, UI Automator XML и снимки экрана работающего эмулятора. Открытие проекта в редакторе Android Studio не подтверждалось. Эмулятор работал без отдельного видимого окна; IDE может использовать его как подключённое устройство.

## Ограничения и личные поля

- Минимальная версия задана API 26; отдельный запуск на API 26 не выполнялся.
- Книга и цитата разработчика ожидают ответа пользователя: ресурсы `developer_book` и `developer_quote` пока содержат `ТРЕБУЕТСЯ ЗАПОЛНИТЬ`. Функциональный возврат книги пользователя проверен на учебных строках.
- Отрасль контрольного задания выбрана как кибербезопасность; страница по умолчанию — сайт МИРЭА.
- Для карты подтверждён запуск Google Maps; на первом запуске показан экран приветствия, затем он пропущен без входа в аккаунт. Скриншоты `12-system-map.png`, `28-map-after-skip.png`.
- Успешный выбор изображения подтвердил возврат content URI. Системная камера вернула миниатюру, её состояние сохранилось при повороте. Скриншоты `25-picker-result.png`, `27-camera-result.png`, `30-camera-landscape.png`.
- Сетевые страницы зависят от сети и сервера. Ошибки TLS не обходятся; браузер разрешает HTTPS.
- Команды git init/add/commit не выполнялись. Lesson1 и Lesson2 использовались только для чтения настроек и оформления.

Промежуточные сбои тестового сценария устранены: внешний dialer требовал отдельного возврата/запуска для следующего сценария; статус камеры в landscape был ниже видимой области и проверяется после прокрутки; загрузка WebView и возврат по истории ожидаются до обновления адреса/готовности страницы. Проверка ошибочного HTTP-адреса выявила, что пояснение setError не видно после потери фокуса — добавлен постоянный статус. В финальном JSON нет непрошедших проверок. Исправлены отступ заголовка шторки и приоритет Back у открытой шторки поверх истории WebView.

## Переносимые исходники

`source-manifest.json` содержит пути и SHA-256 файлов. Резервный `Lesson3-source.zip` в корне включает исходники обоих проектов, инструкции, wrapper и сценарии. В него не входят SDK-путь, кэши сборки и диски AVD.
