/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Передача строки.
 * onClickNewActivity читает input.getText().toString(), создаёт явный Intent(this,
 * SecondActivity.class) и добавляет строку через putExtra(EXTRA_TEXT,...). EXTRA_TEXT - согласованный
 * строковый ключ, а не текст сообщения. SecondActivity читает
 * getIntent().getStringExtra(MainActivity.EXTRA_TEXT) и записывает в received. null означает
 * отсутствие extra; пустая строка является допустимым введённым значением. finish закрывает второй
 * экран и возвращает первый из стека. MultiMain и MultiSecond помогают сравнить callbacks двух
 * Activity.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson2.multiactivity;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.EditText;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import android.util.Log;

/** Второй экран читает строку из Intent; произвольная сериализация здесь не нужна. */
public class SecondActivity extends AppCompatActivity {
    private static final String TAG = "MultiSecond";

    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает Activity и фрагменты.
        EdgeToEdge.enable(this); // Экран использует всю область окна Android 15.
        setContentView(R.layout.activity_second); // Создаём элементы из XML до findViewById.
        applyInsets(); // Элементы не перекрываются системными панелями.
        Log.i(TAG, "onCreate()"); // Отдельный тег позволяет сравнивать оба экрана.
        String text = getIntent().getStringExtra(MainActivity.EXTRA_TEXT); // Извлекаем строку с первого экрана.
        TextView received = findViewById(R.id.received); // Находим область результата.
        received.setText(text == null ? getString(R.string.empty_text) : text); // Обрабатываем отсутствующий extra.
    }

    // РАЗБОР onClickBack:
    // view - кнопка возврата. finish завершает только текущую Activity и позволяет Android показать
    // предыдущую из стека.
    public void onClickBack(View view) {
        finish(); // Удаляем второй экран из стека и возвращаемся к первому.
    }
    @Override
    // РАЗБОР onStart:
    // Экран становится видимым. super сохраняет поведение AndroidX; Log.i выводит событие с TAG. Повторный
    // onStart не обязательно означает новый onCreate.
    protected void onStart() {
        super.onStart(); // Сохраняем стандартную обработку жизненного цикла.
        Log.i(TAG, "onStart()"); // По тегу видим, какой экран изменил состояние.
    }

    @Override
    // РАЗБОР onResume:
    // Activity готова взаимодействовать с пользователем. После возврата на существующий экран callback
    // вызывается снова. Здесь не следует заново стирать содержимое EditText.
    protected void onResume() {
        super.onResume(); // Сохраняем стандартную обработку жизненного цикла.
        Log.i(TAG, "onResume()"); // По тегу видим, какой экран изменил состояние.
    }

    @Override
    // РАЗБОР onPause:
    // Activity теряет активное состояние. Она может ещё быть видна. Callback не равен закрытию приложения
    // и не гарантирует последующий onDestroy.
    protected void onPause() {
        super.onPause(); // Сохраняем стандартную обработку жизненного цикла.
        Log.i(TAG, "onPause()"); // По тегу видим, какой экран изменил состояние.
    }

    @Override
    // РАЗБОР onStop:
    // Activity больше не видна. Существующий экземпляр может остаться в памяти и вернуться через
    // onRestart.
    protected void onStop() {
        super.onStop(); // Сохраняем стандартную обработку жизненного цикла.
        Log.i(TAG, "onStop()"); // По тегу видим, какой экран изменил состояние.
    }

    @Override
    // РАЗБОР onRestart:
    // Возвращается остановленный существующий экземпляр; дальше идут onStart и onResume. При новом
    // экземпляре вместо этого вызывается onCreate.
    protected void onRestart() {
        super.onRestart(); // Сохраняем стандартную обработку жизненного цикла.
        Log.i(TAG, "onRestart()"); // По тегу видим, какой экран изменил состояние.
    }

    @Override
    // РАЗБОР onDestroy:
    // Завершает текущий экземпляр. Поворот тоже может вызвать уничтожение/создание Activity. При
    // уничтожении процесса системой callback не гарантируется.
    protected void onDestroy() {
        super.onDestroy(); // Сохраняем стандартную обработку жизненного цикла.
        Log.i(TAG, "onDestroy()"); // По тегу видим, какой экран изменил состояние.
    }

    @Override
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState); // Android сам сохраняет EditText с уникальным id.
        Log.i(TAG, "onSaveInstanceState()"); // Это сохранение состояния, а не отдельное состояние Activity.
    }

    @Override
    // РАЗБОР onRestoreInstanceState:
    // state содержит ранее сохранённые значения. Родитель восстанавливает View по их ID. Метод вызывается
    // после onStart только при наличии сохранённого состояния.
    protected void onRestoreInstanceState(Bundle state) {
        super.onRestoreInstanceState(state); // Возвращаем сохранённые значения элементов.
        Log.i(TAG, "onRestoreInstanceState()"); // Метод вызывается только при наличии сохранённого состояния.
    }

    /** Сохраняем XML-отступы и добавляем место для системных панелей и клавиатуры. */
    // РАЗБОР applyInsets:
    // root - корневой View; left/top/right/bottom - исходный padding XML. bars - системные панели, ime -
    // клавиатура. Listener прибавляет Insets к исходным отступам, поэтому повторное событие не увеличивает
    // padding бесконечно. max выбирает нижнюю неперекрываемую область.
    private void applyInsets() {
        View root = findViewById(R.id.main); // Корневой ScrollView уже создан setContentView.
        int left = root.getPaddingLeft(); // Исходные отступы запоминаем один раз.
        int top = root.getPaddingTop();
        int right = root.getPaddingRight();
        int bottom = root.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(root, (view, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars()); // Статусная и навигационная панели.
            Insets ime = insets.getInsets(WindowInsetsCompat.Type.ime()); // Нижняя область экранной клавиатуры.
            view.setPadding(left + bars.left, top + bars.top, right + bars.right,
                    bottom + Math.max(bars.bottom, ime.bottom)); // Не складываем перекрывающиеся области.
            return insets; // Другие элементы тоже могут обработать эти Insets.
        });
        ViewCompat.requestApplyInsets(root); // Просим Android применить отступы к новой разметке.
    }
}
