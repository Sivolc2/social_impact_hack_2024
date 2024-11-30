#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up local development environment...${NC}"

# Create Python virtual environment
echo -e "${GREEN}Creating Python virtual environment...${NC}"
python3 -m venv backend/venv

# Activate virtual environment and install dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
source backend/venv/bin/activate
pip install --upgrade pip

# Install system dependencies (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}Installing system dependencies for macOS...${NC}"
    brew install gdal
    export CPLUS_INCLUDE_PATH=/usr/local/include
    export C_INCLUDE_PATH=/usr/local/include
fi

# Install Python requirements
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo -e "${GREEN}Installing frontend dependencies...${NC}"
cd frontend
npm install
cd ..

echo -e "${BLUE}Setup complete!${NC}"
echo -e "${GREEN}To start development:${NC}"
echo "1. Backend: source backend/venv/bin/activate && cd backend && uvicorn app.main:app --reload"
echo "2. Frontend: cd frontend && npm start" 