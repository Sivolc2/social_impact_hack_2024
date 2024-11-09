#!/bin/bash

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