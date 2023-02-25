from fastapi import UploadFile
from typing import Union


class BaseService:

    def __init__(self, request):
        self.request = request

    async def execute(self):
        raise NotImplementedError()


class ProcessImageService(BaseService):

    async def execute(self, img: UploadFile):
        print(img)
        return {'msg': 'Success!'}


class PaintImageService(BaseService):

    async def execute(self, id: str, color: Union[str, None] = None):
        print(id, color)
        return {'msg': 'Success!'}


class ChangeImageService(BaseService):

    async def execute(self, id: str):
        print(id)
        return {'msg': 'Success!'}


class RemoveImageService(BaseService):

    async def execute(self, id: str):
        print(id)
        return {'msg': 'Success!'}
