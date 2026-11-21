# YandexMaps · практика 8

**Требование:** MapKit, собственный API ключ, карта, lifecycle, runtime location, UserLocationLayer с pin/arrow/accuracy.

Добавьте личный MapKit mobile SDK key по ПОДКЛЮЧЕНИЕ_СЕРВИСОВ.md. MapKitFactory.setApiKey вызывается до initialize, карта — MapView с обязательными onStart/onStop вместе с MapKitFactory. Runtime ACCESS_FINE_LOCATION/COARSE_LOCATION выдаётся пользователем, layer = createUserLocationLayer(mapWindow). UserLocationObjectListener настраивает pin, arrow и accuracyCircle; сохраняйте сильную ссылку listener, иначе SDK может перестать доставлять события. Кнопка местоположения переносит камеру к актуальной точке. В отсутствие ключа показывается явная причина и действия не выдаются за работающую карту. В эмуляторе задайте GPS и покажите реальные тайлы и свой значок положения.

[Полный разбор кода](../РАЗБОР_КОДА.md) · [Защита](../ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) · [Фактические проверки](../ОТЧЁТ_О_ПРОВЕРКАХ.md)
