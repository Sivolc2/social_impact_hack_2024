document.addEventListener('DOMContentLoaded', function() {
    console.log('Timeline script loaded');
    
    const slider = document.getElementById('timeline-slider');
    const playButton = document.getElementById('play-button');
    let isPlaying = false;
    let animationFrame;
    let currentSpeed = 500;
    let isInitialLoad = true;
    let currentData = null;
    let timeRangeInitialized = false;
    let availableYears = [];

    // Default time range (will be updated when data is loaded)
    let timeRange = {
        start: 2001,
        end: 2015
    };

    function updateTimelineLabels() {
        const labels = document.querySelector('.timeline-labels');
        if (labels) {
            labels.innerHTML = `
                <span>${timeRange.start}</span>
                <span>${timeRange.end}</span>
            `;
            console.log(`Updated timeline labels: ${timeRange.start} - ${timeRange.end}`);
        }
    }

    function updateTimeRangeFromData(data) {
        if (!data?.features?.length) {
            console.error('No features found in data');
            return;
        }

        // Find unique years from features
        const years = new Set();
        data.features.forEach(feature => {
            if (feature.properties?.year) {
                years.add(parseInt(feature.properties.year));
            }
        });

        // Convert to array and sort
        availableYears = Array.from(years).sort((a, b) => a - b);
        
        if (availableYears.length > 0) {
            timeRange.start = availableYears[0];
            timeRange.end = availableYears[availableYears.length - 1];
            console.log(`Timeline range updated: ${timeRange.start} - ${timeRange.end}`);
            console.log('Available years:', availableYears);
            
            updateTimelineLabels();
            timeRangeInitialized = true;

            // Set initial year
            filterAndDisplayYear(timeRange.start);
        }
    }

    function getYearFromSliderValue(value) {
        if (availableYears.length === 0) return timeRange.start;
        
        const index = Math.min(
            Math.floor((value / 100) * (availableYears.length - 1)),
            availableYears.length - 1
        );
        return availableYears[index];
    }

    function filterAndDisplayYear(year) {
        if (!currentData?.features) {
            console.error('No data available to filter');
            return;
        }

        // Filter features for the selected year
        const filteredFeatures = currentData.features.filter(feature => 
            feature.properties.year === year
        );

        // Create new GeoJSON with filtered features
        const filteredData = {
            type: 'FeatureCollection',
            features: filteredFeatures,
            metadata: currentData.metadata
        };

        console.log(`Filtered to ${filteredFeatures.length} features for year ${year}`);

        // Update the map source directly
        const source = window.map.getSource('h3-hexagons');
        if (source) {
            source.setData(filteredData);
        }
    }

    function animate() {
        if (!isPlaying) return;

        const value = parseInt(slider.value);
        const currentYear = getYearFromSliderValue(value);
        
        // Check if we've reached the end
        if (currentYear >= timeRange.end) {
            isPlaying = false;
            playButton.querySelector('.play-icon').textContent = '▶';
            slider.value = 0;
            filterAndDisplayYear(timeRange.start);
            return;
        }

        // Calculate next value
        const currentIndex = availableYears.indexOf(currentYear);
        const nextIndex = currentIndex + 1;
        if (nextIndex < availableYears.length) {
            const nextValue = (nextIndex / (availableYears.length - 1)) * 100;
            slider.value = nextValue;
            filterAndDisplayYear(availableYears[nextIndex]);
            
            setTimeout(() => {
                if (isPlaying) {
                    animationFrame = requestAnimationFrame(animate);
                }
            }, currentSpeed);
        }
    }

    // Add event listeners
    if (playButton) {
        playButton.addEventListener('click', function() {
            isPlaying = !isPlaying;
            playButton.querySelector('.play-icon').textContent = isPlaying ? '⏸' : '▶';
            
            if (isPlaying) {
                animate();
            } else {
                cancelAnimationFrame(animationFrame);
            }
        });
    }

    if (slider) {
        slider.addEventListener('input', function() {
            const year = getYearFromSliderValue(this.value);
            filterAndDisplayYear(year);
        });
    }

    // Handle new data loading
    window.addEventListener('dataLoaded', function(e) {
        if (e.detail?.data) {
            currentData = e.detail.data;
            timeRangeInitialized = false;
            updateTimeRangeFromData(currentData);
            
            // Reset to start
            slider.value = 0;
            filterAndDisplayYear(timeRange.start);
        }
    });
});