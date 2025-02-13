import csv
from sqlalchemy.orm import Session
from . import models, database

def load_data_to_db():
    db = next(database.get_db())
    
    with open('path_to_your_zomato_data.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            location = models.Location(
                city=row['City'],
                address=row['Address'],
                longitude=row['Longitude'],
                latitude=row['Latitude'],
            )
            db.add(location)
            db.commit()
            db.refresh(location)
            
            restaurant = models.Restaurant(
                name=row['Restaurant Name'],
                country_code=row['Country Code'],
                city=row['City'],
                address=row['Address'],
                price_range=row['Price range'],
                aggregate_rating=row['Aggregate rating'],
                rating_color=row['Rating color'],
                rating_text=row['Rating text'],
                votes=row['Votes'],
                location_id=location.id,
            )
            db.add(restaurant)
            db.commit()
            db.refresh(restaurant)
            print(f"Inserted restaurant: {restaurant.name}")

if __name__ == "__main__":
    load_data_to_db()
