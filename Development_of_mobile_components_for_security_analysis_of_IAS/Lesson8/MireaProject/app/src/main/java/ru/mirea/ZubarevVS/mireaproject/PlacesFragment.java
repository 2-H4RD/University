package ru.mirea.ZubarevVS.mireaproject;

import android.os.Bundle;
import android.view.View;
import android.widget.*;

import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapView;
import org.osmdroid.views.overlay.Marker;
import org.osmdroid.views.overlay.mylocation.*;

import java.util.*;

/**
 * Места — учебные примеры, пока пользователь не добавил собственные. Дополнительная функция — расстояние.
 */
public class PlacesFragment extends LabFragment {
    // ПЕРЕМЕННАЯ: map
    // OSM MapView с тайлами и overlays.
    private MapView map;
    // ПЕРЕМЕННАЯ: location
    // MyLocationNewOverlay или Android Location по типу объявления; источник позиции устройства.
    private MyLocationNewOverlay location;
    // ПЕРЕМЕННАЯ: status
    // TextView состояния конкретного экрана, содержит результат/ошибку.
    private TextView status;
    // ПЕРЕМЕННАЯ: selected
    // Выбранное место, до которого рассчитывается отдельное расстояние по прямой.
    private GeoPoint selected;
    // ПЕРЕМЕННАЯ: points
    // GeoPoint всех заведений для подбора охвата карты.
    private final ArrayList<GeoPoint> points = new ArrayList<>();
    private final androidx.activity.result.ActivityResultLauncher<String[]> permissions = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.RequestMultiplePermissions(), grants -> {
        if (androidx.core.content.ContextCompat.checkSelfPermission(requireContext(), android.Manifest.permission.ACCESS_FINE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED || androidx.core.content.ContextCompat.checkSelfPermission(requireContext(), android.Manifest.permission.ACCESS_COARSE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED) {
            location.enableMyLocation();
            status.setText("Ожидание координат устройства");
        } else status.setText("Местоположение не разрешено");
    });

    @Override
    // ЗАЩИТА: onViewCreated
    // View уже создана. Добавляются элементы предметного экрана, обработчики и наблюдения с
    // getViewLifecycleOwner. Долгая операция выполняется в io/Worker; результат изменяет только актуальный
    // View.
    public void onViewCreated(View view, Bundle state) {
        label("Заведения и интересные места");
        label("Ниже учебные примеры. Добавьте свои заведения с адресами и описанием.");
        org.osmdroid.config.Configuration.getInstance().load(requireContext(), requireContext().getSharedPreferences("osm", 0));
        org.osmdroid.config.Configuration.getInstance().setUserAgentValue(requireContext().getPackageName() + "/1.0 educational");
        map = new MapView(requireContext());
        map.setTileSource(org.osmdroid.tileprovider.tilesource.TileSourceFactory.MAPNIK);
        map.setMultiTouchControls(true);
        binding.content.addView(map, new LinearLayout.LayoutParams(-1, (int) (350 * getResources().getDisplayMetrics().density)));
        map.getController().setZoom(13.0);
        map.getController().setCenter(new GeoPoint(55.705, 37.55));
        location = new MyLocationNewOverlay(new GpsMyLocationProvider(requireContext()), map);
        map.getOverlays().add(location);
        status = label("© OpenStreetMap contributors");
        addPlace("РТУ МИРЭА", "Проспект Вернадского, 78", "Университет, учебные лаборатории. Учебный пример.", 55.6699, 37.4796);
        addPlace("Парк Горького", "Крымский Вал, 9", "Парк культуры и отдыха. Учебный пример.", 55.7298, 37.6010);
        addPlace("Воробьёвы горы", "Улица Косыгина, смотровая площадка", "Панорама Москвы. Учебный пример.", 55.7087, 37.5657);
        // ПЕРЕМЕННАЯ: saved
        // Ранее сохранённое значение, прочитанное при восстановлении экрана.
        String saved = requireContext().getSharedPreferences("places", 0).getString("custom", "[]");
        try {
            org.json.JSONArray list = new org.json.JSONArray(saved);
            for (int i = 0; i < list.length(); i++) {
                org.json.JSONObject p = list.getJSONObject(i);
                addPlace(p.getString("name"), p.getString("address"), p.getString("description"), p.getDouble("lat"), p.getDouble("lon"));
            }
        } catch (Exception e) {
            status.setText("Ошибка сохранённых мест");
        }
        button("Добавить своё заведение", () -> new PlaceDialog().show(getChildFragmentManager(), "place"));
        getChildFragmentManager().setFragmentResultListener("new-place", getViewLifecycleOwner(), (key, data) -> {
            try {
                org.json.JSONArray list = new org.json.JSONArray(requireContext().getSharedPreferences("places", 0).getString("custom", "[]"));
                org.json.JSONObject place = new org.json.JSONObject();
                for (String field : new String[]{"name", "address", "description"})
                    place.put(field, data.getString(field));
                place.put("lat", data.getDouble("lat"));
                place.put("lon", data.getDouble("lon"));
                list.put(place);
                requireContext().getSharedPreferences("places", 0).edit().putString("custom", list.toString()).apply();
                addPlace(data.getString("name"), data.getString("address"), data.getString("description"), data.getDouble("lat"), data.getDouble("lon"));
                map.invalidate();
                status.setText("Заведение сохранено");
            } catch (Exception e) {
                status.setText("Не удалось сохранить место");
            }
        });
        button("Показать все места", () -> map.zoomToBoundingBox(org.osmdroid.util.BoundingBox.fromGeoPoints(points), true, 40));
        button("Определить моё местоположение", () -> permissions.launch(new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION}));
        button("Расстояние до выбранного места", () -> {
            // ПЕРЕМЕННАЯ: from
            // Начальная координата, полученная от источника местоположения.
            GeoPoint from = location.getMyLocation();
            if (from == null || selected == null) {
                status.setText("Получите местоположение и выберите место");
                return;
            }
            status.setText(String.format(Locale.getDefault(), "По прямой до места: %.0f м (не маршрут дороги)", from.distanceToAsDouble(selected)));
        });
    }

    // ЗАЩИТА: addPlace
    // Одна запись связывает название/адрес/описание/GeoPoint, Marker и кнопку списка. При выборе
    // сохраняется selected; нажатие маркера открывает информацию о месте.
    private void addPlace(String name, String address, String description, double lat, double lon) {
        // ПЕРЕМЕННАЯ: point
        // Пара широты/долготы конкретного маркера или вершины маршрута.
        GeoPoint point = new GeoPoint(lat, lon);
        points.add(point);
        // ПЕРЕМЕННАЯ: marker
        // Объект маркера на карте: позиция, название и обработчик нажатия.
        Marker marker = new Marker(map);
        marker.setPosition(point);
        marker.setAnchor(.5f, 1f);
        marker.setTitle(name);
        marker.setSnippet(address + "\n" + description);
        marker.setOnMarkerClickListener((m, mapView) -> {
            selected = point;
            new androidx.appcompat.app.AlertDialog.Builder(requireContext()).setTitle(name).setMessage(address + "\n" + description).setPositiveButton("Закрыть", null).show();
            return true;
        });
        map.getOverlays().add(marker);
        button("На карте: " + name, () -> {
            selected = point;
            map.getController().setCenter(point);
            map.getController().setZoom(16.0);
            status.setText(name + "\n" + address + "\n" + description);
        });
    }

    @Override
    // ЗАЩИТА: onResume
    // Экран снова активен: регистрируются слушатели датчиков или возобновляется карта. Регистрация
    // соответствует очистке в onPause.
    public void onResume() {
        super.onResume();
        if (map != null) {
            map.onResume();
            if (androidx.core.content.ContextCompat.checkSelfPermission(requireContext(), android.Manifest.permission.ACCESS_FINE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED || androidx.core.content.ContextCompat.checkSelfPermission(requireContext(), android.Manifest.permission.ACCESS_COARSE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED)
                location.enableMyLocation();
        }
    }

    @Override
    // ЗАЩИТА: onPause
    // Экран теряет активность: подписки датчиков/карты и воспроизведение, если требуется,
    // приостанавливаются. Долговременные файлы не удаляются.
    public void onPause() {
        if (location != null) location.disableMyLocation();
        if (map != null) map.onPause();
        super.onPause();
    }

    @Override
    // ЗАЩИТА: onDestroyView
    // Жизнь разметки Fragment закончилась, хотя сам Fragment может ещё существовать. Binding/map
    // очищаются, чтобы не удерживать прежний экран.
    public void onDestroyView() {
        if (map != null) map.onDetach();
        map = null;
        points.clear();
        super.onDestroyView();
    }

    public static class PlaceDialog extends androidx.fragment.app.DialogFragment {
        @Override
        // ЗАЩИТА: onCreateDialog
        // Создаёт форму диалога и возвращает AlertDialog. После onShow заменяет обработчик положительной
        // кнопки, чтобы ошибка валидации не закрывала окно. Корректный результат передаётся через
        // FragmentResult API.
        public android.app.Dialog onCreateDialog(Bundle state) {
            LinearLayout form = new LinearLayout(requireContext());
            form.setOrientation(LinearLayout.VERTICAL);
            String[] keys = {"name", "address", "description", "lat", "lon"};
            String[] hints = {"Название", "Адрес", "Описание", "Широта", "Долгота"};
            EditText[] fields = new EditText[5];
            for (int i = 0; i < fields.length; i++) {
                fields[i] = new EditText(requireContext());
                fields[i].setHint(hints[i]);
                fields[i].setContentDescription("place_" + keys[i]);
                form.addView(fields[i]);
            }
            androidx.appcompat.app.AlertDialog dialog = new androidx.appcompat.app.AlertDialog.Builder(requireContext()).setTitle("Своё заведение").setView(form).setNegativeButton("Отмена", null).setPositiveButton("Добавить", null).create();
            dialog.setOnShowListener(v -> dialog.getButton(-1).setOnClickListener(w -> {
                try {
                    // ПЕРЕМЕННАЯ: result
                    // Контейнер/текст/поле результата согласно типу объявления и методу.
                    Bundle result = new Bundle();
                    for (int i = 0; i < 3; i++) {
                        String value = fields[i].getText().toString().trim();
                        if (value.isEmpty()) throw new IllegalArgumentException();
                        result.putString(keys[i], value);
                    }
                    // ПЕРЕМЕННАЯ: lat
                    // Широта в градусах: допустима конечная величина от −90 до 90; Android GeoPoint принимает её первой.
                    double lat = Double.parseDouble(fields[3].getText().toString()), lon = Double.parseDouble(fields[4].getText().toString());
                    if (!Double.isFinite(lat) || !Double.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
                        throw new IllegalArgumentException();
                    }
                    result.putDouble("lat", lat);
                    result.putDouble("lon", lon);
                    getParentFragmentManager().setFragmentResult("new-place", result);
                    dismiss();
                } catch (IllegalArgumentException e) {
                    fields[0].setError("Заполните поля и корректные координаты");
                }
            }));
            return dialog;
        }
    }
}
