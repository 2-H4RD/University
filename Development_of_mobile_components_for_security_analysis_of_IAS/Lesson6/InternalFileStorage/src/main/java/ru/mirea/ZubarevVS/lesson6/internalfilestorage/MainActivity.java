package ru.mirea.ZubarevVS.lesson6.internalfilestorage;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson6.internalfilestorage.databinding.ActivityMainBinding;

/**
 * Историческая дата · внутренний файл. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        if (state == null)
            binding.event.setText("12 апреля 1961 года — первый полёт человека в космос. Юрий Гагарин совершил орбитальный полёт на корабле Восток-1.");
        binding.save.setOnClickListener(v -> {
            // ПЕРЕМЕННАЯ: text
            // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
            // String; в Worker/Data передаётся уже строковое значение.
            String text = binding.event.getText().toString();
            if (text.trim().isEmpty()) {
                binding.event.setError("Введите дату и описание");
                return;
            }
            io.execute(() -> {
                try (java.io.OutputStream stream = openFileOutput("history.txt", MODE_PRIVATE)) {
                    stream.write(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    ui(() -> binding.status.setText("Записано: " + getFileStreamPath("history.txt")));
                } catch (Exception e) {
                    ui(() -> binding.status.setText("Ошибка записи: " + e.getMessage()));
                }
            });
        });
        binding.load.setOnClickListener(v -> io.execute(() -> {
            try (java.io.InputStream stream = openFileInput("history.txt"); java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream()) {
                // ПЕРЕМЕННАЯ: buffer
                // Буфер порционного чтения байтов; не весь файл сразу.
                byte[] buffer = new byte[4096];
                int read;
                while ((read = stream.read(buffer)) != -1) bytes.write(buffer, 0, read);
                // ПЕРЕМЕННАЯ: text
                // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
                // String; в Worker/Data передаётся уже строковое значение.
                String text = bytes.toString("UTF-8");
                ui(() -> {
                    binding.event.setText(text);
                    binding.status.setText("Прочитано из приватного файла");
                });
            } catch (Exception e) {
                ui(() -> binding.status.setText("Файл пока не записан: " + e.getMessage()));
            }
        }));

    }

}
