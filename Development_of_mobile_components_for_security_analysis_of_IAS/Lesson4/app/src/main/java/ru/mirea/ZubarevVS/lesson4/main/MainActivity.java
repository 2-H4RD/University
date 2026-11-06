package ru.mirea.ZubarevVS.lesson4.main;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson4.main.databinding.ActivityMainBinding;

/**
 * Плеер · ViewBinding. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;
    // ПЕРЕМЕННАЯ: player
    // MediaPlayer, владеющий ресурсами воспроизведения; release освобождает их.
    private android.media.MediaPlayer player;
    // ПЕРЕМЕННАЯ: position
    // Позиция проигрывания в миллисекундах для восстановления после поворота.
    private int position;

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        position = state == null ? 0 : state.getInt("position", 0);
        binding.play.setOnClickListener(v -> {
            if (player == null) {
                player = android.media.MediaPlayer.create(this, R.raw.signal);
                player.seekTo(position);
            }
            if (player.isPlaying()) {
                player.pause();
                binding.status.setText("Пауза");
            } else {
                player.start();
                binding.status.setText("Воспроизводится: Сигнал безопасного канала");
            }
        });
        binding.stop.setOnClickListener(v -> {
            if (player != null) {
                player.release();
                player = null;
            }
            position = 0;
            binding.status.setText("Остановлено");
        });

    }

    @Override
    // ЗАЩИТА: onSaveInstanceState
    // Сохраняет компактные данные в out/Bundle, затем вызывает родителя. Это снимок UI для пересоздания, а
    // не постоянное хранилище. Ссылки на старые View/MediaPlayer не сохраняются.
    protected void onSaveInstanceState(Bundle out) {
        if (player != null) position = player.getCurrentPosition();
        out.putInt("position", position);
        super.onSaveInstanceState(out);
    }

    @Override
    // ЗАЩИТА: onPause
    // Экран теряет активность: подписки датчиков/карты и воспроизведение, если требуется,
    // приостанавливаются. Долговременные файлы не удаляются.
    protected void onPause() {
        if (player != null && player.isPlaying()) {
            player.pause();
            binding.status.setText("Пауза");
        }
        super.onPause();
    }

    @Override
    // ЗАЩИТА: onDestroy
    // Завершает жизнь экземпляра: освобождает собственные MediaPlayer/Looper/Executor. super завершает
    // инфраструктуру родителя. onDestroy не гарантирован при убийстве всего процесса ОС.
    protected void onDestroy() {
        if (player != null) player.release();
        super.onDestroy();
    }

}
