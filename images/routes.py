from fastapi import APIRouter
from fastapi import Request


router = APIRouter()


@router.get('')
async def get_images(request: Request):
    db = request.app.state.db
    query = "SELECT id, title, image FROM images;"
    return await db.fetch_all(query)
