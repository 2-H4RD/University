/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Диалоговые окна.
 * MainActivity открывает четыре DialogFragment через showOnce и FragmentManager. Теги
 * alert/time/date/progress помогают обнаружить уже открытое окно. MyDialogFragment создаёт
 * AlertDialog.Builder с тремя ответами; callbacks вызывают методы Activity. MyTimeDialogFragment
 * реализует OnTimeSetListener, MyDateDialogFragment - OnDateSetListener. Calendar задаёт начальное
 * значение устройства. Месяц приходит как 0..11: +1 применяется только при показе. Snackbar сообщает
 * выбранную дату/время, result сохраняет копию. ProgressDialog работает в режиме indeterminate и
 * закрывается вручную; он оставлен как API, явно требуемый заданием.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson2.dialog;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.fragment.app.DialogFragment;
import com.google.android.material.snackbar.Snackbar;

/** Основной AlertDialog и три диалога самостоятельной работы. */
public class MainActivity extends AppCompatActivity {

    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает Activity и фрагменты.
        EdgeToEdge.enable(this); // Экран использует всю область окна Android 15.
        setContentView(R.layout.activity_main); // Создаём элементы из XML до findViewById.
        applyInsets(); // Элементы не перекрываются системными панелями.
        if (savedInstanceState != null) { // Сохраняем видимый выбор при повороте экрана.
            ((TextView) findViewById(R.id.result)).setText(savedInstanceState.getString("result"));
        }
    }

    // РАЗБОР onClickShowDialog:
    // Создаёт MyDialogFragment и передаёт в showOnce с тегом alert. Окно конструирует сам фрагмент в
    // onCreateDialog.
    public void onClickShowDialog(View view) {
        showOnce(new MyDialogFragment(), "alert"); // Фрагмент сам создаст AlertDialog.
    }
    // РАЗБОР onClickShowTime:
    // Создаёт фрагмент штатного TimePickerDialog. Тег time отличает его от других диалогов.
    public void onClickShowTime(View view) {
        showOnce(new MyTimeDialogFragment(), "time"); // Отдельный класс из самостоятельного задания.
    }
    // РАЗБОР onClickShowDate:
    // Создаёт фрагмент DatePickerDialog с тегом date. Дата задаётся Calendar устройства и возвращается
    // listener.
    public void onClickShowDate(View view) {
        showOnce(new MyDateDialogFragment(), "date"); // Отдельный класс выбора даты.
    }
    // РАЗБОР onClickShowProgress:
    // Создаёт учебный ProgressDialog. Вращение не отражает реальную сетевую работу; закрытие выполняет
    // пользователь.
    public void onClickShowProgress(View view) {
        showOnce(new MyProgressDialogFragment(), "progress"); // Учебный пример устаревшего ProgressDialog.
    }
    // РАЗБОР showOnce:
    // dialog - новый DialogFragment, tag - его строковое имя в FragmentManager. findFragmentByTag
    // предотвращает повторный показ уже открытого окна. DialogFragment поддерживает восстановление при
    // повороте.
    private void showOnce(DialogFragment dialog, String tag) {
        if (getSupportFragmentManager().findFragmentByTag(tag) == null) { // Не открываем копию уже показанного окна.
            dialog.show(getSupportFragmentManager(), tag); // Менеджер сохраняет диалог при пересоздании Activity.
        }
    }
    // РАЗБОР onOkClicked:
    // Вызывает showChoice с ресурсом положительного ответа «Иду дальше». Этот callback связан с
    // setPositiveButton.
    public void onOkClicked() {
        showChoice(R.string.ok_result); // Обработчик положительной кнопки, предусмотренный методичкой.
    }
    // РАЗБОР onNeutralClicked:
    // Вызывает showChoice с ответом «На паузе». Порядок отображения кнопок задаёт тема, а не имя метода.
    public void onNeutralClicked() {
        showChoice(R.string.neutral_result); // Обработчик нейтральной кнопки.
    }
    // РАЗБОР onCancelClicked:
    // Вызывает showChoice с отрицательным ответом «Нет». Это выбор кнопки диалога, а не отмена Activity
    // Result.
    public void onCancelClicked() {
        showChoice(R.string.cancel_result); // Обработчик отрицательной кнопки.
    }
    // РАЗБОР showChoice:
    // messageId - целочисленный ID строкового ресурса. getString превращает его в String message. TextView
    // result и Toast показывают одинаковый ответ.
    private void showChoice(int messageId) {
        String message = getString(messageId); // Читаем нужный текст из ресурсов.
        ((TextView) findViewById(R.id.result)).setText(message); // Сохраняем видимый результат на экране.
        Toast.makeText(this, message, Toast.LENGTH_LONG).show(); // Toast соответствует основному заданию.
    }
    // РАЗБОР onTimeSelected:
    // hour и minute - значения TimePicker. getString форматирует оба числа; шаблон %02d дополняет число
    // ведущим нулём.
    public void onTimeSelected(int hour, int minute) {
        showPickerResult(getString(R.string.time_result, hour, minute)); // Форматируем время с ведущими нулями.
    }
    // РАЗБОР onDateSelected:
    // year/month/day приходят от DatePicker. month имеет диапазон 0..11; +1 выполняется только для
    // понятного пользователю отображения.
    public void onDateSelected(int year, int month, int day) {
        showPickerResult(getString(R.string.date_result, day, month + 1, year)); // Calendar.MONTH начинается с нуля.
    }
    // РАЗБОР showPickerResult:
    // text - уже отформатированный результат. TextView оставляет его на экране, Snackbar показывает
    // короткое уведомление внизу текущего View.
    private void showPickerResult(String text) {
        ((TextView) findViewById(R.id.result)).setText(text); // Результат останется после исчезновения Snackbar.
        Snackbar.make(findViewById(R.id.main), text, Snackbar.LENGTH_LONG).show(); // Демонстрируем Snackbar из задания.
    }
    @Override
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState); // FragmentManager сохраняет открытые диалоги.
        outState.putString("result", ((TextView) findViewById(R.id.result)).getText().toString()); // Сохраняем выбранный текст.
    }

    /** Сохраняем XML-отступы и добавляем место для системных панелей и клавиатуры. */
    // РАЗБОР applyInsets:
    // root - корневой View; left/top/right/bottom - исходный padding XML. bars - системные панели, ime -
    // клавиатура. Listener прибавляет Insets к исходным отступам, поэтому повторное событие не увеличивает
    // padding бесконечно. max выбирает нижнюю неперекрываемую область.
    private void applyInsets() {
        View root = findViewById(R.id.main); // Корневой ScrollView уже создан setContentView.
        int left = root.getPaddingLeft(); // Исходные отступы запоминаем один раз.
        int top = root.getPaddingTop();
        int right = root.getPaddingRight();
        int bottom = root.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(root, (view, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars()); // Статусная и навигационная панели.
            Insets ime = insets.getInsets(WindowInsetsCompat.Type.ime()); // Нижняя область экранной клавиатуры.
            view.setPadding(left + bars.left, top + bars.top, right + bars.right,
                    bottom + Math.max(bars.bottom, ime.bottom)); // Не складываем перекрывающиеся области.
            return insets; // Другие элементы тоже могут обработать эти Insets.
        });
        ViewCompat.requestApplyInsets(root); // Просим Android применить отступы к новой разметке.
    }
}
