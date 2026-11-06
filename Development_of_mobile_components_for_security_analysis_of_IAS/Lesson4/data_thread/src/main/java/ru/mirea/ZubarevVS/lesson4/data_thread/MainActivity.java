package ru.mirea.ZubarevVS.lesson4.data_thread;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson4.data_thread.databinding.ActivityMainBinding;

/**
 * Доставка Runnable в UI. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;
    private boolean running;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());
        binding.start.setOnClickListener(v -> runSequence());
    }

    // ЗАЩИТА: runSequence
    // Создаёт три Runnable с захваченным begin — временем монотонных часов. Фоновый исполнитель ждёт 2 с,
    // отправляет runn1 в UI, через 1 с ставит runn3 с задержкой 2 с и сразу post(runn2). Поэтому ожидаемый
    // порядок 1→2→3, а задержка postDelayed является минимальной.
    private void runSequence() {
        if (running) return;
        running = true;
        binding.start.setEnabled(false);
        binding.result.setText("");
        final long begin = android.os.SystemClock.elapsedRealtime();
        Runnable runn1 = () -> binding.result.append("runn1 @ " + (android.os.SystemClock.elapsedRealtime() - begin) + " ms\n");
        Runnable runn2 = () -> binding.result.append("runn2 @ " + (android.os.SystemClock.elapsedRealtime() - begin) + " ms\n");
        Runnable runn3 = () -> {
            binding.result.append("runn3 @ " + (android.os.SystemClock.elapsedRealtime() - begin) + " ms\n");
            running = false;
            binding.start.setEnabled(true);
        };
        io.execute(() -> {
            try {
                Thread.sleep(2000);
                ui(runn1);
                Thread.sleep(1000);
                binding.result.postDelayed(runn3, 2000);
                binding.result.post(runn2);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
    }

}
