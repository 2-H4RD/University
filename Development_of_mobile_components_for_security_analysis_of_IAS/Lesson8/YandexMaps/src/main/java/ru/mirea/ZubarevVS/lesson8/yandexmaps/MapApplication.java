package ru.mirea.ZubarevVS.lesson8.yandexmaps;


/**
 * Ключ устанавливается до создания MapView/MapKitFactory.initialize.
 */
public class MapApplication extends android.app.Application {
    @Override
    // ЗАЩИТА: onCreate
    // Application устанавливает API ключ MapKit до создания карты. Пустой ключ не подменяется чужим;
    // MainActivity показывает инструкцию подключения.
    public void onCreate() {
        super.onCreate();
        if (!BuildConfig.YANDEX_MAPKIT_KEY.isEmpty())
            com.yandex.mapkit.MapKitFactory.setApiKey(BuildConfig.YANDEX_MAPKIT_KEY);
    }
}
