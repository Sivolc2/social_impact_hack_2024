export const globeStyle = {
  version: 8,
  sources: {
    'satellite': {
      type: 'raster',
      url: 'mapbox://mapbox.satellite',
      tileSize: 256
    }
  },
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: {
        'background-color': '#040D21'
      }
    },
    {
      id: 'satellite',
      type: 'raster',
      source: 'satellite',
      paint: {
        'raster-opacity': 0.9,
        'raster-contrast': 0.2,
        'raster-saturation': -0.1,
        'raster-brightness-max': 1,
        'raster-brightness-min': 0.2
      }
    }
  ],
  fog: {
    'range': [0.8, 8],
    'color': 'rgb(186, 210, 235)',
    'high-color': 'rgb(36, 92, 223)',
    'space-color': 'rgb(11, 11, 25)',
    'horizon-blend': 0.02,
    'star-intensity': 0.8
  }
}; 