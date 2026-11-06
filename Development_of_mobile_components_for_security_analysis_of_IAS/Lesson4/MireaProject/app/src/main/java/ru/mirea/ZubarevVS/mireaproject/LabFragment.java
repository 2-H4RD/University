package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.*;
import android.widget.*;

import androidx.fragment.app.Fragment;

import java.util.concurrent.*;

import ru.mirea.ZubarevVS.mireaproject.databinding.FragmentLabBinding;

/**
 * Общий контейнер новых экранов. Binding живёт только между onCreateView и onDestroyView.
 */
public abstract class LabFragment extends Fragment {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    protected FragmentLabBinding binding;
    // ПЕРЕМЕННАЯ: io
    // Однопоточный ExecutorService для I/O; последовательность операций исключает гонку записи и
    // следующего чтения.
    protected final ExecutorService io = Executors.newSingleThreadExecutor();

    @Override
    // ЗАЩИТА: onCreateView
    // Создаёт FragmentLabBinding из fragment_lab.xml и возвращает корень. View принадлежит
    // FragmentManager; Binding очищается при onDestroyView.
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle state) {
        binding = FragmentLabBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    // ЗАЩИТА: label
    // Создаёт текстовую подпись в общем контейнере FragmentLabBinding.content. Возвращённый TextView
    // позволяет обновлять конкретное поле состояния.
    protected TextView label(String value) {
        TextView v = new TextView(requireContext());
        v.setText(value);
        v.setTextSize(18);
        v.setPadding(0, 12, 0, 12);
        binding.content.addView(v, new android.widget.LinearLayout.LayoutParams(-1, -2));
        return v;
    }

    // ЗАЩИТА: edit
    // Создаёт EditText с детерминированным ID и contentDescription. Стабильный ID участвует в
    // восстановлении Android, contentDescription помогает доступности и автоматической проверке.
    protected EditText edit(String id, String hint) {
        EditText v = new EditText(requireContext());
        v.setId(0x02000000 | (id.hashCode() & 0x00ffffff));
        v.setContentDescription(id);
        v.setHint(hint);
        v.setMinHeight(48);
        binding.content.addView(v, new android.widget.LinearLayout.LayoutParams(-1, -2));
        return v;
    }

    // ЗАЩИТА: button
    // Создаёт Button и связывает нажатие с переданным Runnable. Возвращает саму кнопку, если её нужно
    // дополнительно настраивать.
    protected Button button(String text, Runnable action) {
        Button v = new Button(requireContext());
        v.setText(text);
        binding.content.addView(v, new android.widget.LinearLayout.LayoutParams(-1, -2));
        v.setOnClickListener(w -> action.run());
        return v;
    }

    // ЗАЩИТА: ui
    // Передаёт Runnable в главный поток через runOnUiThread. Callback выполняется, только если
    // Activity/Fragment ещё существует. Фоновый io/Thread не должен напрямую изменять TextView.
    protected void ui(Runnable action) {
        if (isAdded()) requireActivity().runOnUiThread(() -> {
            if (isAdded() && binding != null) action.run();
        });
    }

    @Override
    // ЗАЩИТА: onDestroyView
    // Жизнь разметки Fragment закончилась, хотя сам Fragment может ещё существовать. Binding/map
    // очищаются, чтобы не удерживать прежний экран.
    public void onDestroyView() {
        binding = null;
        super.onDestroyView();
    }

    @Override
    // ЗАЩИТА: onDestroy
    // Завершает жизнь экземпляра: освобождает собственные MediaPlayer/Looper/Executor. super завершает
    // инфраструктуру родителя. onDestroy не гарантирован при убийстве всего процесса ОС.
    public void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }
}
