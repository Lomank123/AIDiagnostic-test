import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")


# 3rd party API
API_SECRET = os.environ.get("API_SECRET", "secret")
API_PUBLIC_KEY = os.environ.get("API_PUBLIC_KEY", "public")


# PostgreSQL

DB_CREDENTIALS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "db_user"),
    "password": os.environ.get("DB_PASSWORD", "db_pass"),
    "database": os.environ.get("DB_NAME", "db_name"),
}

# Format: "postgresql://user:password@postgresserver/db"
DB_URL = (
    f"postgresql://{DB_CREDENTIALS['user']}:{DB_CREDENTIALS['password']}"
    f"@{DB_CREDENTIALS['host']}:{DB_CREDENTIALS['port']}"
    f"/{DB_CREDENTIALS['database']}"
)
