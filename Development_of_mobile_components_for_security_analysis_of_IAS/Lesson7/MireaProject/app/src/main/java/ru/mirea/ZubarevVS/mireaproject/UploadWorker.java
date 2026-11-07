package ru.mirea.ZubarevVS.mireaproject;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.work.*;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Реальная фоновая операция: SHA-256 входной строки, без сетевого запроса и без изменения UI.
 */
public class UploadWorker extends Worker {
    public UploadWorker(@NonNull Context context, @NonNull WorkerParameters parameters) {
        super(context, parameters);
    }

    @NonNull
    @Override
    // ЗАЩИТА: doWork
    // Выполняется WorkManager в фоновом потоке после выполнения Constraints. Из inputData читается text,
    // вычисляется SHA-256, байты переводятся в hex, результат возвращается Result.success(Data).
    // Ошибка/отмена не объявляются успехом.
    public Result doWork() {
        try {
            android.util.Log.d("UploadWorker", "doWork: start");
            // ПЕРЕМЕННАЯ: text
            // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
            // String; в Worker/Data передаётся уже строковое значение.
            String text = getInputData().getString("text");
            if (text == null) return Result.failure();
            if (isStopped()) return Result.failure();
            byte[] bytes = MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte b : bytes) hex.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
            android.util.Log.d("UploadWorker", "doWork: end " + hex);
            return Result.success(new Data.Builder().putString("digest", hex.toString()).build());
        } catch (Exception e) {
            return Result.failure(new Data.Builder().putString("error", e.toString()).build());
        }
    }
}
