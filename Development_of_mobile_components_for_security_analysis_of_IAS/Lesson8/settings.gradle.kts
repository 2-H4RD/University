  // Google Maven содержит AndroidX/AGP, Maven Central — внешние библиотеки.
  pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
  dependencyResolutionManagement {
      repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
      repositories { google(); mavenCentral() }
  }
  rootProject.name = "Lesson8"

include(":YandexMaps")
include(":YandexDriver")
include(":OSMMaps")

  // Контрольный проект также включён в общий Verify, но может открываться отдельно.
  include(":MireaProject")
  project(":MireaProject").projectDir=file("MireaProject/app")

include(":UITests")
