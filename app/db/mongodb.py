from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.config.settings import settings

_client = None
_db     = None


async def connect_db():
    """
    Connect to MongoDB and create all collections + indexes on startup.

    Database : Ayurpulse_db  (from .env → DATABASE_NAME)

    Collections created automatically:
    ┌─────────────────────┬──────────────────────────────────────────────────┐
    │ Collection          │ Purpose                                          │
    ├─────────────────────┼──────────────────────────────────────────────────┤
    │ users               │ Registered accounts (Feature 2 — Auth)           │
    │ refresh_tokens      │ Active JWT refresh tokens (Feature 2)            │
    │ token_blacklist     │ Logged-out tokens — TTL 24h (Feature 2)          │
    │ skin_predictions    │ Every AI prediction result (Feature 1)           │
    │ plans               │ Generated 7-day Ayurvedic plans (Feature 3)      │
    │ plan_progress       │ Daily check-ins — ticks + skin rating (Feature 3)│
    └─────────────────────┴──────────────────────────────────────────────────┘

    All indexes are created with create_index() which is idempotent —
    safe to run on every startup, never duplicates.
    """
    global _client, _db
    try:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000   # fail fast if MongoDB unreachable
        )
        # Verify connection before proceeding
        await _client.admin.command("ping")
        _db = _client[settings.DATABASE_NAME]

        # ── FEATURE 2: AUTH ────────────────────────────────────────────────────

        # users.email — unique, used on every login lookup
        await _db["users"].create_index(
            "email", unique=True
        )
        # users.role — filter doctors from users quickly
        await _db["users"].create_index("role")

        # refresh_tokens.token — unique, fast validate/delete on refresh or logout
        await _db["refresh_tokens"].create_index(
            "token", unique=True
        )
        # refresh_tokens.user_id — fast delete all tokens on account deletion
        await _db["refresh_tokens"].create_index("user_id")

        # token_blacklist.token — unique, checked on every protected request
        await _db["token_blacklist"].create_index(
            "token", unique=True
        )
        # token_blacklist TTL — MongoDB auto-deletes documents after 24 hours
        # keeps the blacklist small without any manual cleanup job
        await _db["token_blacklist"].create_index(
            "blacklisted_at",
            expireAfterSeconds=86400   # 24 hours
        )

        # ── FEATURE 1: SKIN PREDICTIONS ───────────────────────────────────────

        # skin_predictions — list user's history, newest first
        await _db["skin_predictions"].create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)]
        )

        # ── FEATURE 3: AYURVEDIC PLANS ────────────────────────────────────────

        # plans — get user's active plan quickly
        await _db["plans"].create_index(
            [("user_id", ASCENDING), ("status", ASCENDING)]
        )
        # plans — list user's plan history, newest first
        await _db["plans"].create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)]
        )

        # plan_progress — unique: one check-in document per plan per day
        # if user re-submits Day 1, it updates the same document
        await _db["plan_progress"].create_index(
            [("plan_id", ASCENDING), ("day", ASCENDING)],
            unique=True
        )
        # plan_progress — get all check-ins for a user sorted by date
        await _db["plan_progress"].create_index(
            [("user_id", ASCENDING), ("checked_at", DESCENDING)]
        )

        print(f"[AyurPulse] MongoDB connected → {settings.DATABASE_NAME}")
        print("[AyurPulse] Collections ready:")
        print("  Auth     → users | refresh_tokens | token_blacklist")
        print("  Feature1 → skin_predictions")
        print("  Feature3 → plans | plan_progress")

    except Exception as e:
        print(f"[AyurPulse] MongoDB connection failed: {e}")
        print("[AyurPulse] Running without database — auth and plan features unavailable.")
        _db = None


async def disconnect_db():
    """Close MongoDB connection gracefully on app shutdown."""
    global _client
    if _client:
        _client.close()
        print("[AyurPulse] MongoDB disconnected.")


def get_db():
    """Return the active database instance. Returns None if not connected."""
    return _db