#!/usr/bin/env python3
"""
Test MongoDB connection and database setup
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017/ntu_travel"
DATABASE_NAME = "ntu_travel"

async def test_connection():
    """Test MongoDB connection"""
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    print()
    
    try:
        # Connect to MongoDB
        print(f"Connecting to: {MONGO_URI}")
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DATABASE_NAME]
        
        # Test connection
        print("Testing connection...")
        await client.admin.command('ping')
        print("✓ Connection successful!")
        print()
        
        # List databases
        print("Available databases:")
        db_list = await client.list_database_names()
        for db_name in db_list:
            print(f"  - {db_name}")
        print()
        
        # List collections in ntu_travel database
        print(f"Collections in '{DATABASE_NAME}' database:")
        collections = await db.list_collection_names()
        if collections:
            for coll in collections:
                count = await db[coll].count_documents({})
                print(f"  - {coll} ({count} documents)")
        else:
            print("  No collections found (database will be created on first write)")
        print()
        
        # Check indexes on users collection
        if "users" in collections:
            print("Indexes on 'users' collection:")
            indexes = await db.users.index_information()
            for idx_name, idx_info in indexes.items():
                print(f"  - {idx_name}: {idx_info.get('key', [])}")
            print()
        
        # Check indexes on otps collection
        if "otps" in collections:
            print("Indexes on 'otps' collection:")
            indexes = await db.otps.index_information()
            for idx_name, idx_info in indexes.items():
                expiry = idx_info.get('expireAfterSeconds', None)
                if expiry:
                    print(f"  - {idx_name}: {idx_info.get('key', [])} (TTL: {expiry}s)")
                else:
                    print(f"  - {idx_name}: {idx_info.get('key', [])}")
            print()
        
        # Server info
        print("Server information:")
        server_info = await client.server_info()
        print(f"  - MongoDB Version: {server_info.get('version', 'Unknown')}")
        print(f"  - Server: {MONGO_URI}")
        print()
        
        print("=" * 60)
        print("✓ All tests passed! Database is ready to use.")
        print("=" * 60)
        
        # Close connection
        client.close()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ Connection failed!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure MongoDB is running")
        print("  2. Check if port 27017 is accessible")
        print("  3. Verify the connection string")
        print()
        print("To start MongoDB:")
        print("  - Windows: Start MongoDB service from Services")
        print("  - Linux: sudo systemctl start mongod")
        print("  - Mac: brew services start mongodb-community")
        print()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_connection())
