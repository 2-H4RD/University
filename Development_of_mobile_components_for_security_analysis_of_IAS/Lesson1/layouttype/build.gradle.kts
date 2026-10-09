// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "ru.mirea.ZubarevVS.layouttype"
    compileSdk { version = release(35) }

    defaultConfig {
        applicationId = "ru.mirea.ZubarevVS.layouttype"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release { optimization { enable = false } }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation(libs.activity.ktx)
    implementation(libs.appcompat)
    implementation(libs.constraintlayout)
    implementation(libs.material)
}
