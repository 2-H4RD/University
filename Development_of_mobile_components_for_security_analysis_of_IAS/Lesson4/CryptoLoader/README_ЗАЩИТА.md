# CryptoLoader · практика 4

**Требование:** AES шифрование фразы, передача ciphertext/ключа в Loader, дешифрование и Toast/Snackbar.

Введите фразу с русскими буквами. KeyGenerator создаёт случайный AES-256 ключ; Cipher AES/GCM/NoPadding при ENCRYPT_MODE создаёт IV и добавляет тег аутентичности. В args попадают три массива: key, iv, cipher; Base64 в поле — только представление ciphertext. restartLoader передаёт Bundle в MyLoader. loadInBackground выполняет DECRYPT_MODE с SecretKeySpec и GCMParameterSpec(128,iv), а doFinal проверяет тег и расшифровывает. UTF-8 возвращает исходные символы. onLoadFinished получает результат в UI и показывает Snackbar. cached позволяет повторно доставить данные без повторного вычисления. Поворот привязывает существующий Loader. AES здесь изучается в памяти процесса: это не долговременное хранение ключей и не замена AndroidKeyStore. Пустая фраза не запускает работу.

[Полный разбор кода](../РАЗБОР_КОДА.md) · [Защита](../ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) · [Фактические проверки](../ОТЧЁТ_О_ПРОВЕРКАХ.md)
