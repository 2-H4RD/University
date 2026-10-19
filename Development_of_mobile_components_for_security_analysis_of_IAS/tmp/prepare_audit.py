"""Готовит предложения и инструкции. Исходники меняет только Android Studio apply_patch."""
from pathlib import Path
import re, json, difflib, xml.etree.ElementTree as ET

ROOT = Path.cwd()
OUT = ROOT / 'tmp/audit-proposals'
OUT.mkdir(parents=True, exist_ok=True)
META = {
 'app': ('Первое приложение', 'Activity загружает activity_main.xml. ConstraintLayout задаёт положение TextView через привязки. Это исходная точка для исследования структуры app, manifest, Java и ресурсов. Здесь нет обработчиков: экран статичен.'),
 'layouttype': ('Типы компоновки', 'По умолчанию показывается activity_second: EditText и шесть кнопок. В layout-land лежит вариант с тремя рядами по две кнопки. LinearLayout располагает детей в линию; вложенные horizontal-контейнеры образуют две строки по три кнопки. TableLayout выравнивает три TableRow по столбцам. ConstraintLayout связывает края элементов с родителем и друг с другом. Меню «Макет» позволяет показать каждый этап упражнения без редактирования setContentView перед защитой.'),
 'control_lesson1': ('Собственный экран', 'Контакт составлен из ImageView, TextView, EditText, CheckBox, Button и ImageButton. Портретная версия использует constraints, альбомная размещает изображение слева и форму справа с весами 1:2. ID nameInput и favoriteCheckBox одинаковы в обеих версиях: Android переносит ввод и отметку при пересоздании Activity. Задание проверяет компоновку; сохранение контакта и телефонный вызов здесь не заданы.'),
 'buttonclicker': ('Два способа обработки событий', 'tvOut хранит ссылку на поле результата, btnWhoAmI и btnItIsNotMe - на кнопки, checkBox - на флажок. oclBtnWhoAmI является объектом View.OnClickListener: onClick меняет текст на номер 5 и вызывает toggle. Вторая кнопка вызывает public void onItIsNotMeClick(View view) через android:onClick из XML. В обоих случаях меняются текст и флажок. Последний текст сохраняется в Bundle; состояние CheckBox сохраняет Android по ID.'),
 'ActivityLifecycle': ('Жизненный цикл', 'TAG=LifecycleMain отделяет сообщения упражнения в Logcat. onCreate создаёт XML; onStart делает экран видимым; onResume означает готовность к взаимодействию. onPause фиксирует потерю активного состояния, onStop - прекращение видимости. onRestart возникает при возвращении остановленного экземпляра. onDestroy завершает экземпляр, но не гарантирован при уничтожении процесса. EditText input автоматически сохраняется при пересоздании, так как имеет ID. onSaveInstanceState и onRestoreInstanceState - callbacks состояния, а не отдельные стадии жизненного цикла.'),
 'MultiActivity': ('Передача строки', 'onClickNewActivity читает input.getText().toString(), создаёт явный Intent(this, SecondActivity.class) и добавляет строку через putExtra(EXTRA_TEXT,...). EXTRA_TEXT - согласованный строковый ключ, а не текст сообщения. SecondActivity читает getIntent().getStringExtra(MainActivity.EXTRA_TEXT) и записывает в received. null означает отсутствие extra; пустая строка является допустимым введённым значением. finish закрывает второй экран и возвращает первый из стека. MultiMain и MultiSecond помогают сравнить callbacks двух Activity.'),
 'IntentFilter': ('Неявные намерения', 'ACTION_VIEW вместе с HTTPS URI открывает страницу МИРЭА. ACTION_SEND, MIME text/plain, EXTRA_SUBJECT и EXTRA_TEXT описывают передачу текста. createChooser каждый раз показывает список обработчиков. В manifest MAIN/LAUNCHER обозначают точку входа. launchSafely ловит ActivityNotFoundException, если подходящего приложения нет. Само появление chooser ещё не означает отправку сообщения.'),
 'ToastApp': ('Подсчёт символов', 'onClickCount читает input без trim, поэтому пробелы считаются. text - String, count - количество Unicode code points от 0 до text.length(), message - форматированная строка из count_result. UTF-16 длина и число code points могут различаться для emoji; составной emoji может содержать несколько code points. Toast.makeText(...).show() выводит временное сообщение, result оставляет его читаемую копию. onSaveInstanceState сохраняет этот результат отдельно, EditText сохраняет Android.'),
 'NotificationApp': ('Уведомления', 'CHANNEL_ID=lesson2_student обозначает канал, NOTIFICATION_ID=1 - отдельную запись уведомления, PERMISSION_CODE=200 - запрос разрешения. Это три разных пространства идентификаторов. onCreate регистрирует NotificationChannel, так как minSdk=26. onClickSendNotification запрашивает POST_NOTIFICATIONS только с API 33. После согласия callback вызывает sendNotification; при отказе показывает статус. sendNotification проверяет разрешение, общий выключатель уведомлений и важность канала. PendingIntent содержит действие будущего нажатия. Builder формирует заголовок Mirea, иконку, короткий и расширенный текст. notify(1,...) обновляет одну запись.'),
 'Dialog': ('Диалоговые окна', 'MainActivity открывает четыре DialogFragment через showOnce и FragmentManager. Теги alert/time/date/progress помогают обнаружить уже открытое окно. MyDialogFragment создаёт AlertDialog.Builder с тремя ответами; callbacks вызывают методы Activity. MyTimeDialogFragment реализует OnTimeSetListener, MyDateDialogFragment - OnDateSetListener. Calendar задаёт начальное значение устройства. Месяц приходит как 0..11: +1 применяется только при показе. Snackbar сообщает выбранную дату/время, result сохраняет копию. ProgressDialog работает в режиме indeterminate и закрывается вручную; он оставлен как API, явно требуемый заданием.'),
 'IntentApp': ('Время и квадрат номера', 'TIME_KEY=sent_time используется и в putExtra, и в getStringExtra. dateInMillis фиксирует системное время в момент нажатия, Date оборачивает миллисекунды, sdf форматирует yyyy-MM-dd HH:mm:ss, dateString является передаваемой строкой. SecondActivity получает именно эту строку, а не вычисляет новое время. STUDENT_NUMBER=5, square=STUDENT_NUMBER*STUDENT_NUMBER даёт 25. Ресурс result подставляет square и time по позициям %1$d и %2$s. Кнопка back вызывает finish.'),
 'Sharer': ('Обмен с другими приложениями', 'message - редактируемый текст для ACTION_SEND; createChooser выбирает получателя. ShareActivity экспортирована и объявляет SEND/DEFAULT/text/plain и image/*. Приём проверяет действие и MIME, извлекает EXTRA_TEXT для текста или EXTRA_STREAM для изображения. picker - ActivityResultLauncher<Intent> с контрактом StartActivityForResult: callback проверяет RESULT_OK и ненулевой Uri. camera - ActivityResultLauncher<Void> с TakePicturePreview: получает Bitmap миниатюры либо null при отмене. pickedText и cameraText хранят подписи, thumbnail - небольшое превью. Bundle сохраняет эти значения при повороте. Встроенные обработчики объявлены до onCreate и регистрируются в одинаковом порядке.'),
 'FavoriteBook': ('Результат второй Activity', 'BOOK_NAME_KEY и QUOTES_KEY передают книгу и цитату разработчика на второй экран; USER_MESSAGE передаёт составленный ответ обратно. launcher зарегистрирован через Activity Result API. MainActivity берёт developer_book/developer_quote из strings.xml и вызывает launcher.launch(intent). ShareActivity читает extras, отображает их, затем получает userBook и userQuote из двух EditText. trim удаляет крайние пробелы; пустое значение вызывает setError и return. Intent data служит контейнером ответа без адреса получателя. setResult(RESULT_OK,data), затем finish возвращают сообщение. RESULT_OK=-1, RESULT_CANCELED=0. При отмене прежний ответ не меняется.'),
 'SystemIntentsApp': ('Телефон, браузер, карта', 'Три setOnClickListener связывают кнопки с onClickCall/onClickOpenBrowser/onClickOpenMaps. ACTION_DIAL с tel:89811112233 открывает набор номера. ACTION_VIEW с HTTPS открывает браузер, с geo:55.749479,37.613944 - карту. open(intent) выполняет запуск и показывает action/data в status; ActivityNotFoundException превращается в понятное сообщение. URI содержит схему и данные: Android ищет получателя по фильтрам. Приложение карты требуется в образе эмулятора, одного наличия geo URI недостаточно.'),
 'SimpleFragmentApp': ('Фрагменты и ориентация', 'FIRST/SECOND - стабильные теги фрагментов. selected хранит выбранный экран portrait, twoPane определяется наличием secondContainer из layout-land. FragmentManager восстанавливает старые экземпляры; их SavedState переносится в новый набор контейнеров. commitNow завершает удаление/добавление до дальнейшей работы. В portrait show(tag) заменяет один фрагмент через replace(...).commit(); в landscape два add создают панели с весами 1:2. Фрагменты используют inflater.inflate(...,container,false): менеджер сам прикрепляет View. Фрагменты не обращаются друг к другу. Состояние каждого поля note хранится независимо, включая переключение и поворот.'),
 'MireaProject': ('Navigation Drawer и браузер', 'MireaApplication включает DynamicColors для Material You. ActivityMainBinding создаётся из activity_main.xml; binding содержит типизированные ссылки на drawerLayout, navView, appBarMain и toolbar. NavHostFragment содержит NavController, mobile_navigation.xml задаёт DataFragment и WebViewFragment. ID nav_data/nav_web совпадают в меню, графе и AppBarConfiguration. NavigationUI связывает эти элементы и управляет заголовком/гамбургером. DataFragment отображает карточки отрасли в NestedScrollView. WebViewFragment управляет binding только пока есть View, сохраняет историю в webState, проверяет HTTPS адреса, показывает реальный прогресс, обработку ошибок, Home/Reload/Back. При открытой шторке Back закрывает её раньше истории WebView.'),
}

METHODS = {
 'onCreate': 'Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и регистрация действий. Это не функция, вызываемая кнопкой.',
 'onStart':'Экран становится видимым. super сохраняет поведение AndroidX; Log.i выводит событие с TAG. Повторный onStart не обязательно означает новый onCreate.',
 'onResume':'Activity готова взаимодействовать с пользователем. После возврата на существующий экран callback вызывается снова. Здесь не следует заново стирать содержимое EditText.',
 'onPause':'Activity теряет активное состояние. Она может ещё быть видна. Callback не равен закрытию приложения и не гарантирует последующий onDestroy.',
 'onStop':'Activity больше не видна. Существующий экземпляр может остаться в памяти и вернуться через onRestart.',
 'onRestart':'Возвращается остановленный существующий экземпляр; дальше идут onStart и onResume. При новом экземпляре вместо этого вызывается onCreate.',
 'onDestroy':'Завершает текущий экземпляр. Поворот тоже может вызвать уничтожение/создание Activity. При уничтожении процесса системой callback не гарантируется.',
 'onSaveInstanceState':'outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение. super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище и не замена файлу/базе данных.',
 'onRestoreInstanceState':'state содержит ранее сохранённые значения. Родитель восстанавливает View по их ID. Метод вызывается после onStart только при наличии сохранённого состояния.',
 'applyInsets':'root - корневой View; left/top/right/bottom - исходный padding XML. bars - системные панели, ime - клавиатура. Listener прибавляет Insets к исходным отступам, поэтому повторное событие не увеличивает padding бесконечно. max выбирает нижнюю неперекрываемую область.',
 'applySystemBarInsets':'root - корень текущего макета. Четыре переменные запоминают исходный padding. Insets дают размеры системных панелей и клавиатуры; к ним добавляются исходные отступы. Listener работает и после поворота/изменения окна.',
 'apply':'Статический метод принимает root текущей разметки. Конструктор закрыт: экземпляры ScreenInsets не нужны. Маска systemBars | ime объединяет области системных панелей и клавиатуры, беря максимальный отступ по каждой стороне.',
 'onClickNewActivity':'view - нажатая кнопка из android:onClick. input ссылается на EditText. intent адресует SecondActivity; EXTRA_TEXT согласовывает имя extra. startActivity отправляет запрос Android, а не вызывает Java-конструктор Activity вручную.',
 'onClickBack':'view - кнопка возврата. finish завершает только текущую Activity и позволяет Android показать предыдущую из стека.',
 'onItIsNotMeClick':'public void и один параметр View обязательны для android:onClick. tvOut.setText меняет содержимое; checkBox.toggle инвертирует boolean checked. btnItIsNotMe найден в коде, но listener этой кнопки назначен XML.',
 'onClickCount':'Получает String text из input. countPointCount считает кодовые точки, getString подставляет count в ресурс. Toast - временный вывод; result - постоянная копия. view обозначает источник события и здесь не используется.',
 'onClickOpenBrowser':'Создаёт URI веб-страницы и неявный Intent ACTION_VIEW. Адрес обработчика не задан: его выбирает ОС. HTTPS использует защищённое соединение.',
 'onClickShare':'Создаёт ACTION_SEND и MIME text/plain. EXTRA_TEXT - содержимое, EXTRA_SUBJECT - тема. createChooser принудительно предлагает список подходящих получателей. Выполнение startActivity ещё не означает фактическую отправку адресату.',
 'launchSafely':'intent - полностью подготовленный запрос. try выполняет startActivity; catch обрабатывает отсутствие подходящей Activity. Исключение нельзя считать успешным выполнением задания.',
 'onClickSendNotification':'view - кнопка из XML. Проверка SDK_INT нужна, чтобы POST_NOTIFICATIONS запрашивалось только с API 33. requestPermissions асинхронен: return заканчивает обработчик, а отправка продолжается в callback после ответа.',
 'onRequestPermissionsResult':'requestCode сравнивается с PERMISSION_CODE. grantResults может быть пустым, поэтому сначала проверяется length. Значение PERMISSION_GRANTED означает согласие; при отказе изменяется status. Ответ передаётся родителю AndroidX.',
 'sendNotification':'manager обращается к системному сервису, channel описывает настройки канала. open - Intent будущего нажатия, pending - PendingIntent, builder - конструктор содержимого. build создаёт Notification; notify с постоянным ID заменяет прежнюю запись. Статус успеха обновляется после вызова сервиса.',
 'onClickShowDialog':'Создаёт MyDialogFragment и передаёт в showOnce с тегом alert. Окно конструирует сам фрагмент в onCreateDialog.',
 'onClickShowTime':'Создаёт фрагмент штатного TimePickerDialog. Тег time отличает его от других диалогов.',
 'onClickShowDate':'Создаёт фрагмент DatePickerDialog с тегом date. Дата задаётся Calendar устройства и возвращается listener.',
 'onClickShowProgress':'Создаёт учебный ProgressDialog. Вращение не отражает реальную сетевую работу; закрытие выполняет пользователь.',
 'showOnce':'dialog - новый DialogFragment, tag - его строковое имя в FragmentManager. findFragmentByTag предотвращает повторный показ уже открытого окна. DialogFragment поддерживает восстановление при повороте.',
 'onOkClicked':'Вызывает showChoice с ресурсом положительного ответа «Иду дальше». Этот callback связан с setPositiveButton.',
 'onNeutralClicked':'Вызывает showChoice с ответом «На паузе». Порядок отображения кнопок задаёт тема, а не имя метода.',
 'onCancelClicked':'Вызывает showChoice с отрицательным ответом «Нет». Это выбор кнопки диалога, а не отмена Activity Result.',
 'showChoice':'messageId - целочисленный ID строкового ресурса. getString превращает его в String message. TextView result и Toast показывают одинаковый ответ.',
 'onTimeSelected':'hour и minute - значения TimePicker. getString форматирует оба числа; шаблон %02d дополняет число ведущим нулём.',
 'onDateSelected':'year/month/day приходят от DatePicker. month имеет диапазон 0..11; +1 выполняется только для понятного пользователю отображения.',
 'showPickerResult':'text - уже отформатированный результат. TextView оставляет его на экране, Snackbar показывает короткое уведомление внизу текущего View.',
 'onCreateDialog':'DialogFragment запрашивает объект Dialog. savedInstanceState может содержать восстановленное состояние. requireContext гарантирует контекст прикреплённого фрагмента. Возвращённое окно показывает и сохраняет FragmentManager.',
 'onDateSet':'view - сам DatePicker, year/month/dayOfMonth - подтверждённый выбор. requireActivity возвращает хозяина, приведение к MainActivity позволяет вызвать onDateSelected.',
 'onTimeSet':'view - TimePicker, hourOfDay/minute - подтверждённое время. callback передаёт его MainActivity, которая занимается форматированием и выводом.',
 'getInfoAboutBook':'view - кнопка открытия. intent содержит явный адрес ShareActivity и два extra разработчика. launcher.launch запускает экран в рамках контракта возврата результата.',
 'showNoApp':'Toast объясняет отсутствие системного обработчика. Метод вызывается из catch, не выдавая ошибку за успешно полученный результат.',
 'onClickCall':'ACTION_DIAL и tel URI открывают набор номера. Они не совершают звонок автоматически; CALL_PHONE для этого варианта не требуется.',
 'onClickOpenMaps':'geo URI хранит широту и долготу. ACTION_VIEW просит установленное приложение карты показать точку. Передача URI сама по себе не загружает приложение Maps.',
 'open':'intent - подготовленный ACTION_DIAL или ACTION_VIEW. status отображает action/data успешного запуска либо понятную ошибку ActivityNotFoundException.',
 'show':'tag - FIRST или SECOND. selected хранит активный экран. replace меняет содержимое одного FragmentContainerView; commit ставит транзакцию в очередь главного потока. SavedState сохраняет ввод уходящего фрагмента для возвращения.',
 'onCreateView':'inflater создаёт View из XML, container даёт параметры будущего родителя. false запрещает немедленное прикрепление: FragmentManager делает его сам. state - восстановленное состояние. Возвращается корень разметки/Binding.',
 'onViewCreated':'view уже создан, поэтому можно назначать listeners и клиенты WebView. Настройки браузера, обработка адреса, прогресс и история относятся к жизненному циклу View фрагмента.',
 'onDestroyView':'View фрагмента уничтожается, хотя сам Fragment может остаться. binding очищается, чтобы не удерживать прежнюю разметку. WebView останавливается, сохраняет историю и освобождает ресурсы.',
 'onSupportNavigateUp':'NavigationUI обрабатывает верхнюю кнопку toolbar по NavController и AppBarConfiguration. Возвращаем true при обработанном действии; иначе даём его родителю.',
 'openAddress':'address - trimmed строка поля url; при отсутствующей схеме добавляется https. uri разбирает адрес; scheme и host проверяются до loadUrl. При ошибке setError/status объясняют причину. При успехе скрывается клавиатура и запускается загрузка.',
 'handleOnBackPressed':'Вызывается включённым OnBackPressedCallback. Открытая шторка должна закрыться раньше истории браузера. Если шторка закрыта и есть история, WebView.goBack возвращает предыдущую страницу.',
 'shouldOverrideUrlLoading':'request содержит целевой Uri. true означает «не передавать загрузку WebView», false - продолжить обычную загрузку. Здесь разрешены HTTPS ссылки.',
 'onPageStarted':'Начало загрузки главной страницы сбрасывает pageFailed и показывает progress. url - текущий URL, icon - favicon, web - источник callback.',
 'onPageFinished':'Загрузка завершилась; url учитывает redirects. pageFailed отличает завершение с ошибкой. canGoBack определяет доступность истории и кнопки Back. После уничтожения View binding=null и callback пропускается.',
 'onReceivedError':'request.isForMainFrame отделяет ошибку основной страницы от ошибок отдельных картинок. Основная ошибка включает pageFailed и меняет status.',
 'onProgressChanged':'progress - реальное целое значение 0..100, переданное WebChromeClient. Оно передаётся ProgressBar без искусственной имитации.',
 'onDrawerOpened':'Шторка открыта: включаем drawerBack, чтобы первый Back закрыл её.',
 'onDrawerClosed':'Шторка закрыта: отключаем drawerBack и возвращаем обработку Back навигации/браузеру.',
 'onCreateOptionsMenu':'Добавляет учебный выбор макетов. menu содержит пункты с ID 1..5; они обозначают варианты разметки, а не ID ресурсов Android.',
 'onOptionsItemSelected':'item содержит выбранный пункт. Его itemId определяет layout, после чего showLayout загружает XML и обновляет безопасные отступы.',
 'showLayout':'layout - один из разрешённых R.layout. selectedLayout сохраняет текущий выбор; setContentView заново создаёт иерархию View, поэтому слушатель Insets назначается после загрузки каждого макета.',
}

VAR = {
 'binding':'Типизированные ссылки на View текущего XML. Во фрагментах живёт только от onCreateView до onDestroyView.',
 'savedInstanceState':'Bundle ранее сохранённого состояния; null при первом создании. Проверяется до getString/getBundle.',
 'outState':'Bundle назначения: приложение кладёт сюда собственные значения для будущего пересоздания.',
 'TAG':'Строка фильтра Logcat; не имеет отношения к ID элемента или extra Intent.',
 'EXTRA_TEXT':'Одинаковое имя строкового extra на отправляющем и принимающем экране.',
 'TIME_KEY':'Строковый ключ переданного времени и состояния подписи отправки.',
 'STUDENT_NUMBER':'Номер по журналу, равный 5; квадрат вычисляется умножением в коде.',
 'square':'Целочисленный результат STUDENT_NUMBER * STUDENT_NUMBER (25).',
 'BOOK_NAME_KEY':'Ключ книги разработчика в Intent от MainActivity к ShareActivity.',
 'QUOTES_KEY':'Ключ цитаты разработчика в том же Intent.',
 'USER_MESSAGE':'Ключ сформированного ответа пользователя при setResult и ключ сохранения отображённого результата.',
 'launcher':'Зарегистрированный запуск второй Activity с ожиданием её результата.',
 'picker':'Launcher выбора изображения; результат содержит code и Intent с content URI.',
 'camera':'Launcher TakePicturePreview с входом Void и выходом Bitmap или null.',
 'pickedText':'Отображаемая подпись результата выбора изображения либо отмены.',
 'cameraText':'Подпись получения/отмены миниатюры, которая сохраняется в Bundle.',
 'thumbnail':'Небольшой Bitmap, полученный от приложения камеры; это не полноразмерный файл фотографии.',
 'CHANNEL_ID':'Строковое имя канала настроек уведомлений.',
 'NOTIFICATION_ID':'Числовой ID одной записи; повторный notify с ID 1 обновляет её.',
 'PERMISSION_CODE':'Числовая метка запроса runtime-разрешения 200, проверяемая в callback.',
 'manager':'FragmentManager или NotificationManager: конкретный тип указан в декларации и определяет назначение.',
 'channel':'NotificationChannel с важностью, названием и описанием.',
 'pending':'PendingIntent будущего нажатия на уведомление; immutable защищает его содержимое от изменения получателем.',
 'builder':'Объект Builder: собирает свойства AlertDialog или Notification до create/build.',
 'intent':'Intent с действием, данными и/или адресом Activity; extra добавляется отдельно от URI data.',
 'data':'Возвращённый/возвращаемый Intent результата. Может быть null при отмене.',
 'uri':'Uri результата выбора либо разобранного адреса; content:// обозначает источник ContentProvider.',
 'text':'Строка введённого/принятого текста; место получения видно справа от =.',
 'count':'Число Unicode code points, включая пробелы.',
 'message':'Готовая строка интерфейса либо CharSequence входящего ACTION_SEND.',
 'input':'Ссылка на EditText из текущей разметки.',
 'result':'TextView результата либо ActivityResult callback; различаются типом и областью видимости.',
 'received':'TextView для строки, полученной вторым экраном.',
 'tvOut':'TextView результата ButtonClicker; поле класса доступно обоим обработчикам.',
 'btnWhoAmI':'Кнопка с Java listener для вывода номера по журналу.',
 'btnItIsNotMe':'Кнопка, чей callback назначен через android:onClick в XML.',
 'checkBox':'CheckBox; checked - boolean, toggle инвертирует его.',
 'oclBtnWhoAmI':'Объект реализации View.OnClickListener, передаваемый первой кнопке.',
 'dateInMillis':'Текущее время в миллисекундах от Unix epoch в момент нажатия.',
 'sdf':'SimpleDateFormat с шаблоном yyyy-MM-dd HH:mm:ss и locale устройства.',
 'dateString':'Отформатированная строка времени; именно она передаётся между экранами.',
 'time':'Полученная строка времени Intent либо View/диалог выбора; контекст задаётся типом.',
 'book':'Книга разработчика из extra, с fallback на строковый ресурс.',
 'quote':'Цитата разработчика из extra, с fallback на ресурс.',
 'bookInput':'EditText названия книги пользователя.',
 'quoteInput':'EditText цитаты пользователя.',
 'userBook':'Введённое название книги после удаления крайних пробелов.',
 'userQuote':'Введённая цитата после удаления крайних пробелов.',
 'now':'Calendar текущей даты/времени устройства для начального значения picker.',
 'root':'Корневой View текущей разметки; сюда назначаются Insets.',
 'left':'Исходный левый padding XML до добавления Insets.',
 'top':'Исходный верхний padding XML.',
 'right':'Исходный правый padding XML.',
 'bottom':'Исходный нижний padding XML.',
 'bars':'Insets системных панелей: left/top/right/bottom.',
 'ime':'Insets экранной клавиатуры, обычно важен нижний отступ.',
 'safe':'Объединённые Insets системных панелей и клавиатуры.',
 'FIRST':'Тег первого Fragment, значение first.',
 'SECOND':'Тег второго Fragment, значение second.',
 'selected':'Тег выбранного экрана portrait; сохраняется при повороте.',
 'twoPane':'boolean: существует ли secondContainer в выбранном layout-land.',
 'oldFirst':'Восстановленный Fragment с тегом FIRST.',
 'oldSecond':'Восстановленный Fragment с тегом SECOND.',
 'firstState':'SavedState первого Fragment для переноса в новую раскладку.',
 'secondState':'SavedState второго Fragment для такого же переноса.',
 'firstSaved':'SavedState первого Fragment для возврата после переключения и пересоздания.',
 'secondSaved':'SavedState второго Fragment для возврата после переключения и пересоздания.',
 'first':'Новый FirstFragment, который получит сохранённое состояние.',
 'second':'Новый SecondFragment, который получит сохранённое состояние.',
 'fragment':'Выбранный объект Fragment для транзакции.',
 'remove':'FragmentTransaction удаления восстановленных экземпляров из старых контейнеров.',
 'selectedLayout':'Целочисленный R.layout выбранного учебного макета, по умолчанию activity_second.',
 'navController':'Управляет текущим destination и стеком переходов графа Navigation.',
 'appBarConfiguration':'Описывает верхние пункты меню и DrawerLayout для кнопки toolbar.',
 'host':'NavHostFragment, у которого берётся NavController после загрузки XML.',
 'header':'View заголовка NavigationView, полученная через getHeaderView(0).',
 'headerLeft':'Исходный левый padding заголовка drawer.',
 'headerTop':'Исходный верхний padding заголовка drawer до statusBars.',
 'headerRight':'Исходный правый padding заголовка drawer.',
 'headerBottom':'Исходный нижний padding заголовка drawer.',
 'statusTop':'Высота status bar, добавляемая к заголовку drawer.',
 'drawerBack':'Callback закрытия открытой шторки. Включается только при её открытии.',
 'webState':'Bundle истории WebView при повороте и смене фрагмента.',
 'pageFailed':'boolean ошибки главного документа, чтобы не показывать ложный успех.',
 'webBack':'Callback возврата по истории WebView, включённый при canGoBack.',
 'address':'Строка адреса после trim и возможного добавления https://.',
 'scheme':'Схема URI; здесь разрешается https.',
 'keyboard':'InputMethodManager для скрытия клавиатуры перед отображением страницы.',
 'status':'TextView состояния операции или браузера.',
 'open':'Intent открытия MainActivity из уведомления.',
 'stream':'Uri входящего изображения из Intent.EXTRA_STREAM.',
}

def project_files(project):
 p=ROOT/project
 result=[]
 for mod in p.iterdir():
  if mod.is_dir() and (mod/'src/main').exists():
   result += list((mod/'src/main').rglob('*.java'))+list((mod/'src/main').rglob('*.xml'))
   if (mod/'src/test').exists():result += list((mod/'src/test').rglob('*.java'))
   if (mod/'build.gradle.kts').exists(): result.append(mod/'build.gradle.kts')
 for f in ['build.gradle.kts','settings.gradle.kts','gradle.properties','gradle/libs.versions.toml','gradle/wrapper/gradle-wrapper.properties']:
  if (p/f).exists(): result.append(p/f)
 return sorted(result)

def module_of(f,project):
 return 'MireaProject' if project.endswith('MireaProject') else f.relative_to(ROOT/project).parts[0]

def explanation_for_java(f, module):
 title,description=META[module]
 if f.name=='ExampleUnitTest.java':description='JUnit4 запускает @Test на JVM компьютера. assertEquals сравнивает ожидаемое 4 и фактическое 2+2. Тест не создаёт Activity, не использует эмулятор и не подтверждает практические сценарии: они проверяются отдельно на APK.'
 if f.name=='ScreenInsets.java': description=METHODS['apply']
 elif f.name=='FirstFragment.java' or f.name=='SecondFragment.java': description=METHODS['onCreateView']+' Каждая панель содержит собственный note; одинаковый ID внутри разных View фрагментов не смешивает их состояния.'
 return title,description

def method_explanation(f,module,name):
 if module=='MireaProject' and f.name=='WebViewFragment.java' and name=='onCreate':
  return 'Метод создаёт экземпляр Fragment, но ещё не его View. state содержит сохранённый Bundle либо null. Ключ web_state извлекает историю в поле webState; разметка будет создана отдельно в onCreateView, а restoreState выполняется в onViewCreated.'
 if module=='MireaProject' and f.name=='MireaApplication.java' and name=='onCreate':
  return 'Android создаёт Application перед Activity. super.onCreate выполняет базовую инициализацию. DynamicColors.applyToActivitiesIfAvailable(this) регистрирует применение системных динамических цветов к Activity, если устройство поддерживает эту возможность. Здесь не создаётся разметка и не загружается WebView.'
 if module=='MireaProject' and f.name=='MainActivity.java' and name=='handleOnBackPressed':
  return 'Callback drawerBack включён только при открытой шторке. Он закрывает DrawerLayout через GravityCompat.START; после onDrawerClosed отключается, чтобы Back снова обрабатывала навигация.'
 return METHODS[name]

def annotate_java(f,text,module):
 text=re.sub(r'^/\*\n \* ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ:.*?\*/\n','',text,flags=re.S)
 text=re.sub(r'(?m)^([ \t]*)// РАЗБОР \w+:\n(?:\1//[^\n]*\n)*','',text)
 title,desc=explanation_for_java(f,module)
 header='/*\n * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: '+title+'.\n'
 import textwrap
 header+='\n'.join(' * '+l for l in textwrap.wrap(desc,100,break_long_words=False))+'\n'
 header+=' * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.\n */\n'
 text=header+text
 lines=[]
 for line in text.splitlines():
  m=re.search(r'\b(?:public|private|protected)\s+(?:(?:static|final)\s+)*(?:[\w<>.?\[\]]+)\s+(\w+)\s*\(',line)
  if m and m.group(1) in METHODS:
   indent=re.match(r'\s*',line).group()
   desc=method_explanation(f,module,m.group(1))
   lines.append(indent+'// РАЗБОР '+m.group(1)+':')
   lines.extend(indent+'// '+v for v in textwrap.wrap(desc,100,break_long_words=False))
  lines.append(line)
 return '\n'.join(lines)+'\n'

ATTR = {
 'id':'Создаёт/ссылается на ID ресурса; Java ищет View через R.id, Binding строит поле по имени.',
 'layout_width':'Ширина: match_parent занимает область родителя, wrap_content - содержимое, 0dp зависит от weights/constraints.',
 'layout_height':'Высота с теми же правилами. Размер в dp не зависит от плотности экрана.',
 'orientation':'Расположение детей LinearLayout: вертикально или горизонтально.',
 'layout_weight':'Доля оставшегося пространства LinearLayout/TableRow; сравнивается с весами соседей.',
 'text':'Реальное содержимое элемента; @string означает ссылку на строковый ресурс.',
 'hint':'Подсказка пустого поля, не является введённым значением.',
 'inputType':'Тип ввода и вид клавиатуры; textPersonName, textUri, textMultiLine задают разные режимы.',
 'onClick':'Имя public void callback(View) Activity, вызываемого через XML.',
 'padding':'Внутренний отступ между краем View и содержимым. Insets прибавляются отдельно.',
 'gravity':'Расположение содержимого внутри самого элемента/контейнера.',
 'layout_gravity':'Расположение элемента внутри родителя, где поддерживается контейнером.',
 'textSize':'Размер текста в sp, учитывает системный масштаб шрифта.',
 'textStyle':'Начертание: например bold.',
 'src':'Изображение ImageView/ImageButton; @drawable или системный @android:drawable.',
 'contentDescription':'Описание для доступности; не заменяет видимый текст.',
 'stretchColumns':'Столбцы TableLayout, которым разрешено растягиваться; * означает все.',
 'fillViewport':'ScrollView растягивает единственного ребёнка минимум до высоты видимой области.',
 'background':'Фон или ссылка на drawable/цвет темы.',
 'theme':'Тема компонента либо приложения.',
 'name':'Имя Activity/Fragment/разрешения/ресурса; смысл определяется тегом.',
 'exported':'Разрешает или запрещает запуск компонента другим приложением.',
 'mimeType':'MIME данные, подходящие этому intent-filter.',
 'scheme':'Схема URI для отбора неявного Intent.',
 'navGraph':'Граф Navigation для NavHostFragment.',
 'defaultNavHost':'Делает NavHost основным обработчиком навигации Back.',
 'menu':'Ресурс меню NavigationView; ID должны совпадать с destination графа.',
 'headerLayout':'Разметка заголовка NavigationView.',
 'startDestination':'Начальный ID фрагмента в Navigation graph.',
 'label':'Название destination или приложения.',
 'usesCleartextTraffic':'Разрешение нешифрованного HTTP трафика; браузер использует HTTPS.',
 'allowBackup':'Параметр системного резервного копирования приложения.',
 'color':'Цвет векторного path/ресурса или theme token.',
 'pathData':'Геометрия SVG-подобного пути VectorDrawable.',
 'viewportWidth':'Логическая ширина координат вектора, независимо от dp отображения.',
 'viewportHeight':'Логическая высота координат вектора.',
 'parent':'Родитель темы/style, от которого наследуются параметры.',
 'title':'Подпись пункта menu либо окна.',
 'icon':'Drawable иконки меню/приложения.',
 'autofillHints':'Подсказка службе автозаполнения, не изменяет getText.',
}

def attr_desc(key):
 k=key.split('}')[-1]
 if k.startswith('layout_constraint'):
  return 'Привязка указанной стороны View к стороне parent/элемента. Влияет на положение при реальном запуске.'
 if 'margin' in k.lower(): return 'Внешний отступ от соседей/края родителя в dp; отличается от padding.'
 if k.startswith('padding'): return 'Внутренний отступ этой стороны View.'
 if k=='context' or k=='layout' or k=='openDrawer' or k=='showIn': return 'Подсказка preview Android Studio, когда находится в namespace tools; не выполняет Java-код.'
 return ATTR.get(k,'Настройка элемента '+k+'; точное значение приведено в соседней колонке.')

def annotate_xml(text,f):
 text=re.sub(r'<!--\n  ПОДРОБНЫЙ РАЗБОР РЕСУРСА .*?-->\n','',text,flags=re.S)
 try: root=ET.fromstring(text)
 except ET.ParseError: return text
 a='{http://schemas.android.com/apk/res/android}'
 note=['ПОДРОБНЫЙ РАЗБОР РЕСУРСА '+f.name+'.']
 if root.tag=='resources':
  note+=['strings: name становится R.string.name, значение - текст getString/setText.', 'Формат %1$s/%2$s подставляет строки, %1$d - число; dp задаёт отступы, sp - текст.', 'style/theme: parent наследует оформление, item переопределяет конкретный атрибут.', 'values-night автоматически выбирается при тёмной теме. Цвета темы используются через ?attr.']
 elif root.tag=='manifest':
  note+=['Manifest объявляет компоненты, разрешения и тему. MAIN/LAUNCHER - точка входа.', 'exported=true нужен launcher и внешним получателям; внутренние Activity используют false.', 'intent-filter: action описывает действие, category - категорию, data - MIME/URI.']
 else:
  note+=['XML описывает иерархию View. setContentView/inflate создаёт из неё реальные объекты.', 'layout-land выбирается системой в альбомной ориентации; имя файла остаётся тем же.', 'android - свойства runtime, app - AndroidX/Material, tools - только preview IDE.', 'id связывает XML с Java/Binding; @string хранит текст, ?attr берёт значение из темы.', 'padding - внутренний, margin - внешний отступ; dp - размеры, sp - размер текста.']
  ids=[(e.tag.split('.')[-1],e.get(a+'id')) for e in root.iter() if e.get(a+'id')]
  note+=['Элементы: '+tag+' '+id+'.' for tag,id in ids]
 note='<!--\n'+ '\n'.join('  '+v for v in note)+'\n-->\n'
 if text.startswith('<?xml'):
  declaration,body=text.split('?>',1)
  return declaration+'?>\n'+note+'\n'+body.lstrip('\n')
 return note+text

def add_patch(parts,relative,old,new):
 if old==new:return
 if old is None:
  parts.append('*** Add File: '+relative+'\n'+''.join('+'+l+'\n' for l in new.splitlines()))
 else:
  diff=list(difflib.unified_diff(old.splitlines(),new.splitlines(),n=3,lineterm=''))[2:]
  parts.append('*** Update File: '+relative+'\n'+'\n'.join('@@' if l.startswith('@@') else l for l in diff)+'\n')

COMMON='''## Как связаны файлы и исполнение

1. settings.gradle.kts включает application-модули и репозитории. build.gradle.kts подключает плагин Android. Каталог libs.versions.toml связывает alias с координатами библиотек и версиями.
2. Android Studio запускает Gradle на встроенном JDK. Java sourceCompatibility=11 задаёт уровень исходного языка, а не путь/версию JVM, на которой работает Gradle. Gradle wrapper фиксирует воспроизводимую версию сборщика.
3. Модуль компилирует Java, ресурсы и manifest в отдельный APK. namespace определяет пакет сгенерированных R/Binding; applicationId определяет установленное приложение. Разные applicationId позволяют держать все учебные APK на одном устройстве.
4. Android находит launcher Activity через MAIN/LAUNCHER. ОС создаёт её экземпляр и вызывает onCreate. Приложение не создаёт Activity через new.
5. setContentView(R.layout...) либо Binding.inflate создаёт View из XML. После этого findViewById(R.id...) возвращает конкретный объект; имя R - сгенерированная ссылка на ресурс, а не путь к файлу.
6. Пользователь нажимает кнопку. Listener/метод android:onClick выполняется в главном потоке. Асинхронные ActivityResult, permission и WebView callbacks приходят позже; return в обработчике не отменяет уже запущенный внешний экран.

## Язык Java на примерах этой практики

`private` ограничивает доступ классом; `public` нужен внешнему вызову и android:onClick; отсутствие модификатора означает доступ внутри package. `static final` - общая неизменяемая константа класса; `private` поле живёт вместе с экземпляром Activity/Fragment. Локальная переменная существует в блоке метода/callback. Одинаковое имя в разных блоках не означает один объект.

`extends AppCompatActivity`/`Fragment` задаёт наследование. `@Override` проверяет переопределение метода родителя. `super` вызывает родительскую реализацию, необходимую для AndroidX состояния. `this` обозначает текущий объект и также служит Context для Activity. Приведение `(TextView)` уточняет тип View; в этой версии findViewById обычно использует вывод типа.

`view -> ...` - lambda, реализующая один метод listener; `this::method` - ссылка на готовый метод подходящей сигнатуры. Код lambda исполняется по событию, а не сразу при setOnClickListener. Цепочка Builder возвращает builder после каждого set, завершаясь build/create. Тернарный `condition ? a : b` выбирает одно значение. `&&` проверяет правую часть только при истинной левой: проверка null/length защищает последующий доступ. `try/catch` обрабатывает конкретную ожидаемую ошибку.

`String` - текст; `int` - целое (код, ID, количество); `long` - миллисекунды времени; `boolean` - состояние; `Bundle` - пары ключ/значение; `Intent` - запрос запуска/контейнер результата; `Uri` - структурированный адрес; `Bitmap` - пиксельное изображение. ID ресурса int, тег фрагмента String, имя extra String и номер уведомления int решают разные задачи и не взаимозаменяемы.

## Отступы, ориентация и состояние

Поворот обычно уничтожает старую Activity и создаёт новую, автоматически выбирая layout-land. Поэтому ссылка на прежний View не является сохранённым состоянием. EditText и CheckBox с стабильными ID Android сохраняет автоматически; вычисленный результат TextView сохраняется явно в Bundle. После Home существующий экземпляр может остаться, но система вправе уничтожить процесс. Bundle не гарантирует сохранность данных после force-stop/новой установки и не является базой данных.

EdgeToEdge разрешает рисовать под системными панелями. Insets сообщают их размеры и область клавиатуры. Исходный padding запоминается до назначения listener; каждый callback вычисляет padding заново от исходного значения. Суммировать прошлый padding с новыми Insets нельзя: отступ будет нарастать. Для пересекающихся нижних областей используются максимум/объединение типов.

## Что показать в Android Studio на защите

Откройте конкретную папку с settings.gradle.kts, дождитесь Gradle Sync, выберите модуль и Pixel 9 API 35, нажмите Run. Покажите исходный Java callback, связанный XML ID и строку strings.xml, затем действие в Running Devices. В Logcat фильтруйте по package/tag; для ошибки ищите FATAL EXCEPTION и первую строку своего кода. Установите breakpoint внутри обработчика, нажмите Debug, вызовите действие, раскройте Local Variables и выполните Step Over; убедитесь, что значение изменилось после нужного оператора.

Сборка assembleDebug подтверждает компиляцию и создание APK. lintDebug проверяет статические проблемы, но не проверяет поведение кнопок. Проверки на эмуляторе дополнительно подтверждают реальные переходы и видимый результат. Их свежие результаты и ограничения находятся в verification/audit-2026-10-09. Каталоги build/.gradle и генерируемые R/Binding не редактируются: их создаёт Gradle.
'''

def md_escape(v):return str(v).replace('|','\\|').replace('\n','<br>')

def build_doc(project, files, proposals):
 chunks=['# Подробный разбор кода и защита '+project+'\n\nДата актуализации: 09.10.2026. Студент: Зубарев Василий Сергеевич, БИСО-02-22, №5.\n\nИнструкция описывает собственные исходники приложения, XML и настройки сборки. Сгенерированные R/Binding, build/.gradle и стандартный wrapper рассматриваются по назначению; их содержимое не является ручным кодом студента.\n',COMMON]
 modules=sorted({module_of(f,project) for f in files if '/src/main/' in f.as_posix()})
 for m in modules:
  title,description=META[m]
  chunks+=['\n## '+m+': '+title+'\n\n'+description+'\n']
  fs=[f for f in files if module_of(f,project)==m and f.suffix=='.java']
  for f in fs:
   text=proposals.get(f,f.read_text(encoding='utf-8'))
   rel=f.relative_to(ROOT/project).as_posix()
   chunks+=['\n### '+rel+'\n\n'+explanation_for_java(f,m)[1]+'\n']
   found=[]
   # Декларации полей и локальных переменных: имя привязано к фактическому месту в листинге.
   for i,line in enumerate(text.splitlines(),1):
    match=re.search(r'\b(?:String|int|long|boolean|Bundle|Intent|Uri|Bitmap|TextView|EditText|Button|CheckBox|View|Insets|Calendar|SimpleDateFormat|Date|Fragment(?:\.SavedState)?|FragmentManager|NotificationChannel|NotificationManagerCompat|PendingIntent|OnBackPressedCallback|NavController|AppBarConfiguration|NavHostFragment|\w+Binding|ActivityResultLauncher<[^>]+>)\s+(\w+)\s*(?:=|;)',line)
    if match:
     name=match.group(1)
     if name in VAR:found.append((name,i,VAR[name]))
   if found:
    chunks+=['\n| Переменная (строка) | Роль и область использования |\n|---|---|\n'+''.join(f'| `{name}` ({i}) | {md_escape(desc)} |\n' for name,i,desc in found)]
   methods=[]
   for i,line in enumerate(text.splitlines(),1):
    match=re.search(r'\b(?:public|private|protected)\s+(?:(?:static|final)\s+)*[\w<>.?\[\]]+\s+(\w+)\s*\(',line)
    if match and match.group(1) in METHODS:methods.append((match.group(1),i,method_explanation(f,m,match.group(1))))
   chunks+=['\n'+''.join('**'+name+' (строка '+str(i)+').** '+desc+'\n\n' for name,i,desc in methods)]
   chunks+=['Полный листинг с пояснениями (номера строк слева относятся к файлу):\n\n```java\n'+ '\n'.join(f'{i:4} | {l}' for i,l in enumerate(text.splitlines(),1))+'\n```\n']
  chunks+=['\n### Разметка и ресурсы '+m+'\n\nВ таблицах приведены реальные атрибуты: по их значениям можно найти связь с Java и поведение компонента.\n']
  for f in files:
   if module_of(f,project)!=m or f.suffix!='.xml':continue
   text=proposals.get(f,f.read_text(encoding='utf-8'))
   root=ET.fromstring(text)
   chunks+=['\n#### '+f.relative_to(ROOT/project).as_posix()+'\n\n']
   if root.tag=='resources':
    chunks+=['| Ресурс | Значение | Назначение |\n|---|---|---|\n']
    for e in root:
     value=''.join(e.itertext()).strip()
     role='Текст для R.string и форматирования getString.' if e.tag=='string' else 'Параметры оформления/цвета/размера, используемые XML и темой.'
     chunks+=['| '+md_escape(e.tag+': '+e.get('name',''))+' | '+md_escape(value)+' | '+role+' |\n']
   else:
    chunks+=['| Элемент / атрибут | Фактическое значение | Как влияет |\n|---|---|---|\n']
    for e in root.iter():
     tag=e.tag.split('.')[-1]
     if not e.attrib:chunks+=['| '+tag+' | - | Контейнер/узел иерархии. |\n']
     for k,v in e.attrib.items():
      ns=k[1:].split('}')[0] if k.startswith('{') else ''
      prefix='tools:' if ns.endswith('/tools') else 'android:' if ns.endswith('/android') else 'app:' if ns.endswith('/res-auto') else ''
      key=prefix+k.split('}')[-1]
      chunks+=['| '+md_escape(tag+' / '+key)+' | `'+md_escape(v)+'` | '+attr_desc(k)+' |\n']
 chunks+=['\n## Сборка и версии: точные значения\n\ncompileSdk/targetSdk=35 и minSdk=26 сохранены для требований и установленного учебного окружения. Советы lint о более новых версиях не означают неправильное выполнение задания. Версии ниже относятся к локальным исходникам, а не к обещанию самой новой версии SDK.\n']
 for f in files:
  if '/src/main/' in f.as_posix():continue
  text=proposals.get(f,f.read_text(encoding='utf-8'))
  chunks+=['\n### '+f.relative_to(ROOT/project).as_posix()+'\n\n```'+('kotlin' if f.name.endswith('.kts') else 'text')+'\n'+text+'\n```\n']
 chunks+=['''
`plugins` включает Android application: выходом будет APK. `defaultConfig` задаёт applicationId, minSdk, targetSdk и версии приложения; compileSdk определяет доступные при компиляции Android API, targetSdk включает поведение совместимости ОС, minSdk ограничивает минимальную поддерживаемую ОС. `implementation` добавляет библиотеку в приложение. AndroidX AppCompat даёт совместимые Activity/диалоги; Activity - EdgeToEdge/Activity Result; Material - темы, MaterialButton, Snackbar, DynamicColors; ConstraintLayout/DrawerLayout/Navigation - соответствующие контейнеры и переходы. `buildFeatures.viewBinding=true` генерирует Binding из XML, если включён в модуле.

`org.gradle.jvmargs` задаёт память процесса сборщика и UTF-8, `android.useAndroidX` включает AndroidX, configuration-cache сохраняет конфигурацию, workers.max ограничивает одновременные задачи. Wrapper distributionUrl фиксирует Gradle, distributionSha256Sum проверяет архив. local.properties содержит местный SDK path и создаётся Android Studio. `.run` сохраняет модуль запуска либо Gradle tasks, но устройство выбирается в IDE отдельно.

## Частые вопросы преподавателя

- Почему Java нельзя найти View до setContentView? Иерархия ещё не создана, поэтому получим null и возможный NullPointerException.
- Чем ресурс отличается от строки? R.string/R.id/R.layout - числовые идентификаторы; getString получает текст по ID, setContentView загружает XML по ID.
- Почему есть проверки null? При отмене/отсутствующем extra Intent и его значения могут отсутствовать. Это обычное условие, а не обязательно ошибка пользователя.
- Что изменится при повороте? Меняется экземпляр Activity и XML квалификатор; компактное состояние восстанавливается по Bundle/ID. Сохранённая ссылка на старую View не заменяет сохранение значения.
- Чем явный Intent отличается от неявного? Явный содержит класс Activity, неявный - действие/data/MIME; выбор обработчика делает Android по manifest-фильтрам.
- Почему finish не равно setResult? setResult готовит ответ, finish завершает второй экран; для возврата пользовательских данных нужны оба действия.
- Где менять данные студента и подписи? В соответствующих strings.xml/константах, а не в сгенерированном R или build. В IntentApp номер задаётся STUDENT_NUMBER.
- Как подтвердить выполнение? Показать требование PDF, участок Java, связанный XML и действие на запущенном APK; отдельно назвать границы проведённой проверки.

## Источники для объяснения API

Методички лежат в самом уроке (Lesson3: assignment). Сверены официальные страницы Android: [жизненный цикл Activity](https://developer.android.com/guide/components/activities/activity-lifecycle), [Activity Result API](https://developer.android.com/training/basics/intents/result), [жизненный цикл Fragment](https://developer.android.com/guide/fragments/lifecycle), [разрешение уведомлений](https://developer.android.com/develop/ui/compose/notifications/notification-permission). Полные листинги и таблицы выше описывают собственный учебный код; примеры документации не копируются.
''']
 return ''.join(chunks)

def prepare():
 METHODS['show']=METHODS['show'].replace('commit ставит транзакцию в очередь главного потока.','commitNow выполняет замену синхронно до следующего нажатия.')
 META['SimpleFragmentApp']=(META['SimpleFragmentApp'][0],META['SimpleFragmentApp'][1].replace('replace(...).commit();','replace(...).commitNow();'))
 META['Sharer'] = (META['Sharer'][0], META['Sharer'][1].replace('SEND/DEFAULT/text/plain и image/*. Приём проверяет действие и MIME, извлекает EXTRA_TEXT для текста или EXTRA_STREAM для изображения.', 'SEND/DEFAULT/text/plain. Приём проверяет действие и MIME и извлекает EXTRA_TEXT. Изображение выбирается отдельным ACTION_PICK, а не принимается текстовым фильтром.'))
 METHODS['onClickCount'] = METHODS['onClickCount'].replace('countPointCount','codePointCount')
 ATTR.update({
  'cardBackgroundColor':'Фон MaterialCardView; семантический цвет темы сохраняет контраст.',
  'cardCornerRadius':'Радиус скругления углов карточки в dp.',
  'checkableBehavior':'single допускает один выбранный пункт группы меню.',
  'clipToPadding':'Определяет, обрезает ли контейнер содержимое в области padding.',
  'fillColor':'Цвет заполнения path в VectorDrawable.',
  'width':'Физическая ширина VectorDrawable при отображении в dp.',
  'height':'Физическая высота VectorDrawable в dp.',
  'imeOptions':'Действие кнопки клавиатуры, например actionGo вызывает OnEditorActionListener.',
  'importantForAutofill':'no исключает учебное поле из службы автозаполнения.',
  'layout':'Ресурс включаемой через include разметки или подсказка tools:layout для preview.',
  'max':'Максимум индикатора прогресса, обычно 100.',
  'maxLines':'Максимальное число строк текста.',
  'minLines':'Минимальное число строк/высота поля.',
  'minHeight':'Минимальная высота элемента в dp, например 48dp для удобного нажатия.',
  'openDrawer':'tools:openDrawer=start показывает раскрытую шторку только в preview IDE.',
  'scaleType':'Способ масштабирования изображения внутри ImageView.',
  'singleLine':'Однострочное поле; не означает ограничение длины строки.',
  'strokeWidth':'Толщина обводки MaterialCardView/вектора.',
  'style':'Ссылка на стиль с общими атрибутами View.',
  'supportsRtl':'Поддержка зеркального интерфейса для языков справа налево.',
  'textColor':'Цвет текста; ?attr/colorOn... согласован с цветом соответствующего контейнера.',
  'textIsSelectable':'Позволяет выделять/копировать текст; также влияет на сохранение его состояния.',
  'visibility':'visible отображает View, invisible скрывает с сохранением места, gone убирает место.',
  'windowSoftInputMode':'adjustResize пересчитывает доступную область при открытой клавиатуре.',
 })
 for project in ['Lesson1','Lesson2','Lesson3','Lesson3/MireaProject']:
  files=project_files(project)
  parts=[]; proposals={}
  for f in files:
   old=f.read_text(encoding='utf-8'); text=old
   if f.suffix=='.java':text=annotate_java(f,text,module_of(f,project))
   elif f.suffix=='.xml':text=annotate_xml(text,f)
   elif f.name.endswith('.gradle.kts'):
    text=re.sub(r'^(?:// РАЗБОР:[^\n]*\n// namespace[^\n]*\n)+','',text)
    text='// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.\n// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.\n'+text
   proposals[f]=text
   add_patch(parts,f.relative_to(ROOT/project).as_posix(),old,text)
  doc=build_doc(project,files,proposals)
  previous=ROOT/project/'РАЗБОР_КОДА.md'
  add_patch(parts,'РАЗБОР_КОДА.md',previous.read_text(encoding='utf-8') if previous.exists() else None,doc)
  patch='*** Begin Patch\n'+''.join(parts)+'*** End Patch\n'
  name=project.replace('/','-')
  (OUT/(name+'.patch')).write_text(patch,encoding='utf-8')
  print(name, len(parts),'operations,',len(doc),'characters of explanation')

if __name__=='__main__':prepare()
