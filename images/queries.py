IMAGES_TABLE_CREATE = (
    """
    CREATE TABLE IF NOT EXISTS images(
        id SERIAL PRIMARY KEY,
        title TEXT NULL,
        image TEXT NOT NULL
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
