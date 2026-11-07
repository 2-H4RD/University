package ru.mirea.ZubarevVS.lesson6.notebook;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson6.notebook.databinding.ActivityMainBinding;

/**
 * Блокнот · публичные Documents. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;

    // ПЕРЕМЕННАЯ: tree
    // SAF tree Uri именно публичной папки Documents, разрешение на него сохраняется явно.
    private android.net.Uri tree;
    private final androidx.activity.result.ActivityResultLauncher<android.net.Uri> directoryPicker = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree(), uri -> {
        if (uri != null) {
            String document = android.provider.DocumentsContract.getTreeDocumentId(uri);
            if (!document.equals("primary:Documents")) {
                binding.status.setText("Выберите именно публичную папку Documents");
                return;
            }
            getContentResolver().takePersistableUriPermission(uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION | android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            tree = uri;
            getPreferences(MODE_PRIVATE).edit().putString("tree", uri.toString()).apply();
            binding.status.setText("Documents доступна: " + uri);
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

        // ПЕРЕМЕННАЯ: saved
        // Ранее сохранённое значение, прочитанное при восстановлении экрана.
        String saved = getPreferences(MODE_PRIVATE).getString("tree", "");
        if (!saved.isEmpty()) {
            tree = android.net.Uri.parse(saved);
            binding.status.setText("Documents: " + tree);
        }
        binding.directory.setOnClickListener(v -> directoryPicker.launch(android.net.Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADocuments")));
        binding.save.setOnClickListener(v -> fileOperation(true));
        binding.load.setOnClickListener(v -> fileOperation(false));

    }

    // ЗАЩИТА: fileOperation
    // Снимает копии filename/quote в UI, проверяет имя без обхода каталогов и выданный SAF tree Uri. В io
    // ищет существующий DocumentFile, при необходимости создаёт новый; режим wt перезаписывает,
    // InputStream читает UTF-8 обратно в поле.
    private void fileOperation(boolean save) {
        String name = binding.filename.getText().toString().trim(), text = binding.quote.getText().toString();
        if (tree == null) {
            binding.status.setText("Сначала разрешите папку Documents");
            return;
        }
        if (!name.matches("[\\p{L}\\p{N}_. -]{1,80}\\.txt") || name.contains("..")) {
            binding.filename.setError("Имя .txt без путей, до 80 символов");
            return;
        }
        if (save && text.trim().isEmpty()) {
            binding.quote.setError("Введите цитату");
            return;
        }
        io.execute(() -> {
            try {
                androidx.documentfile.provider.DocumentFile directory = androidx.documentfile.provider.DocumentFile.fromTreeUri(this, tree);
                // ПЕРЕМЕННАЯ: file
                // Файл текущей операции; путь создаётся в разрешённом каталоге приложения или через SAF.
                androidx.documentfile.provider.DocumentFile file = directory.findFile(name);
                if (save) {
                    if (file == null) file = directory.createFile("text/plain", name);
                    if (file == null) throw new java.io.IOException("Не создан файл");
                    try (java.io.OutputStream stream = getContentResolver().openOutputStream(file.getUri(), "wt")) {
                        stream.write(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    }
                    ui(() -> binding.status.setText("Сохранено с перезаписью в Documents/" + name));
                } else {
                    if (file == null) throw new java.io.FileNotFoundException(name);
                    try (java.io.InputStream stream = getContentResolver().openInputStream(file.getUri()); java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream()) {
                        byte[] b = new byte[4096];
                        int count;
                        while ((count = stream.read(b)) != -1) bytes.write(b, 0, count);
                        String restored = bytes.toString("UTF-8");
                        ui(() -> {
                            binding.quote.setText(restored);
                            binding.status.setText("Загружено из Documents/" + name);
                        });
                    }
                }
            } catch (Exception e) {
                ui(() -> binding.status.setText("Ошибка файла: " + e.getMessage()));
            }
        });
    }

}
