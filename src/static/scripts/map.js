// Add map-related utility functions and event handlers here

let mapInitialized = false;

// Helper function to initialize map layers
function initializeMapLayers(map) {
    if (!mapInitialized) {
        try {
            // Add source if it doesn't exist
            if (!map.getSource('h3-hexagons')) {
                map.addSource('h3-hexagons', {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: []
                    }
                });
            }

            // Add fill layer if it doesn't exist
            if (!map.getLayer('h3-hexagons-fill')) {
                map.addLayer({
                    'id': 'h3-hexagons-fill',
                    'type': 'fill',
                    'source': 'h3-hexagons',
                    'paint': {
                        'fill-color': [
                            'case',
                            ['has', 'color'],
                            ['get', 'color'],
                            '#000000' // Default color
                        ],
                        'fill-opacity': 0.7
                    }
                });
            }

            // Add outline layer if it doesn't exist
            if (!map.getLayer('h3-hexagons-outline')) {
                map.addLayer({
                    'id': 'h3-hexagons-outline',
                    'type': 'line',
                    'source': 'h3-hexagons',
                    'paint': {
                        'line-color': '#ffffff',
                        'line-width': 1,
                        'line-opacity': 0.5
                    }
                });
            }

            // Add mouseover events
            map.on('mousemove', 'h3-hexagons-fill', (e) => {
                if (e.features.length > 0) {
                    const feature = e.features[0];
                    if (feature.properties?.metrics) {
                        let metrics = feature.properties.metrics;
                        if (typeof metrics === 'string') {
                            metrics = JSON.parse(metrics);
                        }

                        // Create popup content with all metrics and year
                        const popupContent = `
                            <div class="popup-content">
                                <h4>Year: ${feature.properties.year}</h4>
                                <p><strong>Land Degradation:</strong> ${metrics.land_degradation.toFixed(2)} index</p>
                                <p><strong>Soil Carbon:</strong> ${metrics.soil_organic_carbon.toFixed(1)} tons/ha</p>
                                <p><strong>Vegetation:</strong> ${metrics.vegetation_cover.toFixed(1)}%</p>
                                <p><strong>Biodiversity:</strong> ${metrics.biodiversity_index.toFixed(2)} index</p>
                                <p><strong>Change Rate:</strong> ${metrics.change_rate?.toFixed(2)}%/year</p>
                                <p><strong>Trend:</strong> ${metrics.trend || 'N/A'}</p>
                                <p><strong>Confidence:</strong> ${metrics.confidence_score?.toFixed(1) || 'N/A'}</p>
                            </div>
                        `;

                        window.popup
                            .setLngLat(e.lngLat)
                            .setHTML(popupContent)
                            .addTo(map);
                    }
                }
            });

            map.on('mouseleave', 'h3-hexagons-fill', () => {
                window.popup.remove();
            });

            // Add hover effect
            map.on('mouseenter', 'h3-hexagons-fill', () => {
                map.getCanvas().style.cursor = 'pointer';
            });

            map.on('mouseleave', 'h3-hexagons-fill', () => {
                map.getCanvas().style.cursor = '';
            });

            mapInitialized = true;
            console.log('Map layers initialized successfully');
        } catch (error) {
            console.error('Error initializing map layers:', error);
        }
    }
}

// Add these helper functions at the top of the file
function getMetricColorScale(metric) {
    const colorScales = {
        land_degradation: ['#2ecc71', '#e74c3c'],  // Green to Red
        soil_organic_carbon: ['#f1c40f', '#8e44ad'], // Yellow to Purple
        vegetation_cover: ['#e67e22', '#27ae60'],   // Orange to Green
        biodiversity_index: ['#3498db', '#2ecc71']  // Blue to Green
    };
    return colorScales[metric] || ['#2ecc71', '#e74c3c']; // Default to green-red
}

function getMetricMaxValue(metric) {
    const maxValues = {
        land_degradation: 1.0,
        soil_organic_carbon: 100,
        vegetation_cover: 100,
        biodiversity_index: 1.0
    };
    return maxValues[metric] || 1.0;
}

function updateLegend(metric, minValue, maxValue) {
    const legendTitle = document.getElementById('legend-title');
    const legendGradient = document.getElementById('legend-gradient-bar');
    const legendMin = document.getElementById('legend-min');
    const legendMax = document.getElementById('legend-max');
    
    if (!legendTitle || !legendGradient || !legendMin || !legendMax) {
        console.error('Legend elements not found');
        return;
    }

    // Ensure values are numbers and handle edge cases
    const numMinValue = Number(minValue) || 0;
    const numMaxValue = Number(maxValue) || 1;

    // Update title with formatted metric name
    legendTitle.textContent = metric.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

    // Update gradient colors
    const [startColor, endColor] = getMetricColorScale(metric);
    legendGradient.style.background = `linear-gradient(to right, ${startColor}, ${endColor})`;

    // Update min/max values with proper number formatting
    try {
        legendMin.textContent = numMinValue.toFixed(1);
        legendMax.textContent = numMaxValue.toFixed(1);
    } catch (error) {
        console.error('Error formatting legend values:', error);
        legendMin.textContent = '0.0';
        legendMax.textContent = '1.0';
    }
}

// Update the handleMapUpdate function
window.handleMapUpdate = async function(geojsonData) {
    try {
        console.log('Handling map update with data:', geojsonData);
        
        if (!map || !geojsonData?.features) {
            console.error('Map not initialized or invalid data');
            return;
        }

        // Wait for map style to load if it hasn't already
        if (!map.isStyleLoaded()) {
            await new Promise(resolve => map.once('style.load', resolve));
        }

        // Initialize map layers
        initializeMapLayers(map);

        // Set the dataRequested flag to true
        window.dataRequested = true;

        // Calculate min/max values for the current metric
        const currentMetric = 'land_degradation'; // Default metric
        let minValue = Infinity;
        let maxValue = -Infinity;

        geojsonData.features.forEach(feature => {
            if (feature.properties?.metrics) {
                const metrics = typeof feature.properties.metrics === 'string' 
                    ? JSON.parse(feature.properties.metrics) 
                    : feature.properties.metrics;
                
                const value = Number(metrics[currentMetric]);
                if (!isNaN(value)) {
                    minValue = Math.min(minValue, value);
                    maxValue = Math.max(maxValue, value);
                }
            }
        });

        // Handle case where no valid values were found
        if (minValue === Infinity || maxValue === -Infinity) {
            minValue = 0;
            maxValue = 1;
        }

        // Update the legend with the calculated values
        updateLegend(currentMetric, minValue, maxValue);

        // Update the source data
        const source = map.getSource('h3-hexagons');
        if (source) {
            source.setData(geojsonData);
        } else {
            console.error('h3-hexagons source still not found after initialization');
            return;
        }

        // Calculate bounds and fit map
        const bounds = new mapboxgl.LngLatBounds();
        geojsonData.features.forEach(feature => {
            if (feature.geometry && feature.geometry.coordinates) {
                feature.geometry.coordinates[0].forEach(coord => {
                    bounds.extend(coord);
                });
            }
        });

        if (!bounds.isEmpty()) {
            map.fitBounds(bounds, {
                padding: 50,
                duration: 1000,
                maxZoom: 10
            });
        }

        // Trigger initial metric update
        const metricSelect = document.getElementById('metric-select');
        if (metricSelect) {
            const event = new Event('change');
            metricSelect.dispatchEvent(event);
        }

        // Dispatch event with the new data
        window.dispatchEvent(new CustomEvent('dataLoaded', {
            detail: { data: geojsonData }
        }));

        return true;
    } catch (error) {
        console.error('Error updating map:', error);
        throw error;
    }
};

// Function to handle the "Send to Map" button click
async function sendToMap() {
    try {
        const response = await fetch('/send-to-map', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            console.error('Error from server:', data.error);
            return;
        }

        await handleMapUpdate(data);
    } catch (error) {
        console.error('Error sending to map:', error);
    }
}

// Make functions available globally
window.handleMapUpdate = handleMapUpdate;
window.sendToMap = sendToMap;
window.mapUtils = {
    fitMapToBounds: (bounds) => {
        if (window.map && bounds) {
            window.map.fitBounds(bounds, {
                padding: {top: 50, bottom: 50, left: 50, right: 50},
                duration: 1500
            });
        }
    },
    setupMapEventListeners: () => {
        if (window.map) {
            window.map.on('moveend', () => {
                console.log('Map move ended');
            });
        }
    }
};