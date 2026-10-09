/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Фрагменты и ориентация.
 * inflater создаёт View из XML, container даёт параметры будущего родителя. false запрещает
 * немедленное прикрепление: FragmentManager делает его сам. state - восстановленное состояние.
 * Возвращается корень разметки/Binding. Каждая панель содержит собственный note; одинаковый ID внутри
 * разных View фрагментов не смешивает их состояния.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson3.simplefragmentapp;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
/** Фрагмент управляет своим XML и не обращается к соседнему фрагменту. */
public class FirstFragment extends Fragment {
    // РАЗБОР onCreateView:
    // inflater создаёт View из XML, container даёт параметры будущего родителя. false запрещает
    // немедленное прикрепление: FragmentManager делает его сам. state - восстановленное состояние.
    // Возвращается корень разметки/Binding.
    @Nullable @Override public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_first, container, false); // Добавление в контейнер выполняет FragmentManager.
    }
}
