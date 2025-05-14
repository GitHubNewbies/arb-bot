import os
from dotenv import load_dotenv

# Load from .env if available
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").lower()

# Example secrets you may later use
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/devdb")
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")
