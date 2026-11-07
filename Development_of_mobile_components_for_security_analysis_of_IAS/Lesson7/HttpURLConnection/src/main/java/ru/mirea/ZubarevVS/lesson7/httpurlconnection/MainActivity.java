package ru.mirea.ZubarevVS.lesson7.httpurlconnection;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson7.httpurlconnection.databinding.ActivityMainBinding;

/**
 * IP, география и погода · HTTPS. Binding содержит типизированные ссылки на ID из activity_main.xml.
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
            // ПЕРЕМЕННАЯ: manager
            // Системный/AndroidX менеджер из getSystemService/getInstance; точный тип показывает строка
            // объявления.
            android.net.ConnectivityManager manager = (android.net.ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
            android.net.NetworkCapabilities caps = manager.getNetworkCapabilities(manager.getActiveNetwork());
            if (caps == null || !caps.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET)) {
                binding.status.setText("Нет подключения к интернету");
                return;
            }
            binding.load.setEnabled(false);
            binding.status.setText("Получение IP и координат…");
            io.execute(() -> {
                try {
                    org.json.JSONObject info = new org.json.JSONObject(NetworkClient.get("https://ipwho.is/"));
                    if (!info.optBoolean("success", true))
                        throw new java.io.IOException(info.optString("message"));
                    String ip = info.getString("ip"), city = info.optString("city"), region = info.optString("region"), country = info.optString("country");
                    double latitude = info.getDouble("latitude"), longitude = info.getDouble("longitude");
                    ui(() -> {
                        binding.ip.setText("IP: " + ip);
                        binding.city.setText("Город: " + city);
                        binding.region.setText("Регион: " + region);
                        binding.country.setText("Страна: " + country);
                        binding.coordinates.setText("Координаты: " + latitude + ", " + longitude);
                        binding.status.setText("IP получен; запрос погоды…");
                    });
                    String address = String.format(Locale.ROOT, "https://api.open-meteo.com/v1/forecast?latitude=%f&longitude=%f&current_weather=true", latitude, longitude);
                    org.json.JSONObject weather = new org.json.JSONObject(NetworkClient.get(address)).getJSONObject("current_weather");
                    String report = String.format(Locale.getDefault(), "Температура: %.1f °C\nВетер: %.1f км/ч\nКод погоды: %d\nВремя: %s", weather.getDouble("temperature"), weather.getDouble("windspeed"), weather.getInt("weathercode"), weather.getString("time"));
                    ui(() -> {
                        binding.weather.setText(report);
                        binding.status.setText("Получено из ipwho.is → Open-Meteo. География IP приблизительна.");
                    });
                } catch (Exception e) {
                    ui(() -> binding.status.setText("Ошибка сети: " + e.getMessage()));
                } finally {
                    ui(() -> binding.load.setEnabled(true));
                }
            });
        });

    }

}
