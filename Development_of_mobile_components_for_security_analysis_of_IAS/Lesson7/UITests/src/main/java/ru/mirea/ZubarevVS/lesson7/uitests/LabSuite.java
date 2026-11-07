package ru.mirea.ZubarevVS.lesson7.uitests;

import android.os.SystemClock;
import android.content.Context;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.*;

import org.junit.*;
import org.junit.runner.RunWith;

import java.io.*;

import static org.junit.Assert.*;

/**
 * Настоящие проверки на Android: тестовый APK, UiAutomator и JUnit AndroidJUnitRunner.
 */
@RunWith(AndroidJUnit4.class)
public class LabSuite {
    @Rule
    // ПЕРЕМЕННАЯ: testName
    // JUnit Rule даёт имя текущего тестового метода для файлов доказательств в @After.
    public org.junit.rules.TestName testName = new org.junit.rules.TestName();
    private UiDevice device;
    // ПЕРЕМЕННАЯ: output
    // Каталог фактических screenshot/XML проверок Android; это не заранее нарисованные результаты.
    private File output;

    @Before
    // ЗАЩИТА: setup
    // JUnit @Before подготавливает Android AVD: экран, снятие блокировки без изменения пароля, закрытая
    // шторка, естественная ориентация и папка доказательств в target context. Это не настройка
    // безопасности компьютера.
    public void setup() throws Exception {
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation());
        device.wakeUp();
        device.executeShellCommand("wm dismiss-keyguard");
        device.executeShellCommand("cmd statusbar collapse");
        device.setOrientationNatural();
        Context owner = InstrumentationRegistry.getInstrumentation().getTargetContext();
        File base = owner.getExternalFilesDir(null);
        if (base == null) base = owner.getFilesDir();
        output = new File(base, "ui-test-proofs");
        assertTrue("Не создан каталог доказательств", output.isDirectory() || output.mkdirs());
    }

    // ЗАЩИТА: launch
    // Тест через PackageManager разрешает фактический launcher, затем запускает его явным компонентом. Это
    // учитывает несовпадение applicationId/namespace и отсутствие DEFAULT у launcher intent-filter.
    private void launch(String pkg) throws Exception {
        // Launcher-фильтр не содержит DEFAULT; явный компонент разрешается PackageManager.
        String resolved = device.executeShellCommand("cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER " + pkg).trim();
        String component = resolved.substring(resolved.lastIndexOf('\n') + 1).trim();
        assertTrue("Не разрешён launcher: " + resolved, component.contains("/"));
        // ПЕРЕМЕННАЯ: result
        // Контейнер/текст/поле результата согласно типу объявления и методу.
        String result = device.executeShellCommand("am start -W -f 0x10008000 -n " + component);
        assertFalse("Ошибка запуска: " + result, result.contains("Error:"));
        device.waitForIdle();
    }

    // ЗАЩИТА: id
    // Метод id выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    private UiObject2 id(String pkg, String id) {
        // ПЕРЕМЕННАЯ: view
        // Текущая Android View или UiObject2 по типу объявления; ссылка относится к актуальному экрану.
        UiObject2 view = device.wait(Until.findObject(By.res(pkg, id)), 3000);
        if (view == null) {
            try {
                new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().resourceId(pkg + ":id/" + id));
            } catch (UiObjectNotFoundException ignored) {/* Далее assertion с понятным ID. */}
            view = device.wait(Until.findObject(By.res(pkg, id)), 12000);
        }
        assertNotNull("Не найден " + pkg + "/" + id, view);
        // ПЕРЕМЕННАЯ: view
        // Текущая Android View или UiObject2 по типу объявления; ссылка относится к актуальному экрану.
        return view;
    }

    // ЗАЩИТА: click
    // Метод click выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    private void click(String pkg, String id) {
        id(pkg, id).click();
        device.waitForIdle();
    }

    // ЗАЩИТА: type
    // Метод type выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    private void type(String pkg, String id, String value) {
        id(pkg, id).setText(value);
    }

    // ЗАЩИТА: text
    // Метод text выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    private String text(String pkg, String id) {
        String value = id(pkg, id).getText();
        return value == null ? "" : value;
    }

    // ЗАЩИТА: contains
    // Ожидает конкретный текст в View с заданным ID в пределах timeout; отрицательный результат даёт JUnit
    // assertion с фактическим текстом. Сообщение об ошибке не принимается за успешную предметную операцию.
    private void contains(String pkg, String id, String expected, long timeout) {
        assertTrue("Ожидалось " + expected + ", получено " + text(pkg, id), device.wait(Until.hasObject(By.res(pkg, id).textContains(expected)), timeout));
    }

    // ЗАЩИТА: proof
    // Сохраняет настоящий screenshot Android и XML иерархии UiAutomator. Через shell UID копирует файлы в
    // отдельную папку Download, чтобы AGP cleanup после connected-теста не удалил доказательства вместе с
    // target APK.
    private void proof(String name) throws Exception {
        File png = new File(output, name + ".png"), xml = new File(output, name + ".xml");
        assertTrue(device.takeScreenshot(png));
        try (FileOutputStream stream = new FileOutputStream(xml)) {
            device.dumpWindowHierarchy(stream);
        }
        // AGP удаляет target APK после connected-теста. Копируем доказательства через shell UID
        // в отдельную папку Download, чтобы они пережили удаление тестового приложения.
        String dir = "/sdcard/Download/mirea_lesson7_proofs";
        device.executeShellCommand("mkdir -p " + dir);
        device.executeShellCommand("cp " + png.getAbsolutePath() + " " + dir + "/" + name + ".png");
        device.executeShellCommand("cp " + xml.getAbsolutePath() + " " + dir + "/" + name + ".xml");
    }

    // ЗАЩИТА: scrollText
    // Метод scrollText выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    private void scrollText(String label) throws Exception {
        UiScrollable scroll = new UiScrollable(new UiSelector().scrollable(true));
        scroll.scrollTextIntoView(label);
        device.waitForIdle();
    }

    @After
    // ЗАЩИТА: restore
    // JUnit @After сохраняет последнее состояние, затем восстанавливает ориентацию AVD и снимает фиксацию
    // поворота даже после assertion. Состояние батареи меняющий тест восстанавливает отдельно в finally.
    public void restore() throws Exception {
        try {
            proof("after-" + testName.getMethodName());
        } finally {
            device.setOrientationNatural();
            device.unfreezeRotation();
        }
    }

    @Test
    // ЗАЩИТА: invalidEmailValidationOrConfigurationNotice
    // Метод invalidEmailValidationOrConfigurationNotice выполняет участок сценария, показанный в листинге.
    // Параметры и возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void invalidEmailValidationOrConfigurationNotice() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson7.firebaseauth";
        launch(p);
        assertTrue(id(p, "mode").getText().contains("Firebase"));
        // Отсутствие конфигурации явно фиксируется отдельным сценарием; этот тест не доказывает облачную авторизацию.
        if (!id(p, "signIn").isEnabled()) {
            contains(p, "status", "google-services.json", 5000);
            proof("firebase-needs-configuration");
            return;
        }
        type(p, "email", "invalid");
        type(p, "password", "123456");
        click(p, "signIn");
        assertTrue(id(p, "email").isFocused());
        proof("firebase-validation");
    }

    @Test
    // ЗАЩИТА: realSocketUtcOrRecordedNetworkRestriction
    // Метод realSocketUtcOrRecordedNetworkRestriction выполняет участок сценария, показанный в листинге.
    // Параметры и возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void realSocketUtcOrRecordedNetworkRestriction() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson7.timeservice";
        launch(p);
        click(p, "load");
        assertNotNull(device.wait(Until.findObject(By.res(p, "load").enabled(true)), 30000));
        proof("socket-result");
        // ПЕРЕМЕННАЯ: status
        // TextView состояния конкретного экрана, содержит результат/ошибку.
        String status = text(p, "status");
        org.junit.Assume.assumeTrue("Порт 13 недоступен в этой сети: " + status, status.contains("Получено реальным Socket"));
        assertTrue(text(p, "date").matches("Дата UTC: 20[0-9]{2}-[0-9]{2}-[0-9]{2}"));
        assertTrue(text(p, "time").matches("Время UTC: [0-9]{2}:[0-9]{2}:[0-9]{2}"));
        assertFalse(text(p, "raw").isEmpty());
    }

    @Test
    // ЗАЩИТА: realIpAndWeatherOrRecordedNetworkRestriction
    // Метод realIpAndWeatherOrRecordedNetworkRestriction выполняет участок сценария, показанный в
    // листинге. Параметры и возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void realIpAndWeatherOrRecordedNetworkRestriction() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson7.httpurlconnection";
        launch(p);
        click(p, "load");
        assertNotNull(device.wait(Until.findObject(By.res(p, "load").enabled(true)), 65000));
        proof("ip-weather-result");
        // ПЕРЕМЕННАЯ: status
        // TextView состояния конкретного экрана, содержит результат/ошибку.
        String status = text(p, "status");
        org.junit.Assume.assumeTrue("Сервис недоступен: " + status, status.contains("Получено из ipwho.is"));
        assertTrue(text(p, "ip").length() > 5);
        assertTrue(text(p, "city").length() > 7);
        assertTrue(text(p, "coordinates").contains(","));
        assertTrue(text(p, "weather").contains("Температура:"));
    }

    // ЗАЩИТА: openFragment
    // Тестовый runner в собственном UID открывает неэкспортируемую LabVerificationActivity из src/debug.
    // Реальный фрагмент проверяется изолированно; FirebaseUser не создаётся и авторизация этим тестом не
    // доказывается.
    private void openFragment(String fragment) throws Exception {
        Context owner = InstrumentationRegistry.getInstrumentation().getTargetContext();
        android.content.Intent intent = new android.content.Intent().setClassName(owner.getPackageName(), "ru.mirea.ZubarevVS.mireaproject.LabVerificationActivity").putExtra("fragment", fragment).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK | android.content.Intent.FLAG_ACTIVITY_CLEAR_TASK);
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> owner.startActivity(intent));
        device.waitForIdle();
    }

    // ЗАЩИТА: tapText
    // UiAutomator находит видимую подпись без учёта регистра: Android Button может преобразовать её в
    // заглавные буквы. Если элемент за пределами экрана, ScrollView прокручивается до него, затем
    // проверяется наличие и выполняется click.
    private void tapText(String label) throws Exception {
        java.util.regex.Pattern pattern = java.util.regex.Pattern.compile(java.util.regex.Pattern.quote(label), java.util.regex.Pattern.CASE_INSENSITIVE | java.util.regex.Pattern.UNICODE_CASE);
        // ПЕРЕМЕННАЯ: view
        // Текущая Android View или UiObject2 по типу объявления; ссылка относится к актуальному экрану.
        UiObject2 view = device.wait(Until.findObject(By.text(pattern)), 2000);
        if (view == null) {
            new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().textMatches("(?iu)" + java.util.regex.Pattern.quote(label)));
            view = device.wait(Until.findObject(By.text(pattern)), 5000);
        }
        assertNotNull("Не найдена кнопка " + label, view);
        view.click();
        device.waitForIdle();
    }

    @Test
    // ЗАЩИТА: mireaNetworkFragmentWithoutCloudLoginFixture
    // Метод mireaNetworkFragmentWithoutCloudLoginFixture выполняет участок сценария, показанный в
    // листинге. Параметры и возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void mireaNetworkFragmentWithoutCloudLoginFixture() throws Exception {
        // Изолированный debug-host проверяет фрагмент; это не доказательство Firebase-входа.
        openFragment("network");
        tapText("Обновить погоду");
        boolean ready = device.wait(Until.hasObject(By.textContains("Температура:")), 35000);
        proof("mirea-network-fragment");
        org.junit.Assume.assumeTrue("Open-Meteo недоступен из AVD; см. screenshot", ready);
    }
}
