from pymongo import MongoClient
from app.config.settings import settings

print("Using database:", settings.DB_NAME)
try:
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]

except Exception as e:
    raise RuntimeError(f"MongoDB connection failed: {e}")