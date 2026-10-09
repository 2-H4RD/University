/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Типы компоновки.
 * По умолчанию показывается activity_second: EditText и шесть кнопок. В layout-land лежит вариант с
 * тремя рядами по две кнопки. LinearLayout располагает детей в линию; вложенные horizontal-контейнеры
 * образуют две строки по три кнопки. TableLayout выравнивает три TableRow по столбцам.
 * ConstraintLayout связывает края элементов с родителем и друг с другом. Меню «Макет» позволяет
 * показать каждый этап упражнения без редактирования setContentView перед защитой.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.layouttype;

import android.os.Bundle;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/**
 * Главный экран модуля layouttype.
 *
 * <p>В модуле сохранены все макеты из задания. Сейчас Activity показывает
 * activity_second.xml, как требует заключительный пункт главы 5. Остальные этапы
 * доступны через меню в правом верхнем углу: Java выбирает R.layout по ID пункта.
 * Выбранный макет записывается в Bundle и восстанавливается после поворота.</p>
 */
public class MainActivity extends AppCompatActivity {
    private int selectedLayout = R.layout.activity_second;

    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // В API 35 приложение рисует интерфейс от края до края экрана.
        EdgeToEdge.enable(this);

        // Android сам выберет activity_second.xml из layout-land при повороте экрана.
        if (savedInstanceState != null) selectedLayout = savedInstanceState.getInt("layout", R.layout.activity_second);
        showLayout(selectedLayout);
    }

    // РАЗБОР showLayout:
    // layout - один из разрешённых R.layout. selectedLayout сохраняет текущий выбор; setContentView заново
    // создаёт иерархию View, поэтому слушатель Insets назначается после загрузки каждого макета.
    private void showLayout(int layout) {
        selectedLayout = layout;
        setContentView(layout); // Каждый выбор создаёт View соответствующего учебного макета.
        applySystemBarInsets();
    }

    @Override
    // РАЗБОР onCreateOptionsMenu:
    // Добавляет учебный выбор макетов. menu содержит пункты с ID 1..5; они обозначают варианты разметки, а
    // не ID ресурсов Android.
    public boolean onCreateOptionsMenu(Menu menu) {
        // Overflow-меню помогает показать все этапы практики, оставляя activity_second стартовым.
        menu.add(0, 1, 0, R.string.menu_six);
        menu.add(0, 2, 1, R.string.menu_linear);
        menu.add(0, 3, 2, R.string.menu_table);
        menu.add(0, 4, 3, R.string.menu_constraint);
        menu.add(0, 5, 4, R.string.menu_text);
        return true;
    }

    @Override
    // РАЗБОР onOptionsItemSelected:
    // item содержит выбранный пункт. Его itemId определяет layout, после чего showLayout загружает XML и
    // обновляет безопасные отступы.
    public boolean onOptionsItemSelected(MenuItem item) {
        int id = item.getItemId();
        if (id == 1) showLayout(R.layout.activity_second);
        else if (id == 2) showLayout(R.layout.linear_layout);
        else if (id == 3) showLayout(R.layout.table_layout);
        else if (id == 4) showLayout(R.layout.constraint_layout);
        else if (id == 5) showLayout(R.layout.activity_main);
        else return super.onOptionsItemSelected(item);
        return true;
    }

    @Override
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    protected void onSaveInstanceState(Bundle outState) {
        outState.putInt("layout", selectedLayout);
        super.onSaveInstanceState(outState);
    }

    /** Добавляет безопасные отступы статус-бара и панели навигации к отступам из XML. */
    // РАЗБОР applySystemBarInsets:
    // root - корень текущего макета. Четыре переменные запоминают исходный padding. Insets дают размеры
    // системных панелей и клавиатуры; к ним добавляются исходные отступы. Listener работает и после
    // поворота/изменения окна.
    private void applySystemBarInsets() {
        View root = findViewById(R.id.main);
        int left = root.getPaddingLeft();
        int top = root.getPaddingTop();
        int right = root.getPaddingRight();
        int bottom = root.getPaddingBottom();

        ViewCompat.setOnApplyWindowInsetsListener(root, (view, windowInsets) -> {
            Insets bars = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.ime());
            view.setPadding(left + bars.left, top + bars.top,
                    right + bars.right, bottom + bars.bottom);
            return windowInsets;
        });
    }
}
