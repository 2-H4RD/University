package ru.mirea.ZubarevVS.lesson5.accelerometer;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson5.accelerometer.databinding.ActivityMainBinding;

/**
 * Акселерометр · м/с². Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity implements android.hardware.SensorEventListener {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;
    // ПЕРЕМЕННАЯ: manager
    // Системный/AndroidX менеджер из getSystemService/getInstance; точный тип показывает строка
    // объявления.
    private android.hardware.SensorManager manager;
    // ПЕРЕМЕННАЯ: sensor
    // Конкретный Sensor; null означает отсутствие аппаратной/виртуальной реализации.
    private android.hardware.Sensor sensor;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        manager = (android.hardware.SensorManager) getSystemService(SENSOR_SERVICE);
        sensor = manager.getDefaultSensor(android.hardware.Sensor.TYPE_ACCELEROMETER);
        if (sensor == null) binding.status.setText("Акселерометр отсутствует");

    }

    @Override
    // ЗАЩИТА: onResume
    // Экран снова активен: регистрируются слушатели датчиков или возобновляется карта. Регистрация
    // соответствует очистке в onPause.
    protected void onResume() {
        super.onResume();
        if (sensor != null)
            manager.registerListener(this, sensor, android.hardware.SensorManager.SENSOR_DELAY_UI);
    }

    @Override
    // ЗАЩИТА: onPause
    // Экран теряет активность: подписки датчиков/карты и воспроизведение, если требуется,
    // приостанавливаются. Долговременные файлы не удаляются.
    protected void onPause() {
        manager.unregisterListener(this);
        super.onPause();
    }

    @Override
    // ЗАЩИТА: onSensorChanged
    // Обрабатывает реальные SensorEvent.values. В Accelerometer показывает XYZ в м/с²; HardwareFragment
    // вычисляет угол наклона через atan2 и выбирает практическую подсказку уровня. Это показания датчика,
    // не выдуманные числа.
    public void onSensorChanged(android.hardware.SensorEvent event) {
        binding.x.setText(String.format(Locale.getDefault(), "X: %.3f м/с²", event.values[0]));
        binding.y.setText(String.format(Locale.getDefault(), "Y: %.3f м/с²", event.values[1]));
        binding.z.setText(String.format(Locale.getDefault(), "Z: %.3f м/с²", event.values[2]));
        binding.status.setText("Данные SensorEvent обновлены");
    }

    @Override
    // ЗАЩИТА: onAccuracyChanged
    // Обязательный callback SensorEventListener для изменения точности. Для текущего учебного интерфейса
    // дополнительная обработка не требуется.
    public void onAccuracyChanged(android.hardware.Sensor sensor, int accuracy) {
    }

}
