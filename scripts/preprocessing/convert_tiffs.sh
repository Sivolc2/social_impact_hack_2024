#!/bin/bash

# Check if input directory is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <input_directory>"
    echo "Example: $0 data/PAN_NaturalEarth_SDG15_TrendsEarth-LPD-5"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="./data/processed"

# Create data directories if they don't exist
mkdir -p "$OUTPUT_DIR"

# Run the conversion script
python tiff_converter.py --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR" --resolution 5
