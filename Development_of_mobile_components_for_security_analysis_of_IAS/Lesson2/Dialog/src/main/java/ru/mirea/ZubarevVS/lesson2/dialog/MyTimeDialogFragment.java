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
import android.app.TimePickerDialog;
import android.widget.TimePicker;
import androidx.fragment.app.DialogFragment;
import java.util.Calendar;

/** Выбор времени реализован штатным TimePickerDialog. */
public class MyTimeDialogFragment extends DialogFragment implements TimePickerDialog.OnTimeSetListener {
    @Override
    // РАЗБОР onCreateDialog:
    // DialogFragment запрашивает объект Dialog. savedInstanceState может содержать восстановленное
    // состояние. requireContext гарантирует контекст прикреплённого фрагмента. Возвращённое окно
    // показывает и сохраняет FragmentManager.
    public Dialog onCreateDialog(Bundle savedInstanceState) {
        Calendar now = Calendar.getInstance(); // При первом открытии выбираем текущее время устройства.
        return new TimePickerDialog(requireContext(), this, now.get(Calendar.HOUR_OF_DAY),
                now.get(Calendar.MINUTE), true); // 24-часовой формат привычен для учебного примера.
    }
    @Override
    // РАЗБОР onTimeSet:
    // view - TimePicker, hourOfDay/minute - подтверждённое время. callback передаёт его MainActivity,
    // которая занимается форматированием и выводом.
    public void onTimeSet(TimePicker view, int hourOfDay, int minute) {
        ((MainActivity) requireActivity()).onTimeSelected(hourOfDay, minute); // Передаём подтверждённое время на экран.
    }
}
