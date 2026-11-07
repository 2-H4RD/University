package ru.mirea.ZubarevVS.lesson6.employeedb;


import androidx.room.*;
import androidx.annotation.NonNull;
import androidx.room.migration.Migration;
import androidx.sqlite.db.SupportSQLiteDatabase;

@Database(entities = {Hero.class}, version = 2, exportSchema = false)
public abstract class AppDatabase extends RoomDatabase {
    /**
     * Однократный сброс по просьбе пользователя при переходе с версии 1 на 2.
     * Room выполняет миграцию при первом открытии прежней базы новой версией приложения.
     * После этого герои с ручными ID сохраняются между обычными запусками.
     */
    public static final Migration RESET_1_2 = new Migration(1, 2) {
        @Override
        public void migrate(@NonNull SupportSQLiteDatabase db) {
            db.execSQL("DROP TABLE IF EXISTS `heroes`");
            db.execSQL("CREATE TABLE `heroes` (`id` INTEGER NOT NULL, "
                    + "`name` TEXT, `power` TEXT, PRIMARY KEY(`id`))");
        }
    };

    public abstract HeroDao heroDao();
}
