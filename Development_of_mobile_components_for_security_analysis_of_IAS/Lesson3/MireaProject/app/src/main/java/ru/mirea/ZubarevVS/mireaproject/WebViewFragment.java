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

import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.activity.OnBackPressedCallback;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import ru.mirea.ZubarevVS.mireaproject.databinding.FragmentWebViewBinding;

/** Простой браузер со стартовой страницей, адресом и историей WebView. */
public class WebViewFragment extends Fragment {
    private FragmentWebViewBinding binding;
    private Bundle webState;
    private boolean pageFailed;
    private OnBackPressedCallback webBack;
    // РАЗБОР onCreate:
    // Метод создаёт экземпляр Fragment, но ещё не его View. state содержит сохранённый Bundle либо null.
    // Ключ web_state извлекает историю в поле webState; разметка будет создана отдельно в onCreateView, а
    // restoreState выполняется в onViewCreated.
    @Override public void onCreate(@Nullable Bundle state) {
        super.onCreate(state);
        if (state != null) webState = state.getBundle("web_state"); // Восстанавливаем историю после поворота.
    }
    // РАЗБОР onCreateView:
    // inflater создаёт View из XML, container даёт параметры будущего родителя. false запрещает
    // немедленное прикрепление: FragmentManager делает его сам. state - восстановленное состояние.
    // Возвращается корень разметки/Binding.
    @Nullable @Override public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle state) {
        binding = FragmentWebViewBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }
    // РАЗБОР onViewCreated:
    // view уже создан, поэтому можно назначать listeners и клиенты WebView. Настройки браузера, обработка
    // адреса, прогресс и история относятся к жизненному циклу View фрагмента.
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle state) {
        super.onViewCreated(view, state);
        binding.webView.getSettings().setJavaScriptEnabled(true); // Нужен для современных веб-страниц.
        binding.webView.getSettings().setDomStorageEnabled(true); // Позволяет сайту использовать DOM storage.
        binding.webView.getSettings().setAllowFileAccess(false); // Браузер работает с web, а не с локальными файлами.
        binding.webView.getSettings().setAllowContentAccess(false);
        webBack = new OnBackPressedCallback(false) {
            // РАЗБОР handleOnBackPressed:
            // Вызывается включённым OnBackPressedCallback. Открытая шторка должна закрыться раньше истории
            // браузера. Если шторка закрыта и есть история, WebView.goBack возвращает предыдущую страницу.
            @Override public void handleOnBackPressed() {
                androidx.drawerlayout.widget.DrawerLayout drawer = requireActivity().findViewById(R.id.drawerLayout);
                if (drawer.isDrawerOpen(androidx.core.view.GravityCompat.START)) {
                    drawer.closeDrawer(androidx.core.view.GravityCompat.START); // Шторка закрывается раньше истории браузера.
                } else { binding.webView.goBack(); }
            }
        };
        requireActivity().getOnBackPressedDispatcher().addCallback(getViewLifecycleOwner(), webBack);
        binding.webView.setWebViewClient(new WebViewClient() {
            // РАЗБОР shouldOverrideUrlLoading:
            // request содержит целевой Uri. true означает «не передавать загрузку WebView», false - продолжить
            // обычную загрузку. Здесь разрешены HTTPS ссылки.
            @Override public boolean shouldOverrideUrlLoading(WebView web, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
                return !"https".equalsIgnoreCase(scheme); // Web-ссылки остаются внутри.
            }
            // РАЗБОР onPageStarted:
            // Начало загрузки главной страницы сбрасывает pageFailed и показывает progress. url - текущий URL,
            // icon - favicon, web - источник callback.
            @Override public void onPageStarted(WebView web, String url, Bitmap icon) {
                pageFailed = false;
                if (binding != null) { binding.status.setText(R.string.loading); binding.progress.setVisibility(View.VISIBLE); }
            }
            // РАЗБОР onPageFinished:
            // Загрузка завершилась; url учитывает redirects. pageFailed отличает завершение с ошибкой. canGoBack
            // определяет доступность истории и кнопки Back. После уничтожения View binding=null и callback
            // пропускается.
            @Override public void onPageFinished(WebView web, String url) {
                if (binding == null) return; // Callback старого WebView может прийти после смены экрана.
                binding.url.setText(url); // Показываем адрес после возможного перенаправления.
                binding.status.setText(pageFailed ? R.string.page_error : R.string.ready);
                binding.progress.setVisibility(View.GONE);
                webBack.setEnabled(web.canGoBack()); // Если истории нет, Back обрабатывает NavController.
                binding.backPage.setEnabled(web.canGoBack());
            }
            // РАЗБОР onReceivedError:
            // request.isForMainFrame отделяет ошибку основной страницы от ошибок отдельных картинок. Основная
            // ошибка включает pageFailed и меняет status.
            @Override public void onReceivedError(WebView web, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame() && binding != null) {
                    pageFailed = true;
                    binding.status.setText(R.string.page_error); // Сетевую ошибку показываем отдельно от навигации.
                }
            }
        });
        binding.webView.setWebChromeClient(new WebChromeClient() {
            // РАЗБОР onProgressChanged:
            // progress - реальное целое значение 0..100, переданное WebChromeClient. Оно передаётся ProgressBar
            // без искусственной имитации.
            @Override public void onProgressChanged(WebView web, int progress) {
                if (binding != null) binding.progress.setProgress(progress); // Индикатор отражает реальную загрузку.
            }
        });
        binding.go.setOnClickListener(v -> openAddress());
        binding.url.setOnEditorActionListener((field, action, event) -> {
            if (action == EditorInfo.IME_ACTION_GO) { openAddress(); return true; } return false;
        });
        binding.home.setOnClickListener(v -> binding.webView.loadUrl(getString(R.string.default_url)));
        binding.reload.setOnClickListener(v -> binding.webView.reload());
        binding.backPage.setOnClickListener(v -> { if (binding.webView.canGoBack()) binding.webView.goBack(); });
        binding.backPage.setEnabled(false);
        if (webState == null || binding.webView.restoreState(webState) == null) {
            binding.webView.loadUrl(getString(R.string.default_url)); // Начальная страница загружается один раз.
        }
    }
    // РАЗБОР openAddress:
    // address - trimmed строка поля url; при отсутствующей схеме добавляется https. uri разбирает адрес;
    // scheme и host проверяются до loadUrl. При ошибке setError/status объясняют причину. При успехе
    // скрывается клавиатура и запускается загрузка.
    private void openAddress() {
        String address = binding.url.getText().toString().trim();
        if (!address.contains("://")) address = "https://" + address; // Для обычного домена добавляем схему.
        Uri uri = Uri.parse(address);
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null || uri.getHost().isEmpty()) {
            binding.url.setError(getString(R.string.invalid_url)); // Помечаем поле с ошибочным адресом.
            binding.status.setText(R.string.invalid_url); // Объяснение видно и после потери фокуса поля.
            return;
        }
        InputMethodManager keyboard = (InputMethodManager) requireContext().getSystemService(Context.INPUT_METHOD_SERVICE);
        keyboard.hideSoftInputFromWindow(binding.url.getWindowToken(), 0); // Оставляем место для веб-страницы.
        binding.url.clearFocus();
        binding.webView.loadUrl(address); // Пользователь выбирает адрес через поле ввода.
    }
    // РАЗБОР onSaveInstanceState:
    // outState - Bundle для компактных значений UI. putString/putParcelable связывают ключ и значение.
    // super позволяет Android сохранить View с ID и состояние FragmentManager. Это не постоянное хранилище
    // и не замена файлу/базе данных.
    @Override public void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        if (binding != null) { webState = new Bundle(); binding.webView.saveState(webState); }
        outState.putBundle("web_state", webState); // История WebView не входит автоматически в состояние Fragment.
    }
    // РАЗБОР onDestroyView:
    // View фрагмента уничтожается, хотя сам Fragment может остаться. binding очищается, чтобы не
    // удерживать прежнюю разметку. WebView останавливается, сохраняет историю и освобождает ресурсы.
    @Override public void onDestroyView() {
        if (binding != null) {
            webState = new Bundle();
            binding.webView.saveState(webState); // Сохраняем историю при переключении пунктов drawer.
            binding.webView.stopLoading();
            binding.webView.setWebChromeClient(null);
            binding.webView.setWebViewClient(new WebViewClient());
            binding.webView.destroy(); // Освобождаем ресурсы браузера вместе с его View.
            binding = null;
        }
        super.onDestroyView();
    }
}
