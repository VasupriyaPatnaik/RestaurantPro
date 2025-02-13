from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from .database import Base

class Cuisine(Base):
    __tablename__ = 'cuisine'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)

class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(255))
    address = Column(Text)
    longitude = Column(DECIMAL(9, 6))
    latitude = Column(DECIMAL(9, 6))

class Restaurant(Base):
    __tablename__ = 'restaurant'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    country_code = Column(Integer)
    city = Column(String(255))
    address = Column(Text)
    price_range = Column(Integer)
    aggregate_rating = Column(Float)
    rating_color = Column(String(50))
    rating_text = Column(String(50))
    votes = Column(Integer)
    
    location_id = Column(Integer, ForeignKey('location.id'))
    location = relationship("Location")

class RestaurantCuisine(Base):
    __tablename__ = 'restaurant_cuisine'

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), primary_key=True)
    cuisine_id = Column(Integer, ForeignKey('cuisine.id'), primary_key=True)

class PriceRange(Base):
    __tablename__ = 'price_range'

    id = Column(Integer, primary_key=True, index=True)
    range_value = Column(String(255))

class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
