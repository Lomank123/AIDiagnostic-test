from fastapi import FastAPI
from images.routes import router as images_router


app = FastAPI()

app.include_router(images_router, prefix="/image")
