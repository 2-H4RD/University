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
import android.app.DatePickerDialog;
import android.widget.DatePicker;
import androidx.fragment.app.DialogFragment;
import java.util.Calendar;

/** Выбор даты реализован штатным DatePickerDialog. */
public class MyDateDialogFragment extends DialogFragment implements DatePickerDialog.OnDateSetListener {
    @Override
    // РАЗБОР onCreateDialog:
    // DialogFragment запрашивает объект Dialog. savedInstanceState может содержать восстановленное
    // состояние. requireContext гарантирует контекст прикреплённого фрагмента. Возвращённое окно
    // показывает и сохраняет FragmentManager.
    public Dialog onCreateDialog(Bundle savedInstanceState) {
        Calendar now = Calendar.getInstance(); // Начальное значение — текущая дата устройства.
        return new DatePickerDialog(requireContext(), this, now.get(Calendar.YEAR),
                now.get(Calendar.MONTH), now.get(Calendar.DAY_OF_MONTH)); // Месяц передаётся в диапазоне 0–11.
    }
    @Override
    // РАЗБОР onDateSet:
    // view - сам DatePicker, year/month/dayOfMonth - подтверждённый выбор. requireActivity возвращает
    // хозяина, приведение к MainActivity позволяет вызвать onDateSelected.
    public void onDateSet(DatePicker view, int year, int month, int dayOfMonth) {
        ((MainActivity) requireActivity()).onDateSelected(year, month, dayOfMonth); // Форматирование выполняет Activity.
    }
}
