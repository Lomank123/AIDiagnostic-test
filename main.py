import databases
from fastapi import FastAPI

from images.queries import IMAGES_TABLE_CREATE
from images.routes import router as images_router
from settings.settings import DB_URL

# DB setup
database = databases.Database(DB_URL)

# FastAPI setup
app = FastAPI()

# Routing
app.include_router(images_router, prefix="/image")


# Events
@app.on_event("startup")
async def startup():
    await database.connect()
    # Save instance to state to use in routes
    app.state.db = database
    # Create table if not exists
    await database.execute(IMAGES_TABLE_CREATE)


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
