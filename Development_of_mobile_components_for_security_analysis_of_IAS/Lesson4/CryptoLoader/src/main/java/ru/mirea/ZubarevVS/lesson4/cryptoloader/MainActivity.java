package ru.mirea.ZubarevVS.lesson4.cryptoloader;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson4.cryptoloader.databinding.ActivityMainBinding;

/**
 * AES и AsyncTaskLoader. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity implements androidx.loader.app.LoaderManager.LoaderCallbacks<String> {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        if (state != null)
            androidx.loader.app.LoaderManager.getInstance(this).initLoader(5, null, this);
        binding.encrypt.setOnClickListener(v -> {
            try {
                // ПЕРЕМЕННАЯ: phrase
                // Исходная пользовательская фраза UTF-8 для AES round-trip.
                String phrase = binding.phrase.getText().toString();
                if (phrase.trim().isEmpty()) {
                    binding.phrase.setError("Введите фразу");
                    return;
                }
                javax.crypto.KeyGenerator generator = javax.crypto.KeyGenerator.getInstance("AES");
                generator.init(256);
                // ПЕРЕМЕННАЯ: key
                // Криптографический ключ/мастер-ключ согласно типу; не является паролем пользователя.
                javax.crypto.SecretKey key = generator.generateKey();
                javax.crypto.Cipher aes = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
                aes.init(javax.crypto.Cipher.ENCRYPT_MODE, key);
                // ПЕРЕМЕННАЯ: cipher
                // Cipher/байты шифротекста согласно объявлению; AES/GCM требует тот же IV при расшифровании.
                byte[] cipher = aes.doFinal(phrase.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                // ПЕРЕМЕННАЯ: args
                // Bundle аргументов Loader: ciphertext, key и IV, копируется в MyLoader.
                Bundle args = new Bundle();
                args.putByteArray("key", key.getEncoded());
                args.putByteArray("cipher", cipher);
                args.putByteArray("iv", aes.getIV());
                binding.cipher.setText(android.util.Base64.encodeToString(cipher, android.util.Base64.NO_WRAP));
                binding.result.setText("Loader выполняет дешифрование…");
                androidx.loader.app.LoaderManager.getInstance(this).restartLoader(5, args, this);
            } catch (Exception e) {
                binding.result.setText("Ошибка AES: " + e.getMessage());
            }
        });

    }

    @Override
    // ЗАЩИТА: onCreateLoader
    // LoaderManager запрашивает экземпляр загрузчика с заданным id. Bundle содержит ciphertext, ключ и IV;
    // MyLoader получает собственную копию аргументов.
    public androidx.loader.content.Loader<String> onCreateLoader(int id, Bundle args) {
        // При восстановлении существующий Loader уже содержит собственный Bundle.
        if (args == null) args = new Bundle();
        return new MyLoader(this, args);
    }

    @Override
    // ЗАЩИТА: onLoadFinished
    // Вызывается на UI после завершения Loader. data/text — результат фонового дешифрования; он
    // отображается в TextView и Snackbar. Этот callback не выполняет криптографическую операцию повторно.
    public void onLoadFinished(androidx.loader.content.Loader<String> loader, String text) {
        binding.result.setText(text);
        com.google.android.material.snackbar.Snackbar.make(binding.getRoot(), text, com.google.android.material.snackbar.Snackbar.LENGTH_LONG).show();
    }

    @Override
    // ЗАЩИТА: onLoaderReset
    // Loader больше не предоставляет прежние данные. Здесь нет Cursor/адаптера с внешними ресурсами,
    // поэтому дополнительного закрытия не требуется.
    public void onLoaderReset(androidx.loader.content.Loader<String> loader) {
    }

}
