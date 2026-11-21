package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.mireaproject.databinding.ActivityPhotoNoteBinding;

/**
 * Камера · полная фотография. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class PhotoNoteActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityPhotoNoteBinding binding;

    // ПЕРЕМЕННАЯ: photoPath
    // Путь последнего успешно полученного полноразмерного JPEG.
    private String photoPath = "", pendingPath = "";
    private final androidx.activity.result.ActivityResultLauncher<String> cameraPermission = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.RequestPermission(), ok -> {
        if (ok) takePhoto();
        else binding.status.setText("Доступ к камере не разрешён. Можно повторить запрос.");
    });
    private final androidx.activity.result.ActivityResultLauncher<android.net.Uri> camera = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.TakePicture(), ok -> {
        if (ok) {
            photoPath = pendingPath;
            getPreferences(MODE_PRIVATE).edit().putString("photo", photoPath).apply();
            showPhoto();
        } else binding.status.setText("Съёмка отменена; прежняя фотография сохранена");
    });

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityPhotoNoteBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());
        binding.caption.setText(getPreferences(MODE_PRIVATE).getString("caption", ""));
        binding.saveNote.setOnClickListener(v -> {
            getPreferences(MODE_PRIVATE).edit().putString("caption", binding.caption.getText().toString()).apply();
            binding.status.setText("Фото и описание инцидента сохранены");
        });

        photoPath = state == null ? getPreferences(MODE_PRIVATE).getString("photo", "") : state.getString("photo", "");
        pendingPath = state == null ? "" : state.getString("pending", "");
        showPhoto();
        binding.take.setOnClickListener(v -> requestCamera());
        binding.photo.setOnClickListener(v -> requestCamera());

    }

    // ЗАЩИТА: requestCamera
    // Проверяет CAMERA. При разрешении вызывает takePhoto; иначе запускает Activity Result
    // RequestPermission. Отказ оставляет экран доступным и позволяет повторить запрос.
    private void requestCamera() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.CAMERA) == android.content.pm.PackageManager.PERMISSION_GRANTED)
            takePhoto();
        else cameraPermission.launch(android.Manifest.permission.CAMERA);
    }

    // ЗАЩИТА: takePhoto
    // Создаёт новый JPEG в Pictures приложения. FileProvider преобразует File в content Uri с authority
    // applicationId.fileprovider. Контракт TakePicture передаёт этот Uri как EXTRA_OUTPUT системной камере
    // и возвращает boolean успеха.
    private void takePhoto() {
        try {
            java.io.File dir = getExternalFilesDir(android.os.Environment.DIRECTORY_PICTURES);
            if (dir == null) throw new java.io.IOException("Хранилище недоступно");
            // ПЕРЕМЕННАЯ: file
            // Файл текущей операции; путь создаётся в разрешённом каталоге приложения или через SAF.
            java.io.File file = java.io.File.createTempFile("photo_", ".jpg", dir);
            pendingPath = file.getAbsolutePath();
            // ПЕРЕМЕННАЯ: uri
            // content Uri, предоставляющий ограниченный доступ к файлу/папке, а не обычный путь Windows.
            android.net.Uri uri = androidx.core.content.FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", file);
            camera.launch(uri); // TakePicture передаёт Uri как EXTRA_OUTPUT, возвращает успех, а не миниатюру.
        } catch (Exception e) {
            binding.status.setText("Не удалось открыть камеру: " + e.getMessage());
        }
    }

    // ЗАЩИТА: showPhoto
    // Читает сначала только размеры JPEG (inJustDecodeBounds). inSampleSize уменьшает декодируемое превью,
    // чтобы не расходовать память на полноразмерную Bitmap. Сам исходный JPEG сохраняет исходные размеры;
    // статус показывает их и путь.
    private void showPhoto() {
        if (photoPath.isEmpty() || !new java.io.File(photoPath).isFile()) return;
        android.graphics.BitmapFactory.Options o = new android.graphics.BitmapFactory.Options();
        o.inJustDecodeBounds = true;
        android.graphics.BitmapFactory.decodeFile(photoPath, o);
        int width = o.outWidth, height = o.outHeight;
        o.inJustDecodeBounds = false;
        o.inSampleSize = 1;
        while (Math.max(width, height) / o.inSampleSize > 1200) o.inSampleSize *= 2;
        binding.photo.setImageBitmap(android.graphics.BitmapFactory.decodeFile(photoPath, o));
        binding.status.setText("Фото: " + width + "×" + height + "\n" + photoPath);
    }

    @Override
    // ЗАЩИТА: onSaveInstanceState
    // Сохраняет компактные данные в out/Bundle, затем вызывает родителя. Это снимок UI для пересоздания, а
    // не постоянное хранилище. Ссылки на старые View/MediaPlayer не сохраняются.
    protected void onSaveInstanceState(Bundle out) {
        out.putString("photo", photoPath);
        out.putString("pending", pendingPath);
        super.onSaveInstanceState(out);
    }

}
