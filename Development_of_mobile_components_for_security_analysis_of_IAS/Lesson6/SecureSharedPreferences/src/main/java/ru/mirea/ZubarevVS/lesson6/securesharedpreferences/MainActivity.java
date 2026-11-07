package ru.mirea.ZubarevVS.lesson6.securesharedpreferences;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson6.securesharedpreferences.databinding.ActivityMainBinding;

/**
 * Поэт · зашифрованные настройки. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // Личный выбор из ответа пользователя; это начальное значение редактируемого поля.
    // Его сохранение выполняет та же кнопка save и тот же EncryptedSharedPreferences, что и другой ввод.
    private static final String DEFAULT_POET = "Пушкин Александр Сергеевич";
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;

    // ПЕРЕМЕННАЯ: secure
    // EncryptedSharedPreferences: шифрует ключи/значения, мастер-ключ хранится в AndroidKeyStore.
    private android.content.SharedPreferences secure;
    // ПЕРЕМЕННАЯ: portrait
    // URI портрета: android.resource:// для встроенного JPEG или content:// для выбранного файла.
    // Здесь хранится ссылка, а не пиксели изображения; шифруются имя и строка URI в настройках.
    private String portrait = "";
    private final androidx.activity.result.ActivityResultLauncher<String[]> picker = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.OpenDocument(), uri -> {
        if (uri != null) {
            getContentResolver().takePersistableUriPermission(uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION);
            portrait = uri.toString();
            binding.photo.setImageURI(uri);
        }
    });

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        binding.save.setEnabled(false);
        binding.pick.setOnClickListener(v -> picker.launch(new String[]{"image/*"}));
        io.execute(() -> {
            try {
                // ПЕРЕМЕННАЯ: key
                // Криптографический ключ/мастер-ключ согласно типу; не является паролем пользователя.
                androidx.security.crypto.MasterKey key = new androidx.security.crypto.MasterKey.Builder(this).setKeyScheme(androidx.security.crypto.MasterKey.KeyScheme.AES256_GCM).build();
                secure = androidx.security.crypto.EncryptedSharedPreferences.create(this, "secret_shared_prefs", key, androidx.security.crypto.EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV, androidx.security.crypto.EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM);
                // ПЕРЕМЕННАЯ: poet
                // Имя любимого поэта, введённое пользователем; сохраняется в зашифрованных настройках.
                String savedPoet = secure.getString("POET", "");
                // Заменяем только известный прежний fixture. Собственные сохранённые значения не стираем.
                boolean previousFixture = "Educational poet fixture".equals(savedPoet);
                String poet = savedPoet.isEmpty() || previousFixture ? DEFAULT_POET : savedPoet;
                String actor = secure.getString("ACTOR", "");
                portrait = previousFixture ? "" : secure.getString("PORTRAIT", "");
                // URI по имени ресурса стабилен после пересборки, в отличие от числового resource ID.
                // JPEG из ответа пользователя находится внутри APK и доступен без сети и разрешений SAF.
                // Выбранное позднее фото получает content:// URI; обе формы сохраняются как строка PORTRAIT.
                if (portrait.isEmpty())
                    portrait = "android.resource://" + getPackageName() + "/drawable/pushkin_portrait";
                ui(() -> {
                    binding.poet.setText(poet);
                    binding.actor.setText(actor.isEmpty() ? "Константин Хабенский (учебный пример)" : actor);
                    if (!portrait.isEmpty())
                        binding.photo.setImageURI(android.net.Uri.parse(portrait));
                    binding.save.setEnabled(true);
                    binding.status.setText("AndroidKeyStore готов. Файл: secret_shared_prefs.xml");
                });
            } catch (Exception e) {
                ui(() -> binding.status.setText("Ошибка защищённого хранилища: " + e.getMessage()));
            }
        });
        binding.save.setOnClickListener(v -> {
            // ПЕРЕМЕННАЯ: poet
            // Имя любимого поэта, введённое пользователем; сохраняется в зашифрованных настройках.
            String poet = binding.poet.getText().toString().trim(), actor = binding.actor.getText().toString().trim();
            if (poet.isEmpty()) {
                binding.poet.setError("Введите своего поэта");
                return;
            }
            if (portrait.isEmpty()) {
                binding.status.setText("Выберите фотографию или рисунок поэта");
                return;
            }
            io.execute(() -> {
                boolean ok = secure.edit().putString("POET", poet).putString("ACTOR", actor).putString("PORTRAIT", portrait).commit();
                ui(() -> binding.status.setText(ok ? "Имя и URI портрета сохранены зашифрованно" : "Ошибка записи"));
            });
        });

    }

}
