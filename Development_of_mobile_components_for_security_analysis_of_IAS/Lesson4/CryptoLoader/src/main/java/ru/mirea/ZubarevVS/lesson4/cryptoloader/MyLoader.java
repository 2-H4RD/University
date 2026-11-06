package ru.mirea.ZubarevVS.lesson4.cryptoloader;


import android.content.Context;
import android.os.Bundle;

import androidx.loader.content.AsyncTaskLoader;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

import java.nio.charset.StandardCharsets;

/**
 * Loader получает только ciphertext/key/IV. Дешифрование выполняется в loadInBackground.
 */
public class MyLoader extends AsyncTaskLoader<String> {
    // ПЕРЕМЕННАЯ: args
    // Bundle аргументов Loader: ciphertext, key и IV, копируется в MyLoader.
    private final Bundle args;
    // ПЕРЕМЕННАЯ: cached
    // Готовый результат Loader, доставляется повторно без новой дешифровки.
    private String cached;

    public MyLoader(Context context, Bundle args) {
        super(context);
        this.args = new Bundle(args);
    }

    @Override
    // ЗАЩИТА: onStartLoading
    // Начинает/возобновляет Loader: уже готовый cached возвращается deliverResult, иначе forceLoad
    // планирует loadInBackground.
    protected void onStartLoading() {
        if (cached != null) deliverResult(cached);
        else forceLoad();
    }

    @Override
    // ЗАЩИТА: loadInBackground
    // Фоновая часть Loader восстанавливает SecretKeySpec из переданных байтов, создаёт AES/GCM/NoPadding,
    // применяет тот же IV и тег длиной 128 бит, возвращает расшифрованную строку UTF-8 либо понятную
    // ошибку.
    public String loadInBackground() {
        try {
            // ПЕРЕМЕННАЯ: cipher
            // Cipher/байты шифротекста согласно объявлению; AES/GCM требует тот же IV при расшифровании.
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(args.getByteArray("key"), "AES"), new GCMParameterSpec(128, args.getByteArray("iv")));
            return new String(cipher.doFinal(args.getByteArray("cipher")), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return "Ошибка дешифрования: " + e.getClass().getSimpleName();
        }
    }

    @Override
    // ЗАЩИТА: deliverResult
    // Запоминает результат в cached и передаёт его базовому Loader для доставки слушателю. Это сохраняет
    // результат Loader при пересоздании подписчика.
    public void deliverResult(String data) {
        cached = data;
        super.deliverResult(data);
    }
}
