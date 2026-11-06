package ru.mirea.ZubarevVS.lesson4.thread;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson4.thread.databinding.ActivityMainBinding;

/**
 * Среднее число пар · Thread. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;
    // ПЕРЕМЕННАЯ: counter
    // AtomicInteger выдаёт уникальные номера параллельным задачам без гонки counter++.
    private final java.util.concurrent.atomic.AtomicInteger counter = new java.util.concurrent.atomic.AtomicInteger();

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        // Выбор пользователя. При повороте Android восстанавливает редактируемое поле по его ID.
        // Значение по умолчанию задаём только новому экрану; обработчик rename читает актуальный ввод.
        if (state == null) binding.movie.setText("Лучше звоните Солу");

        binding.threadInfo.setText("Исходное имя: " + Thread.currentThread().getName());
        binding.rename.setOnClickListener(v -> {
            // ПЕРЕМЕННАЯ: movie
            // Введённый фильм/сериал; личное значение задаёт пользователь.
            String movie = binding.movie.getText().toString().trim();
            if (movie.isEmpty()) {
                binding.movie.setError("Введите свой фильм");
                return;
            }
            Thread.currentThread().setName("БИСО-02-22, №5, фильм: " + movie);
            binding.threadInfo.append("\nНовое имя: " + Thread.currentThread().getName());
        });
        binding.calculate.setOnClickListener(v -> {
            try {
                // ПЕРЕМЕННАЯ: total
                // Общее количество пар за месяц, прочитанное и проверенное в UI.
                int total = Integer.parseInt(binding.total.getText().toString());
                // ПЕРЕМЕННАЯ: days
                // Число учебных дней; должно быть >0, чтобы исключить деление на ноль.
                int days = Integer.parseInt(binding.days.getText().toString());
                if (total < 0 || days <= 0) throw new IllegalArgumentException();
                int task = counter.incrementAndGet();
                // Копии чисел читаются в UI, но деление и журнал работают в отдельном Thread.
                new Thread(() -> {
                    android.util.Log.d("ThreadProject", "Старт №" + task + " БИСО-02-22 №5");
                    // ПЕРЕМЕННАЯ: average
                    // Вещественное среднее (double) total/days, вычисляется в фоновом Thread.
                    double average = (double) total / days;
                    ui(() -> binding.result.setText(String.format(Locale.getDefault(), "Среднее: %.2f пар/день; поток №%d", average, task)));
                    android.util.Log.d("ThreadProject", "Завершён №" + task + "; average=" + average);
                }, "Lesson4-calculation-" + task).start();
            } catch (IllegalArgumentException e) {
                binding.result.setText("Введите целое число пар ≥ 0 и число дней > 0");
            }
        });

    }

}
