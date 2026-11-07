package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.mireaproject.databinding.ActivityVoiceNoteBinding;

/**
 * Диктофон · голосовая заметка. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class VoiceNoteActivity extends BaseActivity {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityVoiceNoteBinding binding;

    // ПЕРЕМЕННАЯ: recorder
    // MediaRecorder для записи микрофона; его методы должны соответствовать состоянию конечного автомата.
    private android.media.MediaRecorder recorder;
    // ПЕРЕМЕННАЯ: player
    // MediaPlayer, владеющий ресурсами воспроизведения; release освобождает их.
    private android.media.MediaPlayer player;
    // ПЕРЕМЕННАЯ: recording
    // Флаг активной записи, определяет текст/доступность кнопок.
    private boolean recording = false, playing = false;
    // ПЕРЕМЕННАЯ: recordFile
    // Файл .3gp во внешнем приватном Music приложения, не публичный Documents.
    private java.io.File recordFile;
    private final androidx.activity.result.ActivityResultLauncher<String> microphonePermission = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.RequestPermission(), ok -> {
        if (ok) startRecording();
        else binding.status.setText("Микрофон не разрешён. Нажмите запись для повторного запроса.");
    });

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityVoiceNoteBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());
        binding.caption.setText(getPreferences(MODE_PRIVATE).getString("caption", ""));
        binding.saveNote.setOnClickListener(v -> {
            getPreferences(MODE_PRIVATE).edit().putString("caption", binding.caption.getText().toString()).apply();
            binding.status.setText("Описание голосовой заметки сохранено");
        });

        recordFile = new java.io.File(getExternalFilesDir(android.os.Environment.DIRECTORY_MUSIC), "voice_note.3gp");
        binding.record.setOnClickListener(v -> {
            if (recording) stopRecording();
            else if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.RECORD_AUDIO) == android.content.pm.PackageManager.PERMISSION_GRANTED)
                startRecording();
            else microphonePermission.launch(android.Manifest.permission.RECORD_AUDIO);
        });
        binding.play.setOnClickListener(v -> {
            if (playing) stopPlaying();
            else startPlaying();
        });
        updateButtons();

    }

    // ЗАЩИТА: updateButtons
    // Отображает конечный автомат диктофона. Во время записи запрещено воспроизведение; при проигрывании
    // запрещена новая запись. Play доступна только при существующем непустом файле.
    private void updateButtons() {
        binding.record.setText(recording ? "Остановить запись" : "Начать запись · №5 · БИСО-02-22");
        binding.record.setEnabled(!playing);
        binding.play.setText(playing ? "Остановить воспроизведение" : "Воспроизвести");
        binding.play.setEnabled(!recording && recordFile.isFile() && recordFile.length() > 0);
    }

    // ЗАЩИТА: startRecording
    // Создаёт MediaRecorder, задаёт MIC → THREE_GPP → AMR_NB и путь output. prepare завершает настройку,
    // start начинает запись. Ошибка освобождает recorder и возвращает доступные кнопки.
    private void startRecording() {
        try {
            recorder = android.os.Build.VERSION.SDK_INT >= 31 ? new android.media.MediaRecorder(this) : new android.media.MediaRecorder();
            recorder.setAudioSource(android.media.MediaRecorder.AudioSource.MIC);
            recorder.setOutputFormat(android.media.MediaRecorder.OutputFormat.THREE_GPP);
            recorder.setAudioEncoder(android.media.MediaRecorder.AudioEncoder.AMR_NB);
            recorder.setOutputFile(recordFile.getAbsolutePath());
            recorder.prepare();
            recorder.start();
            recording = true;
            binding.status.setText("Идёт запись голосовой заметки");
        } catch (Exception e) {
            if (recorder != null) {
                recorder.release();
                recorder = null;
            }
            recording = false;
            binding.status.setText("Ошибка записи: " + e.getMessage());
        }
        updateButtons();
    }

    // ЗАЩИТА: stopRecording
    // Останавливает запись и освобождает MediaRecorder в finally. stop может выбросить RuntimeException
    // для слишком короткой записи; такой незавершённый файл удаляется и объясняется ошибка.
    private void stopRecording() {
        if (recorder == null) return;
        try {
            recorder.stop();
            binding.status.setText("Запись сохранена: " + recordFile.length() + " байт\n" + recordFile.getAbsolutePath());
        } catch (RuntimeException e) {
            binding.status.setText("Запись слишком короткая. Запишите не менее секунды.");
            recordFile.delete();
        } finally {
            recorder.release();
            recorder = null;
            recording = false;
            updateButtons();
        }
    }

    // ЗАЩИТА: startPlaying
    // Создаёт MediaPlayer для сохранённого файла, готовит его и начинает проигрывание.
    // OnCompletionListener автоматически освобождает player и возвращает кнопки.
    private void startPlaying() {
        try {
            player = new android.media.MediaPlayer();
            player.setDataSource(recordFile.getAbsolutePath());
            player.prepare();
            player.setOnCompletionListener(p -> {
                stopPlaying();
                binding.status.setText("Воспроизведение завершено");
            });
            player.start();
            playing = true;
            binding.status.setText("Воспроизведение голосовой заметки");
        } catch (Exception e) {
            stopPlaying();
            binding.status.setText("Ошибка воспроизведения: " + e.getMessage());
        }
        updateButtons();
    }

    // ЗАЩИТА: stopPlaying
    // Освобождает MediaPlayer, сбрасывает playing и пересчитывает кнопки. release обязателен для
    // освобождения аппаратных/системных аудиоресурсов.
    private void stopPlaying() {
        if (player != null) {
            player.release();
            player = null;
        }
        playing = false;
        updateButtons();
    }

    @Override
    // ЗАЩИТА: onStop
    // Экран перестал быть видимым: запись/воспроизведение или обновления геолокации останавливаются,
    // ресурсы освобождаются. Foreground Service имеет собственный жизненный цикл и не зависит от этой
    // Activity.
    protected void onStop() {
        if (recording) stopRecording();
        if (playing) stopPlaying();
        super.onStop();
    }

}
