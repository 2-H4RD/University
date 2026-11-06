/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Navigation Drawer и браузер.
 * MireaApplication включает DynamicColors для Material You. ActivityMainBinding создаётся из
 * activity_main.xml; binding содержит типизированные ссылки на drawerLayout, navView, appBarMain и
 * toolbar. NavHostFragment содержит NavController, mobile_navigation.xml задаёт DataFragment и
 * WebViewFragment. ID nav_data/nav_web совпадают в меню, графе и AppBarConfiguration. NavigationUI
 * связывает эти элементы и управляет заголовком/гамбургером. DataFragment отображает карточки отрасли
 * в NestedScrollView. WebViewFragment управляет binding только пока есть View, сохраняет историю в
 * webState, проверяет HTTPS адреса, показывает реальный прогресс, обработку ошибок, Home/Reload/Back.
 * При открытой шторке Back закрывает её раньше истории WebView.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import ru.mirea.ZubarevVS.mireaproject.databinding.FragmentDataBinding;

/**
 * Информационный экран отрасли; Binding живёт только пока существует View фрагмента.
 */
public class DataFragment extends Fragment {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private FragmentDataBinding binding;

    // РАЗБОР onCreateView:
    // inflater создаёт View из XML, container даёт параметры будущего родителя. false запрещает
    // немедленное прикрепление: FragmentManager делает его сам. state - восстановленное состояние.
    // Возвращается корень разметки/Binding.
    @Nullable
    @Override
    // ЗАЩИТА: onCreateView
    // Создаёт FragmentLabBinding из fragment_lab.xml и возвращает корень. View принадлежит
    // FragmentManager; Binding очищается при onDestroyView.
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle state) {
        binding = FragmentDataBinding.inflate(inflater, container, false); // Создаём XML через сгенерированный класс.
        return binding.getRoot();
    }

    // РАЗБОР onDestroyView:
    // View фрагмента уничтожается, хотя сам Fragment может остаться. binding очищается, чтобы не
    // удерживать прежнюю разметку. WebView останавливается, сохраняет историю и освобождает ресурсы.
    @Override
    // ЗАЩИТА: onDestroyView
    // Жизнь разметки Fragment закончилась, хотя сам Fragment может ещё существовать. Binding/map
    // очищаются, чтобы не удерживать прежний экран.
    public void onDestroyView() {
        super.onDestroyView();
        binding = null; // Не удерживаем старую View после перехода на другой экран.
    }
}
