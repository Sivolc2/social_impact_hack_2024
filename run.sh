#!/bin/bash

# Initialize conda for bash
eval "$(conda shell.bash hook)"

# Check if conda environment exists, create if it doesn't
if ! conda env list | grep -q "the_green"; then
    conda create -n the_green python=3.11 -y
fi

# Activate conda environment
conda activate the_green

# Install dependencies
pip install -e .
pip install -r requirements.txt

# Set the Flask app environment variable
export FLASK_APP=src/app.py
export FLASK_ENV=development

# Run the Flask application
python -m flask run --port=9001

