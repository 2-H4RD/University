/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Телефон, браузер, карта.
 * Три setOnClickListener связывают кнопки с onClickCall/onClickOpenBrowser/onClickOpenMaps.
 * ACTION_DIAL с tel:89811112233 открывает набор номера. ACTION_VIEW с HTTPS открывает браузер, с
 * geo:55.749479,37.613944 - карту. open(intent) выполняет запуск и показывает action/data в status;
 * ActivityNotFoundException превращается в понятное сообщение. URI содержит схему и данные: Android
 * ищет получателя по фильтрам. Приложение карты требуется в образе эмулятора, одного наличия geo URI
 * недостаточно.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson3.systemintentsapp;

import android.os.Bundle;
import android.content.Intent;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import android.content.ActivityNotFoundException;
import android.net.Uri;
/** Задание 1.9: три кнопки с обработчиками setOnClickListener. */
public class MainActivity extends AppCompatActivity {
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает состояние Activity.
        EdgeToEdge.enable(this); // Поддерживаем системное оформление Android 15.
        setContentView(R.layout.activity_main); // Сначала создаём View из XML.
        ScreenInsets.apply(findViewById(R.id.main)); // Убираем пересечение с панелями и клавиатурой.
        if (savedInstanceState != null) ((TextView) findViewById(R.id.status)).setText(savedInstanceState.getString("status"));
        findViewById(R.id.call).setOnClickListener(this::onClickCall); // Назначаем слушатель в коде.
        findViewById(R.id.browser).setOnClickListener(this::onClickOpenBrowser);
        findViewById(R.id.maps).setOnClickListener(this::onClickOpenMaps);
    }
    // РАЗБОР onClickCall:
    // ACTION_DIAL и tel URI открывают набор номера. Они не совершают звонок автоматически; CALL_PHONE для
    // этого варианта не требуется.
    public void onClickCall(View view) {
        open(new Intent(Intent.ACTION_DIAL, Uri.parse("tel:89811112233"))); // Открываем экран набора номера.
    }
    // РАЗБОР onClickOpenBrowser:
    // Создаёт URI веб-страницы и неявный Intent ACTION_VIEW. Адрес обработчика не задан: его выбирает ОС.
    // HTTPS использует защищённое соединение.
    public void onClickOpenBrowser(View view) {
        open(new Intent(Intent.ACTION_VIEW, Uri.parse("https://developer.android.com")));
    }
    // РАЗБОР onClickOpenMaps:
    // geo URI хранит широту и долготу. ACTION_VIEW просит установленное приложение карты показать точку.
    // Передача URI сама по себе не загружает приложение Maps.
    public void onClickOpenMaps(View view) {
        open(new Intent(Intent.ACTION_VIEW, Uri.parse("geo:55.749479,37.613944"))); // Карта с координатами из задания.
    }
    // РАЗБОР open:
    // intent - подготовленный ACTION_DIAL или ACTION_VIEW. status отображает action/data успешного запуска
    // либо понятную ошибку ActivityNotFoundException.
    private void open(Intent intent) {
        TextView status = findViewById(R.id.status);
        try {
            startActivity(intent); // Запускаем напрямую и обрабатываем отсутствие получателя.
            status.setText(getString(R.string.status, intent.getAction(), intent.getDataString()));
        } catch (ActivityNotFoundException exception) {
            status.setText(getString(R.string.no_app, intent.getDataString())); // Например, Maps может не быть в образе.
        }
    }
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    @Override protected void onSaveInstanceState(Bundle outState) {
        outState.putString("status", ((TextView) findViewById(R.id.status)).getText().toString());
        super.onSaveInstanceState(outState);
    }
}
