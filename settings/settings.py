import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

# Static files
STATIC_URL = "static"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# 3rd party API
API_SECRET = os.environ.get("API_SECRET", "secret")
API_PUBLIC_KEY = os.environ.get("API_PUBLIC_KEY", "public")
API_URL = os.environ.get("API_URL", "https://example.com/")


# PostgreSQL

DB_CREDENTIALS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "db_user"),
    "password": os.environ.get("DB_PASSWORD", "db_pass"),
    "database": os.environ.get("DB_NAME", "db_name"),
}
