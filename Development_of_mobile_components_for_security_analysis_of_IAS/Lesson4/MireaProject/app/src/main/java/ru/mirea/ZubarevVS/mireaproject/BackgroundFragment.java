package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.View;
import android.widget.*;

import androidx.work.*;

/**
 * Фрагмент ставит реальный Worker: вычисление контрольной суммы для проверки целостности текста.
 */
public class BackgroundFragment extends LabFragment {
    @Override
    // ЗАЩИТА: onViewCreated
    // View уже создана. Добавляются элементы предметного экрана, обработчики и наблюдения с
    // getViewLifecycleOwner. Долгая операция выполняется в io/Worker; результат изменяет только актуальный
    // View.
    public void onViewCreated(View view, Bundle state) {
        label("Фоновая проверка целостности · SHA-256");
        // ПЕРЕМЕННАЯ: text
        // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
        // String; в Worker/Data передаётся уже строковое значение.
        EditText text = edit("auditText", "Текст для контрольной суммы");
        // ПЕРЕМЕННАЯ: status
        // TextView состояния конкретного экрана, содержит результат/ошибку.
        TextView status = label("Задача ещё не поставлена");
        // ПЕРЕМЕННАЯ: manager
        // Системный/AndroidX менеджер из getSystemService/getInstance; точный тип показывает строка
        // объявления.
        WorkManager manager = WorkManager.getInstance(requireContext());
        manager.getWorkInfosForUniqueWorkLiveData("mirea-audit").observe(getViewLifecycleOwner(), infos -> {
            if (infos != null && !infos.isEmpty()) {
                WorkInfo info = infos.get(0);
                status.setText(info.getState().name() + "\n" + info.getOutputData().getString("digest"));
            }
        });
        button("Запустить Worker", () -> {
            String input = text.getText().toString();
            if (input.isEmpty()) {
                text.setError("Введите текст");
                return;
            }
            OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(UploadWorker.class).setInputData(new Data.Builder().putString("text", input).build()).build();
            manager.enqueueUniqueWork("mirea-audit", ExistingWorkPolicy.REPLACE, request);
        });
        button("Отменить Worker", () -> manager.cancelUniqueWork("mirea-audit"));
    }
}
