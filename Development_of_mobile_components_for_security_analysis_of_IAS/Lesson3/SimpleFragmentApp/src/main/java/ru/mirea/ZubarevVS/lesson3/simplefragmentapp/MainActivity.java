/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Фрагменты и ориентация.
 * FIRST/SECOND - стабильные теги фрагментов. selected хранит выбранный экран portrait, twoPane
 * определяется наличием secondContainer из layout-land. FragmentManager восстанавливает старые
 * экземпляры; их SavedState переносится в новый набор контейнеров. commitNow завершает
 * удаление/добавление до дальнейшей работы. В portrait show(tag) заменяет один фрагмент через
 * replace(...).commitNow(); в landscape два add создают панели с весами 1:2. Фрагменты используют
 * inflater.inflate(...,container,false): менеджер сам прикрепляет View. Фрагменты не обращаются друг к
 * другу. Состояние каждого поля note хранится независимо, включая переключение и поворот.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson3.simplefragmentapp;

import android.os.Bundle;
import android.content.Intent;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
/** Один фрагмент в portrait, два независимых фрагмента в landscape. */
public class MainActivity extends AppCompatActivity {
    private static final String FIRST = "first";
    private static final String SECOND = "second";
    private String selected = FIRST; // Запоминаем выбранный портретный экран.
    private boolean twoPane;
    // FragmentManager хранит только добавленные фрагменты. Эти два снимка сохраняют и скрытый экран.
    private Fragment.SavedState firstSaved;
    private Fragment.SavedState secondSaved;
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает состояние Activity.
        EdgeToEdge.enable(this); // Поддерживаем системное оформление Android 15.
        setContentView(R.layout.activity_main); // Сначала создаём View из XML.
        ScreenInsets.apply(findViewById(R.id.main)); // Убираем пересечение с панелями и клавиатурой.
        twoPane = findViewById(R.id.secondContainer) != null; // Признак XML из layout-land.
        if (savedInstanceState != null) {
            selected = savedInstanceState.getString("selected", FIRST);
            firstSaved = savedInstanceState.getParcelable("first_saved");
            secondSaved = savedInstanceState.getParcelable("second_saved");
        }
        FragmentManager manager = getSupportFragmentManager();
        // При смене ориентации контейнеры различаются. Удаляем восстановленные экземпляры
        // и переносим их сохранённое состояние в соответствующую новую раскладку.
        Fragment oldFirst = manager.findFragmentByTag(FIRST);
        Fragment oldSecond = manager.findFragmentByTag(SECOND);
        if (oldFirst != null) firstSaved = manager.saveFragmentInstanceState(oldFirst);
        if (oldSecond != null) secondSaved = manager.saveFragmentInstanceState(oldSecond);
        androidx.fragment.app.FragmentTransaction remove = manager.beginTransaction();
        for (Fragment fragment : manager.getFragments()) remove.remove(fragment);
        remove.commitNow(); // Сначала освобождаем контейнеры, затем добавляем нужные экраны.
        Fragment first = new FirstFragment();
        Fragment second = new SecondFragment();
        first.setInitialSavedState(firstSaved); // Переносим ввод в новый экземпляр с новой раскладкой.
        second.setInitialSavedState(secondSaved);
        if (twoPane) {
            manager.beginTransaction().setReorderingAllowed(true)
                    .add(R.id.fragmentContainerView, first, FIRST)
                    .add(R.id.secondContainer, second, SECOND).commitNow();
        } else {
            manager.beginTransaction().setReorderingAllowed(true)
                    .add(R.id.fragmentContainerView, FIRST.equals(selected) ? first : second, selected).commitNow();
            findViewById(R.id.btnFirstFragment).setOnClickListener(view -> show(FIRST));
            findViewById(R.id.btnSecondFragment).setOnClickListener(view -> show(SECOND));
        }
    }
    // РАЗБОР show:
    // tag - FIRST или SECOND. selected хранит активный экран. replace меняет содержимое одного
    // FragmentContainerView; commitNow выполняет замену синхронно до следующего нажатия. SavedState
    // сохраняет ввод уходящего фрагмента для возвращения.
    private void show(String tag) {
        if (tag.equals(selected)) return; // Повторное нажатие не сбрасывает текущий ввод.
        FragmentManager manager = getSupportFragmentManager();
        Fragment active = manager.findFragmentByTag(selected);
        if (active != null) {
            if (FIRST.equals(selected)) firstSaved = manager.saveFragmentInstanceState(active);
            else secondSaved = manager.saveFragmentInstanceState(active);
        }
        selected = tag;
        Fragment fragment = FIRST.equals(tag) ? new FirstFragment() : new SecondFragment();
        fragment.setInitialSavedState(FIRST.equals(tag) ? firstSaved : secondSaved);
        manager.beginTransaction().setReorderingAllowed(true)
                .replace(R.id.fragmentContainerView, fragment, tag).commitNow(); // Завершаем замену до следующего нажатия.
    }
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    @Override protected void onSaveInstanceState(Bundle outState) {
        outState.putString("selected", selected);
        FragmentManager manager = getSupportFragmentManager();
        Fragment first = manager.findFragmentByTag(FIRST);
        Fragment second = manager.findFragmentByTag(SECOND);
        if (first != null) firstSaved = manager.saveFragmentInstanceState(first);
        if (second != null) secondSaved = manager.saveFragmentInstanceState(second);
        outState.putParcelable("first_saved", firstSaved);
        outState.putParcelable("second_saved", secondSaved);
        super.onSaveInstanceState(outState); // FragmentManager сохраняет состояние активных фрагментов.
    }
}
