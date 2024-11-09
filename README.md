# the_green
Helping to make the world more greenified! Social Impact Hackathon 2024

# Data Agent

Functional Requirements:
  Conversation:
    - Natural language understanding of data queries
    - Context-aware responses about datasets
    - Confidence scoring explanations
    - Data availability status updates
    
  Data Knowledge:
    - Dataset catalog maintenance
    - Source verification
    - Quality assessment
    - Gap identification
    
  User Interface:
    - Chat message history
    - Dataset recommendations
    - Quick actions/shortcuts
    - Confidence indicators

Technical Requirements:
  Agent Framework:
    - Fetch.ai agent integration
    - Message protocol definition
    - State management
    - Error handling

  Data Management:
    - Dataset indexing
    - Metadata storage
    - Query optimization
    - Cache management

Integration Points:
  - Message API for frontend
  - Dataset reference system
  - Map view communication
  - State synchronization

# Map View

Functional Requirements:
  Visualization:
    - Multiple layer support
    - Layer opacity control
    - Custom color schemes
    - Legend display
    
  Interaction:
    - Layer toggling
    - Region selection
    - Data point inspection
    - View state saving
    
  Analysis:
    - Policy impact visualization
    - Score display
    - Comparison views
    - Time series support

Technical Requirements:
  Map Framework:
    - PyDeck integration
    - Custom layer definitions (ScatterplotLayer, HexagonLayer, etc.)
    - View state management
    - Performance optimization
    - WebGL-powered rendering

  Data Handling:
    - GeoJSON processing
    - DataFrame integration
    - Real-time updates
    - Data caching
    - Pandas/GeoPandas support

Integration Points:
  - Dataset loading API
  - State synchronization
  - Agent communication
  - View state sharing


