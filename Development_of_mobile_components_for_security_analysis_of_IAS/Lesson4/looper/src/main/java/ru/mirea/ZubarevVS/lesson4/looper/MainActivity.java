package ru.mirea.ZubarevVS.lesson4.looper;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson4.looper.databinding.ActivityMainBinding;

/**
 * Looper · возраст и профессия. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;
    // ПЕРЕМЕННАЯ: worker
    // Объект MyLooper/Worker согласно типу объявления, отдельный владелец фоновой работы.
    private MyLooper worker;
    // ПЕРЕМЕННАЯ: main
    // Handler главного потока, получает результат для UI.
    private android.os.Handler main;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        binding.send.setEnabled(false);
        main = new android.os.Handler(android.os.Looper.getMainLooper(), msg -> {
            binding.result.setText(msg.getData().getString("result"));
            binding.send.setEnabled(true);
            return true;
        });
        worker = new MyLooper(main, () -> {
            if (!isDestroyed()) {
                binding.send.setEnabled(true);
                binding.result.setText("Looper готов");
            }
        });
        worker.start();
        binding.send.setOnClickListener(v -> {
            try {
                // ПЕРЕМЕННАЯ: age
                // Возраст пользователя; age*1000L задаёт задержку сообщения в миллисекундах.
                int age = Integer.parseInt(binding.age.getText().toString());
                // ПЕРЕМЕННАЯ: job
                // Введённая профессия/работа, передаётся в Bundle JOB.
                String job = binding.job.getText().toString().trim();
                if (age < 0 || age > 120 || job.isEmpty()) throw new IllegalArgumentException();
                Bundle data = new Bundle();
                data.putInt("AGE", age);
                data.putString("JOB", job);
                // ПЕРЕМЕННАЯ: message
                // Message с Bundle для передачи в очередь другого потока.
                android.os.Message message = android.os.Message.obtain();
                message.setData(data);
                worker.getHandler().sendMessageDelayed(message, age * 1000L);
                binding.result.setText("Сообщение в очереди; ожидание " + age + " с");
                binding.send.setEnabled(false);
            } catch (IllegalArgumentException e) {
                binding.result.setText("Введите возраст 0–120 и профессию");
            }
        });

    }

    @Override
    // ЗАЩИТА: onDestroy
    // Завершает жизнь экземпляра: освобождает собственные MediaPlayer/Looper/Executor. super завершает
    // инфраструктуру родителя. onDestroy не гарантирован при убийстве всего процесса ОС.
    protected void onDestroy() {
        worker.quit();
        main.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
