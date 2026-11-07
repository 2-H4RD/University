package ru.mirea.ZubarevVS.lesson6.main;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson6.main.databinding.ActivityMainBinding;

/**
 * Настройки · SharedPreferences. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;
    // ПЕРЕМЕННАЯ: preferences
    // Приватные SharedPreferences с согласованными ключами и типами.
    private android.content.SharedPreferences preferences;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        preferences = getSharedPreferences("mirea_settings", MODE_PRIVATE);
        binding.group.setText(preferences.getString("GROUP", "БИСО-02-22"));
        binding.number.setText(String.valueOf(preferences.getInt("NUMBER", 5)));
        // Сериал выбран пользователем. Меняем только прежнюю техническую строку теста;
        // любое настоящее сохранённое название имеет приоритет над значением по умолчанию.
        String savedMovie = preferences.getString("MOVIE", "Лучше звоните Солу");
        binding.movie.setText("Training film".equals(savedMovie) ? "Лучше звоните Солу" : savedMovie);
        binding.save.setOnClickListener(v -> {
            try {
                // ПЕРЕМЕННАЯ: group
                // Учебная группа, введённая в поле; строка сохраняется отдельно от номера и фильма.
                String group = binding.group.getText().toString().trim(), movie = binding.movie.getText().toString().trim();
                // ПЕРЕМЕННАЯ: number
                // Номер по списку, проверяется перед сохранением.
                int number = Integer.parseInt(binding.number.getText().toString());
                if (group.isEmpty() || movie.isEmpty() || number <= 0)
                    throw new IllegalArgumentException();
                io.execute(() -> {
                    boolean ok = preferences.edit().putString("GROUP", group).putInt("NUMBER", number).putString("MOVIE", movie).commit();
                    ui(() -> binding.status.setText(ok ? "Настройки сохранены" : "Ошибка записи"));
                });
            } catch (IllegalArgumentException e) {
                binding.status.setText("Заполните группу, положительный номер и фильм");
            }
        });

    }

}
