#!/bin/bash

# Initialize conda for the shell
eval "$(conda shell.bash hook)"

# Remove the environment if it exists
conda deactivate
conda env remove -n the_green -y

# Clean pip cache
pip cache purge

# Remove any build artifacts
rm -rf build/
rm -rf dist/
rm -rf *.egg-info
rm -rf src/*.egg-info 