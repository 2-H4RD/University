package ru.mirea.ZubarevVS.lesson5.main;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson5.main.databinding.ActivityMainBinding;

/**
 * Датчики устройства. Binding содержит типизированные ссылки на ID из activity_main.xml.
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

        // ПЕРЕМЕННАЯ: manager
        // Системный/AndroidX менеджер из getSystemService/getInstance; точный тип показывает строка
        // объявления.
        android.hardware.SensorManager manager = (android.hardware.SensorManager) getSystemService(SENSOR_SERVICE);
        // ПЕРЕМЕННАЯ: sensors
        // Список всех датчиков TYPE_ALL; отображается через адаптер.
        java.util.List<android.hardware.Sensor> sensors = manager.getSensorList(android.hardware.Sensor.TYPE_ALL);
        java.util.ArrayList<java.util.Map<String, String>> rows = new java.util.ArrayList<>();
        for (android.hardware.Sensor sensor : sensors) {
            java.util.Map<String, String> row = new java.util.HashMap<>();
            row.put("name", sensor.getName());
            row.put("detail", "Тип=" + sensor.getType() + "; диапазон=" + sensor.getMaximumRange() + "; " + sensor.getVendor());
            rows.add(row);
        }
        binding.sensorList.setAdapter(new android.widget.SimpleAdapter(this, rows, android.R.layout.simple_list_item_2, new String[]{"name", "detail"}, new int[]{android.R.id.text1, android.R.id.text2}));
        binding.summary.setText("Доступно датчиков: " + sensors.size());

    }

}
