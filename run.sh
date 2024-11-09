#!/bin/bash

# Install the package in development mode if not already installed
pip install -e .

# Set the Flask app environment variable
export FLASK_APP=src.app
export FLASK_ENV=development

# Run the Flask application
flask run