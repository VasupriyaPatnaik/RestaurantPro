from sqlalchemy.orm import Session
from . import models, schemas

# CRUD for Restaurants
def get_restaurants(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Restaurant).offset(skip).limit(limit).all()

def get_restaurant_by_id(db: Session, restaurant_id: int):
    return db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

def create_restaurant(db: Session, restaurant: schemas.RestaurantCreate):
    db_restaurant = models.Restaurant(
        name=restaurant.name,
        country_code=restaurant.country_code,
        city=restaurant.city,
        address=restaurant.address,
        price_range=restaurant.price_range,
        aggregate_rating=restaurant.aggregate_rating,
        rating_color=restaurant.rating_color,
        rating_text=restaurant.rating_text,
        votes=restaurant.votes,
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant
