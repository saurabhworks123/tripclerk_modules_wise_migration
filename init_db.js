// MongoDB Initialization Script for NTU Travel Management System
// Run this script using: mongosh mongodb://localhost:27017/ntu_travel < init_db.js

print("================================================");
print("NTU Travel Management System - Database Setup");
print("================================================");
print("");

// Switch to ntu_travel database
use ntu_travel;

print("Creating collections...");

// Create users collection with validation
db.createCollection("users", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["first_name", "last_name", "email", "password", "employee_id", "phone"],
         properties: {
            first_name: {
               bsonType: "string",
               description: "First name is required and must be a string"
            },
            last_name: {
               bsonType: "string",
               description: "Last name is required and must be a string"
            },
            email: {
               bsonType: "string",
               pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
               description: "Email is required and must be valid"
            },
            password: {
               bsonType: "string",
               description: "Password is required"
            },
            employee_id: {
               bsonType: "string",
               description: "Employee ID is required"
            },
            phone: {
               bsonType: "string",
               description: "Phone number is required"
            },
            email_verified: {
               bsonType: "bool",
               description: "Email verification status"
            },
            phone_verified: {
               bsonType: "bool",
               description: "Phone verification status"
            }
         }
      }
   }
});

print("✓ Users collection created");

// Create OTPs collection
db.createCollection("otps");
print("✓ OTPs collection created");

print("");
print("Creating indexes...");

// Users collection indexes
db.users.createIndex({ "email": 1 }, { unique: true, name: "email_unique" });
print("✓ Email unique index created");

db.users.createIndex({ "employee_id": 1 }, { unique: true, name: "employee_id_unique" });
print("✓ Employee ID unique index created");

db.users.createIndex({ "phone": 1 }, { name: "phone_index" });
print("✓ Phone index created");

db.users.createIndex({ "created_at": 1 }, { name: "created_at_index" });
print("✓ Created at index created");

// OTPs collection indexes
db.otps.createIndex({ "identifier": 1 }, { name: "identifier_index" });
print("✓ OTP identifier index created");

db.otps.createIndex({ "created_at": 1 }, { expireAfterSeconds: 300, name: "ttl_index" });
print("✓ OTP TTL index created (5 minutes expiration)");

print("");
print("Verifying setup...");

// Show collections
var collections = db.getCollectionNames();
print("Collections in database:");
collections.forEach(function(coll) {
    print("  - " + coll);
});

print("");
print("Indexes on users collection:");
db.users.getIndexes().forEach(function(idx) {
    print("  - " + idx.name);
});

print("");
print("Indexes on otps collection:");
db.otps.getIndexes().forEach(function(idx) {
    print("  - " + idx.name);
});

print("");
print("================================================");
print("Database setup completed successfully!");
print("================================================");
print("");
print("You can now start the application using:");
print("  Windows: start.bat");
print("  Linux/Mac: ./start.sh");
print("");
