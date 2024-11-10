import os
import rasterio
import numpy as np
import h3
import json
import logging
from rasterio.warp import transform
from pyproj import CRS
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_tiff_to_geojson(tiff_path: str, output_path: str, resolution: int = 5) -> None:
    """Convert a TIFF file to GeoJSON with H3 cells and save it"""
    try:
        logger.info(f"Processing {tiff_path}")
        
        with rasterio.open(tiff_path) as dataset:
            logger.info(f"TIFF CRS: {dataset.crs}")
            bounds = dataset.bounds
            logger.info(f"TIFF Bounds: {bounds}")
            
            # Read data
            data = dataset.read(1)
            height, width = data.shape
            
            # Create coordinate arrays
            rows, cols = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
            xs, ys = rasterio.transform.xy(dataset.transform, rows.flatten(), cols.flatten())
            xs = np.array(xs).reshape((height, width))
            ys = np.array(ys).reshape((height, width))
            
            # Transform to WGS84 if needed
            if str(dataset.crs).upper() != 'EPSG:4326':
                logger.info(f"Converting from {dataset.crs} to EPSG:4326")
                src_crs = dataset.crs
                dst_crs = CRS.from_epsg(4326)
                
                # Transform coordinates
                xs_flat = xs.flatten()
                ys_flat = ys.flatten()
                lngs, lats = transform(src_crs, dst_crs, xs_flat, ys_flat)
                lngs = np.array(lngs).reshape((height, width))
                lats = np.array(lats).reshape((height, width))
            else:
                lngs, lats = xs, ys
            
            # Process cells
            processed_h3_cells = {}
            features = []
            
            for i in range(height):
                for j in range(width):
                    if data[i, j] != dataset.nodata and not np.isnan(data[i, j]):
                        lng, lat = float(lngs[i, j]), float(lats[i, j])
                        
                        if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                            continue
                        
                        try:
                            h3_index = h3.latlng_to_cell(lat, lng, resolution)
                        except Exception as e:
                            continue
                        
                        if h3_index in processed_h3_cells:
                            processed_h3_cells[h3_index]['count'] += 1
                            processed_h3_cells[h3_index]['sum'] += data[i, j]
                            continue
                        
                        processed_h3_cells[h3_index] = {
                            'sum': data[i, j],
                            'count': 1
                        }
                        
                        boundary = h3.cell_to_boundary(h3_index)
                        coordinates = [[[vertex[1], vertex[0]] for vertex in boundary]]
                        coordinates[0].append(coordinates[0][0])
                        
                        feature = {
                            'type': 'Feature',
                            'geometry': {
                                'type': 'Polygon',
                                'coordinates': coordinates
                            },
                            'properties': {
                                'h3_index': h3_index,
                                'value': float(data[i, j])
                            }
                        }
                        features.append(feature)
            
            if features:
                # Calculate normalized values and colors
                min_val = min(cell['sum'] / cell['count'] for cell in processed_h3_cells.values())
                max_val = max(cell['sum'] / cell['count'] for cell in processed_h3_cells.values())
                value_range = max_val - min_val if max_val != min_val else 1.0
                
                for feature in features:
                    h3_index = feature['properties']['h3_index']
                    cell_data = processed_h3_cells[h3_index]
                    avg_value = cell_data['sum'] / cell_data['count']
                    normalized_value = (avg_value - min_val) / value_range
                    feature['properties']['normalized_value'] = normalized_value
                    feature['properties']['color'] = get_color(normalized_value)
            
            geojson = {
                'type': 'FeatureCollection',
                'features': features,
                'metadata': {
                    'source_file': os.path.basename(tiff_path),
                    'min_value': float(min_val) if features else 0,
                    'max_value': float(max_val) if features else 0,
                    'cell_count': len(features)
                }
            }
            
            # Save GeoJSON
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(geojson, f)
            
            logger.info(f"Saved GeoJSON to {output_path} with {len(features)} features")
            
    except Exception as e:
        logger.error(f"Error processing {tiff_path}: {str(e)}", exc_info=True)
        raise

def get_color(normalized_value: float) -> str:
    """Convert a normalized value (0-1) to a color hex string"""
    colors = [
        '#d32f2f',  # red for low values
        '#f57c00',  # orange
        '#ffd700',  # yellow
        '#7cb342',  # light green
        '#2e7d32'   # dark green for high values
    ]
    index = min(int(normalized_value * len(colors)), len(colors) - 1)
    return colors[index]

def process_all_tiffs(input_dir: str = './data', output_dir: str = './data/processed', resolution: int = 5):
    """Process all TIFF files in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process each TIFF file
    for tiff_file in input_path.glob('*.tif*'):
        output_file = output_path / f"{tiff_file.stem}.geojson"
        logger.info(f"Converting {tiff_file} to {output_file}")
        try:
            convert_tiff_to_geojson(str(tiff_file), str(output_file), resolution)
        except Exception as e:
            logger.error(f"Failed to convert {tiff_file}: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert TIFF files to GeoJSON with H3 cells')
    parser.add_argument('--input-dir', default='./data', help='Input directory containing TIFF files')
    parser.add_argument('--output-dir', default='./data/processed', help='Output directory for GeoJSON files')
    parser.add_argument('--resolution', type=int, default=5, help='H3 resolution (0-15)')
    
    args = parser.parse_args()
    process_all_tiffs(args.input_dir, args.output_dir, args.resolution) 