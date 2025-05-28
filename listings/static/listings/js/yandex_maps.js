
// Yandex Maps integration for property location selection
let map, placemark;

function initYandexMap(containerId, lat = 55.751244, lng = 37.618423, isEditable = false) {
    // Initialize Yandex Map
    ymaps.ready(function () {
        map = new ymaps.Map(containerId, {
            center: [lat, lng],
            zoom: 13
        });

        if (isEditable) {
            // Add click event for location selection
            map.events.add('click', function (e) {
                const coords = e.get('coords');
                setLocation(coords[0], coords[1]);
            });

            // Add search control
            const searchControl = new ymaps.control.SearchControl({
                options: {
                    provider: 'yandex#search'
                }
            });
            map.controls.add(searchControl);

            // Listen for search results
            searchControl.events.add('resultselect', function (e) {
                const results = searchControl.getResultsArray();
                const selected = results[e.get('index')];
                const coords = selected.geometry.getCoordinates();
                setLocation(coords[0], coords[1]);
            });
        }

        // If coordinates are provided, add placemark
        if (lat !== 55.751244 || lng !== 37.618423) {
            addPlacemark(lat, lng);
        }
    });
}

function setLocation(latitude, longitude) {
    // Update hidden form fields
    const latField = document.getElementById('id_latitude');
    const lngField = document.getElementById('id_longitude');
    
    if (latField) latField.value = latitude;
    if (lngField) lngField.value = longitude;

    // Remove existing placemark
    if (placemark) {
        map.geoObjects.remove(placemark);
    }

    // Add new placemark
    addPlacemark(latitude, longitude);

    // Reverse geocoding to get address
    ymaps.geocode([latitude, longitude]).then(function (res) {
        const firstGeoObject = res.geoObjects.get(0);
        if (firstGeoObject) {
            const address = firstGeoObject.getAddressLine();
            
            // Update address field if exists
            const addressField = document.getElementById('id_address');
            if (addressField && !addressField.value) {
                addressField.value = address;
            }
        }
    });
}

function addPlacemark(latitude, longitude) {
    placemark = new ymaps.Placemark([latitude, longitude], {
        hintContent: 'Property Location',
        balloonContent: 'Property is located here'
    }, {
        preset: 'islands#redDotIcon',
        draggable: true
    });

    // Add drag event for placemark
    placemark.events.add('dragend', function () {
        const coords = placemark.geometry.getCoordinates();
        setLocation(coords[0], coords[1]);
    });

    map.geoObjects.add(placemark);
}

// Function to geocode address and set location
function geocodeAddress() {
    const addressField = document.getElementById('id_address');
    const cityField = document.getElementById('id_city');
    const stateField = document.getElementById('id_state');
    const countryField = document.getElementById('id_country');

    if (!addressField) return;

    let fullAddress = addressField.value;
    if (cityField && cityField.value) fullAddress += ', ' + cityField.value;
    if (stateField && stateField.value) fullAddress += ', ' + stateField.value;
    if (countryField && countryField.value) fullAddress += ', ' + countryField.value;

    if (fullAddress.trim()) {
        ymaps.geocode(fullAddress).then(function (res) {
            const firstGeoObject = res.geoObjects.get(0);
            if (firstGeoObject) {
                const coords = firstGeoObject.geometry.getCoordinates();
                setLocation(coords[0], coords[1]);
                map.setCenter(coords, 15);
            }
        });
    }
}
