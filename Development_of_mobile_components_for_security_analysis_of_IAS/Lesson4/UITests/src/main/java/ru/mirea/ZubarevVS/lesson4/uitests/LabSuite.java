package ru.mirea.ZubarevVS.lesson4.uitests;

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
        // Test context принадлежит тестовому APK и может не иметь external files.
        // Runner работает с UID целевого приложения, поэтому используем target context.
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
        String dir = "/sdcard/Download/mirea_lesson4_proofs";
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

    // ЗАЩИТА: restore
    // JUnit @After сохраняет последнее состояние, затем восстанавливает ориентацию AVD и снимает фиксацию
    // поворота даже после assertion. Состояние батареи меняющий тест восстанавливает отдельно в finally.
    @After
    public void restore() throws Exception {
        try {
            proof("after-" + testName.getMethodName());
        } finally {
            device.setOrientationNatural();
            device.unfreezeRotation();
        }
    }

    @Test
    // ЗАЩИТА: threadValidationAndAverage
    // Метод threadValidationAndAverage выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void threadValidationAndAverage() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.thread";
        launch(p);
        assertEquals("Лучше звоните Солу", text(p, "movie"));
        click(p, "rename");
        contains(p, "threadInfo", "фильм: Лучше звоните Солу", 5000);
        proof("thread-personal-series");
        type(p, "total", "60");
        type(p, "days", "20");
        click(p, "calculate");
        contains(p, "result", "3", 10000);
        proof("thread-average");
        type(p, "days", "0");
        click(p, "calculate");
        contains(p, "result", "число дней > 0", 5000);
    }

    @Test
    // ЗАЩИТА: uiRunnableOrder
    // Метод uiRunnableOrder выполняет участок сценария, показанный в листинге. Параметры и возвращаемый
    // тип определяются его сигнатурой; View изменяется только в UI.
    public void uiRunnableOrder() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.data_thread";
        launch(p);
        click(p, "start");
        contains(p, "result", "runn3", 12000);
        String log = text(p, "result");
        assertTrue(log.indexOf("runn1") < log.indexOf("runn2"));
        assertTrue(log.indexOf("runn2") < log.indexOf("runn3"));
        proof("runnable-order");
    }

    @Test
    // ЗАЩИТА: looperMessage
    // Метод looperMessage выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    public void looperMessage() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.looper";
        launch(p);
        type(p, "age", "1");
        type(p, "job", "Analyst");
        click(p, "send");
        contains(p, "result", "работа: Analyst", 8000);
        proof("looper-message");
    }

    @Test
    // ЗАЩИТА: loaderRoundTrip
    // Метод loaderRoundTrip выполняет участок сценария, показанный в листинге. Параметры и возвращаемый
    // тип определяются его сигнатурой; View изменяется только в UI.
    public void loaderRoundTrip() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.cryptoloader";
        launch(p);
        type(p, "phrase", "Mirea AES test 2026");
        click(p, "encrypt");
        contains(p, "result", "Mirea AES test 2026", 10000);
        assertNotEquals("Mirea AES test 2026", text(p, "cipher"));
        proof("aes-loader");
    }

    @Test
    // ЗАЩИТА: workerDigest
    // Метод workerDigest выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    public void workerDigest() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.workmanager";
        launch(p);
        type(p, "text", "abc");
        click(p, "start");
        contains(p, "result", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", 30000);
        proof("worker-sha256");
    }

    // ЗАЩИТА: playerPortraitLandscape
    // Метод playerPortraitLandscape выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    @Test
    public void playerPortraitLandscape() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.main";
        launch(p);
        click(p, "play");
        contains(p, "status", "Воспроизводится", 5000);
        click(p, "play");
        contains(p, "status", "Пауза", 5000);
        device.setOrientationLeft();
        SystemClock.sleep(1000);
        assertNotNull(id(p, "play"));
        click(p, "stop");
        contains(p, "status", "Остановлено", 5000);
        proof("player-landscape");
    }

    // ЗАЩИТА: serviceSurvivesHomeAndStops
    // Метод serviceSurvivesHomeAndStops выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    @Test
    public void serviceSurvivesHomeAndStops() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.serviceapp";
        device.executeShellCommand("pm grant " + p + " android.permission.POST_NOTIFICATIONS");
        launch(p);
        click(p, "play");
        contains(p, "status", "Сервис воспроизводит", 5000);
        device.pressHome();
        SystemClock.sleep(1200);
        String running = device.executeShellCommand("dumpsys activity services " + p);
        assertTrue(running.contains("PlayerService"));
        assertTrue(running.contains("isForeground=true"));
        device.openNotification();
        assertTrue(device.wait(Until.hasObject(By.text("Сигнал безопасного канала")), 5000));
        proof("service-notification-home");
        device.pressBack();
        launch(p);
        click(p, "stop");
        SystemClock.sleep(500);
        assertFalse(device.executeShellCommand("dumpsys activity services " + p).contains("isForeground=true"));
    }

    // ЗАЩИТА: workerChargingConstraintAndCancel
    // Метод workerChargingConstraintAndCancel выполняет участок сценария, показанный в листинге. Параметры
    // и возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    @Test
    public void workerChargingConstraintAndCancel() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson4.workmanager";
        try {
            device.executeShellCommand("dumpsys battery unplug");
            launch(p);
            type(p, "text", "constrained work");
            click(p, "charging");
            click(p, "start");
            contains(p, "result", "ENQUEUED", 10000);
            SystemClock.sleep(1800);
            assertTrue(text(p, "result").contains("ENQUEUED"));
            proof("worker-waits-charging");
            click(p, "cancel");
            contains(p, "result", "CANCELLED", 10000);
        } finally {
            device.executeShellCommand("dumpsys battery reset");
        }
    }

    // ЗАЩИТА: mireaBackgroundDigest
    // Метод mireaBackgroundDigest выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    @Test
    public void mireaBackgroundDigest() throws Exception {
        String p = "ru.mirea.ZubarevVS.mireaproject.lesson4";
        launch(p);
        UiObject2 drawer = device.wait(Until.findObject(By.descContains("navigation drawer")), 5000);
        if (drawer == null) drawer = device.findObject(By.desc("Открыть меню"));
        assertNotNull("Кнопка меню", drawer);
        drawer.click();
        device.waitForIdle();
        UiObject2 dest = device.wait(Until.findObject(By.text("Фоновая задача")), 5000);
        if (dest == null) {
            scrollText("Фоновая задача");
            dest = device.findObject(By.text("Фоновая задача"));
        }
        assertNotNull(dest);
        dest.click();
        UiObject2 input = device.wait(Until.findObject(By.desc("auditText")), 5000);
        assertNotNull(input);
        input.setText("abc");
        // Стандартный Android Button преобразует подпись в верхний регистр.
        UiObject2 start = device.wait(Until.findObject(By.text(java.util.regex.Pattern.compile("(?iu)Запустить Worker"))), 5000);
        assertNotNull(start);
        start.click();
        assertTrue(device.wait(Until.hasObject(By.textContains("ba7816bf8f01cfea")), 20000));
        proof("mirea-background");
    }
}
