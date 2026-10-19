"""Формирует Markdown для применения через редактор Android Studio; источники не изменяет."""
from pathlib import Path
import prepare_audit as a

ROOT=Path.cwd()
COMMON='''
## Среда и запуск

Проект проверяется в установленной Android Studio, со встроенным JDK (`jbr`), Android SDK `C:/Users/H4RD/AppData/Local/Android/Sdk` и устройством **Pixel 9 API 35 Google Play**, AVD **Pixel_9**. Установленные SDK, эмулятор, Chrome, Google Maps и камера остаются доступными после проверки. `local.properties` содержит реальный путь SDK; изменение диска проекта не требует переноса SDK.

Откройте папку текущего урока через File → Open, дождитесь Gradle Sync. Для отдельного приложения выберите его конфигурацию в верхней панели, устройство Pixel 9 и Run. Встроенная панель Running Devices показывает настоящий запущенный APK. Если устройство выключено, откройте Tools → Device Manager и нажмите Start у Pixel_9.

Сохранённая конфигурация **{verify}** выполняет `assembleDebug`, `lintDebug` и существующие `testDebugUnitTest` (если указаны в конфигурации). Её можно выбрать как обычную Run configuration. Сборку и запуск одного Gradle проекта выполняйте последовательно. Lint предупреждения о новых версиях библиотек не являются проверкой практических действий.

## Как пользоваться разбором

[РАЗБОР_КОДА.md](РАЗБОР_КОДА.md) содержит поток данных каждого приложения, таблицы полей и локальных переменных с номерами строк, назначение методов, полные Java листинги с комментариями, значения XML атрибутов, ресурсов, темы, manifest и Gradle. Откройте исходник рядом с разделом соответствующего модуля: в редакторе Ctrl+G переводит к нужной строке. Сгенерированные R/Binding и build не редактируются.

На защите объясняйте цепочку **действие пользователя → Java callback → чтение/изменение значения → XML View или системный компонент → видимый результат**. Переменная со ссылкой на View не является сохранёнными данными. При повороте обычно создаются новая Activity и новая разметка; Bundle и стабильные ID восстанавливают значения.

Свежие результаты, PNG и XML интерфейса находятся в [verification/audit-2026-10-09](verification/audit-2026-10-09). `checks.json` содержит отдельные проверки и фактический статус. Старые отчёты от 08.10.2026 являются архивом и не доказывают текущую сборку.
'''

DEFENSE={
'Lesson1':'''# Инструкция по защите практики №1

Студент: Зубарев Василий Сергеевич, БИСО-02-22, №5. Требования: [Практика № 1.pdf](Практика%20№%201.pdf).

## Последовательность демонстрации

1. **app.** Запустите исходный Hello World. Покажите MAIN/LAUNCHER в AndroidManifest.xml, MainActivity.onCreate и связь `R.layout.activity_main` с ConstraintLayout. Четыре constraints центрируют TextView, а `wrap_content` определяет размер по содержимому.
2. **layouttype.** На старте покажите EditText «New life for mirea activity!» и шесть кнопок. Поверните Pixel 9 через toolbar Running Devices: Android выбирает `layout-land/activity_second.xml`, Java код не меняет ориентацию. Портретные кнопки делят высоту по `layout_weight`, альбомный вариант содержит три горизонтальные строки.
3. Раскройте меню из трёх точек и по очереди выберите **LinearLayout**, **TableLayout**, **ConstraintLayout**, **TextView**. `onCreateOptionsMenu` добавляет пункты с itemId 1..5; `onOptionsItemSelected` сопоставляет их с R.layout; `showLayout` создаёт Views и повторно назначает Insets. itemId и R.layout имеют разные роли. Не нужно изменять исходники перед каждой демонстрацией.
4. В LinearLayout объясните vertical внешний контейнер, horizontal две строки, width=0dp и одинаковые веса трёх кнопок. В TableLayout покажите три TableRow и выравнивание столбцов; ImageButton отличается от Button изображением и contentDescription. В ConstraintLayout покажите стороны привязок каждого элемента.
5. **control_lesson1.** Покажите ImageView, TextView, EditText, CheckBox, Button и ImageButton. Введите имя и отметьте избранное, поверните устройство: одинаковые `nameInput` и `favoriteCheckBox` сохраняют значения. Объясните портретные constraints и альбомные веса. Задание требует компоновку, отдельное сохранение контакта/реальный телефонный звонок здесь не реализуются.
6. **buttonclicker.** Нажмите «Кто Я?»: `oclBtnWhoAmI.onClick` выводит номер5 в tvOut и вызывает checkBox.toggle. Нажмите вторую кнопку: `android:onClick` вызывает `public void onItIsNotMeClick(View)` и выводит «Это не я сделал», одновременно меняя флажок. Java listener назначается первой кнопке; XML назначает callback второй.
7. Поверните экран после нажатия. `onSaveInstanceState` записывает текст в ключ `output`; `onCreate` возвращает его. CheckBox сохраняется системой по ID. Это переживает пересоздание, но не является постоянной базой данных.

## Что изменено при проверке

Добавлен доступ ко всем учебным макетам через меню; выбранный макет и текст ButtonClicker сохраняются при повороте. В подписи ButtonClicker шаблон X заменён номером5. Insets учитывают системные панели и клавиатуру. Комментарии и актуальный подробный разбор добавлены в существующие исходники.
''',
'Lesson2':'''# Инструкция по защите практики №2

Студент: Зубарев Василий Сергеевич, БИСО-02-22, №5. Требования: [Практика № 2.pdf](Практика%20№%202.pdf).

## Последовательность демонстрации

1. **ActivityLifecycle.** Введите текст, откройте Logcat с тегом `LifecycleMain`. Первый запуск: onCreate → onStart → onResume. Home: onPause → onStop; возврат существующего экземпляра: onRestart → onStart → onResume. Back и поворот могут приводить к другим сценариям, поэтому опирайтесь на реальный журнал, а не требуйте onDestroy при любом выходе. Покажите input до и после поворота.
2. **MultiActivity.** Введите ФИО/произвольную строку, откройте SecondActivity. MainActivity читает input, создаёт явный Intent и кладёт `EXTRA_TEXT`; SecondActivity читает тот же ключ и показывает received. Ключ extra не равен содержимому строки. Back вызывает finish; первый экран остаётся в стеке. Сравните `MultiMain` и `MultiSecond` в Logcat.
3. **IntentFilter.** Откройте страницу МИРЭА и затем список отправки текста. ACTION_VIEW + HTTPS URI ищут браузер; ACTION_SEND + text/plain + EXTRA_TEXT описывают передачу строки. createChooser предлагает обработчиков. MAIN/LAUNCHER относится к запуску самого учебного приложения. Показ chooser не означает отправку сообщения.
4. **ToastApp.** Проверьте пустую строку (0), `MIREA` (5), `A B` (3). `codePointCount` считает Unicode code points с пробелами; это отличается от UTF-16 length для emoji. getString подставляет count в `%1$d`; Toast.show выводит сообщение, а result оставляет читаемую копию.
5. **NotificationApp.** Разрешите уведомления и нажмите кнопку. Покажите Mirea в системной шторке. CHANNEL_ID — канал настроек, NOTIFICATION_ID=1 — обновляемая запись, PERMISSION_CODE — запрос разрешения. На API33+ ответ приходит в callback; нельзя отправлять сразу после requestPermissions. PendingIntent описывает будущий переход при нажатии на уведомление. Отказ в разрешении должен давать понятный статус.
6. **Dialog.** Откройте AlertDialog и покажите все три ответа. Затем TimePickerDialog, DatePickerDialog и ProgressDialog. FragmentManager управляет показом/восстановлением DialogFragment. Calendar задаёт исходный выбор; месяц callback равен 0..11 и увеличивается только при показе. Snackbar и поле result отображают выбранные данные. ProgressDialog здесь учебный indeterminate индикатор, а не доказательство сетевого запроса.

## Разбор в отладчике

Откройте ToastApp/MainActivity.java, поставьте breakpoint на строку создания `String message` в `onClickCount`. Выберите ToastApp и Debug. Введите MIREA и нажмите подсчёт: при остановке `text="MIREA"`, `count=5`. Выполните Step Over (F8), проверьте message, затем Resume (F9). После демонстрации удалите breakpoint (Ctrl+F8), чтобы обычный Run не останавливался. Номер строки смотрите в текущем исходнике/РАЗБОР_КОДА.md; комментарии могут сдвигать его.

## Проверка

В папке verification сохранены проверка каждого модуля, журналы lifecycle, доказательства запросов разрешения и системной шторки, результатов диалогов, portrait/landscape. Скрипт `check_apps.py` запускает реальные собранные APK через ADB из установленного SDK; он не подменяет Gradle сборку и не считается unit тестом Java логики.
''',
'Lesson3':'''# Инструкция по защите практики №3

Студент: Зубарев Василий Сергеевич, БИСО-02-22, №5. Требования: [assignment/Практика № 3.pdf](assignment/Практика%20№%203.pdf).

## Последовательность демонстрации

1. **IntentApp.** Нажмите передачу времени. dateInMillis фиксируется один раз, SimpleDateFormat создаёт dateString; TIME_KEY согласован с getStringExtra во второй Activity. SecondActivity вычисляет `square=STUDENT_NUMBER*STUDENT_NUMBER`, то есть25, и подставляет square/time в `%1$d/%2$s`. При возврате первый экран показывает то же время, а не новый результат измерения.
2. **Sharer.** Покажите ACTION_SEND text/plain и chooser; выберите локальный Sharer receiver для проверки EXTRA_TEXT. Manifest экспортирует ShareActivity для SEND/DEFAULT/text/plain. Отдельный picker запускает ACTION_PICK image/* и получает content URI через Activity Result API. Камера возвращает Bitmap миниатюры через TakePicturePreview; это не полноразмерный файл. Отмена может вернуть null, поэтому callback проверяет данные. Покажите сохранение результата и превью при повороте.
3. **FavoriteBook.** MainActivity передаёт книгу/цитату разработчика в два extra; ShareActivity читает их в TextView. Введите свою книгу и цитату в EditText, нажмите отправку: trim проверяет пустые поля, getString формирует USER_MESSAGE, setResult(RESULT_OK,data) готовит ответ, finish возвращает первый экран. Launcher callback принимает ответ только при RESULT_OK и ненулевых данных. Покажите отмену: ранее полученный результат сохраняется.
4. Личные значения разработчика задаются в `FavoriteBook/src/main/res/values/strings.xml`, ресурсы `developer_book` и `developer_quote`. Методичка прямо требует ВАШУ книгу и ВАШУ цитату. До получения личных данных эти два значения нельзя считать завершённой персонализацией; никакая проверка непустоты заглушки не доказывает выполнение этого пункта.
5. **SystemIntentsApp.** ACTION_DIAL открывает номер89811112233 без звонка; ACTION_VIEW открывает developer.android.com; geo:55.749479,37.613944 открывает установленный Google Maps. Объясните схему Uri и поиск обработчика. Отсутствующее приложение даёт ActivityNotFoundException, это обработка ошибки, а не успешный показ карты.
6. **SimpleFragmentApp.** В portrait переключайте First/Second и введите разные note. `selected` — тег выбранного фрагмента; `firstSaved/secondSaved` — независимые снимки состояния, включая скрытый экран. Перед replace сохраняется уходящий фрагмент; setInitialSavedState восстанавливает новый; commitNow завершает замену. В landscape присутствует secondContainer, поэтому twoPane=true, два фрагмента добавляются в контейнеры с весами1:2. Поверните обратно и проверьте обе заметки.
7. **MireaProject.** Откройте папку MireaProject отдельно как Gradle проект, запустите app. На DataFragment покажите карточки кибербезопасности, отступы, семантические цвета Material3 и прокрутку. MireaApplication применяет DynamicColors там, где их поддерживает ОС. Через гамбургер откройте WebViewFragment, загрузите страницу по умолчанию МИРЭА, затем HTTPS example.com, вернитесь по истории и поверните экран. Открытая шторка должна закрываться Back раньше истории браузера.
8. В MireaProject свяжите menu `nav_data/nav_web`, mobile_navigation.xml, NavHostFragment, NavController и AppBarConfiguration. Binding создаётся из XML; binding фрагмента очищается в onDestroyView. WebView.saveState/restoreState сохраняют историю отдельно от обычных View. WebViewClient управляет адресами/ошибками, WebChromeClient сообщает прогресс. Подробный разбор контрольного проекта находится в [MireaProject/РАЗБОР_КОДА.md](MireaProject/РАЗБОР_КОДА.md).

## Что изменено при проверке

Квадрат номера вычисляется в Java. SimpleFragmentApp сохраняет ввод обоих фрагментов при переключении, повороте и восстановлении. В MireaProject добавлен `layout-land/fragment_web_view.xml`: адрес и четыре кнопки размещаются в одну строку, остальная высота отдаётся странице. Проверены загрузка, обновление и сохранение истории при повороте. Добавлены подробные комментарии к исходникам/ресурсам и разбор каждого файла. Скрипты проверки используют реальный текущий каталог/эмулятор и сохраняют отдельные свежие доказательства.
'''
}

MODULES={
'Lesson1':'app, layouttype, control_lesson1, buttonclicker',
'Lesson2':'ActivityLifecycle, MultiActivity, IntentFilter, ToastApp, NotificationApp, Dialog',
'Lesson3':'IntentApp, Sharer, FavoriteBook, SystemIntentsApp, SimpleFragmentApp; отдельный проект MireaProject/app'
}

def run():
 for project in DEFENSE:
  content=DEFENSE[project]+COMMON.format(verify='Verify '+project)
  files={'README.md':f'# {project} — практическое занятие\n\nОбновлено 09.10.2026. Модули: {MODULES[project]}.\n\n[Инструкция по защите](ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) • [Подробный разбор кода](РАЗБОР_КОДА.md) • [Свежая проверка](verification/audit-2026-10-09/ОТЧЁТ.md)\n'+COMMON.format(verify='Verify '+project),
         'ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md':content}
  if project in ('Lesson1','Lesson3'):
   n='Инструкция по реализации и защите практики № '+project[-1]+'.md'
   if (ROOT/project/n).exists():files[n]=content
  parts=[]
  for relative,new in files.items():
   f=ROOT/project/relative
   a.add_patch(parts,relative,f.read_text(encoding='utf-8') if f.exists() else None,new)
  if project=='Lesson3':
   child='MireaProject/README.md'
   new='# MireaProject — контрольное задание №3\n\nОткрывается как самостоятельный Gradle проект. Конфигурация app запускает приложение; Verify MireaProject собирает APK, запускает lint и имеющиеся unit tests.\n\n[Подробный разбор](РАЗБОР_КОДА.md) • [Сценарий защиты](../ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) • [Свежие доказательства](../verification/audit-2026-10-09/ОТЧЁТ.md)\n'+COMMON.format(verify='Verify MireaProject').replace('verification/audit-2026-10-09','../verification/audit-2026-10-09')
   a.add_patch(parts,child,(ROOT/project/child).read_text(encoding='utf-8'),new)
  (a.OUT/(project+'-instructions.patch')).write_text('*** Begin Patch\n'+''.join(parts)+'*** End Patch\n',encoding='utf-8')
  print(project,len(parts),'documents')

if __name__=='__main__':run()
