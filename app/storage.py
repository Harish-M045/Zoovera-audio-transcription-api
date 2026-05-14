from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

client = None


def get_mongo_client(uri: str) -> AsyncIOMotorClient:
    """
    Returns a cached global client so MongoDB does NOT open 
    multiple connections every time an endpoint is called.
    """
    global client
    if client is None:
        client = AsyncIOMotorClient(uri)
    return client


def get_mongo_collection(uri: str, db_name: str, collection_name: str):
    """
    Returns the collection instance.
    """
    mongo_client = get_mongo_client(uri)
    db = mongo_client[db_name]
    return db[collection_name]


async def check_mongo_connection(uri: str) -> bool:
    """
    Performs a 'ping' command to verify if MongoDB is running.
    """
    try:
        mongo_client = get_mongo_client(uri)
        await mongo_client.admin.command("ping")
        return True
    except ConnectionFailure:
        return False
    except Exception:
        return False
