// namespace определяет пакеты R/Binding, applicationId — отдельный устанавливаемый APK.
plugins { id("com.android.application") }
android {
    namespace="ru.mirea.ZubarevVS.lesson7.firebaseauth"
    compileSdk=35
    defaultConfig {
        // -PfirebaseEmulatorHost=10.0.2.2 включает локальные проверки SDK, пусто — реальное облако.
        buildConfigField("String","FIREBASE_EMULATOR_HOST","\"${providers.gradleProperty("firebaseEmulatorHost").orElse("").get()}\"")
  applicationId="ru.mirea.ZubarevVS.lesson7.firebaseauth"; minSdk=26; targetSdk=35; versionCode=1; versionName="1.0" }
    compileOptions { sourceCompatibility=JavaVersion.VERSION_11; targetCompatibility=JavaVersion.VERSION_11 }
    buildFeatures { viewBinding=true; buildConfig=true }
}
dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.activity:activity:1.8.0")
    implementation("com.google.android.material:material:1.14.0")
    implementation("com.google.firebase:firebase-auth:23.1.0")
}

// Собственный google-services.json подключается стандартным плагином только при наличии файла.
if(file("google-services.json").exists())apply(plugin="com.google.gms.google-services")
