from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.config.settings import settings
from app.utils.logger import logger

_client = None
_db     = None


async def connect_db():
    """
    Connect to MongoDB and prepare collection indexes.
    Professional Error Handling & Logging implemented.
    """
    global _client, _db
    try:
        logger.info(f"Attempting MongoDB connection: {settings.MONGODB_URL.split('@')[-1]}")
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000   # Fail fast (5 seconds)
        )
        
        # Verify connection immediately
        await _client.admin.command("ping")
        _db = _client[settings.DATABASE_NAME]

        # ── COLLECTION INDEXES (IDEMPOTENT) ───────────────────────────────────
        
        # User & Doctor Auth
        await _db["users"].create_index("email", unique=True)
        await _db["users"].create_index("role")
        
        # Doctor Professional Profiles (separate collection for scalability)
        await _db["doctors"].create_index("email", unique=True)
        await _db["doctors"].create_index("is_verified")

        # Session & Token Management
        await _db["refresh_tokens"].create_index("token", unique=True)
        await _db["token_blacklist"].create_index("blacklisted_at", expireAfterSeconds=86400)

        # Domain Collections
        await _db["skin_predictions"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        await _db["user_plans"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        logger.info(f"MongoDB Connected Successfully -> Database: {settings.DATABASE_NAME}")

    except Exception as e:
        logger.critical(f"MongoDB Connection CRITICAL FAILURE: {e}")
        _db = None
        # We don't exit here, so the app starts, but endpoints will return 500/503.


async def disconnect_db():
    """Close MongoDB connection gracefully."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed safely.")


def get_db():
    """
    Production-grade DB accessor.
    Throws RuntimeError if the connection was never established.
    """
    if _db is None:
        logger.error("DB ACCESS ATTEMPTED BUT NO ACTIVE CONNECTION FOUND.")
        raise RuntimeError("The database is currently unreachable. Please check logs.")
    return _db