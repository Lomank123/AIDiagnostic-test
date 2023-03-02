import json
from io import BytesIO
from typing import Dict, List, Union

import aiohttp
from fastapi import Request, UploadFile
from PIL import Image, ImageColor, ImageDraw

from images.utils import (
    build_image_address,
    build_image_process_request_data,
    save_image_to_file,
    send_process_request,
    generate_new_filename,
    build_new_image_path,
)


class BaseService:

    def __init__(self, request: Request):
        self.request = request

    async def execute(self):
        raise NotImplementedError()


# TODO: Rename to NewImageService or CreateImageService
class ProcessImageService(BaseService):

    async def _insert_image_to_db(self, old_filename: str, address: str) -> str:
        """Insert static path to image and old title into db."""
        query = (
            f"INSERT INTO images "
            f"VALUES(DEFAULT, '{old_filename}', '{address}') RETURNING id;"
        )
        result = await self.request.app.state.db.fetch(query)
        return result[0].get('id')

    # TODO: Move to utils as well
    async def _insert_faces_to_db(self, faces: List[Dict], image_id: int):
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

    async def execute(self, img: UploadFile, update: bool = False) -> int:
        """Process, insert/update and return id of inserted image."""

        # TODO: Return error based on status from API

        # Process image using 3rd party API
        image_content = await img.read()
        request_data = build_image_process_request_data(image_content)
        response = await send_process_request(data=request_data)
        faces = response['data']['faces']

        # Path, filename and address
        new_filename = generate_new_filename(img.filename)
        new_path = build_new_image_path(new_filename)
        address = build_image_address(
            host=self.request.url.hostname,
            port=self.request.url.port,
            new_filename=new_filename,
        )

        # Create new image file in static dir
        await save_image_to_file(new_path, image_content)

        # All queries are in the same transaction
        async with self.request.app.state.db.transaction():
            image_id = await self._insert_image_to_db(img.filename, address)
            await self._insert_faces_to_db(faces, image_id)

        return image_id


class PaintImageService(BaseService):

    async def _fetch_img_with_faces(self, img_id: int) -> Dict:
        db = self.request.app.state.db
        query = (
            f"SELECT images.image, faces.rectangle, faces.landmark FROM images "
            f"JOIN faces ON images.id = faces.image_id "
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

    async def execute(self, id: str, img: UploadFile):
        # Within 1 transaction
        # Remove old faces (select by image_id)
        # Update row with id (fields: title, path)
        # Insert new faces
        # Remove old image file after all other operations
        print(id)
        return {'msg': 'Success!'}


class RemoveImageService(BaseService):

    async def execute(self, id: str):
        print(id)
        return {'msg': 'Success!'}
