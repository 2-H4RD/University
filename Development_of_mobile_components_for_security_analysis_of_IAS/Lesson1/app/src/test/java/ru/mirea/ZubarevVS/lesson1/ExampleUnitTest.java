/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Первое приложение.
 * JUnit4 запускает @Test на JVM компьютера. assertEquals сравнивает ожидаемое 4 и фактическое 2+2.
 * Тест не создаёт Activity, не использует эмулятор и не подтверждает практические сценарии: они
 * проверяются отдельно на APK.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.lesson1;
import org.junit.Test;
import static org.junit.Assert.assertEquals;
/**
 * Исходный пример JUnit4 из шаблона Android Studio.
 * Выполняется JVM компьютера при testDebugUnitTest, без эмулятора и без Activity.
 * Он проверяет только пример сложения, поэтому не доказывает работу кнопок/разметки:
 * практические действия дополнительно проверяются на настоящем APK в Pixel_9.
 */
public class ExampleUnitTest {
    // @Test сообщает JUnit, что метод нужно выполнить; static import даёт короткое имя assertEquals.
    @Test public void addition_isCorrect() {
        assertEquals(4, 2 + 2); // Первый аргумент — ожидаемое значение, второй — фактический результат.
    }
}
