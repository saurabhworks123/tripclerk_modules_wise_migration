# Database Schema - NTU Travel Management System

## Database Information

- **Database Name**: `ntu_travel`
- **MongoDB URI**: `mongodb://localhost:27017/ntu_travel`
- **Collections**: 2 (users, otps)

## Collections

### 1. Users Collection

**Collection Name**: `users`

**Description**: Stores all user account information including authentication details, personal information, and verification status.

**Indexes**:
- `email` - Unique index for email addresses
- `employee_id` - Unique index for employee IDs
- `phone` - Non-unique index for phone numbers
- `created_at` - Index for sorting by creation date

**Schema**:

```javascript
{
  // System Fields
  "_id": ObjectId("..."),                    // MongoDB auto-generated ID
  
  // Required Fields
  "first_name": "John",                      // User's first name
  "last_name": "Doe",                        // User's last name
  "email": "john.doe@ntu.edu",              // Email (unique, indexed)
  "password": "$2b$12$...",                  // Bcrypt hashed password
  "employee_id": "EMP001",                   // Employee ID (unique, indexed)
  "phone": "5551234567",                     // Phone number (indexed)
  "department": "Engineering",               // User's department
  
  // Optional Fields
  "carrier": "Verizon",                      // Mobile carrier
  "job_title": "TRAVELER",                   // Job title (default: TRAVELER)
  "dob": "1990-01-01",                       // Date of birth (optional)
  "gender": "Male",                          // Gender (optional)
  "address": "123 Main St, City, State",    // Physical address (optional)
  "join_date": "2024-01-01",                // Date joined organization (optional)
  
  // Verification Status
  "email_verified": false,                   // Email verification status
  "phone_verified": false,                   // Phone verification status
  
  // Timestamps
  "created_at": ISODate("2024-01-22T10:30:00Z"),  // Account creation timestamp
  "updated_at": ISODate("2024-01-22T10:30:00Z"),  // Last update timestamp
  "last_login": ISODate("2024-01-22T11:00:00Z")   // Last successful login
}
```

**Field Descriptions**:

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| _id | ObjectId | Yes (auto) | Yes | MongoDB document ID |
| first_name | String | Yes | No | User's first name |
| last_name | String | Yes | No | User's last name |
| email | String | Yes | Yes | Email address (must be valid format) |
| password | String | Yes | No | Bcrypt hashed password (never stored plain) |
| employee_id | String | Yes | Yes | Unique employee identifier |
| phone | String | Yes | No | Phone number (10 digits) |
| department | String | Yes | No | Department name |
| carrier | String | No | No | Mobile carrier for SMS |
| job_title | String | No | No | Job title (default: TRAVELER) |
| dob | String | No | No | Date of birth (YYYY-MM-DD) |
| gender | String | No | No | Gender |
| address | String | No | No | Physical address |
| join_date | String | No | No | Organization join date |
| email_verified | Boolean | Yes (auto) | No | Email verification status |
| phone_verified | Boolean | Yes (auto) | No | Phone verification status |
| created_at | DateTime | Yes (auto) | No | Account creation timestamp |
| updated_at | DateTime | Yes (auto) | No | Last modification timestamp |
| last_login | DateTime | No | No | Last successful login time |

**Sample Document**:

```javascript
{
  "_id": ObjectId("65b8f5e3a1b2c3d4e5f67890"),
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@ntu.edu",
  "password": "$2b$12$KpVq8GYL.5rYqmW3uZ9lO.xM/jVHvK8X5Kp2YsNmWqL3jVr5YsKp2",
  "department": "Engineering",
  "employee_id": "EMP001",
  "phone": "5551234567",
  "carrier": "Verizon",
  "job_title": "TRAVELER",
  "dob": "1990-05-15",
  "gender": "Male",
  "address": "123 Main Street, Crownpoint, NM 87313",
  "join_date": "2023-08-15",
  "email_verified": true,
  "phone_verified": true,
  "created_at": ISODate("2024-01-22T08:30:00.000Z"),
  "updated_at": ISODate("2024-01-22T09:15:00.000Z"),
  "last_login": ISODate("2024-01-22T14:30:00.000Z")
}
```

---

### 2. OTPs Collection

**Collection Name**: `otps`

**Description**: Stores One-Time Passwords (OTPs) for email and phone verification. Documents automatically expire after 5 minutes using MongoDB TTL index.

**Indexes**:
- `identifier` - Index for quick OTP lookup
- `created_at` - TTL index (expires after 300 seconds / 5 minutes)

**Schema**:

```javascript
{
  // System Fields
  "_id": ObjectId("..."),                    // MongoDB auto-generated ID
  
  // OTP Fields
  "identifier": "email_john.doe@ntu.edu",   // Unique identifier (email_* or phone_*)
  "otp": "123456",                           // 6-digit OTP code
  
  // Timestamps
  "created_at": ISODate("2024-01-22T10:30:00Z"),  // Creation time (TTL index)
  "expires_at": ISODate("2024-01-22T10:35:00Z")   // Expiration time (5 min from created_at)
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| _id | ObjectId | Yes (auto) | MongoDB document ID |
| identifier | String | Yes | Unique key format: "email_{email}" or "phone_{phone}" |
| otp | String | Yes | 6-digit numeric OTP code |
| created_at | DateTime | Yes (auto) | Creation timestamp (TTL indexed) |
| expires_at | DateTime | Yes (auto) | Expiration timestamp (5 minutes from creation) |

**Identifier Format**:
- Email OTP: `email_john.doe@ntu.edu`
- Phone OTP: `phone_5551234567`

**TTL (Time To Live)**:
- Documents automatically deleted 300 seconds (5 minutes) after `created_at`
- MongoDB handles deletion automatically via TTL index
- No manual cleanup required

**Sample Documents**:

```javascript
// Email OTP
{
  "_id": ObjectId("65b8f6a2b1c2d3e4f5678901"),
  "identifier": "email_john.doe@ntu.edu",
  "otp": "123456",
  "created_at": ISODate("2024-01-22T10:30:00.000Z"),
  "expires_at": ISODate("2024-01-22T10:35:00.000Z")
}

// Phone OTP
{
  "_id": ObjectId("65b8f6a2b1c2d3e4f5678902"),
  "identifier": "phone_5551234567",
  "otp": "654321",
  "created_at": ISODate("2024-01-22T10:30:00.000Z"),
  "expires_at": ISODate("2024-01-22T10:35:00.000Z")
}
```

---

## Relationships

### User ↔ OTP

- **Type**: One-to-Many (temporary)
- **Relationship**: A user can have multiple OTPs during signup (email and phone)
- **Duration**: Temporary (OTPs auto-expire after 5 minutes)
- **Link**: Linked via email or phone number in identifier field

**Example**:
```
User: john.doe@ntu.edu, phone: 5551234567
  ↓
OTPs:
  - email_john.doe@ntu.edu → "123456"
  - phone_5551234567 → "654321"
```

---

## MongoDB Queries

### Common Queries

**Find user by email**:
```javascript
db.users.findOne({ email: "john.doe@ntu.edu" })
```

**Find verified users**:
```javascript
db.users.find({ 
  email_verified: true, 
  phone_verified: true 
})
```

**Find users by department**:
```javascript
db.users.find({ department: "Engineering" })
```

**Count total users**:
```javascript
db.users.countDocuments()
```

**Find active OTPs**:
```javascript
db.otps.find({ 
  expires_at: { $gt: new Date() } 
})
```

**Get user with phone verification pending**:
```javascript
db.users.find({ 
  email_verified: true, 
  phone_verified: false 
})
```

---

## Backup and Restore

### Backup Database

```bash
# Backup entire database
mongodump --uri="mongodb://localhost:27017/ntu_travel" --out=./backup

# Backup specific collection
mongodump --uri="mongodb://localhost:27017/ntu_travel" --collection=users --out=./backup
```

### Restore Database

```bash
# Restore entire database
mongorestore --uri="mongodb://localhost:27017/ntu_travel" ./backup/ntu_travel

# Restore specific collection
mongorestore --uri="mongodb://localhost:27017/ntu_travel" --collection=users ./backup/ntu_travel/users.bson
```

---

## Data Validation

MongoDB validation rules are applied to ensure data integrity:

### Users Collection Validation

- Email must match regex pattern for valid email format
- Required fields: first_name, last_name, email, password, employee_id, phone
- Email and employee_id must be unique
- Boolean fields for verification status

### OTPs Collection Validation

- OTP must be 6-digit string
- Created_at must be DateTime
- Auto-expiration via TTL index

---

## Performance Considerations

1. **Indexes**: All frequently queried fields are indexed
2. **TTL Index**: Automatic cleanup of expired OTPs
3. **Unique Constraints**: Prevent duplicate emails and employee IDs
4. **Document Size**: Users collection documents are typically <2KB

---

## Security Notes

1. **Passwords**: Always stored as bcrypt hashes, never plain text
2. **OTPs**: Automatically expire and are deleted after use or timeout
3. **Indexes**: Unique indexes prevent duplicate accounts
4. **Validation**: MongoDB schema validation ensures data integrity
