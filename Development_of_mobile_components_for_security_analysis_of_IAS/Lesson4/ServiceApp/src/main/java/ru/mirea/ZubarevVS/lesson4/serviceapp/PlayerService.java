package ru.mirea.ZubarevVS.lesson4.serviceapp;


import android.app.*;
import android.content.Intent;
import android.media.MediaPlayer;
import android.os.IBinder;

import androidx.core.app.NotificationCompat;

/**
 * Service не создаёт отдельный поток автоматически; MediaPlayer сам обрабатывает аудио асинхронно.
 */
public class PlayerService extends Service {
    // ПЕРЕМЕННАЯ: player
    // MediaPlayer, владеющий ресурсами воспроизведения; release освобождает их.
    private MediaPlayer player;

    @Override
    // ЗАЩИТА: onCreate
    // Service создаёт MediaPlayer, канал уведомлений и foreground-уведомление с названием учебной
    // композиции. Жизненный цикл Service независим от видимости Activity; ресурсы освобождаются в
    // onDestroy.
    public void onCreate() {
        super.onCreate();
        // ПЕРЕМЕННАЯ: manager
        // Системный/AndroidX менеджер из getSystemService/getInstance; точный тип показывает строка
        // объявления.
        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("mirea_player", "Плеер · Зубарев В.С.", NotificationManager.IMPORTANCE_LOW));
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pending = PendingIntent.getActivity(this, 5, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification notification = new NotificationCompat.Builder(this, "mirea_player").setSmallIcon(android.R.drawable.ic_media_play).setContentTitle("Сигнал безопасного канала").setContentText("Зубарев В.С. · БИСО-02-22 · №5").setContentIntent(pending).setOngoing(true).build();
        startForeground(5, notification);
        player = MediaPlayer.create(this, R.raw.signal);
        player.setOnCompletionListener(mp -> stopSelf());
    }

    @Override
    // ЗАЩИТА: onStartCommand
    // Service получил команду запуска. Запускает уже созданный MediaPlayer, не создавая второй экземпляр
    // при повторном нажатии. START_NOT_STICKY запрещает бессмысленный автоматический повтор после
    // завершения процесса.
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (player != null && !player.isPlaying()) player.start();
        return START_NOT_STICKY;
    }

    @Override
    // ЗАЩИТА: onBind
    // Возвращает null: данный Service запускается командой startForegroundService и не предоставляет
    // интерфейс bound service.
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    // ЗАЩИТА: onDestroy
    // Завершает жизнь экземпляра: освобождает собственные MediaPlayer/Looper/Executor. super завершает
    // инфраструктуру родителя. onDestroy не гарантирован при убийстве всего процесса ОС.
    public void onDestroy() {
        if (player != null) {
            player.release();
            player = null;
        }
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }
}
