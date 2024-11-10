#!/bin/bash

# Create data directories if they don't exist
mkdir -p ./data/processed

# Run the conversion script
python -m src.scripts.tiff_converter --input-dir ./data --output-dir ./data/processed --resolution 5 