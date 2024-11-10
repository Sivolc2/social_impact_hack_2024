// Add map-related utility functions and event handlers here
// The map is already initialized in map.html

// Example utility function
function fitMapToBounds(bounds) {
    if (window.map && bounds) {
        window.map.fitBounds(bounds, {
            padding: {top: 50, bottom: 50, left: 50, right: 50},
            duration: 1500,
            maxZoom: 10,
            minZoom: 2
        });
    }
}

// Example event handler
function setupMapEventListeners() {
    if (window.map) {
        window.map.on('moveend', () => {
            console.log('Map move ended');
        });
    }
}

// Make utility functions available globally
window.mapUtils = {
    fitMapToBounds,
    setupMapEventListeners
}; 