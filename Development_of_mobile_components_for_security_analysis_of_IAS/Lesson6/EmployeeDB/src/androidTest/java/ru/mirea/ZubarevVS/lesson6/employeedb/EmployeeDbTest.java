package ru.mirea.ZubarevVS.lesson6.employeedb;

import static org.junit.Assert.*;

import android.content.Context;
import android.database.Cursor;
import android.os.SystemClock;
import android.widget.EditText;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.room.Room;
import androidx.sqlite.db.SupportSQLiteDatabase;
import androidx.sqlite.db.SupportSQLiteOpenHelper;
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.concurrent.atomic.AtomicReference;

/** Реальные инструментальные проверки Room и обработчиков экрана на Android. */
@RunWith(AndroidJUnit4.class)
public class EmployeeDbTest {
    private static final String TEST_DB = "employee_reset_migration_test.db";

    @Test
    public void resetsVersionOneOnceAndPreservesManualIdsAfterReopen() {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        context.deleteDatabase(TEST_DB);
        try {
            // Создаём прежнюю схему 1 с AUTOINCREMENT и старой записью.
            SupportSQLiteOpenHelper.Configuration config =
                    SupportSQLiteOpenHelper.Configuration.builder(context).name(TEST_DB)
                            .callback(new SupportSQLiteOpenHelper.Callback(1) {
                                @Override
                                public void onCreate(@NonNull SupportSQLiteDatabase db) {
                                    db.execSQL("CREATE TABLE heroes (id INTEGER PRIMARY KEY "
                                            + "AUTOINCREMENT NOT NULL, name TEXT, power TEXT)");
                                    db.execSQL("INSERT INTO heroes VALUES (15, 'Old hero', 'Old power')");
                                }

                                @Override
                                public void onUpgrade(@NonNull SupportSQLiteDatabase db,
                                                      int oldVersion, int newVersion) {
                                    throw new AssertionError("Обновление выполняет Room");
                                }
                            }).build();
            try (SupportSQLiteOpenHelper old =
                         new FrameworkSQLiteOpenHelperFactory().create(config)) {
                old.getWritableDatabase();
            }

            AppDatabase migrated = Room.databaseBuilder(context, AppDatabase.class, TEST_DB)
                    .addMigrations(AppDatabase.RESET_1_2).build();
            try {
                assertTrue("Старая запись должна быть удалена при переходе 1 → 2",
                        migrated.heroDao().getAll().isEmpty());
                try (Cursor schema = migrated.getOpenHelper().getReadableDatabase().query(
                        "SELECT sql FROM sqlite_master WHERE type='table' AND name='heroes'")) {
                    assertTrue(schema.moveToFirst());
                    assertFalse(schema.getString(0).toUpperCase(java.util.Locale.ROOT)
                            .contains("AUTOINCREMENT"));
                }
                Hero hero = new Hero();
                hero.id = Long.MAX_VALUE;
                hero.name = "Manual hero";
                hero.power = "Manual power";
                assertEquals(Long.MAX_VALUE, migrated.heroDao().insert(hero));
                hero.name = "Rejected replacement";
                assertEquals(-1L, migrated.heroDao().insert(hero));
                assertEquals("Manual hero", migrated.heroDao().getById(Long.MAX_VALUE).name);
            } finally {
                migrated.close();
            }
            // При повторном открытии версии 2 миграция со сбросом больше не выполняется.
            AppDatabase reopened = Room.databaseBuilder(context, AppDatabase.class, TEST_DB)
                    .addMigrations(AppDatabase.RESET_1_2).build();
            try {
                assertEquals(1, reopened.heroDao().getAll().size());
                assertEquals("Manual hero", reopened.heroDao().getById(Long.MAX_VALUE).name);
                Hero lowerId = new Hero();
                lowerId.id = 1;
                lowerId.name = "Lower ID";
                lowerId.power = "Still valid after maximum ID";
                assertEquals(1L, reopened.heroDao().insert(lowerId));
            } finally {
                reopened.close();
            }
        } finally {
            context.deleteDatabase(TEST_DB);
        }
    }

    @Test
    public void validatesManualIdAndPerformsCrudWithoutReplacingDuplicates() {
        String id = String.valueOf(Long.MAX_VALUE);
        try (ActivityScenario<MainActivity> screen = ActivityScenario.launch(MainActivity.class)) {
            awaitResult(screen, "Всего героев:");
            inputAndClick(screen, "", "Test Hero", "Hash vision", R.id.add);
            awaitResult(screen, "Введите ID героя");
            inputAndClick(screen, "abc", "Test Hero", "Hash vision", R.id.add);
            awaitResult(screen, "ID должен быть целым числом");
            inputAndClick(screen, "1.5", "Test Hero", "Hash vision", R.id.add);
            awaitResult(screen, "ID должен быть целым числом");
            inputAndClick(screen, "9223372036854775808", "Test Hero", "Hash vision", R.id.add);
            awaitResult(screen, "ID должен быть целым числом");
            inputAndClick(screen, "0", "Test Hero", "Hash vision", R.id.add);
            awaitResult(screen, "ID должен быть больше нуля");
            inputAndClick(screen, "-3", "Test Hero", "Hash vision", R.id.add);
            awaitResult(screen, "ID должен быть больше нуля");

            inputAndClick(screen, id, "", "Hash vision", R.id.add);
            awaitResult(screen, "Введите имя и способность");
            inputAndClick(screen, id, "Test Hero", "Hash vision", R.id.add);
            awaitResult(screen, "Герой с ID " + id + " добавлен.");
            screen.onActivity(activity -> assertEquals(id,
                    ((EditText) activity.findViewById(R.id.heroId)).getText().toString()));

            inputAndClick(screen, id, "Replacement rejected", "Other power", R.id.add);
            awaitResult(screen, "уже существует");
            inputAndClick(screen, id, "", "", R.id.find);
            awaitResult(screen, "Герой с ID " + id + " найден.");
            screen.onActivity(activity -> assertEquals("Test Hero",
                    ((EditText) activity.findViewById(R.id.heroName)).getText().toString()));
            inputAndClick(screen, id, "Updated Hero", "Updated power", R.id.update);
            awaitResult(screen, "Герой с ID " + id + " изменён.");
        }
        // Закрываем Activity и открываем снова: данные сохраняются в той же версии БД.
        try (ActivityScenario<MainActivity> screen = ActivityScenario.launch(MainActivity.class)) {
            awaitResult(screen, "Updated Hero");
            inputAndClick(screen, id, "", "", R.id.find);
            awaitResult(screen, "Герой с ID " + id + " найден.");
            inputAndClick(screen, id, "", "", R.id.delete);
            awaitResult(screen, "Герой с ID " + id + " удалён.");
            inputAndClick(screen, id, "", "", R.id.find);
            awaitResult(screen, "Герой с ID " + id + " не найден.");
            // Пользователь может снова занять освобождённый ID.
            inputAndClick(screen, id, "Reused ID", "Hash vision", R.id.add);
            awaitResult(screen, "Герой с ID " + id + " добавлен.");
            inputAndClick(screen, id, "", "", R.id.delete);
            awaitResult(screen, "Герой с ID " + id + " удалён.");
        }
    }

    private void inputAndClick(ActivityScenario<MainActivity> screen, String id,
                               String name, String power, int button) {
        screen.onActivity(activity -> {
            ((EditText) activity.findViewById(R.id.heroId)).setText(id);
            ((EditText) activity.findViewById(R.id.heroName)).setText(name);
            ((EditText) activity.findViewById(R.id.power)).setText(power);
            activity.findViewById(button).performClick();
        });
    }

    private void awaitResult(ActivityScenario<MainActivity> screen, String expected) {
        AtomicReference<String> actual = new AtomicReference<>("");
        long deadline = SystemClock.uptimeMillis() + 10000;
        do {
            screen.onActivity(activity -> actual.set(
                    ((TextView) activity.findViewById(R.id.result)).getText().toString()));
            if (actual.get().contains(expected)) {
                return;
            }
            SystemClock.sleep(20);
        } while (SystemClock.uptimeMillis() < deadline);
        fail("Ожидалось: " + expected + "; получено: " + actual.get());
    }
}
