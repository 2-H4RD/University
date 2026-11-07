package ru.mirea.ZubarevVS.lesson6.employeedb;


import androidx.room.*;

/**
 * Entity описывает таблицу heroes. Положительный id вводит пользователь.
 * Первичный ключ обеспечивает уникальность ID, name/power содержат данные героя.
 */
@Entity(tableName = "heroes")
public class Hero {
    @PrimaryKey
    public long id;
    public String name;
    public String power;
}
