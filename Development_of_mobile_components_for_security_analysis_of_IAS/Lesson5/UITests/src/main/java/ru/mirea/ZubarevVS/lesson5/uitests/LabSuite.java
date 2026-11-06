package ru.mirea.ZubarevVS.lesson5.uitests;

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
        // Датчики/карта меняются непрерывно; результат ждут явные Until/assertion, а не 10 секунд UI idle.
        Configurator.getInstance().setWaitForIdleTimeout(1000);
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
                new UiScrollable(new UiSelector().scrollable(true).packageName(pkg)).scrollIntoView(new UiSelector().resourceId(pkg + ":id/" + id));
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
        String dir = "/sdcard/Download/mirea_lesson5_proofs";
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
    // ЗАЩИТА: sensorListAndAccelerometer
    // Метод sensorListAndAccelerometer выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void sensorListAndAccelerometer() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson5.main";
        launch(p);
        contains(p, "summary", "Доступно датчиков:", 5000);
        assertTrue(id(p, "sensorList").getChildCount() > 0);
        proof("sensor-list");
        p = "ru.mirea.ZubarevVS.lesson5.accelerometer";
        launch(p);
        contains(p, "status", "обновлены", 15000);
        assertTrue(text(p, "x").contains("м/с²"));
        assertTrue(text(p, "y").contains("м/с²"));
        assertTrue(text(p, "z").contains("м/с²"));
        proof("accelerometer-values");
    }

    @Test
    // ЗАЩИТА: audioRecordAndPlayback
    // Метод audioRecordAndPlayback выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void audioRecordAndPlayback() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson5.audiorecord";
        device.executeShellCommand("pm grant " + p + " android.permission.RECORD_AUDIO");
        launch(p);
        click(p, "record");
        SystemClock.sleep(2200);
        assertFalse(id(p, "play").isEnabled());
        click(p, "record");
        contains(p, "status", "Запись сохранена:", 10000);
        click(p, "play");
        contains(p, "status", "Воспроизведение", 5000);
        proof("audio-record-play");
    }

    @Test
    // ЗАЩИТА: cameraFullImageAndCancel
    // Метод cameraFullImageAndCancel выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void cameraFullImageAndCancel() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson5.camera";
        device.executeShellCommand("pm grant " + p + " android.permission.CAMERA");
        launch(p);
        click(p, "take");
        SystemClock.sleep(2000);
        UiObject2 first = device.findObject(By.text("Got it"));
        if (first != null) {
            first.click();
            SystemClock.sleep(500);
        }
        UiObject2 shutter = device.wait(Until.findObject(By.res("com.android.camera2", "shutter_button")), 10000);
        if (shutter == null) shutter = device.findObject(By.descContains("Shutter"));
        if (shutter != null) shutter.click();
        else device.pressKeyCode(android.view.KeyEvent.KEYCODE_CAMERA);
        SystemClock.sleep(1500);
        UiObject2 done = device.wait(Until.findObject(By.res("com.android.camera2", "done_button")), 5000);
        if (done == null) done = device.findObject(By.desc("Done"));
        if (done != null) done.click();
        contains(p, "status", "Фото:", 15000);
        // ПЕРЕМЕННАЯ: status
        // TextView состояния конкретного экрана, содержит результат/ошибку.
        String status = text(p, "status");
        assertTrue("Оригинал с размерами", status.matches("(?s).*Фото: [1-9][0-9]{2,}×[1-9][0-9]{2,}.*"));
        proof("camera-full-photo");
        device.setOrientationLeft();
        SystemClock.sleep(1500);
        device.waitForIdle();
        proof("camera-landscape");
        device.setOrientationNatural();
        SystemClock.sleep(1500);
        device.waitForIdle();
        contains(p, "status", "Фото:", 5000);
        click(p, "take");
        SystemClock.sleep(1200);
        device.pressBack();
        contains(p, "status", "Съёмка отменена", 10000);
        proof("camera-cancel-preserves-photo");
    }

    // ЗАЩИТА: hardwareScreen
    // Метод hardwareScreen выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    private void hardwareScreen(String pkg) throws Exception {
        launch(pkg);
        UiObject2 menu = device.wait(Until.findObject(By.desc("Open navigation drawer")), 5000);
        assertNotNull(menu);
        menu.click();
        UiObject2 item = device.wait(Until.findObject(By.text("Аппаратная часть")), 5000);
        assertNotNull(item);
        item.click();
        device.waitForIdle();
        assertTrue(device.wait(Until.hasObject(By.textContains("Наклон:")), 10000));
    }

    // ЗАЩИТА: hardwareButton
    // Метод hardwareButton выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    private void hardwareButton(String label) throws Exception {
        UiObject2 button = device.wait(Until.findObject(By.text(java.util.regex.Pattern.compile("(?iu)" + java.util.regex.Pattern.quote(label)))), 5000);
        assertNotNull(button);
        button.click();
        device.waitForIdle();
    }

    @Test
    // ЗАЩИТА: mireaIncidentVoiceAndPhoto
    // Метод mireaIncidentVoiceAndPhoto выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void mireaIncidentVoiceAndPhoto() throws Exception {
        String p = "ru.mirea.ZubarevVS.mireaproject.lesson5";
        device.executeShellCommand("pm grant " + p + " android.permission.RECORD_AUDIO");
        device.executeShellCommand("pm grant " + p + " android.permission.CAMERA");
        hardwareScreen(p);
        proof("mirea-phone-level");
        hardwareButton("Голосовая заметка");
        click(p, "record");
        SystemClock.sleep(2200);
        click(p, "record");
        contains(p, "status", "Запись сохранена", 10000);
        type(p, "caption", "Incident voice fixture");
        click(p, "saveNote");
        contains(p, "status", "Описание голосовой заметки сохранено", 5000);
        proof("mirea-voice-caption");
        device.pressBack();
        hardwareButton("Фотофиксация инцидента");
        click(p, "take");
        UiObject2 shutter = device.wait(Until.findObject(By.res("com.android.camera2", "shutter_button")), 10000);
        assertNotNull(shutter);
        shutter.click();
        SystemClock.sleep(1000);
        UiObject2 done = device.wait(Until.findObject(By.res("com.android.camera2", "done_button")), 10000);
        assertNotNull(done);
        done.click();
        contains(p, "status", "Фото:", 10000);
        type(p, "caption", "Photo incident fixture");
        click(p, "saveNote");
        contains(p, "status", "Фото и описание инцидента сохранены", 10000);
        proof("mirea-photo-caption");
        device.pressBack();
        hardwareButton("Голосовая заметка");
        assertEquals("Incident voice fixture", text(p, "caption"));
        proof("mirea-voice-caption-restored");
    }
}
