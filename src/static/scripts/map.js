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

            // Wait for both style and map to be loaded
            window.map.on('load', () => {
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

                        // Dispatch event when everything is ready
                        window.dispatchEvent(new Event('mapInitialized'));
                    })
                    .catch(error => {
                        console.error('Error loading policy data:', error);
                    });
            });
        })
        .catch(error => {
            console.error('Error initializing map:', error);
        });

    // Replace the existing exportMapData function with this updated version
    function exportMapData() {
        // Get the current data from the map
        const source = map.getSource('policy-data');
        if (!source || !source._data) {
            alert('No data available to export');
            return;
        }

        const mapData = source._data.features;
        
        // Convert GeoJSON to CSV format
        const headers = ['id', 'value', 'latitude', 'longitude'];
        let csvContent = headers.join(',') + '\n';

        mapData.forEach(feature => {
            const center = feature.geometry.coordinates[0][0]; // Get the first coordinate of the hexagon
            const row = [
                feature.properties.id || '',
                feature.properties.value || '',
                center[1], // latitude
                center[0]  // longitude
            ];
            csvContent += row.join(',') + '\n';
        });
        
        // Create blob and trigger download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `map-data-export-${new Date().toISOString().split('T')[0]}.csv`;
        
        // Trigger download
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    // Move this event listener outside of the DOMContentLoaded event
    // Add it at the end of the file
    window.addEventListener('mapInitialized', () => {
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportMapData);
        } else {
            console.error('Export button not found in the DOM');
        }
    });
}); 