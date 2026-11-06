package ru.mirea.ZubarevVS.lesson4.serviceapp;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson4.serviceapp.databinding.ActivityMainBinding;

/**
 * Музыка в foreground Service. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;

    private final androidx.activity.result.ActivityResultLauncher<String> permission = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.RequestPermission(), granted -> binding.status.setText(granted ? "Уведомления разрешены" : "Уведомления отключены; foreground service доступен через системный список"));

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        if (android.os.Build.VERSION.SDK_INT >= 33 && androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED)
            permission.launch(android.Manifest.permission.POST_NOTIFICATIONS);
        binding.play.setOnClickListener(v -> {
            androidx.core.content.ContextCompat.startForegroundService(this, new android.content.Intent(this, PlayerService.class));
            binding.status.setText("Сервис воспроизводит Сигнал безопасного канала");
        });
        binding.stop.setOnClickListener(v -> {
            stopService(new android.content.Intent(this, PlayerService.class));
            binding.status.setText("Сервис остановлен");
        });

    }

}
