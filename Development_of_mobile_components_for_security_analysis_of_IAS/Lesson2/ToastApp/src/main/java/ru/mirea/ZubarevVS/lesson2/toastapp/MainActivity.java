/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Подсчёт символов.
 * onClickCount читает input без trim, поэтому пробелы считаются. text - String, count - количество
 * Unicode code points от 0 до text.length(), message - форматированная строка из count_result. UTF-16
 * длина и число code points могут различаться для emoji; составной emoji может содержать несколько
 * code points. Toast.makeText(...).show() выводит временное сообщение, result оставляет его читаемую
 * копию. onSaveInstanceState сохраняет этот результат отдельно, EditText сохраняет Android.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson2.toastapp;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/** Показываем результат и в Toast, и на экране, чтобы его можно было прочитать. */
public class MainActivity extends AppCompatActivity {

    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает Activity и фрагменты.
        EdgeToEdge.enable(this); // Экран использует всю область окна Android 15.
        setContentView(R.layout.activity_main); // Создаём элементы из XML до findViewById.
        applyInsets(); // Элементы не перекрываются системными панелями.
        if (savedInstanceState != null) { // Возвращаем последний результат после поворота.
            ((TextView) findViewById(R.id.result)).setText(savedInstanceState.getString("result"));
        }
    }

    // РАЗБОР onClickCount:
    // Получает String text из input. codePointCount считает кодовые точки, getString подставляет count в
    // ресурс. Toast - временный вывод; result - постоянная копия. view обозначает источник события и здесь
    // не используется.
    public void onClickCount(View view) {
        String text = ((EditText) findViewById(R.id.input)).getText().toString(); // Читаем строку без удаления пробелов.
        int count = text.codePointCount(0, text.length()); // Считаем кодовые точки: обычный emoji не равен двум UTF-16 элементам.
        String message = getString(R.string.count_result, count); // Подставляем количество в шаблон с данными студента.
        Toast.makeText(this, message, Toast.LENGTH_LONG).show(); // Показываем стандартное всплывающее сообщение.
        ((TextView) findViewById(R.id.result)).setText(message); // Дублируем длинный текст без ограничения Toast.
    }

    @Override
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState); // Родитель сохраняет поле ввода.
        outState.putString("result", ((TextView) findViewById(R.id.result)).getText().toString()); // Сохраняем результат отдельно.
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
