package ru.mirea.ZubarevVS.lesson8.osmmaps;

import android.os.Bundle;
import java.util.Locale;

import org.osmdroid.events.MapEventsReceiver;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.overlay.MapEventsOverlay;
import org.osmdroid.views.overlay.Marker;

import ru.mirea.ZubarevVS.lesson8.osmmaps.databinding.ActivityMainBinding;

/**
 * OpenStreetMap · места и маршруты. Binding содержит типизированные ссылки на ID из activity_main.xml.
 */
public class MainActivity extends BaseActivity {
    private static final GeoPoint EXAMPLE_DESTINATION = new GeoPoint(55.7298, 37.6010);
    private static final int[] ROUTE_COLORS = {0xff355e74, 0xffbc6b33, 0xff7849a1};

    // Маркеры хранят координаты ручного выбора; null оставляет GPS и учебное назначение.
    private Marker routeStart;
    private Marker routeEnd;
    private enum PointSelection { NONE, START, END }
    private PointSelection selection = PointSelection.NONE;

    // ПЕРЕМЕННАЯ: binding
    // Типизированные ссылки на корень и View с android:id; класс генерируется из XML.
    private ActivityMainBinding binding;

    // ПЕРЕМЕННАЯ: map
    // OSM MapView с тайлами и overlays.
    private org.osmdroid.views.MapView map;
    // ПЕРЕМЕННАЯ: location
    // MyLocationNewOverlay или Android Location по типу объявления; источник позиции устройства.
    private org.osmdroid.views.overlay.mylocation.MyLocationNewOverlay location;
    // ПЕРЕМЕННАЯ: compass
    // CompassOverlay с ориентацией от датчика магнитного поля.
    private org.osmdroid.views.overlay.compass.CompassOverlay compass;
    // ПЕРЕМЕННАЯ: routes
    // Полученные геометрии/оверлеи маршрутов, не прямая между двумя точками.
    private final java.util.ArrayList<org.osmdroid.views.overlay.Polyline> routes = new java.util.ArrayList<>();
    private final androidx.activity.result.ActivityResultLauncher<String[]> locationPermission = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.RequestMultiplePermissions(), grants -> enableLocation());

    @Override
    // ЗАЩИТА: onCreate
    // Android создаёт экземпляр Activity. state равен null при первом запуске и содержит Bundle при
    // восстановлении. Создаётся ActivityMainBinding из XML, устанавливается корень, назначаются
    // обработчики. Считывание полей пользовательского ввода выполняется в обработчиках нажатия.
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        org.osmdroid.config.Configuration.getInstance().load(this, getSharedPreferences("osm_settings", MODE_PRIVATE));
        org.osmdroid.config.Configuration.getInstance().setUserAgentValue(getPackageName() + "/1.0 educational Android project");
        map = new org.osmdroid.views.MapView(this);
        binding.mapHost.addView(map, new android.widget.FrameLayout.LayoutParams(-1, -1));
        map.setTileSource(org.osmdroid.tileprovider.tilesource.TileSourceFactory.MAPNIK);
        map.setMultiTouchControls(true);
        map.getZoomController().setVisibility(org.osmdroid.views.CustomZoomButtonsController.Visibility.ALWAYS);
        map.getController().setZoom(state == null ? 14 : state.getDouble("zoom", 14));
        map.getController().setCenter(new org.osmdroid.util.GeoPoint(state == null ? 55.6699 : state.getDouble("lat"), state == null ? 37.4796 : state.getDouble("lon")));
        org.osmdroid.views.overlay.gestures.RotationGestureOverlay rotate = new org.osmdroid.views.overlay.gestures.RotationGestureOverlay(map);
        rotate.setEnabled(true);
        map.getOverlays().add(rotate);
        org.osmdroid.views.overlay.ScaleBarOverlay scale = new org.osmdroid.views.overlay.ScaleBarOverlay(map);
        scale.setCentred(true);
        map.addOnLayoutChangeListener((view, left, top, right, bottom, oldLeft, oldTop, oldRight, oldBottom) ->
                scale.setScaleBarOffset((right - left) / 2, Math.round(10 * getResources().getDisplayMetrics().density)));
        map.getOverlays().add(scale);
        compass = new org.osmdroid.views.overlay.compass.CompassOverlay(this, new org.osmdroid.views.overlay.compass.InternalCompassOrientationProvider(this), map);
        map.getOverlays().add(compass);
        location = new org.osmdroid.views.overlay.mylocation.MyLocationNewOverlay(new org.osmdroid.views.overlay.mylocation.GpsMyLocationProvider(this), map);
        map.getOverlays().add(location);
        addMarker(55.6699, 37.4796, "РТУ МИРЭА", "Проспект Вернадского, 78. Учебный пример: университет и лаборатории.");
        addMarker(55.7087, 37.5657, "Воробьёвы горы", "Смотровая площадка. Учебный пример: панорама Москвы.");
        addMarker(55.7298, 37.6010, "Парк Горького", "Крымский Вал, 9. Учебный пример: городской парк.");
        if (state != null) {
            routeStart = restorePoint(state, "routeStart", R.string.route_start);
            routeEnd = restorePoint(state, "routeEnd", R.string.route_end);
        }
        // Только долгое нажатие в режиме выбора ставит точку. Обычные нажатия открывают описания мест.
        map.getOverlays().add(new MapEventsOverlay(new MapEventsReceiver() {
            @Override
            public boolean singleTapConfirmedHelper(GeoPoint point) {
                return false;
            }

            @Override
            public boolean longPressHelper(GeoPoint point) {
                if (selection == PointSelection.NONE) return false;
                selectPoint(point);
                return true;
            }
        }));
        binding.selectStart.setOnClickListener(v -> beginSelection(PointSelection.START));
        binding.selectEnd.setOnClickListener(v -> beginSelection(PointSelection.END));
        binding.locate.setOnClickListener(v -> locationPermission.launch(new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION}));
        binding.route.setOnClickListener(v -> loadRoutes());
        showSelectedPoints();
    }

    private void beginSelection(PointSelection next) {
        selection = next;
        location.disableFollowLocation();
        binding.status.setText(next == PointSelection.START ? R.string.pick_start : R.string.pick_end);
    }

    // Меняем только выбранный конец маршрута и убираем геометрию предыдущей пары.
    private void selectPoint(GeoPoint point) {
        if (selection == PointSelection.START) {
            if (routeStart != null) map.getOverlays().remove(routeStart);
            routeStart = addRoutePoint(point, R.string.route_start);
        } else {
            if (routeEnd != null) map.getOverlays().remove(routeEnd);
            routeEnd = addRoutePoint(point, R.string.route_end);
        }
        selection = PointSelection.NONE;
        clearRoutes();
        showSelectedPoints();
        map.invalidate();
    }

    private Marker addRoutePoint(GeoPoint point, int title) {
        Marker marker = new Marker(map);
        marker.setPosition(point);
        marker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM);
        marker.setTitle(getString(title));
        map.getOverlays().add(marker);
        return marker;
    }

    private void showSelectedPoints() {
        String start = routeStart == null ? getString(R.string.route_gps) : formatPoint(routeStart.getPosition());
        String end = routeEnd == null ? getString(R.string.route_example) : formatPoint(routeEnd.getPosition());
        binding.status.setText(getString(R.string.route_points, start, end));
    }

    private String formatPoint(GeoPoint point) {
        return String.format(Locale.ROOT, "%.5f, %.5f", point.getLatitude(), point.getLongitude());
    }

    private void clearRoutes() {
        map.getOverlays().removeAll(routes);
        routes.clear();
    }

    private Marker restorePoint(Bundle state, String key, int title) {
        double[] coordinates = state.getDoubleArray(key);
        return coordinates == null ? null : addRoutePoint(new GeoPoint(coordinates[0], coordinates[1]), title);
    }

    private void savePoint(Bundle state, String key, Marker marker) {
        if (marker != null) {
            GeoPoint point = marker.getPosition();
            state.putDoubleArray(key, new double[]{point.getLatitude(), point.getLongitude()});
        }
    }

    // ЗАЩИТА: addMarker
    // Создаёт OSM Marker с GeoPoint, заголовком и описанием, задаёт anchor и добавляет в overlays карты.
    // Стандартное InfoWindow открывается при нажатии.
    private void addMarker(double lat, double lon, String title, String description) {
        // ПЕРЕМЕННАЯ: marker
        // Объект маркера на карте: позиция, название и обработчик нажатия.
        org.osmdroid.views.overlay.Marker marker = new org.osmdroid.views.overlay.Marker(map);
        marker.setPosition(new org.osmdroid.util.GeoPoint(lat, lon));
        marker.setAnchor(.5f, 1f);
        marker.setTitle(title);
        marker.setSnippet(description);
        map.getOverlays().add(marker);
    }

    // ЗАЩИТА: enableLocation
    // Запрашивает/проверяет разрешение перед MyLocationNewOverlay. Включает получение координат и слежение
    // камеры, а не подставляет учебную точку как позицию устройства.
    private void enableLocation() {
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_FINE_LOCATION) != android.content.pm.PackageManager.PERMISSION_GRANTED && androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_COARSE_LOCATION) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            binding.status.setText("Местоположение не разрешено");
            return;
        }
        location.enableMyLocation();
        location.enableFollowLocation();
        binding.status.setText("Ожидание координат устройства");
    }

    // ЗАЩИТА: loadRoutes
    // Запрашивает OSRM с longitude,latitude в URL и alternatives=true. Читает GeoJSON coordinates (порядок
    // lon/lat), преобразует в GeoPoint (lat/lon), добавляет реальные Polyline на карту. Ошибка остаётся
    // ошибкой.
    private void loadRoutes() {
        GeoPoint from = routeStart == null ? location.getMyLocation() : routeStart.getPosition();
        GeoPoint to = routeEnd == null ? EXAMPLE_DESTINATION : routeEnd.getPosition();
        if (from == null) {
            binding.status.setText(R.string.route_needs_start);
            return;
        }
        if (from.distanceToAsDouble(to) < 1) {
            binding.status.setText(R.string.route_same_points);
            return;
        }
        // OSRM принимает долготу перед широтой; GeoPoint хранит их в обратном порядке.
        String url = String.format(Locale.ROOT, "https://router.project-osrm.org/route/v1/driving/%f,%f;%f,%f?alternatives=true&overview=full&geometries=geojson",
                from.getLongitude(), from.getLatitude(), to.getLongitude(), to.getLatitude());
        selection = PointSelection.NONE;
        setRouteControlsEnabled(false);
        binding.status.setText("Запрос маршрутов OSRM…");
        io.execute(() -> {
            try {
                org.json.JSONObject answer = new org.json.JSONObject(NetworkClient.get(url));
                if (!"Ok".equals(answer.optString("code")))
                    throw new java.io.IOException(answer.optString("code"));
                org.json.JSONArray found = answer.getJSONArray("routes");
                if (found.length() == 0) throw new java.io.IOException(getString(R.string.route_empty));
                java.util.ArrayList<java.util.List<org.osmdroid.util.GeoPoint>> paths = new java.util.ArrayList<>();
                for (int i = 0; i < found.length(); i++) {
                    org.json.JSONArray coordinates = found.getJSONObject(i).getJSONObject("geometry").getJSONArray("coordinates");
                    java.util.List<org.osmdroid.util.GeoPoint> path = new java.util.ArrayList<>();
                    for (int j = 0; j < coordinates.length(); j++) {
                        org.json.JSONArray pair = coordinates.getJSONArray(j);
                        path.add(new org.osmdroid.util.GeoPoint(pair.getDouble(1), pair.getDouble(0)));
                    }
                    paths.add(path);
                }
                ui(() -> {
                    clearRoutes();
                    java.util.ArrayList<GeoPoint> allRoutePoints = new java.util.ArrayList<>();
                    int index = 0;
                    for (java.util.List<org.osmdroid.util.GeoPoint> path : paths) {
                        org.osmdroid.views.overlay.Polyline line = new org.osmdroid.views.overlay.Polyline();
                        line.setPoints(path);
                        line.getOutlinePaint().setColor(ROUTE_COLORS[index++ % ROUTE_COLORS.length]);
                        line.getOutlinePaint().setStrokeWidth(9);
                        routes.add(line);
                        // Маркеры и элементы карты остаются поверх цветных линий.
                        map.getOverlays().add(0, line);
                        allRoutePoints.addAll(path);
                    }
                    location.disableFollowLocation();
                    map.zoomToBoundingBox(org.osmdroid.util.BoundingBox.fromGeoPoints(allRoutePoints), true, 48);
                    map.invalidate();
                    binding.status.setText("Маршрутов OSRM: " + paths.size() + ". © OpenStreetMap contributors");
                });
            } catch (Exception e) {
                ui(() -> binding.status.setText("Ошибка OSRM: " + e.getMessage()));
            } finally {
                ui(() -> setRouteControlsEnabled(true));
            }
        });
    }

    private void setRouteControlsEnabled(boolean enabled) {
        binding.route.setEnabled(enabled);
        binding.selectStart.setEnabled(enabled);
        binding.selectEnd.setEnabled(enabled);
        binding.locate.setEnabled(enabled);
    }

    @Override
    // ЗАЩИТА: onResume
    // Экран снова активен: регистрируются слушатели датчиков или возобновляется карта. Регистрация
    // соответствует очистке в onPause.
    protected void onResume() {
        super.onResume();
        if (map != null) {
            map.onResume();
            if (androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_FINE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED || androidx.core.content.ContextCompat.checkSelfPermission(this, android.Manifest.permission.ACCESS_COARSE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED)
                location.enableMyLocation();
            compass.enableCompass();
        }
    }

    @Override
    // ЗАЩИТА: onPause
    // Экран теряет активность: подписки датчиков/карты и воспроизведение, если требуется,
    // приостанавливаются. Долговременные файлы не удаляются.
    protected void onPause() {
        if (map != null) {
            location.disableMyLocation();
            compass.disableCompass();
            map.onPause();
        }
        super.onPause();
    }

    @Override
    // ЗАЩИТА: onSaveInstanceState
    // Сохраняет компактные данные в out/Bundle, затем вызывает родителя. Это снимок UI для пересоздания, а
    // не постоянное хранилище. Ссылки на старые View/MediaPlayer не сохраняются.
    protected void onSaveInstanceState(Bundle out) {
        if (map != null) {
            out.putDouble("lat", map.getMapCenter().getLatitude());
            out.putDouble("lon", map.getMapCenter().getLongitude());
            out.putDouble("zoom", map.getZoomLevelDouble());
            savePoint(out, "routeStart", routeStart);
            savePoint(out, "routeEnd", routeEnd);
        }
        super.onSaveInstanceState(out);
    }

    @Override
    // ЗАЩИТА: onDestroy
    // Завершает жизнь экземпляра: освобождает собственные MediaPlayer/Looper/Executor. super завершает
    // инфраструктуру родителя. onDestroy не гарантирован при убийстве всего процесса ОС.
    protected void onDestroy() {
        if (map != null) map.onDetach();
        super.onDestroy();
    }

}
