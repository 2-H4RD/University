/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Два способа обработки событий.
 * tvOut хранит ссылку на поле результата, btnWhoAmI и btnItIsNotMe - на кнопки, checkBox - на флажок.
 * oclBtnWhoAmI является объектом View.OnClickListener: onClick меняет текст на номер 5 и вызывает
 // РАЗБОР onItIsNotMeClick:
 // public void и один параметр View обязательны для android:onClick. tvOut.setText меняет содержимое;
 // checkBox.toggle инвертирует boolean checked. btnItIsNotMe найден в коде, но listener этой кнопки
 // назначен XML.
 * toggle. Вторая кнопка вызывает public void onItIsNotMeClick(View view) через android:onClick из XML.
 * В обоих случаях меняются текст и флажок. Последний текст сохраняется в Bundle; состояние CheckBox
 * сохраняет Android по ID.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.buttonclicker;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

/**
 * Пример двух способов обработки нажатий: Java-слушатель и метод из XML.
 */
public class MainActivity extends AppCompatActivity {

    // Поля класса доступны всем обработчикам. Это соответствует требованию методички.
    private TextView tvOut;
    private Button btnWhoAmI;
    private Button btnItIsNotMe;
    private CheckBox checkBox;

    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        applySystemBarInsets();

        // findViewById вызывается только после setContentView: иначе элементы ещё не созданы.
        tvOut = findViewById(R.id.tvOut);
        btnWhoAmI = findViewById(R.id.btnWhoAmI);
        btnItIsNotMe = findViewById(R.id.btnItIsNotMe);
        checkBox = findViewById(R.id.checkBox);
        if (savedInstanceState != null) {
            // TextView не сохраняет вычисленный текст автоматически, поэтому читаем свой ключ.
            tvOut.setText(savedInstanceState.getString("output", getString(R.string.initial_text)));
        }

        // Первый способ из задания: явно создаём объект интерфейса View.OnClickListener.
        View.OnClickListener oclBtnWhoAmI = new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                tvOut.setText(R.string.who_am_i_result);
                checkBox.toggle();
            }
        };
        btnWhoAmI.setOnClickListener(oclBtnWhoAmI);

        // btnItIsNotMe тоже найден через findViewById, как требует пример методички.
        // Его обработчик назначается вторым способом: android:onClick в activity_main.xml.
    }

    /**
     * Второй способ из задания: имя этого метода записано в android:onClick.
     * Метод обязан быть public, возвращать void и принимать единственный View.
     *
     * @param view элемент интерфейса, который вызвал обработчик
     */
    // РАЗБОР onItIsNotMeClick:
    // public void и один параметр View обязательны для android:onClick. tvOut.setText меняет содержимое;
    // checkBox.toggle инвертирует boolean checked. btnItIsNotMe найден в коде, но listener этой кнопки
    // назначен XML.
    public void onItIsNotMeClick(View view) {
        tvOut.setText(R.string.not_me_result);
        checkBox.toggle();
    }

    @Override
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    protected void onSaveInstanceState(Bundle outState) {
        outState.putString("output", tvOut.getText().toString()); // Сохраняем значение, а не ссылку на старую View.
        super.onSaveInstanceState(outState); // Родитель отдельно сохраняет checked у CheckBox с ID.
    }

    /** Сохраняет отступы XML и дополнительно учитывает системные панели Android. */
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
