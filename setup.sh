#!/bin/bash

# Initialize conda for the shell
eval "$(conda shell.bash hook)"

# Activate environment
conda activate the_green

# Install the package in development mode
pip install -e .

# Add the project root to PYTHONPATH (optional now, but keeping for safety)
echo "export PYTHONPATH=$PYTHONPATH:$(pwd)" >> ~/.bashrc
echo "export PYTHONPATH=$PYTHONPATH:$(pwd)" >> ~/.zshrc