import json
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv  # Load environment variables
from bson import ObjectId
from pymongo.errors import BulkWriteError

# Load .env file
load_dotenv()

# Fetch MongoDB details from environment variables
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')

# Step 1: Connect to MongoDB
client = MongoClient(MONGO_URI)  # Use URI from .env
db = client[MONGO_DB_NAME]  # Use database name from .env

# Function to convert latitude and longitude to GeoJSON format
def create_geojson(lat, long):
    return {
        "type": "Point",
        "coordinates": [float(long), float(lat)]
    }

# Function to load JSON data into MongoDB
def load_json_data():
    json_path = "./data/restaurant.json"  # Path to JSON file
    collection = db.restaurants  # Define the collection
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        
        # Process the data and convert latitude, longitude into GeoJSON format
        for item in data:
            if "location" in item:
                location = item["location"]
                if "latitude" in location and "longitude" in location:
                    location["geo"] = create_geojson(location["latitude"], location["longitude"])
        
        # Insert the data into MongoDB
        try:
            result = collection.insert_many(data, ordered=False)
            print(f"✅ JSON data loaded successfully! Inserted {len(result.inserted_ids)} records into 'restaurants_details'.")
        except BulkWriteError as e:
            print(f"❌ Error loading JSON data: {e.details}")

# Step 3: Load CSV Data
def load_csv_data():
    csv_path = "./data/zomato.csv"  # Path to CSV file

    try:
        # Load CSV data
        df = pd.read_csv(csv_path, encoding="ISO-8859-1")

        # Convert DataFrame to a list of dictionaries
        data = df.to_dict(orient='records')

        # Insert CSV data into 'restaurants' collection
        result = db.restaurants.insert_many(data)
        print(f"✅ CSV data loaded successfully! Inserted {len(result.inserted_ids)} records into 'restaurants'.")
    
    except FileNotFoundError:
        print(f"❌ Error: CSV file not found at {csv_path}")
    except pd.errors.EmptyDataError:
        print("❌ Error: CSV file is empty.")
    except pd.errors.ParserError:
        print("❌ Error: CSV file has parsing issues.")
    except Exception as e:
        print(f"❌ Error loading CSV data: {e}")

# Step 4: Run the Data Loading Functions
if __name__ == '__main__':
    load_json_data()  # Load JSON data
    load_csv_data()   # Load CSV data
