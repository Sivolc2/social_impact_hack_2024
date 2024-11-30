#!/bin/bash

# Create directory structure
mkdir -p backend/app/{routers,services,data}
mkdir -p frontend/src/{components,hooks}

# Create backend files
touch backend/app/main.py
touch backend/app/routers/{map.py,chat.py}
touch backend/app/services/{data_processing.py,llm.py}
touch backend/requirements.txt
touch backend/Dockerfile

# Create frontend files
touch frontend/src/components/{Map.jsx,ChatWindow.jsx,Layout.jsx}
touch frontend/src/hooks/{useFetchData.js,useChat.js}
touch frontend/src/App.jsx
touch frontend/package.json
touch frontend/Dockerfile

touch docker-compose.yml
touch .env
touch .gitignore

# Make the script executable
chmod +x setup.sh 