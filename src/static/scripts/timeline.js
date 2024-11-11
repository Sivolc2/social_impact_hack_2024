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

    // Hardcoded time range
    let timeRange = {
        start: 2015,
        end: 2024
    };

    // Available years array
    const availableYears = Array.from(
        {length: timeRange.end - timeRange.start + 1}, 
        (_, i) => timeRange.start + i
    );

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

    function getYearFromSliderValue(value) {
        // Calculate year based on slider value (0-100)
        const yearIndex = Math.floor((value / 100) * (availableYears.length - 1));
        return availableYears[yearIndex];
    }

    function filterAndDisplayYear(year) {
        if (!currentData?.features) {
            console.error('No data available to filter');
            return;
        }

        // Convert year to number for strict comparison
        const targetYear = parseInt(year);
        console.log(`Filtering for year: ${targetYear}`);

        // Filter features for the selected year
        const filteredFeatures = currentData.features.filter(feature => {
            const featureYear = parseInt(feature.properties.year);
            return featureYear === targetYear;
        });

        // Create new GeoJSON with filtered features
        const filteredData = {
            type: 'FeatureCollection',
            features: filteredFeatures,
            metadata: currentData.metadata
        };

        console.log(`Filtered to ${filteredFeatures.length} features for year ${targetYear}`);

        // Update the map source directly
        const source = window.map.getSource('h3-hexagons');
        if (source) {
            source.setData(filteredData);
        } else {
            console.error('Map source not found: h3-hexagons');
        }
    }

    function animate() {
        if (!isPlaying) return;

        const currentValue = parseInt(slider.value);
        const currentYear = getYearFromSliderValue(currentValue);
        
        console.log(`Animating: Current year ${currentYear}, Value ${currentValue}`);
        
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
            // Smoothly update slider value
            const nextValue = (nextIndex / (availableYears.length - 1)) * 100;
            slider.value = nextValue;
            
            // Display the next year
            const nextYear = availableYears[nextIndex];
            console.log(`Advancing to year ${nextYear}`);
            filterAndDisplayYear(nextYear);
            
            // Schedule next frame
            setTimeout(() => {
                if (isPlaying) {
                    requestAnimationFrame(animate);
                }
            }, currentSpeed);
        }
    }

    // Initialize timeline
    updateTimelineLabels();
    
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
            console.log('New data received:', e.detail.data);
            currentData = e.detail.data;
            
            // Reset to start
            slider.value = 0;
            filterAndDisplayYear(timeRange.start);
        }
    });

    // Add speed control functionality
    const speedButtons = document.querySelectorAll('.speed-button');
    const customSpeedInput = document.getElementById('custom-speed');
    
    function updateSpeed(newSpeed) {
        currentSpeed = 1000 / newSpeed; // Convert multiplier to milliseconds
        console.log(`Animation speed updated: ${newSpeed}x (${currentSpeed}ms)`);
    }

    // Add speed button listeners
    speedButtons.forEach(button => {
        button.addEventListener('click', function() {
            speedButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            const speed = parseInt(this.dataset.speed);
            updateSpeed(speed);
        });
    });

    // Add custom speed input listener
    if (customSpeedInput) {
        customSpeedInput.addEventListener('change', function() {
            const speed = parseInt(this.value);
            if (!isNaN(speed) && speed > 0) {
                speedButtons.forEach(btn => btn.classList.remove('active'));
                updateSpeed(speed);
            }
        });
    }
});