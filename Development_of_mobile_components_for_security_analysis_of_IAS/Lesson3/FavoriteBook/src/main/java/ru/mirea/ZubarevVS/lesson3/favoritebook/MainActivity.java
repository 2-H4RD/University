/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Результат второй Activity.
 * BOOK_NAME_KEY и QUOTES_KEY передают книгу и цитату разработчика на второй экран; USER_MESSAGE
 * передаёт составленный ответ обратно. launcher зарегистрирован через Activity Result API.
 * MainActivity берёт developer_book/developer_quote из strings.xml и вызывает launcher.launch(intent).
 * ShareActivity читает extras, отображает их, затем получает userBook и userQuote из двух EditText.
 * trim удаляет крайние пробелы; пустое значение вызывает setError и return. Intent data служит
 * контейнером ответа без адреса получателя. setResult(RESULT_OK,data), затем finish возвращают
 * сообщение. RESULT_OK=-1, RESULT_CANCELED=0. При отмене прежний ответ не меняется.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson3.favoritebook;

import android.os.Bundle;
import android.content.Intent;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import android.app.Activity;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

/** Задание 1.7: явный Intent туда, Activity Result API обратно. */
public class MainActivity extends AppCompatActivity {
    static final String BOOK_NAME_KEY = "book_name";
    static final String QUOTES_KEY = "quotes_name"; // Строковые константы предотвращают несовпадение ключей.
    static final String USER_MESSAGE = "MESSAGE";
    private final ActivityResultLauncher<Intent> launcher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(), result -> {
                if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                    String message = result.getData().getStringExtra(USER_MESSAGE); // Ответ подготовлен ShareActivity.
                    if (message != null) ((TextView) findViewById(R.id.textViewBook)).setText(message);
                } // При Back/Отмене оставляем предыдущий результат.
            });
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает состояние Activity.
        EdgeToEdge.enable(this); // Поддерживаем системное оформление Android 15.
        setContentView(R.layout.activity_main); // Сначала создаём View из XML.
        ScreenInsets.apply(findViewById(R.id.main)); // Убираем пересечение с панелями и клавиатурой.
        if (savedInstanceState != null) {
            ((TextView) findViewById(R.id.textViewBook)).setText(savedInstanceState.getString(USER_MESSAGE));
        }
        findViewById(R.id.open).setOnClickListener(this::getInfoAboutBook);
    }
    // РАЗБОР getInfoAboutBook:
    // view - кнопка открытия. intent содержит явный адрес ShareActivity и два extra разработчика.
    // launcher.launch запускает экран в рамках контракта возврата результата.
    public void getInfoAboutBook(View view) {
        Intent intent = new Intent(this, ShareActivity.class); // Внутренний экран не требуется выбирать через chooser.
        intent.putExtra(BOOK_NAME_KEY, getString(R.string.developer_book)); // Личные данные хранятся в ресурсах.
        intent.putExtra(QUOTES_KEY, getString(R.string.developer_quote));
        launcher.launch(intent); // Ждём результат, а не просто запускаем Activity.
    }
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    @Override protected void onSaveInstanceState(Bundle outState) {
        outState.putString(USER_MESSAGE, ((TextView) findViewById(R.id.textViewBook)).getText().toString());
        super.onSaveInstanceState(outState); // Не теряем полученную книгу после поворота.
    }
}
