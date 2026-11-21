import java.util.Properties
val mapSecrets=Properties().apply { val secrets=rootProject.file("secrets.properties");if(secrets.exists())secrets.inputStream().use { load(it) } }
// namespace определяет пакеты R/Binding, applicationId — отдельный устанавливаемый APK.
plugins { id("com.android.application") }
android {
    namespace="ru.mirea.ZubarevVS.lesson8.yandexdriver"
    compileSdk=35
    defaultConfig {
        buildConfigField("String","YANDEX_MAPKIT_KEY","\"${mapSecrets.getProperty("yandexMapkitKey","")}\"")
  applicationId="ru.mirea.ZubarevVS.lesson8.yandexdriver"; minSdk=26; targetSdk=35; versionCode=1; versionName="1.0" }
    compileOptions { sourceCompatibility=JavaVersion.VERSION_11; targetCompatibility=JavaVersion.VERSION_11 }
    buildFeatures { viewBinding=true; buildConfig=true }
}
dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.activity:activity:1.8.0")
    implementation("com.google.android.material:material:1.14.0")
    implementation("com.yandex.android:maps.mobile:4.45.0-full")
}
