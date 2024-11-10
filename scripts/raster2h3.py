import rasterio
import h3
import numpy as np
from shapely.geometry import Point
import geopandas as gpd

def raster_to_h3(raster_path, h3_resolution):
    # Load the raster
    with rasterio.open(raster_path) as src:
        raster_data = src.read(1)  # Read the first band
        transform = src.transform

        # breakpoint()
        # Loop through each pixel in the raster
        last_seen = {}
        for row in range(src.height):
            for col in range(src.width):
                # Get the pixel value
                value = raster_data[row, col]

                # Only consider valid values (not nodata)
                if value != src.nodata:
                    # Convert pixel coordinates to geographic coordinates
                    lon, lat = transform * (col, row)

                    # Get H3 cell for the lat/lon at specified resolution
                    h3_cell = h3.latlng_to_cell(lat, lon, h3_resolution)
                    if h3_cell in last_seen.keys():
                        last_seen[h3_cell].append(value)
                        continue
                    else:
                        last_seen[h3_cell] = [value]


        # Store the result as dictionary with cell and value
        h3_cells = [
            {
                'h3_index': h3_cell,
                "year": 2015,
                "timestamp": "2015-01-01T00:00:00",
                'productivity': max(values)
            } for h3_cell, values in last_seen.items()
        ]


    return h3_cells



if __name__ == "__main__":
    import sys
    raster_path = sys.argv[1]
    h3_path = sys.argv[2]
    h3_resolution = 3 if len(sys.argv) < 4 else int(sys.argv[3])
    h3_data = raster_to_h3(raster_path, h3_resolution)
    # Convert to a GeoDataFrame for easy export and visualization
    gdf = gpd.GeoDataFrame(
        h3_data,
        geometry=gpd.points_from_xy([h3.cell_to_latlng(h['h3_index'])[1] for h in h3_data],
                                   [h3.cell_to_latlng(h['h3_index'])[0] for h in h3_data]),
        crs='EPSG:4326'
    )

    # Optional: Save to a file
    gdf.to_file(h3_path, driver="GeoJSON")
