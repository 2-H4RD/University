package ru.mirea.ZubarevVS.mireaproject;

import android.content.Context;

import com.google.firebase.*;
import com.google.firebase.auth.FirebaseAuth;

/**
 * Конфигурация поставляется владельцем. Пустая конфигурация не подменяется фиктивным успешным входом.
 */
public final class AuthConfig {
    // ПЕРЕМЕННАЯ: auth
    // Настоящий FirebaseAuth SDK, null только при отсутствующей конфигурации.
    private static FirebaseAuth auth;

    // ЗАЩИТА: get
    // Инициализирует реальную FirebaseApp из конфигурации владельца либо явно включённый debug Auth
    // Emulator. Отсутствующий облачный JSON возвращает null и понятный экран настройки.
    public static synchronized FirebaseAuth get(Context context) {
        if (auth != null) return auth;
        FirebaseApp app;
        if (!BuildConfig.FIREBASE_EMULATOR_HOST.isEmpty()) {
            // Только явный debug-параметр Gradle включает официальный локальный Firebase Auth Emulator.
            // Демонстрационный projectId не позволяет обращаться к чужим облачным проектам.
            if (!BuildConfig.DEBUG)
                throw new IllegalStateException("Эмулятор разрешён только в debug");
            FirebaseOptions options = new FirebaseOptions.Builder().setProjectId("demo-mirea-labs").setApplicationId("1:1234567890:android:0123456789abcdef").setApiKey("AIzaSyDemoMireaOnlyLocalEmulator123456789").build();
            app = FirebaseApp.getApps(context).isEmpty() ? FirebaseApp.initializeApp(context, options) : FirebaseApp.getInstance();
            auth = FirebaseAuth.getInstance(app);
            auth.useEmulator(BuildConfig.FIREBASE_EMULATOR_HOST, 9099);
        } else {
            app = FirebaseApp.initializeApp(context);
            if (app == null) return null;
            auth = FirebaseAuth.getInstance(app);
        }
        // ПЕРЕМЕННАЯ: auth
        // Настоящий FirebaseAuth SDK, null только при отсутствующей конфигурации.
        return auth;
    }
}
