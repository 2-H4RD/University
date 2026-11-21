package ru.mirea.ZubarevVS.lesson8.uitests;

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
        UiObject2 v = device.wait(Until.findObject(By.res(pkg, id)), 15000);
        assertNotNull("Не найден " + pkg + "/" + id, v);
        return v;
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
        String dir = "/sdcard/Download/mirea_lesson8_proofs";
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
        device.setOrientationNatural();
        device.unfreezeRotation();
    }

    @Test
    // ЗАЩИТА: osmMapControls
    // Метод osmMapControls выполняет участок сценария, показанный в листинге. Параметры и возвращаемый тип
    // определяются его сигнатурой; View изменяется только в UI.
    public void osmMapControls() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson8.osmmaps";
        launch(p);
        assertNotNull(id(p, "mapHost"));
        contains(p, "status", "OpenStreetMap", 5000);
        assertTrue(id(p, "locate").isEnabled());
        proof("osm-initial");
    }

    @Test
    public void osmSelectsBothRoutePoints() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson8.osmmaps";
        launch(p);

        click(p, "selectStart");
        contains(p, "status", "точку старта A", 5000);
        holdMapPoint(p, 0.44, 0.58);
        contains(p, "status", "A: 55.", 5000);
        contains(p, "status", "B: Парк Горького", 5000);

        click(p, "selectEnd");
        contains(p, "status", "точку финиша B", 5000);
        holdMapPoint(p, 0.64, 0.44);
        contains(p, "status", "B: 55.", 5000);
        String selections = text(p, "status");
        assertTrue(selections.matches("(?s)A: [0-9.]+, [0-9.]+\\s+B: [0-9.]+, [0-9.]+.*"));
        String[] lines = selections.split("\\n");
        assertNotEquals(lines[0].substring(3), lines[1].substring(3));
        proof("osm-manual-route-points");

        device.setOrientationLeft();
        contains(p, "status", selections, 10000);
        device.setOrientationNatural();
        contains(p, "status", selections, 10000);

        click(p, "route");
        assertNotNull(device.wait(Until.findObject(By.res(p, "route").enabled(true)), 65000));
        String routeResult = text(p, "status");
        proof("osm-manual-route-result");
        org.junit.Assume.assumeTrue("Сервис OSRM недоступен: " + routeResult, !routeResult.startsWith("Ошибка OSRM"));
        assertTrue("Маршрут между вручную выбранными точками: " + routeResult,
                routeResult.matches("(?s).*Маршрутов OSRM: [1-9][0-9]*.*"));
    }

    // UiAutomator отправляет долгое нажатие внутрь области карты, которую видно на экране.
    private void holdMapPoint(String pkg, double xRatio, double yRatio) {
        android.graphics.Rect bounds = id(pkg, "mapHost").getVisibleBounds();
        int x = bounds.left + (int) (bounds.width() * xRatio);
        int y = bounds.top + (int) (bounds.height() * yRatio);
        assertTrue(device.swipe(x, y, x, y, 150));
        device.waitForIdle();
    }

    @Test
    // ЗАЩИТА: mapkitConfigurationVisible
    // Метод mapkitConfigurationVisible выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void mapkitConfigurationVisible() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson8.yandexmaps";
        launch(p);
        assertNotNull(id(p, "mapHost"));
        if (!id(p, "locate").isEnabled()) {
            contains(p, "status", "Нужен ключ", 5000);
            proof("mapkit-needs-key");
        }
        p = "ru.mirea.ZubarevVS.lesson8.yandexdriver";
        launch(p);
        assertNotNull(id(p, "mapHost"));
        if (!id(p, "locate").isEnabled()) {
            contains(p, "status", "Нужен ключ", 5000);
            assertFalse(id(p, "route").isEnabled());
            proof("yandex-driver-needs-key");
        }
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
        // Карта обновляет accessibility-дерево во время анимации прокрутки.
        // Повторно находим ту же кнопку при смене экземпляра узла, сохраняя все предметные assertions.
        boolean clicked = false;
        for (int attempt = 0; attempt < 3 && !clicked; attempt++) {
            try {
                UiObject2 fresh = device.wait(Until.findObject(By.text(pattern)), 5000);
                assertNotNull("Кнопка исчезла: " + label, fresh);
                fresh.click();
                clicked = true;
            } catch (androidx.test.uiautomator.StaleObjectException transientNode) {
                SystemClock.sleep(300);
            }
        }
        assertTrue("Не удалось нажать " + label, clicked);
        device.waitForIdle();
    }

    @Test
    // ЗАЩИТА: mireaPlacesListAndCustomPlace
    // Метод mireaPlacesListAndCustomPlace выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    public void mireaPlacesListAndCustomPlace() throws Exception {
        // Test-only host открывает реальный PlacesFragment без подмены Firebase-сессии.
        openFragment("places");
        tapText("На карте: РТУ МИРЭА");
        assertTrue(device.wait(Until.hasObject(By.textContains("Проспект Вернадского, 78")), 5000));
        proof("mirea-place-selected");
        tapText("Добавить своё заведение");
        for (String[] field : new String[][]{{"name", "QA place"}, {"address", "Test address"}, {"description", "Educational fixture"}, {"lat", "55.7"}, {"lon", "37.5"}}) {
            UiObject2 input = device.wait(Until.findObject(By.desc("place_" + field[0])), 5000);
            assertNotNull(input);
            input.setText(field[1]);
        }
        tapText("Добавить");
        assertTrue(device.wait(Until.hasObject(By.text("Заведение сохранено")), 10000));
        proof("mirea-custom-place");
        openFragment("places");
        tapText("На карте: QA place");
        // После прокрутки к кнопке сохранённого места строка статуса выше экрана.
        // Проверяем фактический результат после возврата к нему, а не только видимую область.
        new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().textContains("Educational fixture"));
        assertTrue(device.wait(Until.hasObject(By.textContains("Educational fixture")), 5000));
        proof("mirea-custom-restored");
    }

    // ЗАЩИТА: osmGpsAndRealRoadRoutes
    // Метод osmGpsAndRealRoadRoutes выполняет участок сценария, показанный в листинге. Параметры и
    // возвращаемый тип определяются его сигнатурой; View изменяется только в UI.
    @Test
    public void osmGpsAndRealRoadRoutes() throws Exception {
        String p = "ru.mirea.ZubarevVS.lesson8.osmmaps";
        device.executeShellCommand("pm grant " + p + " android.permission.ACCESS_COARSE_LOCATION");
        device.executeShellCommand("pm grant " + p + " android.permission.ACCESS_FINE_LOCATION");
        launch(p);
        click(p, "locate");
        for (int attempt = 0; attempt < 12; attempt++) {
            SystemClock.sleep(1500);
            click(p, "route");
            if (!text(p, "status").contains("Сначала получите")) break;
        }
        assertFalse("Не получен GPS AVD", text(p, "status").contains("Сначала получите"));
        assertNotNull(device.wait(Until.findObject(By.res(p, "route").enabled(true)), 65000));
        proof("osm-real-road-routes");
        // ПЕРЕМЕННАЯ: result
        // Контейнер/текст/поле результата согласно типу объявления и методу.
        String result = text(p, "status");
        org.junit.Assume.assumeTrue("Сервис OSRM недоступен: " + result, !result.startsWith("Ошибка OSRM"));
        assertTrue("Нужны реальные варианты от сервиса", result.matches("(?s).*Маршрутов OSRM: [1-9][0-9]*.*"));
    }
}
