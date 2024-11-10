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
}); 