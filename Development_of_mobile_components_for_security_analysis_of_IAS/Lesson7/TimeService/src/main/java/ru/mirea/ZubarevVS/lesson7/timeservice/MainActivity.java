package ru.mirea.ZubarevVS.lesson7.timeservice;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson7.timeservice.databinding.ActivityMainBinding;

/**
 * Socket · время NIST UTC. Binding содержит типизированные ссылки на ID из activity_main.xml.
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

        binding.load.setOnClickListener(v -> {
            binding.load.setEnabled(false);
            binding.status.setText("Подключение к time.nist.gov:13…");
            io.execute(() -> {
                try (java.net.Socket socket = new java.net.Socket()) {
                    socket.connect(new java.net.InetSocketAddress("time.nist.gov", 13), 10000);
                    socket.setSoTimeout(10000);
                    java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(socket.getInputStream(), java.nio.charset.StandardCharsets.US_ASCII));
                    String line, received = "";
                    while ((line = reader.readLine()) != null) {
                        if (!line.trim().isEmpty()) {
                            received = line;
                            break;
                        }
                    }
                    java.util.regex.Matcher match = java.util.regex.Pattern.compile("(\\d{2}-\\d{2}-\\d{2})\\s+(\\d{2}:\\d{2}:\\d{2})").matcher(received);
                    if (!match.find())
                        throw new java.io.IOException("Неожиданный формат NIST: " + received);
                    String date = "20" + match.group(1), time = match.group(2), raw = received;
                    ui(() -> {
                        binding.date.setText("Дата UTC: " + date);
                        binding.time.setText("Время UTC: " + time);
                        binding.raw.setText(raw);
                        binding.status.setText("Получено реальным Socket с time.nist.gov:13");
                    });
                } catch (Exception e) {
                    ui(() -> binding.status.setText("Socket недоступен: " + e.getClass().getSimpleName() + ". " + e.getMessage() + ". Проверьте доступ сети к порту 13."));
                } finally {
                    ui(() -> binding.load.setEnabled(true));
                }
            });
        });

    }

}
