package ru.mirea.ZubarevVS.lesson6.employeedb;


/**
 * Один экземпляр Room на процесс. Запросы выполняются в io, allowMainThreadQueries не используется.
 */
public class App extends android.app.Application {
    // ПЕРЕМЕННАЯ: database
    // Один экземпляр AppDatabase на процесс приложения.
    private AppDatabase database;

    @Override
    // ЗАЩИТА: onCreate
    // Application создаёт один AppDatabase через Room.databaseBuilder. Запросы DAO выполняются позже в io,
    // allowMainThreadQueries не включён.
    public void onCreate() {
        super.onCreate();
        database = androidx.room.Room.databaseBuilder(this, AppDatabase.class, "heroes.db")
                .addMigrations(AppDatabase.RESET_1_2)
                .build();
    }

    // ЗАЩИТА: database
    // Возвращает общий экземпляр AppDatabase из Application. Повторный Room.databaseBuilder для каждого
    // запроса не нужен.
    public AppDatabase database() {
        // ПЕРЕМЕННАЯ: database
        // Один экземпляр AppDatabase на процесс приложения.
        return database;
    }
}
