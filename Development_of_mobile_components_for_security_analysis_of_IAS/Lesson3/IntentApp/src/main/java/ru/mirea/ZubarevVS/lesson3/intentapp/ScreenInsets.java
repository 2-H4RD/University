/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Время и квадрат номера.
 * Статический метод принимает root текущей разметки. Конструктор закрыт: экземпляры ScreenInsets не
 * нужны. Маска systemBars | ime объединяет области системных панелей и клавиатуры, беря максимальный
 * отступ по каждой стороне.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson3.intentapp;

import android.view.View;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/** Добавляет безопасные отступы, сохраняя исходный padding из XML. */
public final class ScreenInsets {
    private ScreenInsets() { } // Создавать объект этого служебного класса не нужно.
    // РАЗБОР apply:
    // Статический метод принимает root текущей разметки. Конструктор закрыт: экземпляры ScreenInsets не
    // нужны. Маска systemBars | ime объединяет области системных панелей и клавиатуры, беря максимальный
    // отступ по каждой стороне.
    public static void apply(View root) {
        int left = root.getPaddingLeft(); // Запоминаем исходный отступ один раз.
        int top = root.getPaddingTop();
        int right = root.getPaddingRight();
        int bottom = root.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(root, (view, insets) -> {
            Insets safe = insets.getInsets(WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.ime());
            view.setPadding(left + safe.left, top + safe.top, right + safe.right, bottom + safe.bottom);
            return insets; // Не накапливаем padding при повторной доставке insets.
        });
        ViewCompat.requestApplyInsets(root); // Запрашиваем размеры панелей после загрузки XML.
    }
}
