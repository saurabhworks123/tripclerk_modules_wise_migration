from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/ntu_travel")
DATABASE_NAME = "ntu_travel"

client: Optional[AsyncIOMotorClient] = None
db = None

async def connect_to_mongo():
    """Connect to MongoDB and initialize database"""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DATABASE_NAME]
        
        # Test the connection
        await client.admin.command('ping')
        print(f"✓ MongoDB connected successfully to database: {DATABASE_NAME}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {str(e)}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("✓ MongoDB connection closed")

async def create_indexes():
    """Create indexes for collections"""
    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("employee_id", unique=True)
        await db.users.create_index("phone")
        
        # OTP collection indexes
        await db.otps.create_index("identifier")
        await db.otps.create_index("created_at", expireAfterSeconds=300)  # Auto-expire after 5 minutes
        
        print("✓ Database indexes created successfully")
    except Exception as e:
        print(f"⚠ Index creation warning: {str(e)}")

def get_database():
    """Get database instance"""
    return db
