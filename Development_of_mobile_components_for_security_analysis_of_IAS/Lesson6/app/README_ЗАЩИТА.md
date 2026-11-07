# app · практика 6

**Требование:** Три поля группа/номер/фильм; SharedPreferences; восстановление при новом запуске; скрин Device Explorer в raw.

Введите свою группу, положительный номер и фильм. getSharedPreferences("mirea_settings",MODE_PRIVATE) открывает XML приватного приложения. GROUP и MOVIE — String, NUMBER — int. onCreate восстанавливает значения; EditText содержит текст, поэтому Integer.parseInt с проверкой нужен до putInt. В io вызывается Editor.commit: его boolean позволяет показать ошибку записи; UI не блокируется синхронной записью. После сообщения об успехе остановите процесс и откройте снова. В Device Explorer перейдите /data/data/<applicationId>/shared_prefs/mirea_settings.xml, откройте файл и сделайте настоящий скрин IDE. Скрин лежит в app/src/main/res/raw. MODE_PRIVATE ограничивает приложения, но сам XML обычных Preferences не шифрует.

[Полный разбор кода](../РАЗБОР_КОДА.md) · [Защита](../ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) · [Фактические проверки](../ОТЧЁТ_О_ПРОВЕРКАХ.md)

## Личный выбор пользователя

Сериал — **«Лучше звоните Солу»**, выбран в ответе пользователя. В app это начальное значение MOVIE; прежняя техническая строка Training film заменяется только в отображении, а другой сохранённый ввод имеет приоритет. Кнопка сохранения записывает фактическое поле через Editor.commit.

Поэт — **Пушкин Александр Сергеевич**. [Портрет из ответа пользователя](../SecureSharedPreferences/src/main/res/drawable/pushkin_portrait.jpg) сохранён без изменения JPEG (192×148, 4171 байт). Ресурс находится в SecureSharedPreferences/src/main/res/drawable и открывается через Android Studio. DEFAULT_POET задаёт только начальное имя, previousFixture распознаёт старую учебную заглушку; собственные сохранённые имена/фотографии не удаляются. Начальный URI android.resource://<applicationId>/drawable/pushkin_portrait ссылается на ресурс внутри APK, поэтому интернет/SAF для первого показа не нужны. Кнопка выбора всё ещё открывает системный OpenDocument: новый content:// URI получает сохраняемое право чтения. save записывает POET/ACTOR/PORTRAIT в EncryptedSharedPreferences; после force-stop читаются те же значения. **JPEG внутри APK не шифруется**: шифруются значения настроек, включая ссылку на портрет.
