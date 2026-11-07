package ru.mirea.ZubarevVS.mireaproject;

/**
 * Только debug: изолированный контейнер для инструментальных проверок настоящих фрагментов.
 * Компонент не экспортируется и не входит в release APK. Firebase-вход проверяется отдельно
 * через штатную LoginActivity; тестовый контейнер не создаёт и не имитирует FirebaseUser.
 */
public class LabVerificationActivity extends BaseActivity {
    @Override
    // ЗАЩИТА: onCreate
    // Только src/debug: создаёт FrameLayout с постоянным ID и добавляет настоящий Fragment через
    // commitNow. Компонент не экспортируется, не входит в release и не изменяет Firebase-сессию; облачный
    // вход проверяется штатной LoginActivity отдельно.
    protected void onCreate(android.os.Bundle state) {
        super.onCreate(state);
        // ПЕРЕМЕННАЯ: host
        // FrameLayout только debug-контейнера для настоящего Fragment, идентификатор android.R.id.custom.
        android.widget.FrameLayout host = new android.widget.FrameLayout(this);
        host.setId(android.R.id.custom);
        frame(host);
        if (state != null) return;
        // ПЕРЕМЕННАЯ: fragment
        // Конкретный Fragment, выбранный из разрешённого списка в test-only Activity.
        androidx.fragment.app.Fragment fragment;
        switch (getIntent().getStringExtra("fragment")) {
            case "network":
                fragment = new NetworkFragment();
                break;
            default:
                throw new IllegalArgumentException("Неизвестный тестовый фрагмент");
        }
        getSupportFragmentManager().beginTransaction().replace(android.R.id.custom, fragment).commitNow();
    }
}
