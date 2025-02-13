from fastapi import FastAPI
from routes import restaurant
from .database import engine, Base

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include router
app.include_router(restaurant.router)
