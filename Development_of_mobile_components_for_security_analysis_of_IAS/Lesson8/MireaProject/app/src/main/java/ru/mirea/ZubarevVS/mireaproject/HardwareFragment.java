package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.hardware.*;

/**
 * Логическая задача датчика: уровень телефона. Фото/голос помогают фиксировать инцидент.
 */
public class HardwareFragment extends LabFragment implements SensorEventListener {
    // ПЕРЕМЕННАЯ: manager
    // Системный/AndroidX менеджер из getSystemService/getInstance; точный тип показывает строка
    // объявления.
    private SensorManager manager;
    // ПЕРЕМЕННАЯ: accelerometer
    // Доступный датчик TYPE_ACCELEROMETER, отдаёт ускорения по трём осям.
    private Sensor accelerometer;
    private TextView level;

    @Override
    // ЗАЩИТА: onViewCreated
    // View уже создана. Добавляются элементы предметного экрана, обработчики и наблюдения с
    // getViewLifecycleOwner. Долгая операция выполняется в io/Worker; результат изменяет только актуальный
    // View.
    public void onViewCreated(View view, Bundle state) {
        label("Аппаратная часть · журнал инцидента");
        level = label("Ожидание акселерометра");
        manager = (SensorManager) requireContext().getSystemService(android.content.Context.SENSOR_SERVICE);
        accelerometer = manager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        if (accelerometer == null) level.setText("Акселерометр отсутствует");
        button("Фотофиксация инцидента", () -> startActivity(new android.content.Intent(requireContext(), PhotoNoteActivity.class)));
        button("Голосовая заметка", () -> startActivity(new android.content.Intent(requireContext(), VoiceNoteActivity.class)));
    }

    @Override
    // ЗАЩИТА: onResume
    // Экран снова активен: регистрируются слушатели датчиков или возобновляется карта. Регистрация
    // соответствует очистке в onPause.
    public void onResume() {
        super.onResume();
        if (accelerometer != null)
            manager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_UI);
    }

    @Override
    // ЗАЩИТА: onPause
    // Экран теряет активность: подписки датчиков/карты и воспроизведение, если требуется,
    // приостанавливаются. Долговременные файлы не удаляются.
    public void onPause() {
        if (manager != null) manager.unregisterListener(this);
        super.onPause();
    }

    @Override
    // ЗАЩИТА: onSensorChanged
    // Обрабатывает реальные SensorEvent.values. В Accelerometer показывает XYZ в м/с²; HardwareFragment
    // вычисляет угол наклона через atan2 и выбирает практическую подсказку уровня. Это показания датчика,
    // не выдуманные числа.
    public void onSensorChanged(SensorEvent e) {
        double tilt = Math.toDegrees(Math.atan2(Math.hypot(e.values[0], e.values[1]), Math.abs(e.values[2])));
        level.setText(String.format(java.util.Locale.getDefault(), "Наклон: %.1f°\n%s", tilt, tilt < 5 ? "Устройство лежит ровно: можно сделать фото документа" : "Выровняйте устройство перед фиксацией"));
    }

    @Override
    // ЗАЩИТА: onAccuracyChanged
    // Обязательный callback SensorEventListener для изменения точности. Для текущего учебного интерфейса
    // дополнительная обработка не требуется.
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }
}
