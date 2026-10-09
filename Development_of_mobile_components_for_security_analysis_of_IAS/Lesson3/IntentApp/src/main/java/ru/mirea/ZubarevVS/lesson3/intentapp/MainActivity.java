/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Время и квадрат номера.
 * TIME_KEY=sent_time используется и в putExtra, и в getStringExtra. dateInMillis фиксирует системное
 * время в момент нажатия, Date оборачивает миллисекунды, sdf форматирует yyyy-MM-dd HH:mm:ss,
 * dateString является передаваемой строкой. SecondActivity получает именно эту строку, а не вычисляет
 * новое время. STUDENT_NUMBER=5, square=STUDENT_NUMBER*STUDENT_NUMBER даёт 25. Ресурс result
 * подставляет square и time по позициям %1$d и %2$s. Кнопка back вызывает finish.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson3.intentapp;

import android.os.Bundle;
import android.content.Intent;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Задание 1.5: передаём фактическое время в отдельную Activity. */
public class MainActivity extends AppCompatActivity {
    static final String TIME_KEY = "sent_time"; // Одинаковый ключ используется обоими экранами.
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
            ((TextView) findViewById(R.id.time)).setText(savedInstanceState.getString(TIME_KEY));
        }
        findViewById(R.id.send).setOnClickListener(view -> {
            long dateInMillis = System.currentTimeMillis(); // Время компьютера/телефона в миллисекундах.
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
            String dateString = sdf.format(new Date(dateInMillis)); // Форматируем дату и время из задания.
            ((TextView) findViewById(R.id.time)).setText(getString(R.string.time_value, dateString));
            Intent intent = new Intent(this, SecondActivity.class); // Явно указываем получателя.
            intent.putExtra(TIME_KEY, dateString); // Extra передаёт строку, а не заново вычисленное время.
            startActivity(intent); // Android открывает второй экран.
        });
    }
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    @Override protected void onSaveInstanceState(Bundle outState) {
        outState.putString(TIME_KEY, ((TextView) findViewById(R.id.time)).getText().toString());
        super.onSaveInstanceState(outState); // Последняя отправка остаётся видна после поворота.
    }
}
