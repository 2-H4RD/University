package ru.mirea.ZubarevVS.lesson6.uitests;

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
        String dir = "/sdcard/Download/mirea_lesson6_proofs";
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
    // ЗАЩИТА: preferencesPersistAcrossProcess
    // Метод preferencesPersistAcrossProcess выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void preferencesPersistAcrossProcess() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson6.main";
        launch(p);
        assertEquals("Лучше звоните Солу", text(p, "movie"));
        type(p, "group", "BISO-02-22");
        type(p, "number", "5");
        type(p, "movie", "Лучше звоните Солу");
        click(p, "save");
        contains(p, "status", "сохранены", 10000);
        device.executeShellCommand("am force-stop " + p);
        launch(p);
        assertEquals("Лучше звоните Солу", text(p, "movie"));
        assertEquals("5", text(p, "number"));
        proof("preferences-restored");
    }

    @Test
    // ЗАЩИТА: internalFileRoundTrip
    // Метод internalFileRoundTrip выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void internalFileRoundTrip() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson6.internalfilestorage";
        launch(p);
        click(p, "save");
        contains(p, "status", "Записано", 10000);
        type(p, "event", "changed");
        click(p, "load");
        contains(p, "event", "1961", 10000);
        proof("internal-file-restored");
    }

    @Test
    // ЗАЩИТА: roomCrud
    // Метод roomCrud выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    public void roomCrud() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson6.employeedb";
        launch(p);
        type(p, "heroId", String.valueOf(System.currentTimeMillis()));
        type(p, "heroName", "Test Hero");
        type(p, "power", "Hash vision");
        click(p, "add");
        contains(p, "result", "Test Hero", 10000);
        String id = text(p, "heroId");
        assertFalse(id.isEmpty());
        type(p, "heroName", "Updated Hero");
        click(p, "update");
        contains(p, "result", "Updated Hero", 10000);
        device.executeShellCommand("am force-stop " + p);
        launch(p);
        type(p, "heroId", id);
        click(p, "find");
        contains(p, "heroName", "Updated Hero", 10000);
        proof("room-updated");
        click(p, "delete");
        SystemClock.sleep(1000);
        assertFalse(text(p, "result").contains("Updated Hero"));
    }

    @Test
    // ЗАЩИТА: notebookDocumentsOverwriteAndTwoFiles
    // Метод notebookDocumentsOverwriteAndTwoFiles выполняет участок сценария, показанный в листинге.
    // Параметры и возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void notebookDocumentsOverwriteAndTwoFiles() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson6.notebook";
        launch(p);
        click(p, "directory");
        UiObject2 select = device.wait(Until.findObject(By.text(java.util.regex.Pattern.compile("(?i)use this folder|использовать эту папку"))), 10000);
        assertNotNull("Выбор Documents", select);
        select.click();
        UiObject2 allow = device.wait(Until.findObject(By.text(java.util.regex.Pattern.compile("(?i)allow|разрешить"))), 5000);
        if (allow != null) allow.click();
        contains(p, "status", "Documents", 10000);
        type(p, "filename", "quote_one.txt");
        type(p, "quote", "Знание — сила. Фрэнсис Бэкон. Длинный хвост для проверки перезаписи.");
        click(p, "save");
        contains(p, "status", "Сохранено", 10000);
        type(p, "quote", "Знание — сила. Фрэнсис Бэкон.");
        click(p, "save");
        contains(p, "status", "Сохранено", 10000);
        type(p, "quote", "wrong");
        click(p, "load");
        contains(p, "status", "Загружено", 10000);
        assertEquals("Знание — сила. Фрэнсис Бэкон.", text(p, "quote"));
        proof("notebook-overwrite");
        type(p, "filename", "quote_two.txt");
        type(p, "quote", "Я мыслю, следовательно, я существую. Рене Декарт.");
        click(p, "save");
        contains(p, "status", "Сохранено", 10000);
        device.executeShellCommand("am force-stop " + p);
        launch(p);
        type(p, "filename", "quote_two.txt");
        click(p, "load");
        contains(p, "quote", "Декарт", 10000);
        proof("notebook-persisted-tree");
    }

    @Test
    // ЗАЩИТА: securePreferencesFixtureRoundTrip
    // Метод securePreferencesFixtureRoundTrip выполняет участок сценария, показанный в листинге. Параметры
    // и возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void securePreferencesFixtureRoundTrip() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson6.securesharedpreferences";
        launch(p);
        contains(p, "status", "AndroidKeyStore готов", 15000);
        assertEquals("Пушкин Александр Сергеевич", text(p, "poet"));
        assertNotNull(id(p, "photo"));
        proof("pushkin-default-portrait");
        type(p, "poet", "Пушкин Александр Сергеевич");
        type(p, "actor", "Константин Хабенский (учебный пример)");
        click(p, "pick");
        // DocumentsUI в сетке отдаёт имя файла в contentDescription, а не в text.
        UiObject2 fixture = device.wait(Until.findObject(By.descStartsWith("pushkin_portrait.jpg,")), 10000);
        assertNotNull("Присланный портрет Пушкина должен быть подготовлен в Downloads/Recent", fixture);
        fixture.click();
        click(p, "save");
        contains(p, "status", "сохранены зашифрованно", 15000);
        device.executeShellCommand("am force-stop " + p);
        launch(p);
        contains(p, "status", "AndroidKeyStore готов", 15000);
        assertEquals("Пушкин Александр Сергеевич", text(p, "poet"));
        proof("secure-preferences-restored");
        String xml = device.executeShellCommand("run-as " + p + " cat shared_prefs/secret_shared_prefs.xml");
        assertTrue(xml.contains("<?xml"));
        assertFalse(xml.contains("Пушкин Александр Сергеевич"));
        assertFalse(xml.contains("Константин Хабенский"));
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
    // ЗАЩИТА: mireaProfileAndFileDialog
    // Метод mireaProfileAndFileDialog выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void mireaProfileAndFileDialog() throws Exception {
        openFragment("profile");
        UiObject2 role = device.wait(Until.findObject(By.desc("profileRole")), 5000);
        assertNotNull(role);
        role.setText("Security analyst fixture");
        tapText("Сохранить профиль");
        assertTrue(device.wait(Until.hasObject(By.text("Профиль сохранён")), 5000));
        openFragment("profile");
        // После пересоздания Activity прежний accessibility-узел может быть уже уничтожен.
        // Until ищет актуальный узел и проверяет точное значение, не удерживая устаревший UiObject2.
        assertTrue(device.wait(Until.hasObject(By.desc("profileRole").text("Security analyst fixture")), 5000));
        proof("mirea-profile-restored");
        openFragment("files");
        // ПЕРЕМЕННАЯ: fab
        // FloatingActionButton, открывающая диалог новой записи.
        UiObject2 fab = device.wait(Until.findObject(By.desc("Создать запись")), 5000);
        assertNotNull(fab);
        fab.click();
        device.wait(Until.findObject(By.desc("noteName")), 5000).setText("audit_fixture");
        device.findObject(By.desc("noteText")).setText("abc");
        tapText("Сохранить");
        assertTrue(device.wait(Until.hasObject(By.textContains("audit_fixture")), 10000));
        proof("mirea-file-fab");
        Context owner = InstrumentationRegistry.getInstrumentation().getTargetContext();
        // ПЕРЕМЕННАЯ: file
        // Файл текущей операции; путь создаётся в разрешённом каталоге приложения или через SAF.
        String file = device.executeShellCommand("run-as " + owner.getPackageName() + " cat files/file_lab/audit_fixture.txt");
        assertTrue(file.contains("YWJj"));
        assertTrue(file.contains("ba7816bf8f01cfea"));
    }
}
