import os

import asyncpg
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from images.queries import IMAGE_FACES_TABLE_CREATE, IMAGES_TABLE_CREATE
from images.routes import router as images_router
from settings.settings import DB_CREDENTIALS, STATIC_ROOT, STATIC_URL

# FastAPI setup
app = FastAPI()

# Routing
app.include_router(images_router, prefix="/image")

# Create dir if none
dir_name = os.path.dirname(os.path.abspath(f"{STATIC_ROOT}/images/1"))
if not os.path.isdir(dir_name):
    os.makedirs(dir_name)

# Static files
app.mount(f"/{STATIC_URL}", StaticFiles(directory="static"), name="static")


# Events
@app.on_event("startup")
async def startup():
    connection = await asyncpg.connect(**DB_CREDENTIALS)
    # Save instance to state to use in routes
    app.state.db = connection
    # Create table if not exists
    queries = [IMAGES_TABLE_CREATE, IMAGE_FACES_TABLE_CREATE]
    for query in queries:
        await connection.execute(query)


@app.on_event("shutdown")
async def shutdown():
    await app.state.db.disconnect()
