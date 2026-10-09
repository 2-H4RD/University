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

import android.os.Bundle;
import android.content.Intent;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.EdgeToEdge;
import androidx.core.view.GravityCompat;
import androidx.activity.OnBackPressedCallback;
import androidx.navigation.NavController;
import androidx.navigation.fragment.NavHostFragment;
import androidx.navigation.ui.AppBarConfiguration;
import androidx.navigation.ui.NavigationUI;
import ru.mirea.ZubarevVS.mireaproject.databinding.ActivityMainBinding;
/** Структура Navigation Drawer Activity: Toolbar, DrawerLayout, NavHost и граф. */
public class MainActivity extends AppCompatActivity {
    private ActivityMainBinding binding;
    private NavController navController;
    private AppBarConfiguration appBarConfiguration;
    // РАЗБОР onCreate:
    // Android вызывает метод для нового экземпляра. savedInstanceState - Bundle предыдущего состояния или
    // null при первом создании. Сначала super, затем загрузка XML/Binding, затем поиск элементов и
    // регистрация действий. Это не функция, вызываемая кнопкой.
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        binding = ActivityMainBinding.inflate(getLayoutInflater()); // Имя Binding получено из activity_main.xml.
        setContentView(binding.getRoot());
        ScreenInsets.apply(binding.appBarMain.getRoot());
        View header = binding.navView.getHeaderView(0); // У шторки собственный header вне основного экрана.
        int headerLeft = header.getPaddingLeft();
        int headerTop = header.getPaddingTop();
        int headerRight = header.getPaddingRight();
        int headerBottom = header.getPaddingBottom();
        androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(binding.drawerLayout, (view, insets) -> {
            int statusTop = insets.getInsets(androidx.core.view.WindowInsetsCompat.Type.statusBars()).top;
            header.setPadding(headerLeft, headerTop + statusTop, headerRight, headerBottom); // Заголовок drawer ниже статус-бара.
            return insets;
        });
        androidx.core.view.ViewCompat.requestApplyInsets(binding.drawerLayout);
        setSupportActionBar(binding.appBarMain.toolbar); // Toolbar становится ActionBar.
        NavHostFragment host = (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host_fragment_content_main);
        navController = host.getNavController(); // Берём контроллер у NavHost, как рекомендовано в задании.
        appBarConfiguration = new AppBarConfiguration.Builder(R.id.nav_data, R.id.nav_web)
                .setOpenableLayout(binding.drawerLayout).build(); // Оба экрана — верхний уровень с «гамбургером».
        NavigationUI.setupActionBarWithNavController(this, navController, appBarConfiguration);
        NavigationUI.setupWithNavController(binding.navView, navController); // Одинаковые ID связывают меню и граф.
        OnBackPressedCallback drawerBack = new OnBackPressedCallback(false) {
            // РАЗБОР handleOnBackPressed:
            // Callback drawerBack включён только при открытой шторке. Он закрывает DrawerLayout через
            // GravityCompat.START; после onDrawerClosed отключается, чтобы Back снова обрабатывала навигация.
            @Override public void handleOnBackPressed() { binding.drawerLayout.closeDrawer(GravityCompat.START); }
        };
        getOnBackPressedDispatcher().addCallback(this, drawerBack);
        binding.drawerLayout.addDrawerListener(new androidx.drawerlayout.widget.DrawerLayout.SimpleDrawerListener() {
            // РАЗБОР onDrawerOpened:
            // Шторка открыта: включаем drawerBack, чтобы первый Back закрыл её.
            @Override public void onDrawerOpened(View drawerView) { drawerBack.setEnabled(true); }
            // РАЗБОР onDrawerClosed:
            // Шторка закрыта: отключаем drawerBack и возвращаем обработку Back навигации/браузеру.
            @Override public void onDrawerClosed(View drawerView) { drawerBack.setEnabled(false); }
        }); // Back сначала закрывает открытую шторку.
    }
    // РАЗБОР onSupportNavigateUp:
    // NavigationUI обрабатывает верхнюю кнопку toolbar по NavController и AppBarConfiguration. Возвращаем
    // true при обработанном действии; иначе даём его родителю.
    @Override public boolean onSupportNavigateUp() {
        return NavigationUI.navigateUp(navController, appBarConfiguration) || super.onSupportNavigateUp();
    }
}
