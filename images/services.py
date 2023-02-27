import os
import json
import secrets
from typing import Dict, List, Union

import aiohttp
from aiohttp import FormData
from fastapi import Request, UploadFile
import aiofiles
from io import BytesIO
from PIL import Image, ImageDraw, ImageColor

from settings.settings import (
    API_PUBLIC_KEY,
    API_SECRET,
    API_URL,
    STATIC_ROOT,
    STATIC_URL,
)


class BaseService:

    def __init__(self, request: Request):
        self.request = request

    async def execute(self):
        raise NotImplementedError()


class ProcessImageService(BaseService):

    def __init__(self, request):
        super().__init__(request)
        self.image_content = b""

    async def _build_request_data(self) -> FormData:
        formdata = FormData()
        data = {
            'api_key': API_PUBLIC_KEY,
            'api_secret': API_SECRET,
            'image_file': self.image_content,
            'return_landmark': '1',
        }
        for key in data:
            formdata.add_field(name=key, value=data[key])
        return formdata

    async def _send_process_request(self):
        async with aiohttp.ClientSession() as session:
            data = await self._build_request_data()
            # Send async request
            async with session.post(API_URL, data=data) as response:
                response_data = {
                    'status': response.status,
                    'data': await response.json(),
                }
                return response_data

    async def _save_image(self, filename: str) -> int:
        """
        Create new file in static dir,
        write image content to it and insert static path into db.
        """
        temp = filename.split(".")
        title = temp[0]
        extension = temp[1]

        # Generate new file name
        # Example: path/to/static/images/qweqweqwe.jpg
        new_name = f"{secrets.token_hex(10)}.{extension}"
        new_path = os.path.abspath(f"{STATIC_ROOT}/images/{new_name}")
        # Create new file and write image to it
        async with aiofiles.open(new_path, "wb+") as new_file:
            await new_file.write(self.image_content)

        # Generate url
        host = self.request.url.hostname
        port = self.request.url.port
        img_url = f"{STATIC_URL}/images"
        address = f"http://{host}:{port}/{img_url}/{new_name}"

        # Perform query
        query = (
            f"INSERT INTO images "
            f"VALUES(DEFAULT, '{title}', '{address}') RETURNING id;"
        )
        return await self.request.app.state.db.fetch(query)

    async def _save_faces(self, faces: List[Dict], image_id: int):
        """Insert faces coordinates into db."""
        insert_data = [
            (
                image_id,
                json.dumps(face['landmark']),
                json.dumps(face['face_rectangle']),
            ) for face in faces
        ]
        query = "INSERT INTO faces VALUES(DEFAULT, $1, $2, $3);"
        await self.request.app.state.db.executemany(query, insert_data)

    async def execute(self, img: UploadFile) -> int:
        """Process, insert and return id of inserted image."""

        # Process image using 3rd party API
        self.image_content = await img.read()
        # TODO: Return error based on status from API
        response = await self._send_process_request()
        faces = response['data']['faces']

        # All queries are in the same transaction
        async with self.request.app.state.db.transaction():
            saved_image = await self._save_image(filename=img.filename)
            image_id = saved_image[0]['id']
            await self._save_faces(faces, image_id)

        return image_id


class PaintImageService(BaseService):

    async def _fetch_img_with_faces(self, img_id: int) -> Dict:
        db = self.request.app.state.db
        query = (
            f"SELECT images.image, faces.rectangle, faces.landmark FROM images "
            f"LEFT JOIN faces ON images.id = faces.image_id "
            f"WHERE images.id = {img_id};"
        )
        result = await db.fetch(query)
        return result

    async def _fetch_img_content(self, img_url: str) -> Dict:
        async with aiohttp.ClientSession() as session:
            # Send async request
            async with session.get(img_url) as response:
                response_data = {
                    'status': response.status,
                    'data': await response.content.read(),
                }
                return response_data

    async def _paint_faces(
        self,
        content: bytes,
        faces: List[Dict],
        color: Union[str, None] = None
    ):
        # Color
        fill = None
        if color is not None:
            fill = ImageColor.getrgb(color)
        # Drawing
        img = Image.open(BytesIO(content))
        new_img = ImageDraw.Draw(img)
        for face in faces:
            marks = json.loads(face["landmark"])
            for point in marks:
                xy = (int(marks[point]['x']), int(marks[point]['y']))
                new_img.point(xy, fill=fill)

        # Use buffer to return bytes of edited image
        buff = BytesIO()
        img.save(buff, format='JPEG')
        return buff.getvalue()

    async def execute(self, id: str, color: Union[str, None] = None) -> bytes:
        # Fetch img with faces
        result = await self._fetch_img_with_faces(id)
        # Get image content
        # TODO: Return error based on response status
        img_content = await self._fetch_img_content(result[0]['image'])
        raw_img = img_content.get('data')
        # Open content with pillow and paint faces
        edited_image: bytes = await self._paint_faces(raw_img, result, color)
        return edited_image


class ChangeImageService(BaseService):

    async def execute(self, id: str):
        print(id)
        return {'msg': 'Success!'}


class RemoveImageService(BaseService):

    async def execute(self, id: str):
        print(id)
        return {'msg': 'Success!'}
