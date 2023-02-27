from typing import Union

from fastapi import APIRouter, Request, UploadFile, Response

from images.services import (
    ChangeImageService,
    PaintImageService,
    ProcessImageService,
    RemoveImageService,
)

router = APIRouter()


@router.post('')
async def process(request: Request, img: UploadFile):
    service = ProcessImageService(request)
    img_id = await service.execute(img)
    return {"id": img_id}


@router.get('/{id}')
async def paint(id: str, request: Request, color: Union[str, None] = None):
    service = PaintImageService(request)
    processed_image = await service.execute(id, color)
    return Response(content=processed_image, media_type="image/jpg")


@router.put('/{id}')
async def change(id: str, request: Request):
    service = ChangeImageService(request)
    return await service.execute(id)


@router.delete('/{id}')
async def remove(id: str, request: Request):
    service = RemoveImageService(request)
    return await service.execute(id)


@router.get('/test')
async def test(request: Request):
    return {'message': 'Test method.'}
