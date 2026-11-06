package ru.mirea.ZubarevVS.lesson4.workmanager;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson4.workmanager.databinding.ActivityMainBinding;

/**
 * Worker с ограничениями. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;
    // ПЕРЕМЕННАЯ: manager
    // Системный/AndroidX менеджер из getSystemService/getInstance; точный тип показывает строка
    // объявления.
    private androidx.work.WorkManager manager;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        manager = androidx.work.WorkManager.getInstance(this);
        manager.getWorkInfosForUniqueWorkLiveData("lesson4-audit").observe(this, list -> {
            if (list != null && !list.isEmpty()) {
                androidx.work.WorkInfo info = list.get(0);
                binding.result.setText(info.getState().name() + "\n" + info.getOutputData().getString("digest"));
            }
        });
        binding.start.setOnClickListener(v -> {
            // ПЕРЕМЕННАЯ: text
            // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
            // String; в Worker/Data передаётся уже строковое значение.
            String text = binding.text.getText().toString();
            if (text.isEmpty()) {
                binding.text.setError("Введите текст");
                return;
            }
            androidx.work.Constraints constraints = new androidx.work.Constraints.Builder().setRequiredNetworkType(androidx.work.NetworkType.CONNECTED).setRequiresCharging(binding.charging.isChecked()).build();
            androidx.work.OneTimeWorkRequest request = new androidx.work.OneTimeWorkRequest.Builder(UploadWorker.class).setConstraints(constraints).setInputData(new androidx.work.Data.Builder().putString("text", text).build()).build();
            manager.enqueueUniqueWork("lesson4-audit", androidx.work.ExistingWorkPolicy.REPLACE, request);
        });
        binding.cancel.setOnClickListener(v -> manager.cancelUniqueWork("lesson4-audit"));

    }

}
