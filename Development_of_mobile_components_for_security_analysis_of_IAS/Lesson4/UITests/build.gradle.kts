plugins { id("com.android.test") }
android { namespace="ru.mirea.ZubarevVS.lesson4.uitests"; compileSdk=35; targetProjectPath=":MireaProject"
    defaultConfig { minSdk=26; targetSdk=35; testInstrumentationRunner="androidx.test.runner.AndroidJUnitRunner" }
    compileOptions { sourceCompatibility=JavaVersion.VERSION_11;targetCompatibility=JavaVersion.VERSION_11 }
}
dependencies { implementation("androidx.test:runner:1.5.2");implementation("androidx.test.ext:junit:1.1.5");implementation("androidx.test.uiautomator:uiautomator:2.3.0") }
