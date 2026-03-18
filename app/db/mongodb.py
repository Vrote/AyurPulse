from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

_client = None
_db = None


async def connect_db():
    """
    Connect to MongoDB and create required indexes on startup.

    Indexes created:
        users.email          — unique, for fast login lookup
        refresh_tokens.token — unique, for fast token validation
        token_blacklist.token — unique, for fast blacklist lookup
        token_blacklist.blacklisted_at — TTL index, auto-deletes expired tokens after 24h
    """
    global _client, _db
    try:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000   # fail fast if MongoDB is not reachable
        )
        # Ping to confirm connection
        await _client.admin.command("ping")
        _db = _client[settings.DATABASE_NAME]

        # ── Create indexes ─────────────────────────────────────────────────
        # Unique index on email — prevents duplicate accounts
        await _db["users"].create_index("email", unique=True)

        # Unique index on refresh token — fast lookup on refresh/logout
        await _db["refresh_tokens"].create_index("token", unique=True)

        # Unique index on blacklisted token
        await _db["token_blacklist"].create_index("token", unique=True)

        # TTL index — MongoDB auto-deletes blacklisted tokens after 24 hours
        # Keeps the blacklist collection small without manual cleanup
        await _db["token_blacklist"].create_index(
            "blacklisted_at",
            expireAfterSeconds=86400   # 24 hours
        )

        print(f"[AyurPulse] MongoDB connected → {settings.DATABASE_NAME}")

    except Exception as e:
        print(f"[AyurPulse] MongoDB connection failed: {e}")
        print("[AyurPulse] Running without database — auth features will be unavailable.")
        _db = None


async def disconnect_db():
    """Close MongoDB connection gracefully on shutdown."""
    global _client
    if _client:
        _client.close()
        print("[AyurPulse] MongoDB disconnected.")


def get_db():
    """Return the active database instance, or None if not connected."""
    return _db