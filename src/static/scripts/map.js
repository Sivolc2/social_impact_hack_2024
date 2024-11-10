document.addEventListener('DOMContentLoaded', function() {
    const MAPBOX_TOKEN = 'pk.eyJ1Ijoic2l2b2xjMiIsImEiOiJjbTNhbmd1dWsxM21tMmlvcms2Ym01b3J1In0.Oeee5mLjSKlT-vyBX5DpGQ';
    mapboxgl.accessToken = MAPBOX_TOKEN;

    // Initialize the map
    fetch('/api/map/base')
        .then(response => response.json())
        .then(config => {
            // Create map and expose it globally
            window.map = new mapboxgl.Map({
                container: 'map',
                style: config.mapStyle,
                center: [config.initialViewState.longitude, config.initialViewState.latitude],
                zoom: config.initialViewState.zoom,
                bearing: config.initialViewState.bearing,
                pitch: config.initialViewState.pitch,
                projection: 'globe',
                antialias: true
            });

            // Add navigation controls
            window.map.addControl(new mapboxgl.NavigationControl(), 'top-left');

            // Wait for map style to load before adding layers
            window.map.on('style.load', () => {
                setupMapFeatures();
            });
        })
        .catch(error => {
            console.error('Error initializing map:', error);
        });

    function setupMapFeatures() {
        // Add atmosphere and fog effects
        window.map.setFog({
            'color': 'rgb(186, 210, 235)',
            'high-color': 'rgb(36, 92, 223)',
            'horizon-blend': 0.02,
            'space-color': 'rgb(11, 11, 25)',
            'star-intensity': 0.6
        });

        // Add terrain source and layer
        window.map.addSource('mapbox-dem', {
            'type': 'raster-dem',
            'url': 'mapbox://mapbox.terrain-rgb',
            'tileSize': 512,
            'maxzoom': 14
        });

        window.map.setTerrain({
            'source': 'mapbox-dem',
            'exaggeration': 1.5
        });

        window.map.addLayer({
            'id': 'sky',
            'type': 'sky',
            'paint': {
                'sky-type': 'atmosphere',
                'sky-atmosphere-sun': [0.0, 90.0],
                'sky-atmosphere-sun-intensity': 15
            }
        });

        // Initialize H3 grid data
        fetch('/api/map/policy/water_management')
            .then(response => response.json())
            .then(data => {
                window.map.addSource('policy-data', {
                    type: 'geojson',
                    data: data
                });

                window.map.addLayer({
                    'id': 'policy-hexagons',
                    'type': 'fill',
                    'source': 'policy-data',
                    'paint': {
                        'fill-color': ['get', 'color'],
                        'fill-opacity': 0.6
                    }
                });

                window.map.addLayer({
                    'id': 'policy-hexagons-outline',
                    'type': 'line',
                    'source': 'policy-data',
                    'paint': {
                        'line-color': '#ffffff',
                        'line-width': 1,
                        'line-opacity': 0.5
                    }
                });

                // Dispatch event when everything is ready
                window.dispatchEvent(new Event('mapInitialized'));
            })
            .catch(error => {
                console.error('Error loading policy data:', error);
            });
    }

    function updateMapWithGeoJSON(geojsonData) {
        // Remove existing policy layers if they exist
        ['policy-hexagons', 'policy-hexagons-outline'].forEach(layerId => {
            if (window.map.getLayer(layerId)) {
                window.map.removeLayer(layerId);
            }
        });
        if (window.map.getSource('policy-data')) {
            window.map.removeSource('policy-data');
        }

        // Add new source and layers
        window.map.addSource('policy-data', {
            type: 'geojson',
            data: geojsonData
        });

        // Add fill layer
        window.map.addLayer({
            'id': 'policy-hexagons',
            'type': 'fill',
            'source': 'policy-data',
            'paint': {
                'fill-color': ['get', 'color'],
                'fill-opacity': 0.6
            }
        });

        // Add outline layer
        window.map.addLayer({
            'id': 'policy-hexagons-outline',
            'type': 'line',
            'source': 'policy-data',
            'paint': {
                'line-color': '#ffffff',
                'line-width': 1,
                'line-opacity': 0.5
            }
        });

        // Add popup on hover
        const popup = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false
        });

        window.map.on('mouseenter', 'policy-hexagons', (e) => {
            window.map.getCanvas().style.cursor = 'pointer';
            
            const properties = e.features[0].properties;
            const coordinates = e.lngLat;
            
            // Create popup content
            const html = `
                <div class="popup-content">
                    <h4>Land Degradation Metrics</h4>
                    <p>Impact Level: ${properties.impact_level}</p>
                    <p>Degradation Value: ${(properties.degradation_value * 100).toFixed(1)}%</p>
                    <p>Productivity Trend: ${properties.productivity_trend.toFixed(2)}</p>
                    <p>Soil Carbon: ${properties.soil_carbon.toFixed(1)} tons/ha</p>
                </div>
            `;

            popup.setLngLat(coordinates)
                .setHTML(html)
                .addTo(window.map);
        });

        window.map.on('mouseleave', 'policy-hexagons', () => {
            window.map.getCanvas().style.cursor = '';
            popup.remove();
        });

        // Fit map to GeoJSON bounds
        if (geojsonData.metadata?.bounds) {
            const bounds = [
                [geojsonData.metadata.bounds.left, geojsonData.metadata.bounds.bottom],
                [geojsonData.metadata.bounds.right, geojsonData.metadata.bounds.top]
            ];
            window.map.fitBounds(bounds, { padding: 50 });
        }
    }

    // Update the existing sendToMap function in chat.html to call this
    function handleMapUpdate(data) {
        if (data.success && data.data) {
            updateMapWithGeoJSON(data.data);
        } else {
            console.error('Error updating map:', data.error);
        }
    }
}); 