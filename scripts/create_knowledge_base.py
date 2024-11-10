import json
from pathlib import Path

# Dataset information as a Python dictionary
knowledge_base = {
    "datasets": [
        {
            "id": "sdg-15-3-1",
            "name": "SDG 15.3.1 Land Degradation",
            "source": "TrendsEarth",
            "category": "land_degradation",
            "temporal_range": "2000-2020",
            "spatial_resolution": "300m",
            "description": "Comprehensive dataset tracking land degradation neutrality through productivity dynamics, land cover changes, and soil carbon stocks. Covers global land surface with particular focus on agricultural and forest areas.",
            "variables": ["productivity_trend", "land_cover", "soil_carbon"],
            "text": "The SDG 15.3.1 dataset provides global coverage of land degradation metrics. It includes three main components: land productivity dynamics measuring vegetation growth trends, land cover monitoring detecting changes in ecosystem types, and soil organic carbon stock changes. The data is particularly valuable for analyzing agricultural sustainability and forest health trends."
        },
        {
            "id": "forest-cover-hansen",
            "name": "Global Forest Change",
            "source": "Hansen/UMD/Google/USGS/NASA",
            "category": "forest_cover",
            "temporal_range": "2000-2023",
            "spatial_resolution": "30m",
            "description": "Annual tree cover loss and gain data, providing detailed forest change analysis globally",
            "variables": ["tree_cover", "forest_loss", "forest_gain"],
            "text": "The Hansen Global Forest Change dataset tracks annual forest loss and gain at 30-meter resolution. It provides detailed information about forest cover changes, helping identify deforestation patterns and forest recovery areas. The dataset is particularly useful for monitoring tropical deforestation and forest management effectiveness."
        },
        {
            "id": "ucdp-ged",
            "name": "UCDP Georeferenced Event Dataset",
            "source": "Uppsala Conflict Data Program (UCDP)",
            "category": "conflict_events",
            "temporal_range": "1989-2023",
            "spatial_resolution": "Variable; events are geocoded to specific locations, often down to individual villages",
            "description": "Detailed data on individual events of organized violence worldwide, including information on date, location, actors involved, and fatalities",
            "variables": ["event_date", "location", "actor1", "actor2", "fatalities", "event_type"],
            "text": "The UCDP Georeferenced Event Dataset (GED) provides comprehensive information on organized violence events globally from 1989 to 2023. Each event is geocoded to precise locations and includes details such as the date, actors involved, and number of fatalities."
        }
    ]
}

# Create the data directory if it doesn't exist
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Write to JSON file with proper formatting and UTF-8 encoding
output_path = data_dir / "knowledge_base.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(knowledge_base, f, indent=2, ensure_ascii=False)

print(f"Knowledge base written to {output_path}")

# Verify the file can be read back
with open(output_path, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)
    print(f"Successfully verified JSON file with {len(loaded_data['datasets'])} datasets") 