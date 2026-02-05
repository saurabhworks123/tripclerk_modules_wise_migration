# Quick Start Guide - NTU Travel Management System

## 🚀 Get Started in 5 Minutes

### Step 1: Ensure MongoDB is Running

**Check if MongoDB is running:**
```bash
mongosh mongodb://localhost:27017/ntu_travel
```

If you see the MongoDB shell, you're good! Type `exit` to close it.

**If MongoDB is not running:**

- **Windows**: Open Services and start "MongoDB Server"
- **Linux**: `sudo systemctl start mongod`
- **Mac**: `brew services start mongodb-community`

### Step 2: Start the Application

**Windows:**
```bash
# Just double-click start.bat
# OR run from command prompt:
start.bat
```

**Linux/Mac:**
```bash
# Make executable (first time only)
chmod +x start.sh

# Run
./start.sh
```

### Step 3: Open the API Documentation

Once started, open in your browser:
```
http://localhost:8000/docs
```

## 📝 Test the API

### 1. Create a New User (Signup)

In the API docs at `/docs`:
1. Find **POST /auth/signup**
2. Click "Try it out"
3. Fill in the request body:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@ntu.edu",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "department": "Engineering",
  "employee_id": "EMP001",
  "phone": "5551234567",
  "job_title": "TRAVELER"
}
```
4. Click "Execute"
5. **Check the console** where the app is running - you'll see the OTP codes printed!

### 2. Verify Email

1. Find **POST /auth/verify-email-otp**
2. Click "Try it out"
3. Enter:
```json
{
  "email": "john.doe@ntu.edu",
  "otp": "123456"
}
```
(Use the OTP from the console output)
4. Click "Execute"

### 3. Verify Phone

1. Find **POST /auth/verify-phone-otp**
2. Click "Try it out"
3. Enter:
```json
{
  "phone": "5551234567",
  "otp": "654321"
}
```
(Use the phone OTP from the console output)
4. Click "Execute"

### 4. Login

1. Find **POST /auth/login**
2. Click "Try it out"
3. Enter:
```json
{
  "email": "john.doe@ntu.edu",
  "password": "SecurePass123"
}
```
4. Click "Execute"
5. You should see "Login successful!"

## 🔍 Verify Database

You can check the data in MongoDB:

```bash
# Connect to MongoDB
mongosh mongodb://localhost:27017/ntu_travel

# View all users
db.users.find().pretty()

# View all OTPs
db.otps.find().pretty()

# Count users
db.users.countDocuments()

# Exit
exit
```

## 🐛 Troubleshooting

### Application won't start?
1. Make sure Python 3.8+ is installed: `python --version`
2. Make sure MongoDB is running
3. Check if port 8000 is not already in use

### Can't connect to MongoDB?
1. Verify MongoDB is running: `mongosh mongodb://localhost:27017`
2. Check if the MongoDB service is started
3. Ensure no firewall is blocking port 27017

### OTP not showing?
- OTPs are printed to the console where the application is running
- Look for lines starting with 📧 (email) or 📱 (phone)
- In production, these would be sent via email/SMS

## 📚 Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore all endpoints in the API documentation
3. Check the database schema and indexes
4. Customize the application for your needs

## 🎯 Key URLs

- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## 💡 Tips

- **Development Mode**: OTPs are printed to console
- **Production Mode**: Configure email/SMS providers in `.env`
- **Database Browser**: Use MongoDB Compass for visual database management
- **API Testing**: Use Postman or the built-in Swagger UI

---

**Need Help?** Check the console output for errors and the README.md for detailed troubleshooting.
