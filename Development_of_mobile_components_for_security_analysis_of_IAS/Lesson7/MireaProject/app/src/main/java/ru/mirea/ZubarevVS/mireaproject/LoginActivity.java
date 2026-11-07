package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.mireaproject.databinding.ActivityLoginBinding;

/**
 * Firebase · вход и регистрация. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class LoginActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityLoginBinding binding;
    // ПЕРЕМЕННАЯ: auth
    // Настоящий FirebaseAuth SDK, null только при отсутствующей конфигурации.
    private com.google.firebase.auth.FirebaseAuth auth;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityLoginBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        auth = AuthConfig.get(this);
        binding.mode.setText(BuildConfig.FIREBASE_EMULATOR_HOST.isEmpty() ? "Firebase: облачный проект" : "Firebase Auth Emulator: demo-mirea-labs (локально)");
        binding.signIn.setOnClickListener(v -> authenticate(false));
        binding.register.setOnClickListener(v -> authenticate(true));
        binding.signOut.setOnClickListener(v -> {
            if (auth != null) {
                auth.signOut();
                refresh();
            }
        });
        binding.verify.setOnClickListener(v -> {
            if (auth != null && auth.getCurrentUser() != null)
                auth.getCurrentUser().sendEmailVerification().addOnCompleteListener(this, t -> binding.status.setText(t.isSuccessful() ? "Письмо проверки отправлено" : "Ошибка проверки: " + t.getException().getMessage()));
        });
        binding.reload.setOnClickListener(v -> {
            if (auth != null && auth.getCurrentUser() != null)
                auth.getCurrentUser().reload().addOnCompleteListener(this, t -> refresh());
        });
        binding.continueButton.setOnClickListener(v -> afterSignIn());
        refresh();

    }

    // ЗАЩИТА: authenticate
    // Проверяет конфигурацию, email и минимальную длину пароля. create выбирает
    // createUserWithEmailAndPassword, иначе signInWithEmailAndPassword. Task callback обновляет UI и
    // очищает пароль; пароль не записывается в SharedPreferences/логи.
    private void authenticate(boolean create) {
        if (auth == null) {
            refresh();
            return;
        }
        // ПЕРЕМЕННАЯ: email
        // Email для Firebase; уникальность и ошибки проверяет Firebase backend.
        String email = binding.email.getText().toString().trim(), password = binding.password.getText().toString();
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.email.setError("Корректный email");
            return;
        }
        if (password.length() < 6) {
            binding.password.setError("Не менее 6 символов");
            return;
        }
        binding.signIn.setEnabled(false);
        binding.register.setEnabled(false);
        binding.status.setText("Обращение к Firebase…");
        com.google.android.gms.tasks.Task<com.google.firebase.auth.AuthResult> task = create ? auth.createUserWithEmailAndPassword(email, password) : auth.signInWithEmailAndPassword(email, password);
        task.addOnCompleteListener(this, t -> {
            refresh();
            binding.password.setText("");
            if (!t.isSuccessful())
                binding.status.setText("Firebase: " + t.getException().getLocalizedMessage());
            else if (!create) afterSignIn();
        });
    }

    // ЗАЩИТА: refresh
    // Состояние настоящего FirebaseUser определяет видимость полей входа и кнопок verify/signOut.
    // Отсутствующий google-services.json показывает инструкцию настройки, а не фиктивную авторизацию.
    private void refresh() {
        boolean configured = auth != null;
        // ПЕРЕМЕННАЯ: user
        // FirebaseUser текущей сессии либо null после выхода/до входа.
        com.google.firebase.auth.FirebaseUser user = configured ? auth.getCurrentUser() : null;
        boolean signed = user != null;
        binding.email.setVisibility(signed ? View.GONE : View.VISIBLE);
        binding.password.setVisibility(signed ? View.GONE : View.VISIBLE);
        binding.signIn.setVisibility(signed ? View.GONE : View.VISIBLE);
        binding.register.setVisibility(signed ? View.GONE : View.VISIBLE);
        binding.signIn.setEnabled(configured);
        binding.register.setEnabled(configured);
        binding.signOut.setVisibility(signed ? View.VISIBLE : View.GONE);
        binding.verify.setVisibility(signed ? View.VISIBLE : View.GONE);
        binding.reload.setVisibility(signed ? View.VISIBLE : View.GONE);
        binding.continueButton.setVisibility(signed ? View.VISIBLE : View.GONE);
        binding.status.setText(!configured ? "Требуется ваш google-services.json и Email/Password в Firebase. См. ПОДКЛЮЧЕНИЕ_СЕРВИСОВ.md." : signed ? "Email: " + user.getEmail() + "\nUID: " + user.getUid() + "\nПочта подтверждена: " + user.isEmailVerified() : "Вход не выполнен");
    }

    // ЗАЩИТА: afterSignIn
    // Точка различия упражнения и контрольного проекта: отдельный FirebaseAuth остаётся на экране
    // состояния; LoginActivity MireaProject запускает MainActivity и finish после успешного входа.
    protected void afterSignIn() {
        if (auth != null && auth.getCurrentUser() != null) {
            startActivity(new android.content.Intent(this, MainActivity.class));
            finish();
        }
    }

    @Override
    // ЗАЩИТА: onStart
    // Экран видим: передаётся событие lifecycle компонентам, которым оно нужно. Для MapKit вызываются
    // onStart у MapKit и MapView; это не повторная инициализация API ключа.
    protected void onStart() {
        super.onStart();
        if (binding != null) refresh();
    }

}
