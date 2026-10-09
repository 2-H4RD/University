# Проверяет оба самостоятельных проекта практики.
$lessonProjectRoot = Split-Path -Parent $PSScriptRoot
$lessonJdk = 'D:\Android Studio\jbr'
if (Test-Path -LiteralPath $lessonJdk) { $env:JAVA_HOME = $lessonJdk }
Push-Location -LiteralPath $lessonProjectRoot
try {
    & .\gradlew.bat assembleDebug lintDebug --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Сборка Lesson3 завершилась ошибкой.' }
    Push-Location -LiteralPath (Join-Path $lessonProjectRoot 'MireaProject')
    try {
        & .\gradlew.bat assembleDebug lintDebug --console=plain
        if ($LASTEXITCODE -ne 0) { throw 'Сборка MireaProject завершилась ошибкой.' }
    } finally { Pop-Location }
} finally { Pop-Location }
