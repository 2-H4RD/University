package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.View;
import android.widget.*;

/**
 * Профиль исследователя хранит только выбранные поля в приватных SharedPreferences.
 */
public class ProfileFragment extends LabFragment {
    @Override
    // ЗАЩИТА: onViewCreated
    // View уже создана. Добавляются элементы предметного экрана, обработчики и наблюдения с
    // getViewLifecycleOwner. Долгая операция выполняется в io/Worker; результат изменяет только актуальный
    // View.
    public void onViewCreated(View view, Bundle state) {
        label("Профиль исследователя безопасности");
        // ПЕРЕМЕННАЯ: preferences
        // Приватные SharedPreferences с согласованными ключами и типами.
        android.content.SharedPreferences preferences = requireContext().getSharedPreferences("profile", 0);
        EditText name = edit("profileName", "Имя"), group = edit("profileGroup", "Группа"), role = edit("profileRole", "Роль в команде");
        name.setText(preferences.getString("name", "Зубарев Василий Сергеевич"));
        group.setText(preferences.getString("group", "БИСО-02-22"));
        role.setText(preferences.getString("role", ""));
        // ПЕРЕМЕННАЯ: status
        // TextView состояния конкретного экрана, содержит результат/ошибку.
        TextView status = label("");
        button("Сохранить профиль", () -> {
            String a = name.getText().toString().trim(), b = group.getText().toString().trim(), c = role.getText().toString().trim();
            if (a.isEmpty() || b.isEmpty() || c.isEmpty()) {
                status.setText("Заполните все поля профиля");
                return;
            }
            preferences.edit().putString("name", a).putString("group", b).putString("role", c).apply();
            status.setText("Профиль сохранён");
        });
    }
}
