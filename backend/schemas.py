from pydantic import BaseModel
from typing import List, Optional

class LocationBase(BaseModel):
    city: str
    address: str
    longitude: float
    latitude: float

class CuisineBase(BaseModel):
    name: str

class RestaurantBase(BaseModel):
    name: str
    country_code: int
    city: str
    address: str
    price_range: int
    aggregate_rating: float
    rating_color: str
    rating_text: str
    votes: int

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantResponse(RestaurantBase):
    location: LocationBase
    cuisines: List[CuisineBase]

    class Config:
        orm_mode = True
