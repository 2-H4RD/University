// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
// Application-модуль создаёт самостоятельное учебное приложение.
plugins { alias(libs.plugins.android.application) }
android {
    namespace = "ru.mirea.ZubarevVS.lesson2.notificationapp" // Namespace определяет пакет сгенерированного класса R.
    compileSdk = 35 // Используем уже установленную платформу из Lesson1.
    defaultConfig {
        applicationId = "ru.mirea.ZubarevVS.lesson2.notificationapp" // Уникальный ID позволяет установить все шесть APK.
        minSdk = 26 // Android 8: уведомления работают с каналами.
        targetSdk = 35 // Учитываем разрешения Android 13 и edge-to-edge Android 15.
        versionCode = 1
        versionName = "1.0"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}
dependencies {
    implementation(libs.appcompat) // Activity и AlertDialog из AndroidX.
    implementation(libs.activity.ktx) // EdgeToEdge для правильных системных отступов.
    implementation(libs.material) // Тема, кнопки и Snackbar.
}
