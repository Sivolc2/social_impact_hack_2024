document.addEventListener('DOMContentLoaded', function() {
    console.log('Timeline script loaded');
    
    const slider = document.getElementById('timeline-slider');
    const playButton = document.getElementById('play-button');
    let isPlaying = false;
    let animationFrame;
    let currentSpeed = 500;
    const customSpeedInput = document.getElementById('custom-speed');
    let isInitialLoad = true;
    let currentData = null;
    let timeRangeInitialized = false;
    let availableYears = [];

    // Default time range (will be updated when data is loaded)
    let timeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2025-01-01')
    };

    function updateTimelineLabels() {
        const labels = document.querySelector('.timeline-labels');
        if (labels) {
            labels.innerHTML = `
                <span>${timeRange.start.getFullYear()}</span>
                <span>${timeRange.end.getFullYear()}</span>
            `;
            console.log(`Updated timeline labels: ${timeRange.start.getFullYear()} - ${timeRange.end.getFullYear()}`);
        }
    }

    function updateTimeRangeFromData(data) {
        if (timeRangeInitialized) return;
        
        if (!data?.features?.length) return;

        // First pass: find unique years
        const years = new Set();
        data.features.forEach(feature => {
            if (feature.properties?.year) {
                years.add(feature.properties.year);
            } else if (feature.properties?.timestamp) {
                const timestamp = new Date(feature.properties.timestamp);
                years.add(timestamp.getFullYear());
            }
        });

        // Convert to array and sort
        availableYears = Array.from(years).sort((a, b) => a - b);
        
        if (availableYears.length > 0) {
            timeRange.start = new Date(availableYears[0], 0, 1);
            timeRange.end = new Date(availableYears[availableYears.length - 1], 11, 31);
            console.log(`Timeline range updated: ${timeRange.start.getFullYear()} - ${timeRange.end.getFullYear()}`);
            console.log(`Available years:`, availableYears);
            
            updateTimelineLabels();
            timeRangeInitialized = true;
        } else {
            console.error('No valid years found in data');
        }
    }

    function getYearFromSliderValue(value) {
        if (availableYears.length === 0) return timeRange.start.getFullYear();
        
        const index = Math.min(
            Math.floor((value / 100) * (availableYears.length - 1)),
            availableYears.length - 1
        );
        return availableYears[index];
    }

    async function updateMapData(year) {
        try {
            if (!currentData) {
                console.log('Fetching initial data for year:', year);
                const response = await fetch(`/api/map/policy/water_management?timestamp=${new Date(year, 0, 1).toISOString()}`);
                if (!response.ok) throw new Error('Network response was not ok');
                currentData = await response.json();
                console.log('Loaded data with', currentData.features.length, 'features');
                
                updateTimeRangeFromData(currentData);
            }

            // Filter features based on year only
            const filteredData = {
                ...currentData,
                features: currentData.features.filter(feature => {
                    return feature.properties.year === year;
                })
            };

            console.log(`Filtered to ${filteredData.features.length} features for year ${year}`);

            if (window.handleMapUpdate && filteredData.features.length > 0) {
                await window.handleMapUpdate(filteredData);
            } else {
                console.error('No features found for year:', year);
            }
        } catch (error) {
            console.error('Error updating map data:', error);
        }
    }

    function animate() {
        if (!isPlaying) return;

        let value = parseInt(slider.value);
        const currentYear = getYearFromSliderValue(value);
        
        console.log(`Current value: ${value}, Current year: ${currentYear}`);

        // Check if we've reached the end
        if (currentYear >= timeRange.end.getFullYear()) {
            isPlaying = false;
            playButton.querySelector('.play-icon').textContent = '▶';
            slider.value = 0;
            updateMapData(timeRange.start.getFullYear());
            return;
        }

        // Calculate next value to show next year
        const currentIndex = availableYears.indexOf(currentYear);
        const nextIndex = currentIndex + 1;
        if (nextIndex < availableYears.length) {
            value = (nextIndex / (availableYears.length - 1)) * 100;
            slider.value = value;
            updateMapData(availableYears[nextIndex])
                .then(() => {
                    if (isPlaying) {
                        setTimeout(() => {
                            animationFrame = requestAnimationFrame(animate);
                        }, currentSpeed);
                    }
                });
        }
    }

    function initializeTimeline() {
        console.log('Initializing timeline');
        
        if (isInitialLoad) {
            isInitialLoad = false;
            return;
        }

        slider.value = 0;
        updateMapData(new Date(timeRange.start.getFullYear(), 0, 1).toISOString());
    }

    // Add event listeners
    if (playButton) {
        playButton.addEventListener('click', function() {
            console.log('Play button clicked, current state:', isPlaying);
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
            const currentYear = getYearFromSliderValue(this.value);
            const date = new Date(currentYear, 0, 1);
            
            console.log('Slider changed to year:', currentYear);
            updateMapData(date.toISOString());
        });
    }

    // Initialize timeline when map is ready
    window.addEventListener('mapInitialized', initializeTimeline);

    // Add handler for new data
    window.addEventListener('dataLoaded', function(e) {
        if (e.detail?.data) {
            currentData = e.detail.data;
            timeRangeInitialized = false;
            updateTimeRangeFromData(currentData);
            // Reset to start of new range
            slider.value = 0;
            updateMapData(new Date(timeRange.start.getFullYear(), 0, 1).toISOString());
        }
    });
});