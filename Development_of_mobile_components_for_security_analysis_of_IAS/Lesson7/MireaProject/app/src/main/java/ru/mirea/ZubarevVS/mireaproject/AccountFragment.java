package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

public class AccountFragment extends LabFragment {
    @Override
    // ЗАЩИТА: onViewCreated
    // View уже создана. Добавляются элементы предметного экрана, обработчики и наблюдения с
    // getViewLifecycleOwner. Долгая операция выполняется в io/Worker; результат изменяет только актуальный
    // View.
    public void onViewCreated(View view, Bundle state) {
        // ПЕРЕМЕННАЯ: auth
        // Настоящий FirebaseAuth SDK, null только при отсутствующей конфигурации.
        com.google.firebase.auth.FirebaseAuth auth = AuthConfig.get(requireContext());
        // ПЕРЕМЕННАЯ: user
        // FirebaseUser текущей сессии либо null после выхода/до входа.
        com.google.firebase.auth.FirebaseUser user = auth == null ? null : auth.getCurrentUser();
        TextView info = label(user == null ? "Вход не выполнен" : "Email: " + user.getEmail() + "\nUID: " + user.getUid() + "\nПодтверждён: " + user.isEmailVerified());
        button("Отправить письмо проверки", () -> {
            if (user != null)
                user.sendEmailVerification().addOnCompleteListener(task -> ui(() -> info.setText(task.isSuccessful() ? "Письмо отправлено" : "Ошибка: " + task.getException().getMessage())));
        });
        button("Выйти из аккаунта", () -> {
            if (auth != null) auth.signOut();
            startActivity(new android.content.Intent(requireContext(), LoginActivity.class));
            requireActivity().finish();
        });
    }
}
