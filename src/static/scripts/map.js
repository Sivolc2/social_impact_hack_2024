document.addEventListener('DOMContentLoaded', function() {
    const MAPBOX_TOKEN = 'pk.eyJ1Ijoic2l2b2xjMiIsImEiOiJjbTNhbmd1dWsxM21tMmlvcms2Ym01b3J1In0.Oeee5mLjSKlT-vyBX5DpGQ';
    mapboxgl.accessToken = MAPBOX_TOKEN;

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
                antialias: true,
                padding: {top: 100, bottom: 100}
            });

            // Add atmosphere and globe effects
            window.map.on('style.load', () => {
                window.map.setFog({
                    'color': 'rgb(186, 210, 235)',
                    'high-color': 'rgb(36, 92, 223)',
                    'horizon-blend': 0.02,
                    'space-color': 'rgb(11, 11, 25)',
                    'star-intensity': 0.6
                });

                // Add terrain and sky layers
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

                // Set initial pitch for globe view
                window.map.setPitch(50);

                // Load policy data
                fetch('/api/map/policy/water_management')
                    .then(response => response.json())
                    .then(policyData => {
                        // Add source for policy data
                        window.map.addSource('policy-data', {
                            type: 'geojson',
                            data: policyData
                        });

                        // Add layer for policy hexagons
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

                        // Add hover effect
                        let currentPopup = null;

                        window.map.on('mousemove', 'policy-hexagons', (e) => {
                            if (e.features.length > 0) {
                                const feature = e.features[0];
                                const metrics = feature.properties.metrics;
                                
                                if (currentPopup) {
                                    currentPopup.remove();
                                }
                                
                                const popupContent = `
                                    <strong>Impact Level:</strong> ${feature.properties.impact_level}<br>
                                    <strong>Hectares Restored:</strong> ${metrics.hectares_restored}<br>
                                    <strong>Communities Affected:</strong> ${metrics.communities_affected}<br>
                                    <strong>Cost Efficiency:</strong> ${metrics.cost_efficiency}
                                `;
                                
                                currentPopup = new mapboxgl.Popup()
                                    .setLngLat(e.lngLat)
                                    .setHTML(popupContent)
                                    .addTo(window.map);
                            }
                        });

                        window.map.on('mouseleave', 'policy-hexagons', () => {
                            if (currentPopup) {
                                currentPopup.remove();
                                currentPopup = null;
                            }
                        });
                    });
            });

            // Add zoom controls
            window.map.addControl(new mapboxgl.NavigationControl(), 'top-left');

            // Adjust pitch based on zoom level
            window.map.on('zoom', () => {
                const currentZoom = window.map.getZoom();
                if (currentZoom < 2) {
                    window.map.setPitch(50);
                } else if (currentZoom > 5) {
                    window.map.setPitch(0);
                } else {
                    const pitch = Math.max(0, 50 * (5 - currentZoom) / 3);
                    window.map.setPitch(pitch);
                }
            });
        })
        .catch(error => {
            console.error('Error initializing map:', error);
        });
}); 