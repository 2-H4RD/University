// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
// Каждый application-модуль устанавливается как самостоятельное приложение.
plugins { alias(libs.plugins.android.application) }
android {
    namespace = "ru.mirea.ZubarevVS.mireaproject" // Пакет сгенерированных R и Binding.
    compileSdk = 35 // Та же установленная платформа, что в Lesson1 и Lesson2.
    defaultConfig {
        applicationId = "ru.mirea.ZubarevVS.mireaproject" // Уникальный ID не заменяет предыдущие практики.
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures { viewBinding = true } // Binding связывает XML с Java без поиска по id.
}
dependencies {
    implementation(libs.appcompat) // AppCompatActivity и поддержка тем.
    implementation(libs.activity.ktx) // EdgeToEdge и Activity Result API доступны из Java.
    implementation(libs.material) // Компоненты и тема Material 3.
    implementation("androidx.fragment:fragment:1.5.4") // AndroidX Fragment и FragmentContainerView.
    implementation("androidx.navigation:navigation-fragment:2.8.9")
    implementation("androidx.navigation:navigation-ui:2.8.9") // NavController связывает граф с меню.
    implementation("androidx.drawerlayout:drawerlayout:1.2.0")
}
