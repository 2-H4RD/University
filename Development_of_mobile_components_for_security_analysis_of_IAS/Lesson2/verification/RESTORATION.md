# Восстановление Lesson2

Дата: 08.10.2026.

Восстановлены шесть самостоятельных application-модулей практики №2 из сохранённых команд создания и исправления исходников этого чата. Включены 11 Java-файлов, XML-ресурсы, комментарии, Gradle Wrapper, каталог версий, README, конфигурации запуска и сценарий тестирования. Общие файлы Gradle Wrapper/каталога версий взяты из сохранившейся локальной копии; проект не зависит от Lesson1 и не подключает его модули.

## Повторная проверка

- `gradlew.bat assembleDebug lintDebug`: **BUILD SUCCESSFUL**, код завершения 0.
- Получены все 6 непустых APK.
- Lint: **0 ошибок, 33 предупреждений**. Подробности в отчётах каждого модуля `build/reports/lint-results-debug.html`.
- XML разобран без ошибок; комментарии присутствуют во всех Java-файлах.
- Резервный архив `../Lesson2-restored-source.zip` проверен через testzip.
- Журнал сборки: `../verification-build-restored.log`.

## Ограничение повторной визуальной проверки

Новый локальный AVD API35 создан. Эмулятор завершился до подключения к ADB, установка APK и визуальный тест в этом запуске не выполнены. Захват окна плагином также завершился ошибкой `window crop is outside captured monitor`. Старые 67 проверок, PNG и журналы от 03.10.2026 утрачены и не представлены как новые результаты.

Исходники восстановлены; на API26 отдельный запуск не выполнялся. Git init/add/commit не выполнялись.

## APK

- `ActivityLifecycle/build/outputs/apk/debug/ActivityLifecycle-debug.apk`
- `MultiActivity/build/outputs/apk/debug/MultiActivity-debug.apk`
- `IntentFilter/build/outputs/apk/debug/IntentFilter-debug.apk`
- `ToastApp/build/outputs/apk/debug/ToastApp-debug.apk`
- `NotificationApp/build/outputs/apk/debug/NotificationApp-debug.apk`
- `Dialog/build/outputs/apk/debug/Dialog-debug.apk`
