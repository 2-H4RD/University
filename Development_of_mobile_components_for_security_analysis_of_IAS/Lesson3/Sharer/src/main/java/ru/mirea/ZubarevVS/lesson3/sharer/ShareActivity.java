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
/** Экспортируемый получатель текста из системного окна «Поделиться». */
public class ShareActivity extends AppCompatActivity {
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_share);
        ScreenInsets.apply(findViewById(R.id.main));
        Intent intent = getIntent(); // Данные пришли от другого приложения и могут быть пустыми.
        CharSequence message = Intent.ACTION_SEND.equals(intent.getAction()) && "text/plain".equals(intent.getType())
                ? intent.getCharSequenceExtra(Intent.EXTRA_TEXT) : null;
        ((TextView) findViewById(R.id.received)).setText(message == null ? getString(R.string.receive_empty) : message);
        findViewById(R.id.back).setOnClickListener(view -> finish());
    }
}
