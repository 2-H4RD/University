package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

/**
 * Настоящий сетевой ресурс: текущая погода в районе кампуса. Запрос выполняется в io.
 */
public class NetworkFragment extends LabFragment {
    @Override
    // ЗАЩИТА: onViewCreated
    // View уже создана. Добавляются элементы предметного экрана, обработчики и наблюдения с
    // getViewLifecycleOwner. Долгая операция выполняется в io/Worker; результат изменяет только актуальный
    // View.
    public void onViewCreated(View view, Bundle state) {
        label("Погода у кампуса · Open-Meteo");
        // ПЕРЕМЕННАЯ: status
        // TextView состояния конкретного экрана, содержит результат/ошибку.
        TextView status = label("Нажмите обновить");
        button("Обновить погоду", () -> {
            status.setText("HTTPS запрос…");
            io.execute(() -> {
                try {
                    org.json.JSONObject weather = new org.json.JSONObject(NetworkClient.get("https://api.open-meteo.com/v1/forecast?latitude=55.6699&longitude=37.4796&current_weather=true")).getJSONObject("current_weather");
                    // ПЕРЕМЕННАЯ: text
                    // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
                    // String; в Worker/Data передаётся уже строковое значение.
                    String text = "Температура: " + weather.getDouble("temperature") + " °C\nВетер: " + weather.getDouble("windspeed") + " км/ч\nВремя: " + weather.getString("time");
                    ui(() -> status.setText(text));
                } catch (Exception e) {
                    ui(() -> status.setText("Ошибка сети: " + e.getMessage()));
                }
            });
        });
    }
}
