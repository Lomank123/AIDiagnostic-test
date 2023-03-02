import os
import secrets
from typing import Dict, List
import json

import aiofiles
from aiofiles.os import remove
import aiohttp
from aiohttp import FormData
from asyncpg.connection import Connection

from settings.settings import (
    API_PUBLIC_KEY,
    API_SECRET,
    API_URL,
    STATIC_ROOT,
    STATIC_URL,
)


async def send_process_request(data: FormData) -> Dict:
    async with aiohttp.ClientSession() as session:
        # Send async request
        async with session.post(API_URL, data=data) as response:
            response_data = {
                'status': response.status,
                'data': await response.json(),
            }
            return response_data


async def save_image_to_file(new_path: str, image_content: bytes):
    """Create new file in static dir and write image content to it."""
    async with aiofiles.open(new_path, "wb+") as new_file:
        await new_file.write(image_content)


async def insert_faces_into_db(
    connection: Connection, faces: List[Dict], image_id: int,
):
    """Insert faces coordinates into db."""
    insert_data = [
        (
            int(image_id),
            json.dumps(face['landmark']),
            json.dumps(face['face_rectangle']),
        ) for face in faces
    ]
    query = "INSERT INTO faces VALUES(DEFAULT, $1, $2, $3);"
    await connection.executemany(query, insert_data)


async def remove_image_faces_from_db(connection: Connection, image_id: int):
    """Delete faces by image_id from db."""
    query = f"DELETE FROM faces WHERE image_id = {image_id};"
    await connection.execute(query)


async def remove_image_file(path: str):
    try:
        await remove(path)
    except FileNotFoundError:
        pass


def generate_new_filename(old_filename: str) -> str:
    extension = old_filename.split(".")[1]
    return f"{secrets.token_hex(10)}.{extension}"


def build_new_image_path(new_filename: str) -> str:
    # Example: path/to/static/images/qweqweqwe.jpg
    return os.path.abspath(f"{STATIC_ROOT}/images/{new_filename}")


def build_image_address(host: str, port: str, new_filename: str) -> str:
    """Return static path (address) from given filename."""
    img_url = f"{STATIC_URL}/images"
    return f"http://{host}:{port}/{img_url}/{new_filename}"


def build_image_process_request_data(image_content: bytes) -> FormData:
    formdata = FormData()
    data = {
        'api_key': API_PUBLIC_KEY,
        'api_secret': API_SECRET,
        'image_file': image_content,
        'return_landmark': '1',
    }
    for key in data:
        formdata.add_field(name=key, value=data[key])
    return formdata
