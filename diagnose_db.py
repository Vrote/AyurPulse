import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add the project root to sys.path to import app modules
# Assuming this script is run from the project root or Ayurpulse directory
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "Ayurpulse")))

from app.config.settings import settings

async def diagnostic():
    print(f"Connecting to MongoDB: {settings.MONGODB_URL}")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        await client.admin.command("ping")
        print("MongoDB Ping successful.")
    except Exception as e:
        print(f"MongoDB Ping failed: {e}")
        return

    users_count = await db["users"].count_documents({})
    doctors_count = await db["doctors"].count_documents({})
    
    print(f"Users in 'users' collection: {users_count}")
    print(f"Users in 'doctors' collection: {doctors_count}")
    
    if users_count > 0:
        print("Users found:")
        async for user in db["users"].find({}):
            print(f" - {user.get('email')} (Role: {user.get('role')})")
            
    if doctors_count > 0:
        print("Doctors found:")
        async for doc in db["doctors"].find({}):
            print(f" - {doc.get('email')} (Role: {doc.get('role')})")

if __name__ == "__main__":
    asyncio.run(diagnostic())
