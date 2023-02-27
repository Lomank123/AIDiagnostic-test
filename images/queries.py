IMAGES_TABLE_CREATE = (
    """
    CREATE TABLE IF NOT EXISTS images(
        id SERIAL PRIMARY KEY,
        title TEXT NULL,
        image TEXT NOT NULL
    );
    """
)
IMAGE_FACES_TABLE_CREATE = (
    """
    CREATE TABLE IF NOT EXISTS faces(
        id SERIAL PRIMARY KEY,
        image_id INT NOT NULL,
        landmark JSON NULL,
        rectangle JSON NULL,
        FOREIGN KEY (image_id) REFERENCES images(id)
    );
    """
)

# For testing purposes only
TEST_INSERT = (
    """
    INSERT INTO images VALUES(1, NULL, 'path/to/img');
    """
)
TEST_FETCH_ALL = "SELECT id, title, image FROM images;"
