/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Собственный экран.
 * Контакт составлен из ImageView, TextView, EditText, CheckBox, Button и ImageButton. Портретная
 * версия использует constraints, альбомная размещает изображение слева и форму справа с весами 1:2. ID
 * nameInput и favoriteCheckBox одинаковы в обеих версиях: Android переносит ввод и отметку при
 * пересоздании Activity. Задание проверяет компоновку; сохранение контакта и телефонный вызов здесь не
 * заданы.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.control_lesson1;

import android.os.Bundle;
import android.view.View;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/**
 * Демонстрирует экран, составленный из обязательных элементов управления.
 * Поведение кнопок в этой части методички не задано, поэтому Activity только
 * загружает XML и не добавляет лишнюю бизнес-логику.
 */
public class MainActivity extends AppCompatActivity {

    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        EdgeToEdge.enable(this);

        // При альбомной ориентации Android автоматически возьмёт layout-land/activity_main.xml.
        setContentView(R.layout.activity_main);
        applySystemBarInsets();
    }

    /** Не даёт элементам оказаться под статус-баром или системной панелью навигации. */
    // РАЗБОР applySystemBarInsets:
    // root - корень текущего макета. Четыре переменные запоминают исходный padding. Insets дают размеры
    // системных панелей и клавиатуры; к ним добавляются исходные отступы. Listener работает и после
    // поворота/изменения окна.
    private void applySystemBarInsets() {
        View root = findViewById(R.id.main);
        int left = root.getPaddingLeft();
        int top = root.getPaddingTop();
        int right = root.getPaddingRight();
        int bottom = root.getPaddingBottom();

        ViewCompat.setOnApplyWindowInsetsListener(root, (view, windowInsets) -> {
            Insets bars = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.ime());
            view.setPadding(left + bars.left, top + bars.top,
                    right + bars.right, bottom + bars.bottom);
            return windowInsets;
        });
    }
}
