/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Первое приложение.
 * Activity загружает activity_main.xml. ConstraintLayout задаёт положение TextView через привязки. Это
 * исходная точка для исследования структуры app, manifest, Java и ресурсов. Здесь нет обработчиков:
 * экран статичен.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson1;

import android.os.Bundle;
import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/** Исходный экран первой практики, созданный по шаблону Empty Views Activity. */
public class MainActivity extends AppCompatActivity {
    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        // Системные отступы защищают интерфейс от перекрытия панелями Android.
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (view, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return insets;
        });
    }
}
