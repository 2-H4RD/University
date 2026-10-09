/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Неявные намерения.
 * ACTION_VIEW вместе с HTTPS URI открывает страницу МИРЭА. ACTION_SEND, MIME text/plain, EXTRA_SUBJECT
 * и EXTRA_TEXT описывают передачу текста. createChooser каждый раз показывает список обработчиков. В
 * manifest MAIN/LAUNCHER обозначают точку входа. launchSafely ловит ActivityNotFoundException, если
 * подходящего приложения нет. Само появление chooser ещё не означает отправку сообщения.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson2.intentfilter;

import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import android.content.Intent;
import android.content.ActivityNotFoundException;
import android.net.Uri;

/** Неявный Intent задаёт действие, а приложение-обработчик выбирает система. */
public class MainActivity extends AppCompatActivity {

    @Override
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); // Родитель восстанавливает Activity и фрагменты.
        EdgeToEdge.enable(this); // Экран использует всю область окна Android 15.
        setContentView(R.layout.activity_main); // Создаём элементы из XML до findViewById.
        applyInsets(); // Элементы не перекрываются системными панелями.

    }

    // РАЗБОР onClickOpenBrowser:
    // Создаёт URI веб-страницы и неявный Intent ACTION_VIEW. Адрес обработчика не задан: его выбирает ОС.
    // HTTPS использует защищённое соединение.
    public void onClickOpenBrowser(View view) {
        Uri address = Uri.parse("https://www.mirea.ru/"); // Преобразуем адрес в объект URI.
        Intent intent = new Intent(Intent.ACTION_VIEW, address); // Просим систему открыть HTTPS-страницу.
        launchSafely(intent); // Учитываем отсутствие браузера на устройстве.
    }

    // РАЗБОР onClickShare:
    // Создаёт ACTION_SEND и MIME text/plain. EXTRA_TEXT - содержимое, EXTRA_SUBJECT - тема. createChooser
    // принудительно предлагает список подходящих получателей. Выполнение startActivity ещё не означает
    // фактическую отправку адресату.
    public void onClickShare(View view) {
        Intent intent = new Intent(Intent.ACTION_SEND); // Действие передачи данных другому приложению.
        intent.setType("text/plain"); // Получатель должен поддерживать обычный текст.
        intent.putExtra(Intent.EXTRA_SUBJECT, getString(R.string.share_subject)); // Тема сообщения.
        intent.putExtra(Intent.EXTRA_TEXT, getString(R.string.share_text)); // Подтверждённые ФИО и университет.
        launchSafely(Intent.createChooser(intent, getString(R.string.chooser_title))); // Показываем системный выбор.
    }

    // РАЗБОР launchSafely:
    // intent - полностью подготовленный запрос. try выполняет startActivity; catch обрабатывает отсутствие
    // подходящей Activity. Исключение нельзя считать успешным выполнением задания.
    private void launchSafely(Intent intent) {
        try {
            startActivity(intent); // Запуск не зависит от имени или пакета стороннего приложения.
        } catch (ActivityNotFoundException error) {
            Toast.makeText(this, R.string.no_app, Toast.LENGTH_LONG).show(); // Ошибка не приводит к падению.
        }
    }

    /** Сохраняем XML-отступы и добавляем место для системных панелей и клавиатуры. */
    // РАЗБОР applyInsets:
    // root - корневой View; left/top/right/bottom - исходный padding XML. bars - системные панели, ime -
    // клавиатура. Listener прибавляет Insets к исходным отступам, поэтому повторное событие не увеличивает
    // padding бесконечно. max выбирает нижнюю неперекрываемую область.
    private void applyInsets() {
        View root = findViewById(R.id.main); // Корневой ScrollView уже создан setContentView.
        int left = root.getPaddingLeft(); // Исходные отступы запоминаем один раз.
        int top = root.getPaddingTop();
        int right = root.getPaddingRight();
        int bottom = root.getPaddingBottom();
        ViewCompat.setOnApplyWindowInsetsListener(root, (view, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars()); // Статусная и навигационная панели.
            Insets ime = insets.getInsets(WindowInsetsCompat.Type.ime()); // Нижняя область экранной клавиатуры.
            view.setPadding(left + bars.left, top + bars.top, right + bars.right,
                    bottom + Math.max(bars.bottom, ime.bottom)); // Не складываем перекрывающиеся области.
            return insets; // Другие элементы тоже могут обработать эти Insets.
        });
        ViewCompat.requestApplyInsets(root); // Просим Android применить отступы к новой разметке.
    }
}
