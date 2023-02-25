from images.queries import TEST_FETCH_ALL


class ImageRepository:

    def __init__(self, db):
        self.db = db

    async def fetch_all(self):
        return await self.db.fetch_all(TEST_FETCH_ALL)
