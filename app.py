import os
import shutil
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient, GEOSPHERE
from bson import ObjectId
from dotenv import load_dotenv
import google.generativeai as genai
from werkzeug.utils import secure_filename
from PIL import Image
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import math

# Load environment variables
load_dotenv()

# Configuration constants
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_uploads():
    """Clean up uploaded files"""
    if os.path.exists(UPLOAD_FOLDER):
        try:
            shutil.rmtree(UPLOAD_FOLDER)
        except PermissionError:
            # If we can't remove the directory, try to clear its contents
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
    
    # Create the directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_app():
    """Factory function to create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure app
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    # Get environment variables
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Initialize MongoDB connection
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    collection = db['restaurants_details']
    
    # Create database indexes
    def setup_indexes():
        collection.create_index([("Restaurant Name", "text")])
        collection.create_index("Country Code")
        collection.create_index("Cuisines")
        collection.create_index("Average Cost for two")
        collection.create_index("Locality")
        collection.create_index([("location", GEOSPHERE)])
    
    # Initialize Gemini AI
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro-vision")
    
    # Country Code to Country Name mapping
    country_mapping = {
        1: "India",
        14: "Australia",
        30: "Brazil",
        37: "Canada",
        94: "Indonesia",
        148: "New Zealand",
        162: "Philippines",
        166: "Qatar",
        184: "Singapore",
        189: "South Africa",
        191: "Sri Lanka",
        208: "Turkey",
        214: "UAE",
        215: "United Kingdom",
        216: "United States"
    }
    
    # Application initialization
    setup_indexes()
    cleanup_uploads()
    
    # ===== HTML TEMPLATE ROUTES =====
    
    @app.route('/')
    def home():
        """Render home page"""
        return "hello"
    
    @app.route('/nearby-search')
    def nearby_search():
        """Render nearby search page"""
        return render_template('nearby-search.html')
    
    @app.route('/image-search')
    def image_search():
        """Render image search page"""
        return render_template('image-search.html')
    
    @app.route('/restaurant-list')
    def restaurant_list():
        """Render restaurant list page"""
        return render_template('restaurant-list.html')
    
    @app.route('/restaurant/<restaurant_id>')
    def restaurant_detail(restaurant_id):
        """Render restaurant detail page"""
        return render_template('restaurant-details.html', restaurant_id=restaurant_id)
    
    # ===== API ROUTES =====
    
    @app.route('/api/restaurant/<restaurant_id>', methods=["GET"])
    def get_restaurant_by_id(restaurant_id):
        """Get a single restaurant by ID"""
        try:
            restaurant = collection.find_one({"_id": ObjectId(restaurant_id)})
            if restaurant:
                restaurant["_id"] = str(restaurant["_id"])
                
                # Format boolean fields
                restaurant["has_table_booking"] = "✅ Available" if restaurant.get("has_table_booking") else "❌ Not Available"
                restaurant["has_online_delivery"] = "✅ Yes" if restaurant.get("has_online_delivery") else "❌ No"
                restaurant["is_delivering_now"] = "✅ Yes" if restaurant.get("is_delivering_now") else "❌ No"
                restaurant["switch_to_order_menu"] = "✅ Available" if restaurant.get("switch_to_order_menu") else "❌ Not Available"
                
                return jsonify(restaurant), 200
            else:
                return jsonify({"error": "Restaurant not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/restaurants', methods=['GET'])
    def get_restaurants():
        """Get restaurants with filters and pagination"""
        try:
            # Pagination parameters
            page = int(request.args.get("page", 1))
            limit = int(request.args.get("limit", 9))
            offset = (page - 1) * limit
            
            # Filtering parameters
            country_code = request.args.get("country_code", type=int)
            search_query = request.args.get("search", "").strip()
            avg_cost_raw = request.args.get("avg_cost")
            cuisine_filter = request.args.get("cuisine", "").strip().lower()
            
            avg_cost = None
            if avg_cost_raw:
                try:
                    avg_cost = int(float(avg_cost_raw))
                except ValueError:
                    return jsonify({"error": "Invalid average cost value"}), 400
            
            # Build query
            query = {}
            
            if country_code:
                query["Country Code"] = country_code
            
            if search_query:
                query["$or"] = [
                    {"Restaurant Name": {"$regex": search_query, "$options": "i"}},
                    {"Address": {"$regex": search_query, "$options": "i"}},
                    {"Locality": {"$regex": search_query, "$options": "i"}}
                ]
            
            if avg_cost is not None:
                query["Average Cost for two"] = {"$lte": avg_cost}
            
            if cuisine_filter:
                query["Cuisines"] = {"$regex": cuisine_filter, "$options": "i"}
            
            # Get total count
            total_count = collection.count_documents(query)
            total_pages = max(1, math.ceil(total_count / limit))
            
            # Get paginated results
            restaurants = list(collection.find(query).skip(offset).limit(limit))
            for restaurant in restaurants:
                restaurant["_id"] = str(restaurant["_id"])
            
            return jsonify({
                "restaurants": restaurants,
                "page": page,
                "total_pages": total_pages,
                "total_count": total_count
            }), 200
        
        except Exception as e:
            import traceback
            print("[ERROR] API Failure:", traceback.format_exc())
            return jsonify({"error": f"Server error: {str(e)}"}), 500
    
    @app.route('/api/cuisines', methods=["GET"])
    def get_cuisines():
        """Get all unique cuisines from the database"""
        try:
            cuisines = collection.distinct("Cuisines")
            all_cuisines = set()
            
            for cuisine_string in cuisines:
                if cuisine_string:
                    for cuisine in cuisine_string.split(","):
                        all_cuisines.add(cuisine.strip())
            
            return jsonify({"cuisines": sorted(all_cuisines)}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
        @app.route('/api/restaurants/nearby', methods=['GET'])
        def get_nearby_restaurants():
            """Get restaurants near a specified location"""
            try:
                location = request.args.get("location")
                lat = request.args.get("lat")
                lon = request.args.get("lon")
                radius = float(request.args.get("radius", 3))
                page = int(request.args.get("page", 1))
                limit = int(request.args.get("limit", 9))
                offset = (page - 1) * limit
            except:
                return jsonify({"error": "Invalid request parameters"}), 400
    
            # Get coordinates from location name if provided
            if location:
                geocoder = Nominatim(user_agent="restaurant_finder_app")
                location_data = geocoder.geocode(location)
                if not location_data:
                    return jsonify({"error": "Location not found"}), 404
                lat = location_data.latitude
                lon = location_data.longitude
    
            # Validate coordinates
            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid coordinates"}), 400
    
            radius_in_radians = radius / 6378.1
    
            nearby_restaurants = collection.find({
                "location": {
                    "$geoWithin": {
                        "$centerSphere": [[lon, lat], radius_in_radians]
                    }
                }
            }).skip(offset).limit(limit)
    
            results = []
            for restaurant in nearby_restaurants:
                results.append({
                    "_id": str(restaurant["_id"]),
                    "Restaurant Name": restaurant.get("Restaurant Name", ""),
                    "Location": restaurant.get("Location", ""),
                    "Cuisines": restaurant.get("Cuisines", "")
                })
    
            return jsonify({
                "restaurants": results,
                "page": page,
                "total_count": len(results)
            })

    
    @app.route('/api/restaurants/search-by-image', methods=["POST"])
    def search_restaurant_by_image():
        """Search for restaurants based on uploaded image"""
        try:
            # Check for image file
            if "image" not in request.files:
                return jsonify({"error": "No image file found"}), 400
            image = request.files["image"]
            
            if image.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(image_path)
                
                # Process the image with Gemini AI
                with open(image_path, 'rb') as img_file:
                    response = model.analyze(image=img_file)
                
                # Clean up image file after processing
                os.remove(image_path)
                
                # Extract relevant details from AI response
                if response:
                    # Logic to process AI response (e.g., finding similar restaurants)
                    return jsonify({"result": response}), 200
                else:
                    return jsonify({"error": "No results from image processing"}), 404
            else:
                return jsonify({"error": "Invalid file format. Please upload a PNG, JPG, or JPEG file."}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app

    # Pass the collection to the function
    app.get_nearby_restaurants = lambda: get_nearby_restaurants(collection)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=5000)