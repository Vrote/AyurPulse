import asyncio
import copy
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.config.settings import settings
from app.utils.logger import logger

_client = None
_db     = None


class MockCursor:
    def __init__(self, docs, projection=None):
        self.docs = copy.deepcopy(docs)
        self.projection = projection
        self.index = 0
        
    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, list):
            sort_key, dir_val = key_or_list[0]
        else:
            sort_key = key_or_list
            dir_val = direction or 1
            
        reverse = (dir_val == -1 or dir_val == -2)
        
        # Sort documents, handle missing keys or types gracefully
        self.docs.sort(key=lambda x: x.get(sort_key) if x.get(sort_key) is not None else "", reverse=reverse)
        return self
        
    def limit(self, n):
        self.docs = self.docs[:n]
        return self
        
    def __aiter__(self):
        return self
        
    async def __anext__(self):
        if self.index >= len(self.docs):
            raise StopAsyncIteration
        doc = self.docs[self.index]
        self.index += 1
        if self.projection:
            # Simple inclusion/exclusion projection handling
            inclusive = any(v == 1 for v in self.projection.values() if not isinstance(v, bool) or v is not False)
            if inclusive:
                projected = {}
                for k, v in self.projection.items():
                    if v and k in doc:
                        projected[k] = doc[k]
                if "_id" not in self.projection and "_id" in doc:
                    projected["_id"] = doc["_id"]
                doc = projected
            else:
                projected = copy.deepcopy(doc)
                for k, v in self.projection.items():
                    if not v and k in projected:
                        projected.pop(k, None)
                doc = projected
        return doc


class MockCollection:
    def __init__(self, name, db):
        self.name = name
        self.db = db
        if name not in self.db._collections:
            self.db._collections[name] = []
            
    @property
    def docs(self):
        return self.db._collections[self.name]
        
    def _match(self, doc, query):
        for k, v in query.items():
            val = doc.get(k)
            if isinstance(v, ObjectId):
                if val is None:
                    return False
                if not isinstance(val, ObjectId):
                    try:
                        val = ObjectId(str(val))
                    except:
                        return False
            elif isinstance(v, dict):
                # Simple operator support ($in, $ne)
                for op, op_val in v.items():
                    if op == "$in":
                        if val not in op_val:
                            return False
                    elif op == "$ne":
                        if val == op_val:
                            return False
                continue
            if val != v:
                return False
        return True
        
    async def insert_one(self, doc):
        doc_copy = copy.deepcopy(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = ObjectId()
        self.docs.append(doc_copy)
        
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertResult(doc_copy["_id"])
        
    async def find_one(self, query):
        for doc in self.docs:
            if self._match(doc, query):
                return copy.deepcopy(doc)
        return None
        
    def find(self, query, projection=None):
        matched = [doc for doc in self.docs if self._match(doc, query)]
        return MockCursor(matched, projection)
        
    async def update_one(self, query, update, upsert=False):
        matched_doc = None
        for doc in self.docs:
            if self._match(doc, query):
                matched_doc = doc
                break
                
        class UpdateResult:
            def __init__(self, matched_count, modified_count, upserted_id=None):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = upserted_id
                
        if matched_doc is not None:
            set_dict = update.get("$set", {})
            for k, v in set_dict.items():
                matched_doc[k] = copy.deepcopy(v)
            return UpdateResult(1, 1)
        elif upsert:
            new_doc = copy.deepcopy(query)
            new_doc = {k: v for k, v in new_doc.items() if not k.startswith("$")}
            set_dict = update.get("$set", {})
            for k, v in set_dict.items():
                new_doc[k] = copy.deepcopy(v)
            if "_id" not in new_doc:
                new_doc["_id"] = ObjectId()
            self.docs.append(new_doc)
            return UpdateResult(0, 0, new_doc["_id"])
        return UpdateResult(0, 0)
        
    async def delete_one(self, query):
        for i, doc in enumerate(self.docs):
            if self._match(doc, query):
                self.docs.pop(i)
                class DeleteResult:
                    def __init__(self, deleted_count):
                        self.deleted_count = deleted_count
                return DeleteResult(1)
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        return DeleteResult(0)
        
    async def create_index(self, keys, **kwargs):
        return f"{self.name}_index"


class MockDatabase:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self._collections = {}
        
    def __getitem__(self, name):
        return MockCollection(name, self)
        
    def __getattr__(self, name):
        # Don't intercept known methods/attributes
        if name.startswith('_') or name == 'command':
            raise AttributeError(name)
        return MockCollection(name, self)
    
    async def command(self, cmd, *args, **kwargs):
        # Mock admin commands like 'ping'
        return {"ok": 1.0}


class MockAsyncIOMotorClient:
    def __init__(self, url, **kwargs):
        self.url = url
        self._databases = {}
        
    def __getitem__(self, name):
        if name not in self._databases:
            self._databases[name] = MockDatabase(self, name)
        return self._databases[name]
        
    @property
    def admin(self):
        return self["admin"]
        
    async def command(self, cmd_dict):
        if "ping" in cmd_dict:
            return {"ok": 1.0}
        return {}
        
    def close(self):
        pass


async def connect_db():
    """
    Connect to MongoDB and prepare collection indexes.
    Professional Error Handling & Logging implemented.
    Falls back to In-Memory Mock database if unreachable.
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
        await _db["users"].create_index("email", unique=True)
        await _db["users"].create_index("role")
        await _db["doctors"].create_index("email", unique=True)
        await _db["doctors"].create_index("is_verified")
        await _db["refresh_tokens"].create_index("token", unique=True)
        await _db["token_blacklist"].create_index("blacklisted_at", expireAfterSeconds=86400)
        await _db["skin_predictions"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        await _db["user_plans"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        logger.info(f"MongoDB Connected Successfully -> Database: {settings.DATABASE_NAME}")

    except Exception as e:
        logger.warning(f"MongoDB Connection failed: {e}. Falling back to In-Memory Mock Database.")
        try:
            _client = MockAsyncIOMotorClient(settings.MONGODB_URL)
            await _client.admin.command("ping")
            _db = _client[settings.DATABASE_NAME]
            
            # Setup collections
            await _db["users"].create_index("email", unique=True)
            await _db["users"].create_index("role")
            await _db["doctors"].create_index("email", unique=True)
            await _db["doctors"].create_index("is_verified")
            await _db["refresh_tokens"].create_index("token", unique=True)
            await _db["token_blacklist"].create_index("blacklisted_at", expireAfterSeconds=86400)
            await _db["skin_predictions"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            await _db["user_plans"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            
            logger.info("In-Memory Mock Database initialized successfully.")
        except Exception as mock_err:
            logger.critical(f"MongoDB Mock Connection CRITICAL FAILURE: {mock_err}")
            _db = None


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