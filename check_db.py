import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

async def main():
    print(f"Connecting to MongoDB: {settings.MONGODB_URL}")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    count = await db['user_plans'].count_documents({})
    print("User plans count:", count)
    
    async for p in db['user_plans'].find({}):
        print(f"Plan ID: {p.get('_id')} | Title: {p.get('title')} | User: {p.get('user_id')}")

if __name__ == '__main__':
    asyncio.run(main())
