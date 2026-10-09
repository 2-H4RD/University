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
/** Внутренняя Activity читает переданное время и показывает квадрат номера 5. */
public class SecondActivity extends AppCompatActivity {
    // Один источник номера: при его изменении результат вычисляется заново, а не остаётся строкой «25».
    private static final int STUDENT_NUMBER = 5;
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_second); // Здесь нужен макет именно второго экрана.
        ScreenInsets.apply(findViewById(R.id.main));
        String time = getIntent().getStringExtra(MainActivity.TIME_KEY); // Ключ должен совпасть с putExtra.
        TextView result = findViewById(R.id.result);
        int square = STUDENT_NUMBER * STUDENT_NUMBER; // Арифметическое умножение целых чисел: 5 × 5 = 25.
        result.setText(time == null ? getString(R.string.missing) : getString(R.string.result, square, time));
        findViewById(R.id.back).setOnClickListener(view -> finish()); // Закрываем текущий экран, возвращаясь к первому.
    }
}
