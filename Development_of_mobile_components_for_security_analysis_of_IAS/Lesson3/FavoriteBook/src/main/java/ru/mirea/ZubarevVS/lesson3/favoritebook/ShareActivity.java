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
import android.widget.EditText;
/** Показывает книгу разработчика и возвращает введённую книгу пользователя. */
public class ShareActivity extends AppCompatActivity {
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_share);
        ScreenInsets.apply(findViewById(R.id.main));
        String book = getIntent().getStringExtra(MainActivity.BOOK_NAME_KEY);
        String quote = getIntent().getStringExtra(MainActivity.QUOTES_KEY);
        ((TextView) findViewById(R.id.developer_book)).setText(book == null ? getString(R.string.developer_book) : book);
        ((TextView) findViewById(R.id.developer_quote)).setText(quote == null ? getString(R.string.developer_quote) : quote);
        findViewById(R.id.send).setOnClickListener(view -> {
            EditText bookInput = findViewById(R.id.book_name);
            EditText quoteInput = findViewById(R.id.quote);
            String userBook = bookInput.getText().toString().trim();
            String userQuote = quoteInput.getText().toString().trim();
            if (userBook.isEmpty()) { bookInput.setError(getString(R.string.required)); return; }
            if (userQuote.isEmpty()) { quoteInput.setError(getString(R.string.required)); return; }
            Intent data = new Intent(); // Для возвращаемых данных адрес Activity не нужен.
            data.putExtra(MainActivity.USER_MESSAGE, getString(R.string.result, userBook, userQuote));
            setResult(Activity.RESULT_OK, data); // RESULT_OK равен -1; 1 не является кодом успеха.
            finish(); // Передаём управление и результат обратно родительскому экрану.
        });
        findViewById(R.id.cancel).setOnClickListener(view -> {
            setResult(Activity.RESULT_CANCELED); // Отмена не затирает ранее полученную книгу.
            finish();
        });
    }
}
