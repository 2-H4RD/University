// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
// Репозитории плагинов и библиотек используются всеми шестью модулями.
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "Lesson2"
// Каждый application-модуль собирается в отдельный APK для отдельного упражнения.
include(":ActivityLifecycle", ":MultiActivity", ":IntentFilter", ":ToastApp", ":NotificationApp", ":Dialog")
