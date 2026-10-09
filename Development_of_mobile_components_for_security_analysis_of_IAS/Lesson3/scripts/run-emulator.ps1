# Запускает AVD этой практики. На другом ПК создайте устройство в Device Manager.
$lessonProjectRoot = Split-Path -Parent $PSScriptRoot
$lessonSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$lessonAvdHome = Join-Path $lessonProjectRoot 'verification\avd-home'
if (-not (Test-Path -LiteralPath (Join-Path $lessonAvdHome 'Lesson3_API35.ini'))) {
    throw 'Локальный AVD отсутствует. Создайте устройство API 35 в Device Manager.'
}
$env:ANDROID_AVD_HOME = $lessonAvdHome
Start-Process -FilePath (Join-Path $lessonSdk 'emulator\emulator.exe') -WindowStyle Hidden -ArgumentList @('-avd','Lesson3_API35','-port','5558','-gpu','swiftshader','-no-snapshot','-no-boot-anim','-no-audio','-no-metrics')
