# Запускает только AVD этой практики, сохранённый внутри verification.
$lessonProjectRoot = Split-Path -Parent $PSScriptRoot
$lessonSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$lessonAvdHome = Join-Path $lessonProjectRoot 'verification\avd-home'
if (-not (Test-Path -LiteralPath (Join-Path $lessonAvdHome 'Lesson2_API35.ini'))) {
    throw 'Учебный AVD не найден. Создайте устройство API 35 через Device Manager.'
}
$env:ANDROID_AVD_HOME = $lessonAvdHome # Позволяет emulator найти локальную конфигурацию устройства.
Start-Process -FilePath (Join-Path $lessonSdk 'emulator\emulator.exe') -WindowStyle Hidden `
    -ArgumentList @('-avd', 'Lesson2_API35', '-port', '5556', '-no-snapshot', '-no-boot-anim', '-no-audio')
# Если появился запрос Allow USB debugging, подтвердите его вручную в эмуляторе.
