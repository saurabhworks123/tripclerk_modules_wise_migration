# NTU Travel Management System

A comprehensive travel management system built for Navajo Technical University using FastAPI and MongoDB.

## 🚀 Features

- **User Authentication**
  - Email/Password based signup and login
  - OTP verification for email and phone
  - Password hashing with bcrypt
  - Secure user session management

- **Database**
  - MongoDB for flexible document storage
  - Automatic indexing for performance
  - TTL indexes for OTP expiration

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8 or higher
- MongoDB 4.4 or higher
- pip (Python package manager)

## 🔧 Installation

### 1. Clone or Extract the Project

If you have the zip file, extract it to your desired location.

### 2. Install MongoDB (if not already installed)

**Windows:**
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Install with default settings
3. MongoDB will start automatically as a Windows service

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install mongodb

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

**macOS:**
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community
```

### 3. Verify MongoDB is Running

```bash
# Test MongoDB connection
mongosh mongodb://localhost:27017/ntu_travel
```

You should see the MongoDB shell. Type `exit` to close it.

## 🏃 Running the Application

### Quick Start (Recommended)

**Windows:**
```bash
# Double-click start.bat
# OR run from command prompt:
start.bat
```

**Linux/Mac:**
```bash
# Make the script executable (first time only)
chmod +x start.sh

# Run the script
./start.sh
```

### Manual Start

1. **Create Virtual Environment:**
```bash
python -m venv venv
```

2. **Activate Virtual Environment:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install Dependencies:**
```bash
pip install -r app/requirements.txt
```

4. **Start the Application:**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 Access the Application

Once the application is running:

- **API Documentation (Swagger UI):** http://localhost:8000/docs
- **Alternative Documentation (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Root Endpoint:** http://localhost:8000/

## 📡 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Login with email and password |
| POST | `/auth/verify-email-otp` | Verify email with OTP |
| POST | `/auth/verify-phone-otp` | Verify phone with OTP |
| POST | `/auth/resend-otp` | Resend OTP to email/phone |
| GET | `/auth/profile/{email}` | Get user profile |

### Example Requests

**Signup:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@ntu.edu",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123",
    "department": "Engineering",
    "employee_id": "EMP001",
    "phone": "5551234567",
    "job_title": "TRAVELER"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@ntu.edu",
    "password": "SecurePass123"
  }'
```

**Verify Email OTP:**
```bash
curl -X POST "http://localhost:8000/auth/verify-email-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@ntu.edu",
    "otp": "123456"
  }'
```

## 🗄️ Database Schema

### Users Collection

```javascript
{
  "_id": ObjectId,
  "first_name": String,
  "last_name": String,
  "email": String (unique, indexed),
  "password": String (hashed),
  "department": String,
  "employee_id": String (unique, indexed),
  "phone": String (indexed),
  "carrier": String,
  "job_title": String,
  "dob": String,
  "gender": String,
  "address": String,
  "join_date": String,
  "email_verified": Boolean,
  "phone_verified": Boolean,
  "created_at": DateTime,
  "updated_at": DateTime,
  "last_login": DateTime
}
```

### OTPs Collection

```javascript
{
  "_id": ObjectId,
  "identifier": String (indexed),
  "otp": String,
  "created_at": DateTime (TTL index - auto-expires after 5 minutes),
  "expires_at": DateTime
}
```

## 🔒 Security Features

- **Password Hashing:** All passwords are hashed using bcrypt
- **OTP Verification:** Two-factor authentication for email and phone
- **Auto-expiring OTPs:** OTPs automatically expire after 5 minutes
- **Input Validation:** Pydantic models validate all input data
- **Unique Constraints:** Email and employee_id must be unique

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the root directory (or copy from `.env.example`):

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/ntu_travel

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
```

### MongoDB Connection String Format

```
mongodb://[username:password@]host[:port]/database[?options]
```

Examples:
- Local: `mongodb://localhost:27017/ntu_travel`
- With Auth: `mongodb://admin:password@localhost:27017/ntu_travel`
- MongoDB Atlas: `mongodb+srv://username:password@cluster.mongodb.net/ntu_travel`

## 📊 Database Management

### View Collections

```bash
mongosh mongodb://localhost:27017/ntu_travel

# List all collections
show collections

# View users
db.users.find().pretty()

# View OTPs
db.otps.find().pretty()

# Count documents
db.users.countDocuments()
```

### Create Indexes Manually (if needed)

```javascript
// The application creates these automatically, but you can also run manually:
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "employee_id": 1 }, { unique: true })
db.users.createIndex({ "phone": 1 })
db.otps.createIndex({ "identifier": 1 })
db.otps.createIndex({ "created_at": 1 }, { expireAfterSeconds: 300 })
```

## 🧪 Testing the API

### Using Swagger UI (Recommended)

1. Open http://localhost:8000/docs
2. Click on any endpoint to expand
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

### Using cURL

See the "Example Requests" section above.

### Using Postman

1. Import the API by creating requests for each endpoint
2. Set the base URL to `http://localhost:8000`
3. Add the appropriate headers and body

## 📝 Development Notes

### Project Structure

```
tripclerk_modules_wise_migration/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py      # Pydantic models
│   │   ├── routes.py      # Authentication endpoints
│   │   └── utils.py       # Helper functions
│   ├── DataBase/
│   │   ├── models.py      # Database models (legacy)
│   │   └── mongodb.py     # MongoDB connection
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
├── .env                   # Environment variables
├── .env.example          # Environment template
├── start.sh              # Linux/Mac startup script
├── start.bat             # Windows startup script
└── README.md             # This file
```

### Adding New Features

1. Create new route modules in the appropriate directory
2. Register routes in `main.py`
3. Update database models if needed
4. Add any new dependencies to `requirements.txt`

## 🐛 Troubleshooting

### MongoDB Connection Issues

**Error: "MongoDB connection failed"**
- Ensure MongoDB is running: `sudo systemctl status mongod` (Linux) or check Services (Windows)
- Verify the connection string in `.env`
- Check if port 27017 is not blocked by firewall

### Module Import Errors

**Error: "ModuleNotFoundError: No module named 'xyz'"**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r app/requirements.txt`

### Port Already in Use

**Error: "Address already in use"**
- Change the port in the startup command: `--port 8001`
- Or kill the process using port 8000

### OTP Not Working

- Check console output for OTP codes (development mode)
- Ensure OTP hasn't expired (5 minute limit)
- Verify the identifier (email/phone) matches exactly

## 📞 Support

For issues or questions:
- Check the API documentation at `/docs`
- Review the MongoDB logs
- Check application logs in the console

## 🔄 Updates and Maintenance

### Updating Dependencies

```bash
pip install --upgrade -r app/requirements.txt
```

### Database Backup

```bash
# Backup
mongodump --uri="mongodb://localhost:27017/ntu_travel" --out=./backup

# Restore
mongorestore --uri="mongodb://localhost:27017/ntu_travel" ./backup/ntu_travel
```

## 📜 License

This project is proprietary to Navajo Technical University.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database: [MongoDB](https://www.mongodb.com/)
- Password Hashing: [Passlib](https://passlib.readthedocs.io/)
