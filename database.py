from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get MongoDB credentials from environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

try:
    # Establishing connection
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]  # Use database name from .env
    print(f"✅ Successfully connected to MongoDB database: {MONGO_DB_NAME}")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
