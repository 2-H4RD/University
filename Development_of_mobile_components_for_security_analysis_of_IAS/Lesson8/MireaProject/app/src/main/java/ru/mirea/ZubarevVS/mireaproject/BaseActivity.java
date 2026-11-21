package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.graphics.Insets;

import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;

/**
 * Общая механика экрана: Insets и фоновые операции. Предметная логика находится в MainActivity.
 */
public class BaseActivity extends AppCompatActivity {
    // Один последовательный исполнитель исключает гонку чтения/записи файлов.
    // ПЕРЕМЕННАЯ: io
    // Однопоточный ExecutorService для I/O; последовательность операций исключает гонку записи и
    // следующего чтения.
    protected final ExecutorService io = Executors.newSingleThreadExecutor();

    // ЗАЩИТА: frame
    // Принимает корень ActivityMainBinding, включает EdgeToEdge и устанавливает contentView. Исходные
    // padding сохраняются один раз. Insets systemBars|ime пересчитывают свободную область экрана и
    // клавиатуры; прошлый padding не накапливается.
    protected void frame(android.view.View root) {
        EdgeToEdge.enable(this);
        setContentView(root);
        final int l = root.getPaddingLeft(), t = root.getPaddingTop(), r = root.getPaddingRight(), b = root.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(root, (v, w) -> {
            Insets s = w.getInsets(WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.ime());
            v.setPadding(l + s.left, t + s.top, r + s.right, b + s.bottom);
            return w;
        });
        ViewCompat.requestApplyInsets(root);
    }

    // Callback из фонового потока допускается только пока Activity существует.
    // ЗАЩИТА: ui
    // Передаёт Runnable в главный поток через runOnUiThread. Callback выполняется, только если
    // Activity/Fragment ещё существует. Фоновый io/Thread не должен напрямую изменять TextView.
    protected void ui(Runnable action) {
        runOnUiThread(() -> {
            if (!isDestroyed() && !isFinishing()) action.run();
        });
    }

    @Override
    // ЗАЩИТА: onDestroy
    // Завершает жизнь экземпляра: освобождает собственные MediaPlayer/Looper/Executor. super завершает
    // инфраструктуру родителя. onDestroy не гарантирован при убийстве всего процесса ОС.
    protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }
}
