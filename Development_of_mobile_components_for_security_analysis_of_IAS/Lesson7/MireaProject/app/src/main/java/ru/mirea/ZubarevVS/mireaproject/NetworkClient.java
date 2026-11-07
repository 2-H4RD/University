package ru.mirea.ZubarevVS.mireaproject;

import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

/**
 * Ограниченный HTTPS GET: timeout, HTTP status, UTF-8, закрытие потока и disconnect. Вызывается из io.
 */
public final class NetworkClient {
    // ЗАЩИТА: get
    // Выполняет ограниченный HTTPS GET: connect/read timeout, HTTP 200, чтение до 1 МБ в UTF-8, закрытие
    // InputStream и disconnect в finally. В UI-потоке не вызывается.
    public static String get(String address) throws Exception {
        URL url = new URL(address);
        if (!"https".equals(url.getProtocol())) throw new IOException("Разрешён только HTTPS");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(15000);
        connection.setRequestProperty("Accept", "application/json");
        try {
            // ПЕРЕМЕННАЯ: status
            // Числовой HTTP-код ответа getResponseCode; только 200 разрешает разбор тела, остальные значения
            // становятся IOException.
            int status = connection.getResponseCode();
            if (status != 200) throw new IOException("HTTP " + status);
            try (InputStream in = connection.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                // ПЕРЕМЕННАЯ: buffer
                // Буфер порционного чтения байтов; не весь файл сразу.
                byte[] buffer = new byte[4096];
                // ПЕРЕМЕННАЯ: n
                // Число байтов, прочитанное текущим read; −1 означает конец потока.
                int n;
                while ((n = in.read(buffer)) != -1) {
                    if (out.size() + n > 1048576) throw new IOException("Ответ больше 1 МБ");
                    out.write(buffer, 0, n);
                }
                return out.toString("UTF-8");
            }
        } finally {
            connection.disconnect();
        }
    }
}
