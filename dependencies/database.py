"""
Database Connection and Dependency
Compatible with unified main.py
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
from functools import lru_cache

# Global database connection
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


class Settings:
    """Application settings"""
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "ntu_travel")
    
    # File upload settings
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours


@lru_cache()
def get_settings() -> Settings:
    return Settings()


async def connect_to_mongo():
    """Connect to MongoDB"""
    global _client, _database
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _database = _client[settings.MONGODB_DATABASE]
    
    # Test connection
    await _client.admin.command('ping')
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}")
    
    # Create indexes
    try:
        await _database.users.create_index("email", unique=True)
        await _database.users.create_index("employee_id", unique=True)
        await _database.travel_requests.create_index("traveler_id")
        await _database.travel_requests.create_index("status")
        await _database.travel_requests.create_index("ta_number")
        await _database.otps.create_index("identifier")
        await _database.otps.create_index("created_at", expireAfterSeconds=600)
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️ Index warning: {e}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        print("✅ MongoDB connection closed")


def set_database(db: AsyncIOMotorDatabase):
    """Set database instance from main.py"""
    global _database
    _database = db


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance - dependency injection"""
    global _database
    
    # If database is not set, try to connect synchronously (fallback)
    if _database is None:
        import asyncio
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context but DB not initialized
                # This shouldn't happen if lifespan is working
                settings = get_settings()
                global _client
                _client = AsyncIOMotorClient(settings.MONGODB_URI)
                _database = _client[settings.MONGODB_DATABASE]
                print(f"⚠️ Late database connection to: {settings.MONGODB_DATABASE}")
            else:
                loop.run_until_complete(connect_to_mongo())
        except RuntimeError:
            # No event loop, create one
            asyncio.run(connect_to_mongo())
    
    return _database


# Dependency for FastAPI - async version
async def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency for database access"""
    global _database
    
    if _database is None:
        await connect_to_mongo()
    
    return _database


# Collection shortcuts
def get_collection(name: str):
    """Get a specific collection"""
    db = get_database()
    return db[name]


# Commonly used collections
async def get_travel_requests_collection():
    return get_database()["travel_requests"]


async def get_users_collection():
    return get_database()["users"]


async def get_departments_collection():
    return get_database()["departments"]


async def get_notifications_collection():
    return get_database()["notifications"]


async def get_counters_collection():
    return get_database()["counters"]