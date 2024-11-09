#!/bin/bash

# Initialize conda for the shell
eval "$(conda shell.bash hook)"

# Activate conda environment
conda activate the_green

# Add the current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Set Flask environment variables
export FLASK_APP=src/app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run Flask application
flask run --host=0.0.0.0 --port=9001