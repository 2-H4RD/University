// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
// Общая версия Android Gradle Plugin взята из Lesson2.
plugins { alias(libs.plugins.android.application) apply false }
