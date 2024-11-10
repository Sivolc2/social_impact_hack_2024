pip install --upgrade pip
pip install GDAL==$(gdal-config --version) --no-binary gdal
pip install rasterio