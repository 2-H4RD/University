/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Обмен с другими приложениями.
 * message - редактируемый текст для ACTION_SEND; createChooser выбирает получателя. ShareActivity
 * экспортирована и объявляет SEND/DEFAULT/text/plain. Приём проверяет действие и MIME и извлекает
 * EXTRA_TEXT. Изображение выбирается отдельным ACTION_PICK, а не принимается текстовым фильтром.
 * picker - ActivityResultLauncher<Intent> с контрактом StartActivityForResult: callback проверяет
 * RESULT_OK и ненулевой Uri. camera - ActivityResultLauncher<Void> с TakePicturePreview: получает
 * Bitmap миниатюры либо null при отмене. pickedText и cameraText хранят подписи, thumbnail - небольшое
 * превью. Bundle сохраняет эти значения при повороте. Встроенные обработчики объявлены до onCreate и
 * регистрируются в одинаковом порядке.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson3.sharer;

import android.os.Bundle;
import android.content.Intent;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import android.content.ActivityNotFoundException;
import android.app.Activity;
import android.graphics.Bitmap;
import android.net.Uri;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

/** ACTION_SEND и два примера возврата результата из системного приложения. */
public class MainActivity extends AppCompatActivity {
    private String pickedText; // Сохраняем текст результата отдельно от launcher.
    private String cameraText;
    private Bitmap thumbnail; // Это маленькое превью; полное фото в задании не требуется.
    // Регистрация выполняется при каждом создании Activity, до её запуска.
    private final ActivityResultLauncher<Intent> picker = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(), result -> {
                Intent data = result.getData(); // При отмене Intent может отсутствовать.
                Uri uri = data == null ? null : data.getData();
                pickedText = result.getResultCode() == Activity.RESULT_OK && uri != null
                        ? getString(R.string.picked, uri.toString()) : getString(R.string.cancelled);
                ((TextView) findViewById(R.id.picked)).setText(pickedText);
            });
    private final ActivityResultLauncher<Void> camera = registerForActivityResult(
            new ActivityResultContracts.TakePicturePreview(), bitmap -> {
                thumbnail = bitmap; // null означает отмену съёмки.
                ((ImageView) findViewById(R.id.preview)).setImageBitmap(bitmap);
                cameraText = getString(bitmap == null ? R.string.camera_cancel : R.string.camera_ok);
                ((TextView) findViewById(R.id.camera_status)).setText(cameraText);
            });
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает состояние Activity.
        EdgeToEdge.enable(this); // Поддерживаем системное оформление Android 15.
        setContentView(R.layout.activity_main); // Сначала создаём View из XML.
        ScreenInsets.apply(findViewById(R.id.main)); // Убираем пересечение с панелями и клавиатурой.
        ((EditText) findViewById(R.id.message)).setText(R.string.default_text);
        if (savedInstanceState != null) {
            pickedText = savedInstanceState.getString("picked", getString(R.string.picked_initial));
            cameraText = savedInstanceState.getString("camera", getString(R.string.camera_initial));
            thumbnail = savedInstanceState.getParcelable("thumbnail"); // Миниатюра восстанавливается после поворота.
            ((TextView) findViewById(R.id.picked)).setText(pickedText);
            ((TextView) findViewById(R.id.camera_status)).setText(cameraText);
            ((ImageView) findViewById(R.id.preview)).setImageBitmap(thumbnail);
        }
        findViewById(R.id.share).setOnClickListener(view -> {
            Intent intent = new Intent(Intent.ACTION_SEND); // Просим другой экран обработать текст.
            intent.setType("text/plain"); // MIME-тип сужает выбор до текстовых получателей.
            intent.putExtra(Intent.EXTRA_TEXT, ((EditText) findViewById(R.id.message)).getText().toString());
            try { startActivity(Intent.createChooser(intent, getString(R.string.chooser))); }
            catch (ActivityNotFoundException e) { showNoApp(); }
        });
        findViewById(R.id.pick).setOnClickListener(view -> {
            Intent intent = new Intent(Intent.ACTION_PICK); // Системный выбор с возвратом URI.
            intent.setType("image/*"); // Конкретный тип надёжнее неоднозначного */* из примера.
            try { picker.launch(intent); } catch (ActivityNotFoundException e) { showNoApp(); }
        });
        findViewById(R.id.camera).setOnClickListener(view -> {
            try { camera.launch(null); } catch (ActivityNotFoundException e) { showNoApp(); }
        });
    }
    // РАЗБОР showNoApp:
    // Toast объясняет отсутствие системного обработчика. Метод вызывается из catch, не выдавая ошибку за
    // успешно полученный результат.
    private void showNoApp() { Toast.makeText(this, R.string.no_app, Toast.LENGTH_LONG).show(); }
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    @Override protected void onSaveInstanceState(Bundle outState) {
        outState.putString("picked", ((TextView) findViewById(R.id.picked)).getText().toString());
        outState.putString("camera", ((TextView) findViewById(R.id.camera_status)).getText().toString());
        outState.putParcelable("thumbnail", thumbnail); // Храним только малое превью, не полное изображение.
        super.onSaveInstanceState(outState);
    }
}
