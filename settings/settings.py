import os
from dotenv import load_dotenv


load_dotenv()


DB_CREDENTIALS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "db_user"),
    "password": os.environ.get("DB_PASSWORD", "db_pass"),
    "database": os.environ.get("DB_NAME", "db_name"),
}
