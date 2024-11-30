#!/bin/bash
export REACT_APP_MAPBOX_TOKEN=$(grep REACT_APP_MAPBOX_TOKEN .env | cut -d '=' -f2)
cd frontend && npm start