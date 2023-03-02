import json
from io import BytesIO
from typing import Dict, List, Union

import aiohttp
from fastapi import HTTPException, Request, UploadFile
from PIL import Image, ImageColor, ImageDraw

from images.utils import (
    build_image_address,
    build_image_process_request_data,
    build_new_image_path,
    build_old_image_path,
    check_by_id,
    generate_new_filename,
    insert_faces_into_db,
    remove_image_faces_from_db,
    remove_image_file,
    remove_image_from_db,
    save_image_to_file,
    send_process_request,
)


class BaseService:

    def __init__(self, request: Request):
        self.request = request

    async def execute(self):
        raise NotImplementedError()


class CreateImageService(BaseService):

    async def _insert_image_into_db(
        self, old_filename: str, address: str
    ) -> str:
        """Insert static path to image and old title into db."""
        query = (
            f"INSERT INTO images "
            f"VALUES(DEFAULT, '{old_filename}', '{address}') RETURNING id;"
        )
        result = await self.request.app.state.db.fetch(query)
        return result[0].get('id')

    async def execute(self, img: UploadFile) -> int:
        """Process, insert/update and return id of inserted image."""

        # Process image using 3rd party API
        image_content = await img.read()
        request_data = build_image_process_request_data(image_content)
        response = await send_process_request(data=request_data)
        status_code = int(response.get('status'))
        data = response.get('data')

        # Error during image processing
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=str(data))

        faces = data.get('faces')

        # Path, filename and address
        new_filename = generate_new_filename(img.filename)
        new_path = build_new_image_path(new_filename)
        address = build_image_address(
            host=self.request.url.hostname,
            port=self.request.url.port,
            new_filename=new_filename,
        )

        # All queries are in the same transaction
        db = self.request.app.state.db
        async with db.transaction():
            image_id = await self._insert_image_into_db(img.filename, address)
            await insert_faces_into_db(
                connection=db, faces=faces, image_id=image_id)

        # Create new image file in static dir
        await save_image_to_file(new_path, image_content)

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
        db = self.request.app.state.db
        is_found = await check_by_id(db, 'images', id)
        if not is_found:
            raise HTTPException(status_code=404, detail='Image not found.')

        # Fetch img with faces
        result = await self._fetch_img_with_faces(id)
        # Get image content
        img_content = await self._fetch_img_content(result[0]['image'])
        raw_img = img_content.get('data')
        # Open content with pillow and paint faces
        edited_image: bytes = await self._paint_faces(raw_img, result, color)
        return edited_image


class ChangeImageService(BaseService):

    async def _update_image(self, title: str, address: str, img_id: str):
        query = (
            f"UPDATE images "
            f"SET title = '{title}', image = '{address}' "
            f"WHERE id = {img_id};"
        )
        await self.request.app.state.db.execute(query)

    async def execute(self, img_id: str, img: UploadFile):
        """
        Update existing image item in db. Create new faces and image file.
        Remove old faces and image file.
        """

        db = self.request.app.state.db
        is_found = await check_by_id(db, 'images', img_id)
        if not is_found:
            raise HTTPException(status_code=404, detail='Image not found.')

        # Process image using 3rd party API
        image_content = await img.read()
        request_data = build_image_process_request_data(image_content)
        response = await send_process_request(data=request_data)
        status_code = int(response.get('status'))
        data = response.get('data')

        # Error during image processing
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=str(data))

        faces = data.get('faces')

        # Path, filename and address
        new_filename = generate_new_filename(img.filename)
        new_path = build_new_image_path(new_filename)
        address = build_image_address(
            host=self.request.url.hostname,
            port=self.request.url.port,
            new_filename=new_filename,
        )

        # Remove old image
        old_img_path = await build_old_image_path(db, img_id)
        await remove_image_file(old_img_path)

        # All queries are in the same transaction
        async with db.transaction():
            await self._update_image(
                title=img.filename, address=address, img_id=img_id)
            await remove_image_faces_from_db(db, image_id=img_id)
            await insert_faces_into_db(
                connection=db, faces=faces, image_id=img_id)

        # Create new image file in static dir
        await save_image_to_file(new_path, image_content)

        return img_id


class RemoveImageService(BaseService):

    async def execute(self, img_id: str):
        # Remove old image file
        db = self.request.app.state.db
        is_found = await check_by_id(db, 'images', img_id)
        if not is_found:
            raise HTTPException(status_code=404, detail='Image not found.')

        old_img_path = await build_old_image_path(db, img_id)
        await remove_image_file(old_img_path)

        # Remove faces and image from db
        async with db.transaction():
            await remove_image_faces_from_db(db, img_id)
            await remove_image_from_db(db, img_id)
