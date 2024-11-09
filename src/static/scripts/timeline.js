document.addEventListener('DOMContentLoaded', function() {
    const slider = document.getElementById('timeline-slider');
    const playButton = document.getElementById('play-button');
    let isPlaying = false;
    let animationFrame;
    let currentSpeed = 50; // Default to 10x speed (1000ms / 20 = 50ms)
    const customSpeedInput = document.getElementById('custom-speed');

    // Function to update map data based on slider value
    async function updateMapData(timestamp) {
        try {
            if (!window.map) {
                console.log('Map not initialized yet');
                return;
            }

            const response = await fetch(`/api/map/policy/water_management?timestamp=${timestamp}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            
            const source = window.map.getSource('policy-data');
            if (source) {
                source.setData(data);
                window.map.triggerRepaint();
            }
        } catch (error) {
            console.error('Error updating map data:', error);
        }
    }

    // Initialize the timeline
    function initializeTimeline() {
        slider.value = 0;
        updateMapData(new Date(2024, 0, 1).toISOString());
    }

    // Play/pause functionality
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

    // Animation function
    function animate() {
        if (!isPlaying) return;
        
        let value = parseInt(slider.value);
        value = (value + 1) % 101;
        slider.value = value;
        
        const date = new Date(2024, 0, 1);
        date.setDate(date.getDate() + (value * 3.65));
        
        updateMapData(date.toISOString());
        
        setTimeout(() => {
            animationFrame = requestAnimationFrame(animate);
        }, currentSpeed);
    }

    // Update on slider manual change
    if (slider) {
        slider.addEventListener('input', function() {
            const date = new Date(2024, 0, 1);
            date.setDate(date.getDate() + (slider.value * 3.65));
            updateMapData(date.toISOString());
        });
    }

    // Speed control functionality
    document.querySelectorAll('.speed-button').forEach(button => {
        button.addEventListener('click', function() {
            const speed = parseInt(this.dataset.speed);
            currentSpeed = speed;
            
            // Update custom speed input to match button speed
            if (customSpeedInput) {
                customSpeedInput.value = Math.round(1000 / speed);
            }
            
            // Update active state
            document.querySelectorAll('.speed-button').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
        });
    });

    // Add custom speed input handler
    if (customSpeedInput) {
        customSpeedInput.addEventListener('change', function() {
            let speedMultiplier = parseFloat(this.value);
            
            // Validate input
            if (speedMultiplier < 1) speedMultiplier = 1;
            if (speedMultiplier > 100) speedMultiplier = 100;
            
            // Update input value to validated number
            this.value = speedMultiplier;
            
            // Convert multiplier to milliseconds (1000ms base divided by multiplier)
            currentSpeed = Math.round(1000 / speedMultiplier);
            
            // Update button states
            document.querySelectorAll('.speed-button').forEach(btn => {
                btn.classList.remove('active');
            });
        });
    }

    // Wait for map to be initialized
    window.addEventListener('mapInitialized', initializeTimeline);
});