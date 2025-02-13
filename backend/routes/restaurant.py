from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, database

router = APIRouter()

@router.get("/restaurants", response_model=List[schemas.RestaurantResponse])
def read_restaurants(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    return crud.get_restaurants(db=db, skip=skip, limit=limit)

@router.get("/restaurant/{restaurant_id}", response_model=schemas.RestaurantResponse)
def read_restaurant(restaurant_id: int, db: Session = Depends(database.get_db)):
    db_restaurant = crud.get_restaurant_by_id(db, restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@router.post("/restaurants", response_model=schemas.RestaurantResponse)
def create_restaurant(restaurant: schemas.RestaurantCreate, db: Session = Depends(database.get_db)):
    return crud.create_restaurant(db=db, restaurant=restaurant)
