import React, { useEffect, useRef } from 'react';
import DeckGL from '@deck.gl/react';
import { _GlobeView as GlobeView } from '@deck.gl/core';
import { Map as MapGL } from 'react-map-gl';
import { globeStyle } from '../utils/mapStyle';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;
if (!MAPBOX_TOKEN) {
    console.error('Mapbox token is missing. Please check your .env file');
  }

console.log('MAPBOX_TOKEN:', process.env.REACT_APP_MAPBOX_TOKEN ? 'Present' : 'Missing');

function Map() {
  const mapRef = useRef(null);

  const INITIAL_VIEW_STATE = {
    latitude: 23.4162,
    longitude: 15.3242,
    zoom: 2.5,
    pitch: 0,
    bearing: 0,
    minZoom: 0,
    maxZoom: 20
  };

  useEffect(() => {
    if (mapRef.current) {
      const map = mapRef.current.getMap();
      map.on('style.load', () => {
        map.setFog({
          'range': [0.8, 8],
          'color': 'rgb(186, 210, 235)',
          'high-color': 'rgb(36, 92, 223)',
          'space-color': 'rgb(11, 11, 25)',
          'horizon-blend': 0.02,
          'star-intensity': 0.8
        });
      });
    }
  }, []);

  return (
    <div className="absolute inset-0 bg-[#040D21]">
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={{
        //   inertia: true,
          scrollZoom: {
            speed: 10,
            smooth: true
          },
          dragRotate: true,
          touchRotate: true,
          keyboard: true,
          dragPan: true,
          touchZoom: true,
          doubleClickZoom: true,
          dragSpeed: 1.5,
          touchZoomRotate: {
            speed: 2
          }
        }}
        views={[
          new GlobeView({
            id: 'globe',
            resolution: 1,
            atmosphereEnabled: true,
            atmosphereStrength: 2,
            atmosphereColor: [25, 35, 68],
            backgroundColor: '#040D21'
          })
        ]}
      >
        <MapGL
          ref={mapRef}
          mapboxAccessToken={MAPBOX_TOKEN}
          mapStyle={globeStyle}
          preventStyleDiffing
          projection="globe"
          attributionControl={false}
          logoPosition="bottom-right"
        />
      </DeckGL>
    </div>
  );
}

export default Map; 