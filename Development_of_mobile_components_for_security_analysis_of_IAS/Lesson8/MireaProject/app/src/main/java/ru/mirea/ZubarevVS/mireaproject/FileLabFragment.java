package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.View;
import android.widget.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * FAB создаёт запись. Файл преобразуется в Base64 и сопровождается SHA-256 — кодировка не является шифрованием.
 */
public class FileLabFragment extends LabFragment {
    // ПЕРЕМЕННАЯ: result
    // Контейнер/текст/поле результата согласно типу объявления и методу.
    private TextView result;

    @Override
    // ЗАЩИТА: onViewCreated
    // View уже создана. Добавляются элементы предметного экрана, обработчики и наблюдения с
    // getViewLifecycleOwner. Долгая операция выполняется в io/Worker; результат изменяет только актуальный
    // View.
    public void onViewCreated(View view, Bundle state) {
        label("Файловая лаборатория · Base64 и SHA-256");
        result = label("Нажмите + для новой записи");
        // ПЕРЕМЕННАЯ: fab
        // FloatingActionButton, открывающая диалог новой записи.
        com.google.android.material.floatingactionbutton.FloatingActionButton fab = new com.google.android.material.floatingactionbutton.FloatingActionButton(requireContext());
        fab.setImageResource(android.R.drawable.ic_input_add);
        fab.setContentDescription("Создать запись");
        binding.content.addView(fab);
        fab.setOnClickListener(v -> new CreateNoteDialog().show(getChildFragmentManager(), "create-note"));
        getChildFragmentManager().setFragmentResultListener("new-note", getViewLifecycleOwner(), (key, data) -> save(data.getString("name"), data.getString("text")));
        button("Обновить список файлов", this::list);
        list();
    }

    // ЗАЩИТА: save
    // Сохраняет запись файловой лаборатории: исходный UTF-8, Base64 и SHA-256 в приватный файл. Base64 —
    // обратимая кодировка, SHA-256 — контрольная сумма; ни одно из них не называется шифрованием.
    private void save(String name, String text) {
        java.io.File directory = new java.io.File(requireContext().getFilesDir(), "file_lab");
        io.execute(() -> {
            try {
                if (!directory.exists() && !directory.mkdirs())
                    throw new IOException("Не создан каталог");
                byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
                StringBuilder hex = new StringBuilder();
                for (byte b : MessageDigest.getInstance("SHA-256").digest(bytes))
                    hex.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
                String report = "Текст: " + text + "\nBase64: " + android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP) + "\nSHA-256: " + hex;
                try (FileOutputStream out = new FileOutputStream(new File(directory, name + ".txt"))) {
                    out.write(report.getBytes(StandardCharsets.UTF_8));
                }
                ui(() -> result.setText("Сохранено " + name + ".txt\n" + report));
            } catch (Exception e) {
                ui(() -> result.setText("Ошибка файла: " + e.getMessage()));
            }
        });
    }

    // ЗАЩИТА: list
    // Читает имена файлов только из приватного каталога file_lab в фоновом io и показывает список. Чужие
    // файлы устройства не просматриваются.
    private void list() {
        File directory = new File(requireContext().getFilesDir(), "file_lab");
        io.execute(() -> {
            String[] names = directory.list();
            // ПЕРЕМЕННАЯ: text
            // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
            // String; в Worker/Data передаётся уже строковое значение.
            String text = names == null || names.length == 0 ? "Записей пока нет" : android.text.TextUtils.join("\n", names);
            ui(() -> result.setText(text));
        });
    }

    public static class CreateNoteDialog extends androidx.fragment.app.DialogFragment {
        @Override
        // ЗАЩИТА: onCreateDialog
        // Создаёт форму диалога и возвращает AlertDialog. После onShow заменяет обработчик положительной
        // кнопки, чтобы ошибка валидации не закрывала окно. Корректный результат передаётся через
        // FragmentResult API.
        public android.app.Dialog onCreateDialog(Bundle state) {
            LinearLayout form = new LinearLayout(requireContext());
            form.setOrientation(LinearLayout.VERTICAL);
            form.setPadding(32, 16, 32, 16);
            EditText name = new EditText(requireContext());
            name.setHint("Имя записи");
            name.setContentDescription("noteName");
            // ПЕРЕМЕННАЯ: text
            // Исходный текст либо ссылка на EditText по типу объявления. getText читает поле, toString даёт
            // String; в Worker/Data передаётся уже строковое значение.
            EditText text = new EditText(requireContext());
            text.setHint("Текст записи");
            text.setContentDescription("noteText");
            form.addView(name);
            form.addView(text);
            androidx.appcompat.app.AlertDialog dialog = new androidx.appcompat.app.AlertDialog.Builder(requireContext()).setTitle("Создание записи").setView(form).setNegativeButton("Отмена", null).setPositiveButton("Сохранить", null).create();
            dialog.setOnShowListener(v -> dialog.getButton(-1).setOnClickListener(button -> {
                String a = name.getText().toString().trim(), b = text.getText().toString();
                if (!a.matches("[a-zA-Z0-9_-]{1,40}")) {
                    name.setError("Латиница/цифры/_/-, до 40 символов");
                    return;
                }
                if (b.trim().isEmpty()) {
                    text.setError("Введите текст");
                    return;
                }
                // ПЕРЕМЕННАЯ: result
                // Контейнер/текст/поле результата согласно типу объявления и методу.
                Bundle result = new Bundle();
                result.putString("name", a);
                result.putString("text", b);
                getParentFragmentManager().setFragmentResult("new-note", result);
                dismiss();
            }));
            return dialog;
        }
    }
}
