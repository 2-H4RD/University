package ru.mirea.ZubarevVS.lesson6.employeedb;


import androidx.room.*;

import java.util.List;

/**
 * Room проверяет SQL при компиляции и генерирует реализацию интерфейса.
 */
@Dao
public interface HeroDao {
    @Query("SELECT * FROM heroes ORDER BY id")
    List<Hero> getAll();

    @Query("SELECT * FROM heroes WHERE id=:id")
    Hero getById(long id);

    // Повторный ID не заменяет существующего героя. IGNORE возвращает -1 при конфликте.
    // Это защищает запись и при совпадении ID между проверкой getById и вставкой.
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    long insert(Hero hero);

    @Update
    int update(Hero hero);

    @Delete
    int delete(Hero hero);
}
