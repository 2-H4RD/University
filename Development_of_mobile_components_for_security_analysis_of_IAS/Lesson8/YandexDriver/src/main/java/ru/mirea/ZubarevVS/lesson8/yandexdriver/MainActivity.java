package ru.mirea.ZubarevVS.lesson8.yandexdriver;

import android.os.Bundle;
import android.widget.*;
import android.view.View;

import java.util.Locale;

import ru.mirea.ZubarevVS.lesson8.yandexdriver.databinding.ActivityMainBinding;

/**
 * Яндекс · маршрут до заведения. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity implements com.yandex.mapkit.user_location.UserLocationObjectListener, com.yandex.mapkit.directions.driving.DrivingSession.DrivingRouteListener {
    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;

    // ПЕРЕМЕННАЯ: mapView
    // Нативный Yandex MapView, события lifecycle передаются SDK.
    private com.yandex.mapkit.mapview.MapView mapView;
    // ПЕРЕМЕННАЯ: userLayer
    // UserLocationLayer MapKit с иконками и областью точности.
    private com.yandex.mapkit.user_location.UserLocationLayer userLayer;
    // ПЕРЕМЕННАЯ: locations
    // Android LocationManager для получения GPS/network координат с runtime permission.
    private android.location.LocationManager locations;
    // ПЕРЕМЕННАЯ: userPoint
    // Последние реальные координаты устройства для начала маршрута.
    private com.yandex.mapkit.geometry.Point userPoint;
    private boolean mapStarted;
    // Одно нажатие «Моё местоположение» фокусирует камеру при первом полученном GPS.
    // ПЕРЕМЕННАЯ: focusLocation
    // Одноразовый запрос фокусировки карты на первой реальной координате после нажатия кнопки.
    private boolean focusLocation;
    private final androidx.activity.result.ActivityResultLauncher<String[]> locationPermission = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.RequestMultiplePermissions(), result -> startLocation());
    private final android.location.LocationListener listener = new android.location.LocationListener() {
        @Override
        // ЗАЩИТА: onLocationChanged
        // Сохраняет широту/долготу настоящего Android Location в userPoint. focusLocation разрешает одно
        // перемещение камеры после кнопки; затем флаг сбрасывается, чтобы поток GPS не мешал ручному просмотру
        // карты.
        public void onLocationChanged(android.location.Location location) {
            userPoint = new com.yandex.mapkit.geometry.Point(location.getLatitude(), location.getLongitude());
            if (focusLocation && mapView != null) {
                mapView.getMapWindow().getMap().move(new com.yandex.mapkit.map.CameraPosition(userPoint, 16, 0, 0));
                focusLocation = false;
            }
            binding.status.setText("Местоположение: " + location.getLatitude() + ", " + location.getLongitude());
        }
    };

    // ПЕРЕМЕННАЯ: router
    // DrivingRouter MapKit, строит настоящие дорожные маршруты.
    private com.yandex.mapkit.directions.driving.DrivingRouter router;
    // ПЕРЕМЕННАЯ: session
    // DrivingSession текущего асинхронного запроса; сохраняется, чтобы не потерять callback.
    private com.yandex.mapkit.directions.driving.DrivingSession session;
    // ПЕРЕМЕННАЯ: taps
    // Сильные ссылки на MapObjectTapListener; MapKit не должен потерять listener после GC.
    private final java.util.ArrayList<com.yandex.mapkit.map.MapObjectTapListener> taps = new java.util.ArrayList<>();

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        if (BuildConfig.YANDEX_MAPKIT_KEY.isEmpty()) {
            binding.status.setText("Нужен ключ MapKit — мобильный SDK. Укажите yandexMapkitKey в secrets.properties; см. ПОДКЛЮЧЕНИЕ_СЕРВИСОВ.md.");
            binding.locate.setEnabled(false);
        } else {
            com.yandex.mapkit.MapKitFactory.initialize(this);
            mapView = new com.yandex.mapkit.mapview.MapView(this);
            binding.mapHost.addView(mapView, new android.widget.FrameLayout.LayoutParams(-1, -1));
            mapView.getMapWindow().getMap().move(new com.yandex.mapkit.map.CameraPosition(new com.yandex.mapkit.geometry.Point(55.6699, 37.4796), 15, 0, 0));
            userLayer = com.yandex.mapkit.MapKitFactory.getInstance().createUserLocationLayer(mapView.getMapWindow());
            userLayer.setHeadingModeActive(true);
            // SDK 4.45 принимает WeakReference; сама Activity удерживается системой до onDestroy.
            userLayer.setObjectListener(new java.lang.ref.WeakReference<>(this));
        }
        locations = (android.location.LocationManager) getSystemService(LOCATION_SERVICE);
        binding.locate.setOnClickListener(v -> {
            focusLocation = true;
            locationPermission.launch(new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION});
        });

        if (state == null) {
            binding.destination.setText("Учебный пример: Парк Горького, Крымский Вал, 9. Городской парк.");
            binding.latitude.setText("55.7298");
            binding.longitude.setText("37.6010");
        }
        binding.route.setEnabled(mapView != null);
        binding.route.setOnClickListener(v -> buildRoutes());

    }

    // ЗАЩИТА: startLocation
    // Проверяет выданные fine/coarse permissions перед запросом LocationManager. Использует доступные
    // GPS/network providers, сохраняет реальное местоположение, включает UserLocationLayer. При отсутствии
    // координат просит задать их в эмуляторе.
    private void startLocation() {
        boolean fine = androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_FINE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED;
        boolean coarse = androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_COARSE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED;
        if (!fine && !coarse) {
            binding.status.setText("Местоположение не разрешено");
            return;
        }
        if (userLayer != null) userLayer.setVisible(true);
        try {
            for (String provider : locations.getProviders(true)) {
                if ((provider.equals(android.location.LocationManager.GPS_PROVIDER) && fine) || provider.equals(android.location.LocationManager.NETWORK_PROVIDER)) {
                    android.location.Location last = locations.getLastKnownLocation(provider);
                    if (last != null) listener.onLocationChanged(last);
                    locations.requestLocationUpdates(provider, 1000, 1, listener);
                }
            }
            binding.status.setText(userPoint == null ? "Ожидание GPS. Задайте координаты в Extended Controls эмулятора." : "Координаты получены");
        } catch (SecurityException e) {
            binding.status.setText("Разрешение местоположения изменилось");
        }
    }

    @Override
    // ЗАЩИТА: onObjectAdded
    // MapKit создал UserLocationView: настраиваются иконки pin/arrow и цвет accuracyCircle. Этот callback
    // не устанавливает координаты пользователя вручную.
    public void onObjectAdded(com.yandex.mapkit.user_location.UserLocationView view) {
        view.getAccuracyCircle().setFillColor(0x30355E74);
        view.getPin().setIcon(icon());
        view.getArrow().setIcon(icon());
    }

    @Override
    // ЗАЩИТА: onObjectRemoved
    // Обязательный метод UserLocationObjectListener. В текущем интерфейсе не требует дополнительных
    // действий.
    public void onObjectRemoved(com.yandex.mapkit.user_location.UserLocationView view) {
    }

    @Override
    // ЗАЩИТА: onObjectUpdated
    // Обязательный метод для обновления объекта слоя MapKit. Геометрию пользователя обновляет сам SDK.
    public void onObjectUpdated(com.yandex.mapkit.user_location.UserLocationView view, com.yandex.mapkit.layers.ObjectEvent event) {
    }

    // ЗАЩИТА: icon
    // Создаёт собственную небольшую Bitmap и ImageProvider для маркера. Canvas рисует круги; это
    // программный ресурс, не скачанный значок.
    private com.yandex.runtime.image.ImageProvider icon() {
        android.graphics.Bitmap image = android.graphics.Bitmap.createBitmap(48, 48, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas canvas = new android.graphics.Canvas(image);
        android.graphics.Paint paint = new android.graphics.Paint(3);
        paint.setColor(0xff355e74);
        canvas.drawCircle(24, 24, 20, paint);
        paint.setColor(0xffffffff);
        canvas.drawCircle(24, 24, 7, paint);
        return com.yandex.runtime.image.ImageProvider.fromBitmap(image);
    }

    @Override
    // ЗАЩИТА: onStart
    // Экран видим: передаётся событие lifecycle компонентам, которым оно нужно. Для MapKit вызываются
    // onStart у MapKit и MapView; это не повторная инициализация API ключа.
    protected void onStart() {
        super.onStart();
        if (mapView != null) {
            com.yandex.mapkit.MapKitFactory.getInstance().onStart();
            mapView.onStart();
            mapStarted = true;
        }
    }

    @Override
    // ЗАЩИТА: onStop
    // Экран перестал быть видимым: запись/воспроизведение или обновления геолокации останавливаются,
    // ресурсы освобождаются. Foreground Service имеет собственный жизненный цикл и не зависит от этой
    // Activity.
    protected void onStop() {
        if (session != null) session.cancel();
        if (locations != null) locations.removeUpdates(listener);
        if (mapStarted) {
            mapView.onStop();
            com.yandex.mapkit.MapKitFactory.getInstance().onStop();
            mapStarted = false;
        }
        super.onStop();
    }

    // ЗАЩИТА: buildRoutes
    // Берёт реальное userPoint и введённые координаты/описание заведения. Создаёт начальный/конечный
    // RequestPoint, просит до трёх DrivingRoute у DirectionsFactory, сохраняет DrivingSession/listener и
    // отображает описание маркера по нажатию.
    private void buildRoutes() {
        if (userPoint == null) {
            binding.status.setText("Сначала получите координаты устройства");
            return;
        }
        try {
            // ПЕРЕМЕННАЯ: lat
            // Широта в градусах: допустима конечная величина от −90 до 90; Android GeoPoint принимает её первой.
            double lat = Double.parseDouble(binding.latitude.getText().toString()), lon = Double.parseDouble(binding.longitude.getText().toString());
            String description = binding.destination.getText().toString().trim();
            if (!Double.isFinite(lat) || !Double.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180 || description.isEmpty())
                throw new IllegalArgumentException();
            com.yandex.mapkit.geometry.Point end = new com.yandex.mapkit.geometry.Point(lat, lon);
            mapView.getMapWindow().getMap().getMapObjects().clear();
            taps.clear();
            // ПЕРЕМЕННАЯ: marker
            // Объект маркера на карте: позиция, название и обработчик нажатия.
            com.yandex.mapkit.map.PlacemarkMapObject marker = mapView.getMapWindow().getMap().getMapObjects().addPlacemark();
            marker.setGeometry(end);
            marker.setIcon(icon());
            com.yandex.mapkit.map.MapObjectTapListener tap = (object, point) -> {
                new androidx.appcompat.app.AlertDialog.Builder(this).setTitle("Заведение").setMessage(description).setPositiveButton("Закрыть", null).show();
                return true;
            };
            taps.add(tap);
            marker.addTapListener(new java.lang.ref.WeakReference<>(tap));
            // ПЕРЕМЕННАЯ: points
            // GeoPoint всех заведений для подбора охвата карты.
            java.util.ArrayList<com.yandex.mapkit.RequestPoint> points = new java.util.ArrayList<>();
            points.add(new com.yandex.mapkit.RequestPoint(userPoint, com.yandex.mapkit.RequestPointType.WAYPOINT, null, null, null));
            points.add(new com.yandex.mapkit.RequestPoint(end, com.yandex.mapkit.RequestPointType.WAYPOINT, null, null, null));
            router = com.yandex.mapkit.directions.DirectionsFactory.getInstance().createDrivingRouter(com.yandex.mapkit.directions.driving.DrivingRouterType.COMBINED);
            com.yandex.mapkit.directions.driving.DrivingOptions options = new com.yandex.mapkit.directions.driving.DrivingOptions();
            options.setRoutesCount(3);
            if (session != null) session.cancel();
            session = router.requestRoutes(points, options, new com.yandex.mapkit.directions.driving.VehicleOptions(), this);
            binding.status.setText("Запрос маршрутов Яндекс…");
        } catch (IllegalArgumentException e) {
            binding.status.setText("Введите название/адрес/описание, широту -90..90 и долготу -180..180");
        }
    }

    @Override
    // ЗАЩИТА: onDrivingRoutes
    // Получает реальные маршруты MapKit. Для каждой геометрии добавляет PolylineMapObject с отдельным
    // цветом. Weight содержит локализованные расстояние и время с пробками; Geometry.fromPolyline
    // преобразует линию для cameraPosition. Проверка lifecycle защищает уничтоженную карту.
    public void onDrivingRoutes(java.util.List<com.yandex.mapkit.directions.driving.DrivingRoute> routes) {
        if (isFinishing() || isDestroyed() || mapView == null) return;
        int index = 0;
        for (com.yandex.mapkit.directions.driving.DrivingRoute route : routes) {
            com.yandex.mapkit.map.PolylineMapObject line = mapView.getMapWindow().getMap().getMapObjects().addPolyline(route.getGeometry());
            line.setStrokeColor(index++ == 0 ? 0xff355e74 : 0xffbc6b33);
            line.setStrokeWidth(5);
        }
        StringBuilder report = new StringBuilder("Получено маршрутов Яндекс: " + routes.size());
        for (int i = 0; i < routes.size(); i++) {
            // ПЕРЕМЕННАЯ: weight
            // Метаданные варианта DrivingRoute: длина и время, локализованные самим сервисом маршрутизации.
            com.yandex.mapkit.directions.driving.Weight weight = routes.get(i).getMetadata().getWeight();
            report.append("\n").append(i + 1).append(": ").append(weight.getDistance().getText())
                    .append("; с пробками: ").append(weight.getTimeWithTraffic().getText());
        }
        binding.status.setText(report);
        if (!routes.isEmpty())
            mapView.getMapWindow().getMap().move(mapView.getMapWindow().getMap().cameraPosition(com.yandex.mapkit.geometry.Geometry.fromPolyline(routes.get(0).getGeometry())));
    }

    @Override
    // ЗАЩИТА: onDrivingRoutesError
    // Отдельно сообщает ошибку картографического сервиса. Не рисует фиктивную прямую вместо неуспешного
    // дорожного маршрута.
    public void onDrivingRoutesError(com.yandex.runtime.Error error) {
        binding.status.setText("Ошибка маршрута Яндекс: " + error.getClass().getSimpleName());
    }

}
