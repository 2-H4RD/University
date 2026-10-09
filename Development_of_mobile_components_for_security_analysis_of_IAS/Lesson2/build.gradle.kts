// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
// Версия плагина взята из проверенного локального проекта Lesson1.
plugins { alias(libs.plugins.android.application) apply false }
