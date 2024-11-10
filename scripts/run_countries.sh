#!/bin/bash

# Set input file path
INPUT_FILE="preprocessing/data/GEDEvent_v24_1.csv"

# Create output directory if it doesn't exist
mkdir -p data/countries

# Array of resolutions to process
RESOLUTIONS=(6)

# Array of countries
COUNTRIES=("Panama" "Malawi" "Ethiopia")

# Process each country at different resolutions
for country in "${COUNTRIES[@]}"; do
    # Convert country name to lowercase using tr
    country_lower=$(echo "$country" | tr '[:upper:]' '[:lower:]')
    
    for res in "${RESOLUTIONS[@]}"; do
        echo "Processing $country at resolution $res..."
        python scripts/convert_ged_to_h3.py \
            --input "$INPUT_FILE" \
            --output "data/countries/ged_h3_${country_lower}_res${res}.geojson" \
            --resolution "$res" \
            --country "$country"
    done
done

echo "Processing complete! Files are saved in data/countries/"