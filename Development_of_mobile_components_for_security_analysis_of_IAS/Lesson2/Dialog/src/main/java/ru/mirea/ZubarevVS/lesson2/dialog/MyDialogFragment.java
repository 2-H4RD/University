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
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.DialogFragment;

/** DialogFragment управляет показом окна и восстановлением при повороте. */
public class MyDialogFragment extends DialogFragment {
    @Override
    // РАЗБОР onCreateDialog:
    // DialogFragment запрашивает объект Dialog. savedInstanceState может содержать восстановленное
    // состояние. requireContext гарантирует контекст прикреплённого фрагмента. Возвращённое окно
    // показывает и сохраняет FragmentManager.
    public Dialog onCreateDialog(Bundle savedInstanceState) {
        AlertDialog.Builder builder = new AlertDialog.Builder(requireContext()); // Контекст прикреплённого фрагмента.
        builder.setTitle(R.string.alert_title) // Заголовок из методички.
                .setMessage(R.string.alert_message) // Текст вопроса.
                .setIcon(R.drawable.ic_school) // Значок учебного приложения.
                .setPositiveButton(R.string.positive, (dialog, which) ->
                        ((MainActivity) requireActivity()).onOkClicked()) // Передаём выбор родительской Activity.
                .setNeutralButton(R.string.neutral, (dialog, which) ->
                        ((MainActivity) requireActivity()).onNeutralClicked()) // Нейтральный ответ.
                .setNegativeButton(R.string.negative, (dialog, which) ->
                        ((MainActivity) requireActivity()).onCancelClicked()); // Отрицательный ответ; окно закроется автоматически.
        return builder.create(); // Возвращаем окно, показом которого занимается DialogFragment.
    }
}
