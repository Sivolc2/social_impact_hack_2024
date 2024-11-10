// Initialize map and popup globally
let map;
let popup;
window.dataRequested = false;

// Initialize the map when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Get mapbox token from meta tag
    const mapboxToken = document.querySelector('meta[name="mapbox-token"]')?.content;
    
    if (!mapboxToken || mapboxToken === 'None') {
        console.error('Mapbox token not found');
        document.getElementById('map-container').innerHTML = `
            <div style="padding: 20px; color: red;">
                Error: Mapbox token not configured. Please check your environment variables.
            </div>`;
        return;
    }

    // Initialize mapboxgl map
    mapboxgl.accessToken = mapboxToken;
    
    try {
        map = new mapboxgl.Map({
            container: 'map-container',
            style: 'mapbox://styles/mapbox/satellite-v9',
            center: [0, 20],
            zoom: 2,
            pitch: 0,
            bearing: 0,
            projection: 'globe'
        });

        // Add atmosphere and stars
        map.on('style.load', () => {
            map.setFog({
                'color': 'rgb(186, 210, 235)',
                'high-color': 'rgb(36, 92, 223)',
                'horizon-blend': 0.02,
                'space-color': 'rgb(11, 11, 25)',
                'star-intensity': 0.6
            });
        });

        // Initialize popup
        popup = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false
        });

        // Wait for map to load before making it available globally
        map.on('load', () => {
            window.map = map;
            window.popup = popup;
            console.log('Map initialized successfully');
            
            initializeMapLayers(map);
            
            // Load initial data
            loadInitialData();
            
            // Dispatch initialization event
            window.dispatchEvent(new Event('mapInitialized'));
        });

    } catch (error) {
        console.error('Error initializing map:', error);
    }
});

// Add map-related utility functions and event handlers here

let mapInitialized = false;

// Helper function to initialize map layers
function initializeMapLayers(map) {
    if (!mapInitialized) {
        try {
            // Add source if it doesn't exist - start with empty features
            if (!map.getSource('h3-hexagons')) {
                map.addSource('h3-hexagons', {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: []  // Start empty
                    }
                });
            }

            // Check if layers exist before adding
            const layers = ['h3-hexagons-fill', 'h3-hexagons-outline'];
            layers.forEach(layerId => {
                if (map.getLayer(layerId)) {
                    map.removeLayer(layerId);
                }
            });

            // Add fill layer with complete transparency by default
            if (!map.getLayer('h3-hexagons-fill')) {
                map.addLayer({
                    'id': 'h3-hexagons-fill',
                    'type': 'fill',
                    'source': 'h3-hexagons',
                    'paint': {
                        'fill-color': [
                            'case',
                            ['all',
                                ['has', 'color'],
                                ['!=', ['get', 'color'], null],
                                ['get', 'visible']
                            ],
                            ['get', 'color'],
                            'rgba(0,0,0,0)'
                        ],
                        'fill-opacity': 0  // Start completely transparent
                    }
                });
            }

            // Add outline layer with complete transparency by default
            if (!map.getLayer('h3-hexagons-outline')) {
                map.addLayer({
                    'id': 'h3-hexagons-outline',
                    'type': 'line',
                    'source': 'h3-hexagons',
                    'paint': {
                        'line-color': '#ffffff',
                        'line-width': 1,
                        'line-opacity': 0  // Start completely transparent
                    }
                });
            }

            mapInitialized = true;
            console.log('Map layers initialized with empty data');
        } catch (error) {
            console.error('Error initializing map layers:', error);
        }
    }
}

// Add these helper functions at the top of the file
function getMetricColorScale(metric) {
    const colorScales = {
        incident_count: ['#ffffcc', '#800026'],      // Yellow to Dark Red
        deaths_total: ['#ffffcc', '#800026'],        // Yellow to Dark Red
        deaths_civilians: ['#ffffcc', '#800026'],    // Yellow to Dark Red
        deaths_military: ['#ffffcc', '#800026'],     // Yellow to Dark Red
        land_degradation: ['#2ecc71', '#e74c3c'],    // Green to Red
        soil_organic_carbon: ['#fff7fb', '#023858'], // White to Dark Blue
        vegetation_cover: ['#ffffe5', '#004529'],    // Light Yellow to Dark Green
        biodiversity_index: ['#ffffcc', '#800026']   // Yellow to Dark Red
    };
    return colorScales[metric] || ['#ffffcc', '#800026']; // Default color scale
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

function updateLegend(metricId, minValue, maxValue) {
    const legendTitle = document.getElementById('legend-title');
    const legendGradient = document.getElementById('legend-gradient-bar');
    const legendMin = document.getElementById('legend-min');
    const legendMax = document.getElementById('legend-max');
    
    if (!legendTitle || !legendGradient || !legendMin || !legendMax) {
        console.warn('Legend elements not found, skipping update');
        return;
    }

    // Format metric name
    const formattedName = metricId
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

    // Update title
    legendTitle.textContent = formattedName;

    // Get color scale
    const [startColor, endColor] = getMetricColorScale(metricId);
    
    // Update gradient
    legendGradient.style.background = `linear-gradient(to right, ${startColor}, ${endColor})`;

    // Format values
    const formatValue = (val) => {
        if (typeof val !== 'number') return '0';
        return val.toFixed(1);
    };

    // Update min/max labels
    legendMin.textContent = formatValue(minValue);
    legendMax.textContent = formatValue(maxValue);
}

// Update the handleMapUpdate function
window.handleMapUpdate = async function(geojsonData) {
    try {
        // Wait for map to be initialized
        if (!map || !map.loaded()) {
            console.log('Waiting for map to initialize...');
            await new Promise(resolve => map.once('load', resolve));
        }

        if (!geojsonData?.features) {
            console.error('Invalid data format received');
            return;
        }

        console.log(`Processing ${geojsonData.features.length} features...`);

        // Initialize map layers if needed
        initializeMapLayers(map);

        // Store the full dataset
        window.currentData = geojsonData;

        // Update the source data
        const source = map.getSource('h3-hexagons');
        if (source) {
            source.setData(geojsonData);
        }

        // Calculate and fit bounds if needed
        if (geojsonData.features.length > 0) {
            const bounds = new mapboxgl.LngLatBounds();
            geojsonData.features.forEach(feature => {
                if (feature.geometry?.coordinates) {
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
        }

        // Dispatch event with the new data
        window.dispatchEvent(new CustomEvent('dataLoaded', {
            detail: { data: geojsonData }
        }));

        // Initialize first metric
        const firstMetric = geojsonData.features[0]?.properties?.metrics;
        if (firstMetric) {
            const metrics = typeof firstMetric === 'string' 
                ? JSON.parse(firstMetric) 
                : firstMetric;
            const defaultMetric = Object.keys(metrics)[0] || 'incident_count';
            updateMapMetric(defaultMetric);
        }

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
        
        // Check for the correct data structure
        if (data.status === 'success' && data.datasets) {
            // Use loadMultipleDatasets instead of handleMapUpdate
            await loadMultipleDatasets(data.datasets);
            console.log('Data sent to map successfully');
        } else if (data.error) {
            console.error('Error from server:', data.error);
        } else {
            console.error('Invalid data format received from server');
        }
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

// Add this function to handle multiple datasets
async function loadMultipleDatasets(datasets) {
    try {
        if (!datasets || datasets.length === 0) {
            console.warn('No datasets provided to load');
            return;
        }

        // Process and combine all datasets but don't display them yet
        const allFeatures = datasets.reduce((acc, dataset) => {
            if (dataset.data?.features) {
                const features = dataset.data.features.map(feature => ({
                    ...feature,
                    properties: {
                        ...feature.properties,
                        dataset_id: dataset.id,
                        visible: false,
                        color: 'rgba(0,0,0,0)'
                    }
                }));
                return [...acc, ...features];
            }
            return acc;
        }, []);

        // Store the data globally without displaying it
        window.currentData = {
            type: 'FeatureCollection',
            features: allFeatures,
            metadata: {
                ...datasets[0]?.data?.metadata,
                dataset_count: datasets.length,
                feature_count: allFeatures.length
            }
        };

        // Initialize empty source
        const source = map.getSource('h3-hexagons');
        if (source) {
            source.setData({
                type: 'FeatureCollection',
                features: []  // Start with empty features
            });
        }

        // Only center on region if data was explicitly requested via "Send to Map"
        if (window.dataRequested && allFeatures.length > 0) {
            const bounds = new mapboxgl.LngLatBounds();
            
            allFeatures.forEach(feature => {
                if (feature.geometry?.coordinates) {
                    // For polygon features
                    if (Array.isArray(feature.geometry.coordinates[0])) {
                        feature.geometry.coordinates[0].forEach(coord => {
                            bounds.extend(coord);
                        });
                    }
                }
            });

            if (!bounds.isEmpty()) {
                map.fitBounds(bounds, {
                    padding: { top: 50, bottom: 50, left: 50, right: 50 },
                    duration: 1000,
                    maxZoom: 10
                });
            }
            
            // Reset the flag after centering
            window.dataRequested = false;
        }

        console.log(`Loaded ${allFeatures.length} features from ${datasets.length} datasets (ready to display)`);
    } catch (error) {
        console.error('Error in loadMultipleDatasets:', error);
    }
}

// Update the loadMapData function
window.loadMapData = async function(shouldZoom = true) {
    try {
        if (!map || !map.loaded()) {
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Map initialization timeout'));
                }, 10000);  // 10-second timeout

                map.once('load', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            });
        }

        const response = await fetch('/api/datasets/map');
        if (!response.ok) {
            throw new Error(`Failed to load datasets: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.datasets) {
            await loadMultipleDatasets(data.datasets);
            console.log('Map data loaded successfully');
            return true;
        } else {
            throw new Error('No datasets available');
        }
    } catch (error) {
        console.error('Error loading map data:', error);
        // Propagate error for UI handling
        throw error;
    }
};

// Update the updateMapMetric function
function updateMapMetric(metricId) {
    if (!window.currentData?.features) {
        console.error('No data available to update metrics');
        return;
    }

    // If no metric selected, clear the map
    if (!metricId) {
        const source = map.getSource('h3-hexagons');
        if (source) {
            source.setData({
                type: 'FeatureCollection',
                features: []
            });
        }
        return;
    }

    // Calculate min/max values for the metric
    let minValue = Infinity;
    let maxValue = -Infinity;

    // Filter features that have the selected metric and calculate min/max
    const validFeatures = window.currentData.features.filter(feature => {
        const metrics = typeof feature.properties.metrics === 'string' 
            ? JSON.parse(feature.properties.metrics) 
            : feature.properties.metrics;
        
        if (metrics && metrics[metricId] !== undefined) {
            const value = parseFloat(metrics[metricId]);
            if (!isNaN(value)) {
                minValue = Math.min(minValue, value);
                maxValue = Math.max(maxValue, value);
                return true;
            }
        }
        return false;
    });

    // If no valid features found, clear the map
    if (validFeatures.length === 0) {
        const source = map.getSource('h3-hexagons');
        if (source) {
            source.setData({
                type: 'FeatureCollection',
                features: []
            });
        }
        return;
    }

    // Update features with colors for the selected metric
    const displayFeatures = validFeatures.map(feature => {
        const metrics = typeof feature.properties.metrics === 'string' 
            ? JSON.parse(feature.properties.metrics) 
            : feature.properties.metrics;
        
        const value = parseFloat(metrics[metricId]);
        const normalizedValue = (maxValue === minValue) 
            ? 0.5 
            : (value - minValue) / (maxValue - minValue);
        
        const [startColor, endColor] = getMetricColorScale(metricId);
        const color = interpolateColor(startColor, endColor, normalizedValue);

        return {
            ...feature,
            properties: {
                ...feature.properties,
                visible: true,
                color: color
            }
        };
    });

    // Update the source with only the relevant features
    const source = map.getSource('h3-hexagons');
    if (source) {
        source.setData({
            type: 'FeatureCollection',
            features: displayFeatures
        });
    }

    // Update layer opacity to make features visible
    if (map.getLayer('h3-hexagons-fill')) {
        map.setPaintProperty('h3-hexagons-fill', 'fill-opacity', 0.7);
    }
    if (map.getLayer('h3-hexagons-outline')) {
        map.setPaintProperty('h3-hexagons-outline', 'line-opacity', 0.5);
    }

    // Update legend
    updateLegend(metricId, minValue, maxValue);
}

// Add helper function for color interpolation
function interpolateColor(startColor, endColor, value) {
    // Ensure value is between 0 and 1
    const ratio = Math.min(Math.max(value || 0, 0), 1);
    
    try {
        // Validate input colors
        if (!isValidHexColor(startColor) || !isValidHexColor(endColor)) {
            console.error('Invalid color values:', { startColor, endColor });
            return '#ff0000';  // Return red for invalid colors
        }

        const start = hexToRgb(startColor);
        const end = hexToRgb(endColor);
        
        if (!start || !end) {
            console.error('Failed to parse colors:', { startColor, endColor });
            return '#ff0000';
        }
        
        const r = Math.round(start.r + (end.r - start.r) * ratio);
        const g = Math.round(start.g + (end.g - start.g) * ratio);
        const b = Math.round(start.b + (end.b - start.b) * ratio);
        
        const hex = rgbToHex(r, g, b);
        return isValidHexColor(hex) ? hex : '#ff0000';
    } catch (error) {
        console.error('Error interpolating color:', error);
        return '#ff0000';  // Return red for errors
    }
}

// Add color validation function
function isValidHexColor(color) {
    if (typeof color !== 'string') return false;
    color = color.replace(/^#/, '');
    return /^[0-9A-F]{6}$/i.test(color) || /^[0-9A-F]{3}$/i.test(color);
}

// Update hexToRgb with better validation
function hexToRgb(hex) {
    if (!hex || typeof hex !== 'string') {
        return null;
    }

    // Remove # if present
    hex = hex.replace(/^#/, '');

    // Validate hex format
    if (!/^[0-9A-F]{3}$/i.test(hex) && !/^[0-9A-F]{6}$/i.test(hex)) {
        return null;
    }

    // Handle both 3-digit and 6-digit hex codes
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }

    const result = /^([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return null;

    return {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    };
}

// Update rgbToHex with better validation
function rgbToHex(r, g, b) {
    try {
        // Ensure values are numbers and in valid range
        r = Math.max(0, Math.min(255, Math.round(Number(r) || 0)));
        g = Math.max(0, Math.min(255, Math.round(Number(g) || 0)));
        b = Math.max(0, Math.min(255, Math.round(Number(b) || 0)));
        
        const hex = ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        return `#${hex}`;
    } catch (error) {
        console.error('Error converting RGB to hex:', error);
        return '#ff0000';
    }
}

// Add function to load initial data
async function loadInitialData() {
    try {
        // Get all available datasets from the API
        const response = await fetch('/api/datasets/map');
        if (!response.ok) {
            throw new Error(`Failed to load datasets: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.datasets) {
            // Store the data but don't display it
            window.currentData = {
                type: 'FeatureCollection',
                features: [],  // Start with empty features
                metadata: data.datasets[0]?.data?.metadata || {}
            };

            // Ensure the source starts empty
            const source = map.getSource('h3-hexagons');
            if (source) {
                source.setData({
                    type: 'FeatureCollection',
                    features: []
                });
            }

            console.log('Initial data loaded and stored (not displayed)');
        } else {
            throw new Error('No datasets available');
        }
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}