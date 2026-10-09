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
import android.app.Dialog;
import android.app.ProgressDialog;
import android.content.DialogInterface;
import androidx.fragment.app.DialogFragment;

/** ProgressDialog устарел с API 26, но прямо указан в самостоятельной работе.
 * В новом прикладном проекте вместо него следует использовать ProgressBar в разметке.
 * Этот пример показывает окно ожидания, не имитируя реальную загрузку данных.
 */
@SuppressWarnings("deprecation") // Предупреждение ожидаемо: изучаем API, требуемый методичкой.
public class MyProgressDialogFragment extends DialogFragment {
    @Override
    // РАЗБОР onCreateDialog:
    // DialogFragment запрашивает объект Dialog. savedInstanceState может содержать восстановленное
    // состояние. requireContext гарантирует контекст прикреплённого фрагмента. Возвращённое окно
    // показывает и сохраняет FragmentManager.
    public Dialog onCreateDialog(Bundle savedInstanceState) {
        ProgressDialog dialog = new ProgressDialog(requireContext()); // Создаём учебный модальный индикатор.
        dialog.setTitle(R.string.progress_title); // Заголовок явно указывает учебный характер окна.
        dialog.setMessage(getString(R.string.progress_message)); // Поясняем способ завершения.
        dialog.setIndeterminate(true); // Проценты неизвестны: отображаем вращающийся индикатор.
        dialog.setButton(DialogInterface.BUTTON_NEGATIVE, getString(R.string.close),
                (window, which) -> dismiss()); // Пользователь может закрыть окно без блокировки приложения.
        return dialog; // DialogFragment поддерживает Back и восстановление окна при повороте.
    }
}
