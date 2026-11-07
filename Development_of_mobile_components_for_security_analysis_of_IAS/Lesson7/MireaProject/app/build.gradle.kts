// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
// Каждый application-модуль устанавливается как самостоятельное приложение.
plugins { alias(libs.plugins.android.application) }
android {
    namespace = "ru.mirea.ZubarevVS.mireaproject" // Пакет сгенерированных R и Binding.
    compileSdk = 35 // Та же установленная платформа, что в Lesson1 и Lesson2.
    defaultConfig {
        buildConfigField(
            "String",
            "FIREBASE_EMULATOR_HOST",
            "\"${providers.gradleProperty("firebaseEmulatorHost").orElse("").get()}\""
        )

        applicationId =
            "ru.mirea.ZubarevVS.mireaproject" // Общий Firebase applicationId: практика 8 обновляет установленную версию практики 7.
        minSdk = 26
        targetSdk = 35
        versionCode = 7
        versionName = "1.0"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        viewBinding = true; buildConfig = true
    } // Binding связывает XML с Java без поиска по id.
}
dependencies {
    implementation("com.google.firebase:firebase-auth:23.1.0")
    implementation("androidx.work:work-runtime:2.9.0")
    implementation(libs.appcompat) // AppCompatActivity и поддержка тем.
    implementation(libs.activity.ktx) // EdgeToEdge и Activity Result API доступны из Java.
    implementation(libs.material) // Компоненты и тема Material 3.
    implementation("androidx.fragment:fragment:1.5.4") // AndroidX Fragment и FragmentContainerView.
    implementation("androidx.navigation:navigation-fragment:2.8.9")
    implementation("androidx.navigation:navigation-ui:2.8.9") // NavController связывает граф с меню.
    implementation("androidx.drawerlayout:drawerlayout:1.2.0")
}

if (file("google-services.json").exists()) apply(plugin = "com.google.gms.google-services")
