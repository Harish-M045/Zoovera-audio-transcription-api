from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

_client: AsyncIOMotorClient | None = None

def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client

def get_mongo_collection():
    client = get_mongo_client()
    return client[settings.MONGO_DB][settings.MONGO_COLLECTION]

async def check_mongo_connection() -> bool:
    try:
        client = get_mongo_client()
        await client.admin.command("ping")
        return True
    except Exception as e:
        print("MongoDB connection failed:", e)
        return False
