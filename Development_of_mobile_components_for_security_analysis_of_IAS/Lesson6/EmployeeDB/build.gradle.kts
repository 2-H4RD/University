 // namespace определяет пакеты R/Binding, applicationId — отдельный устанавливаемый APK.
 plugins { id("com.android.application") }
 android {
     namespace="ru.mirea.ZubarevVS.lesson6.employeedb"
     compileSdk=35
     defaultConfig { applicationId="ru.mirea.ZubarevVS.lesson6.employeedb"; minSdk=26; targetSdk=35; versionCode=1; versionName="1.0" }
     defaultConfig { testInstrumentationRunner="androidx.test.runner.AndroidJUnitRunner" }
     compileOptions { sourceCompatibility=JavaVersion.VERSION_11; targetCompatibility=JavaVersion.VERSION_11 }
     buildFeatures { viewBinding=true; buildConfig=true }
 }
 dependencies {
     implementation("androidx.appcompat:appcompat:1.6.1")
     implementation("androidx.activity:activity:1.8.0")
     implementation("com.google.android.material:material:1.14.0")
     implementation("androidx.room:room-runtime:2.6.1")
annotationProcessor("androidx.room:room-compiler:2.6.1")
     androidTestImplementation("androidx.test:core:1.5.0")
     androidTestImplementation("androidx.test:runner:1.5.2")
     androidTestImplementation("androidx.test.ext:junit:1.1.5")
 }
