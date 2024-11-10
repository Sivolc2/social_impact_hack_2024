#!/bin/bash

# Source environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Validate Mapbox token
if [ -z "$MAPBOX_API_KEY" ] || [ "$MAPBOX_API_KEY" = "your_actual_mapbox_token_here" ]; then
    echo "Error: Invalid MAPBOX_API_KEY. Please set a valid token in your .env file"
    exit 1
fi

# Initialize conda for the shell
eval "$(conda shell.bash hook)"

# Create conda environment if it doesn't exist
conda create -n the_green python=3.10 -y || true

# Activate environment
conda activate the_green

# Install pip dependencies
pip install --upgrade pip
pip install -e . --no-cache-dir

# Add the project root to PYTHONPATH
echo "export PYTHONPATH=$PYTHONPATH:$(pwd)" >> ~/.bashrc
echo "export PYTHONPATH=$PYTHONPATH:$(pwd)" >> ~/.zshrc

source ~/.env
source ./.secrets
