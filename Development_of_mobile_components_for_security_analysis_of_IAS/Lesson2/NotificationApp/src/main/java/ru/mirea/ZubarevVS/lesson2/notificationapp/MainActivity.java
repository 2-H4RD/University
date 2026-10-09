/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Уведомления.
 * CHANNEL_ID=lesson2_student обозначает канал, NOTIFICATION_ID=1 - отдельную запись уведомления,
 * PERMISSION_CODE=200 - запрос разрешения. Это три разных пространства идентификаторов. onCreate
 * регистрирует NotificationChannel, так как minSdk=26. onClickSendNotification запрашивает
 * POST_NOTIFICATIONS только с API 33. После согласия callback вызывает sendNotification; при отказе
 * показывает статус. sendNotification проверяет разрешение, общий выключатель уведомлений и важность
 * канала. PendingIntent содержит действие будущего нажатия. Builder формирует заголовок Mirea, иконку,
 * короткий и расширенный текст. notify(1,...) обновляет одну запись.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson2.notificationapp;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;

/** Канал обязателен с API 26, а runtime-разрешение — только с API 33. */
public class MainActivity extends AppCompatActivity {
    private static final String CHANNEL_ID = "lesson2_student"; // Строковый ID канала; не ID отдельного уведомления.
    private static final int NOTIFICATION_ID = 1; // Одинаковый ID обновляет предыдущее уведомление.
    private static final int PERMISSION_CODE = 200; // Отличает ответ на этот запрос разрешения.

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
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID,
                getString(R.string.channel_name), NotificationManager.IMPORTANCE_DEFAULT); // minSdk 26 позволяет создать канал напрямую.
        channel.setDescription(getString(R.string.channel_description)); // Описание видно в системных настройках.
        getSystemService(NotificationManager.class).createNotificationChannel(channel); // Повторная регистрация безопасна.
    }

    // РАЗБОР onClickSendNotification:
    // view - кнопка из XML. Проверка SDK_INT нужна, чтобы POST_NOTIFICATIONS запрашивалось только с API
    // 33. requestPermissions асинхронен: return заканчивает обработчик, а отправка продолжается в callback
    // после ответа.
    public void onClickSendNotification(View view) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) { // На Android 13+ нельзя отправлять без согласия пользователя.
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.POST_NOTIFICATIONS}, PERMISSION_CODE); // Показываем системный запрос.
            return; // Продолжим отправку только после ответа пользователя.
        }
        sendNotification(); // На Android 8–12 отдельного runtime-разрешения нет.
    }

    @Override
    // РАЗБОР onRequestPermissionsResult:
    // requestCode сравнивается с PERMISSION_CODE. grantResults может быть пустым, поэтому сначала
    // проверяется length. Значение PERMISSION_GRANTED означает согласие; при отказе изменяется status.
    // Ответ передаётся родителю AndroidX.
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults); // AndroidX тоже должен получить ответ.
        if (requestCode == PERMISSION_CODE) { // Обрабатываем только наш запрос.
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                sendNotification(); // Первое нажатие выполняется сразу после получения разрешения.
            } else {
                ((TextView) findViewById(R.id.status)).setText(R.string.denied_status); // Отказ не приводит к падению.
            }
        }
    }

    // РАЗБОР sendNotification:
    // manager обращается к системному сервису, channel описывает настройки канала. open - Intent будущего
    // нажатия, pending - PendingIntent, builder - конструктор содержимого. build создаёт Notification;
    // notify с постоянным ID заменяет прежнюю запись. Статус успеха обновляется после вызова сервиса.
    private void sendNotification() {
        if (Build.VERSION.SDK_INT >= 33 && ContextCompat.checkSelfPermission(this,
                Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return; // Повторно проверяем право непосредственно перед notify.
        }
        NotificationManagerCompat manager = NotificationManagerCompat.from(this); // Совместимый менеджер уведомлений.
        NotificationChannel channel = getSystemService(NotificationManager.class).getNotificationChannel(CHANNEL_ID);
        if (!manager.areNotificationsEnabled() || (channel != null
                && channel.getImportance() == NotificationManager.IMPORTANCE_NONE)) { // Канал может быть выключен отдельно.
            ((TextView) findViewById(R.id.status)).setText(R.string.disabled_status);
            return; // Не сообщаем об успешной отправке заблокированного уведомления.
        }
        Intent open = new Intent(this, MainActivity.class); // Нажатие на уведомление вернёт в приложение.
        open.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP); // Не создаём лишние копии экрана.
        PendingIntent pending = PendingIntent.getActivity(this, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE); // Получатель не может менять Intent.
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_school) // Маленькая иконка обязательна для уведомления.
                .setContentTitle(getString(R.string.notification_title)) // Заголовок из задания.
                .setContentText(getString(R.string.notification_text)) // Короткий текст в свёрнутом виде.
                .setStyle(new NotificationCompat.BigTextStyle().bigText(getString(R.string.notification_long))) // Полный текст.
                .setPriority(NotificationCompat.PRIORITY_DEFAULT) // На API 26+ важность задаёт канал.
                .setContentIntent(pending) // Действие нажатия на уведомление.
                .setAutoCancel(true); // После открытия приложения уведомление исчезает.
        manager.notify(NOTIFICATION_ID, builder.build()); // Передаём готовое уведомление системе.
        ((TextView) findViewById(R.id.status)).setText(R.string.sent_status); // Подтверждаем действие на экране.
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
