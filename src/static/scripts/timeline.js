document.addEventListener('DOMContentLoaded', function() {
    let isPlaying = false;
    let animationFrame;
    const playButton = document.getElementById('play-button');
    const timelineSlider = document.getElementById('timeline-slider');

    function getColorForImpact(impact) {
        const colors = {
            "critical": "#ff1744",
            "high": "#ff4444",
            "medium-high": "#ff8a65",
            "medium": "#ffbb33",
            "medium-low": "#79c879",
            "low": "#00C851",
            "minimal": "#00e676"
        };
        return colors[impact];
    }

    function updateTimelineValue(value, map) {
        if (!map || !map.getSource('policy-data')) return;
        
        timelineSlider.value = value;
        const features = map.getSource('policy-data')._data.features;
        const updatedFeatures = features.map(feature => {
            // Create wave-like pattern over time
            const timeInfluence = Math.sin(value * Math.PI / 50) * 0.3;
            const currentWeight = parseFloat(feature.properties.metrics.cost_efficiency) / 100;
            const newWeight = Math.max(0.1, Math.min(0.9, currentWeight + timeInfluence));
            
            // Determine new impact level based on weight
            let newImpact;
            if (newWeight > 0.8) newImpact = "critical";
            else if (newWeight > 0.7) newImpact = "high";
            else if (newWeight > 0.6) newImpact = "medium-high";
            else if (newWeight > 0.5) newImpact = "medium";
            else if (newWeight > 0.4) newImpact = "medium-low";
            else if (newWeight > 0.3) newImpact = "low";
            else newImpact = "minimal";

            return {
                ...feature,
                properties: {
                    ...feature.properties,
                    impact_level: newImpact,
                    color: getColorForImpact(newImpact),
                    metrics: {
                        ...feature.properties.metrics,
                        hectares_restored: Math.round(500 * newWeight),
                        communities_affected: Math.round(12 * newWeight),
                        cost_efficiency: `${Math.round(85 * newWeight)}%`
                    }
                }
            };
        });

        map.getSource('policy-data').setData({
            type: "FeatureCollection",
            features: updatedFeatures
        });
    }

    function animate(map) {
        if (isPlaying) {
            let currentValue = parseInt(timelineSlider.value);
            currentValue = (currentValue + 1) % 101;
            updateTimelineValue(currentValue, map);
            animationFrame = requestAnimationFrame(() => animate(map));
        }
    }

    // Wait for map to be initialized
    const checkMapInterval = setInterval(() => {
        const map = window.map; // Access the global map object
        if (map && map.loaded()) {
            clearInterval(checkMapInterval);

            // Add timeline control event listeners
            playButton.addEventListener('click', () => {
                isPlaying = !isPlaying;
                playButton.querySelector('.play-icon').textContent = isPlaying ? '⏸' : '▶';
                if (isPlaying) {
                    animate(map);
                } else {
                    cancelAnimationFrame(animationFrame);
                }
            });

            timelineSlider.addEventListener('input', (e) => {
                updateTimelineValue(e.target.value, map);
            });
        }
    }, 100);
}); 