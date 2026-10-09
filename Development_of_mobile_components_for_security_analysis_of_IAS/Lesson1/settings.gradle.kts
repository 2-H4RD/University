// РАЗБОР: plugins выбирает Android-плагин; android задаёт SDK/ID/Java; dependencies добавляет библиотеки.
// namespace создаёт пакет R/Binding, applicationId - ID APK; Java 11 не задаёт JVM Gradle.
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}

rootProject.name = "Lesson1"
include(":app")
include(":layouttype")
include(":control_lesson1")
include(":buttonclicker")
