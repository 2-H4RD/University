// namespace определяет пакеты R/Binding, applicationId — отдельный устанавливаемый APK.
plugins { id("com.android.application") }
android {
    namespace="ru.mirea.ZubarevVS.lesson4.looper"
    compileSdk=35
    defaultConfig { applicationId="ru.mirea.ZubarevVS.lesson4.looper"; minSdk=26; targetSdk=35; versionCode=1; versionName="1.0" }
    compileOptions { sourceCompatibility=JavaVersion.VERSION_11; targetCompatibility=JavaVersion.VERSION_11 }
    buildFeatures { viewBinding=true; buildConfig=true }
}
dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.activity:activity:1.8.0")
    implementation("com.google.android.material:material:1.14.0")

}
