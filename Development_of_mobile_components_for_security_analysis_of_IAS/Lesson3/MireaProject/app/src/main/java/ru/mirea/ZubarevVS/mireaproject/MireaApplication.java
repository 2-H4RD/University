/*
 * ПОДРОБНЫЙ РАЗБОР ДЛЯ ЗАЩИТЫ: Navigation Drawer и браузер.
 * MireaApplication включает DynamicColors для Material You. ActivityMainBinding создаётся из
 * activity_main.xml; binding содержит типизированные ссылки на drawerLayout, navView, appBarMain и
 * toolbar. NavHostFragment содержит NavController, mobile_navigation.xml задаёт DataFragment и
 * WebViewFragment. ID nav_data/nav_web совпадают в меню, графе и AppBarConfiguration. NavigationUI
 * связывает эти элементы и управляет заголовком/гамбургером. DataFragment отображает карточки отрасли
 * в NestedScrollView. WebViewFragment управляет binding только пока есть View, сохраняет историю в
 * webState, проверяет HTTPS адреса, показывает реальный прогресс, обработку ошибок, Home/Reload/Back.
 * При открытой шторке Back закрывает её раньше истории WebView.
 * Связанные XML, переменные и сценарии разобраны в РАЗБОР_КОДА.md.
 */
package ru.mirea.ZubarevVS.mireaproject;

import android.app.Application;
import com.google.android.material.color.DynamicColors;
/** Material You: на Android 12+ используем палитру текущих обоев. */
public class MireaApplication extends Application {
    // РАЗБОР onCreate:
    // Android создаёт Application перед Activity. super.onCreate выполняет базовую инициализацию.
    // DynamicColors.applyToActivitiesIfAvailable(this) регистрирует применение системных динамических
    // цветов к Activity, если устройство поддерживает эту возможность. Здесь не создаётся разметка и не
    // загружается WebView.
    @Override public void onCreate() {
        super.onCreate();
        DynamicColors.applyToActivitiesIfAvailable(this); // На старых версиях остаются цвета из themes.xml.
    }
}
