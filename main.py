
# """
# NTU Travel Management System - Unified FastAPI Application
# All modules in ONE server: Auth, Travel Requests, Approvals, Reports, Admin

# Run with: uvicorn main:app --reload --port 8000

# NOTE: Authentication DISABLED for testing. Re-enable for production!
# """

# from fastapi import FastAPI, Request, HTTPException, status, Form, Query
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from datetime import datetime, timedelta
# from bson import ObjectId
# import os
# import random
# import string
# import bcrypt
# from pathlib import Path

# # Import database module - this will be shared with routers
# from dependencies.database import (
#     connect_to_mongo, 
#     close_mongo_connection, 
#     get_database,
#     get_settings
# )

# # ============================================================
# # AUTH UTILITIES
# # ============================================================

# def hash_password(password: str) -> str:
#     """Hash password using bcrypt"""
#     password_bytes = password.encode('utf-8')[:72]
#     salt = bcrypt.gensalt()
#     hashed = bcrypt.hashpw(password_bytes, salt)
#     return hashed.decode('utf-8')


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify password against hash"""
#     try:
#         password_bytes = plain_password.encode('utf-8')[:72]
#         hashed_bytes = hashed_password.encode('utf-8')
#         return bcrypt.checkpw(password_bytes, hashed_bytes)
#     except Exception as e:
#         print(f"Password verification error: {e}")
#         return False


# def generate_otp(length: int = 6) -> str:
#     """Generate random OTP"""
#     return ''.join(random.choices(string.digits, k=length))


# async def store_otp(identifier: str, otp: str, expiration: int = 10):
#     """Store OTP in MongoDB"""
#     db = get_database()
#     await db.otps.update_one(
#         {"identifier": identifier},
#         {
#             "$set": {
#                 "otp": otp,
#                 "created_at": datetime.utcnow(),
#                 "expires_at": datetime.utcnow() + timedelta(minutes=expiration)
#             }
#         },
#         upsert=True
#     )


# async def validate_otp(identifier: str, otp: str) -> bool:
#     """Validate OTP"""
#     db = get_database()
#     otp_data = await db.otps.find_one({"identifier": identifier})
    
#     if not otp_data:
#         return False
    
#     if datetime.utcnow() > otp_data['expires_at']:
#         await db.otps.delete_one({"identifier": identifier})
#         return False
    
#     is_valid = otp_data['otp'] == otp
#     if is_valid:
#         await db.otps.delete_one({"identifier": identifier})
    
#     return is_valid


# def send_otp_email(email: str, otp: str) -> bool:
#     """
#     Send OTP via SMTP email (actual email delivery)
#     Uses Gmail SMTP with app password from environment variables
#     """
#     import smtplib
#     from email.mime.text import MIMEText
#     from email.mime.multipart import MIMEMultipart
    
#     # SMTP Configuration from environment
#     SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
#     SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
#     EMAIL_ADDRESS = os.getenv("MAIL_USERNAME", os.getenv("EMAIL_ADDRESS", ""))
#     EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))
#     FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_ADDRESS)
    
#     if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
#         print(f"⚠️ SMTP credentials not configured. OTP for {email}: {otp}")
#         return False
    
#     try:
#         # Create email message
#         msg = MIMEMultipart("alternative")
#         msg["Subject"] = "NTU Travel Management - Your OTP Verification Code"
#         msg["From"] = FROM_EMAIL
#         msg["To"] = email
        
#         # Plain text body
#         text_body = f"""
# NTU Travel Management System

# Your OTP verification code is: {otp}

# This code will expire in 10 minutes.

# If you did not request this code, please ignore this email.

# Thank you,
# NTU Travel Desk Team
#         """
        
#         # HTML body
#         html_body = f"""
#         <html>
#         <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
#             <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
#                 <div style="text-align: center; padding: 20px; background: #413178; border-radius: 5px 5px 0 0;">
#                     <h1 style="color: white; margin: 0;">NTU Travel Management</h1>
#                 </div>
#                 <div style="padding: 30px; background: #f9f9f9; border: 1px solid #ddd; border-top: none;">
#                     <h2 style="color: #413178;">Email Verification Code</h2>
#                     <p>Hello,</p>
#                     <p>Your OTP verification code is:</p>
#                     <div style="text-align: center; margin: 30px 0;">
#                         <span style="font-size: 32px; font-weight: bold; color: #413178; 
#                                      background: #e8e4f0; padding: 15px 30px; border-radius: 5px;
#                                      letter-spacing: 5px;">{otp}</span>
#                     </div>
#                     <p style="color: #666; font-size: 14px;">
#                         ⏱️ This code will expire in <strong>10 minutes</strong>.
#                     </p>
#                     <p style="color: #999; font-size: 12px;">
#                         If you did not request this code, please ignore this email.
#                     </p>
#                 </div>
#                 <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
#                     <p>© 2025 NTU Travel Management System</p>
#                     <p>Navajo Technical University</p>
#                 </div>
#             </div>
#         </body>
#         </html>
#         """
        
#         msg.attach(MIMEText(text_body, "plain"))
#         msg.attach(MIMEText(html_body, "html"))
        
#         # Connect to SMTP server and send
#         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#             server.starttls()
#             server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
#             server.sendmail(FROM_EMAIL, email, msg.as_string())
        
#         print(f"✅ OTP email sent successfully to: {email}")
#         return True
        
#     except smtplib.SMTPAuthenticationError as e:
#         print(f"❌ SMTP Authentication failed: {e}")
#         print(f"📧 [FALLBACK] OTP for {email}: {otp}")
#         return False
#     except smtplib.SMTPException as e:
#         print(f"❌ SMTP Error: {e}")
#         print(f"📧 [FALLBACK] OTP for {email}: {otp}")
#         return False
#     except Exception as e:
#         print(f"❌ Email sending failed: {e}")
#         print(f"📧 [FALLBACK] OTP for {email}: {otp}")
#         return False


# def send_otp_sms(phone: str, otp: str):
#     """
#     Simulate sending OTP via SMS (kept as random code generation)
#     Phone OTP remains in console/simulation mode
#     """
#     print(f"📱 Sending OTP to phone: {phone}. OTP: {otp}")


# # ============================================================
# # PYDANTIC MODELS FOR AUTH
# # ============================================================

# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str


# class SignupRequest(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#     password: str
#     confirm_password: str
#     department: str
#     employee_id: str
#     phone: str
#     carrier: Optional[str] = None
#     job_title: Optional[str] = 'TRAVELER'
#     dob: Optional[str] = None
#     gender: Optional[str] = None
#     address: Optional[str] = None
#     join_date: Optional[str] = None


# class OTPRequest(BaseModel):
#     email: Optional[EmailStr] = None
#     otp: str
#     phone: Optional[str] = None


# # ============================================================
# # FASTAPI APPLICATION SETUP
# # ============================================================

# BASE_DIR = Path(__file__).resolve().parent


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Startup and shutdown events"""
#     # Connect to MongoDB on startup
#     await connect_to_mongo()
#     print("✅ Application started - all modules loaded")
#     yield
#     # Disconnect on shutdown
#     await close_mongo_connection()
#     print("✅ Application shutdown complete")


# app = FastAPI(
#     title="NTU Travel Management System",
#     description="Complete Travel Authorization and Reimbursement System with Auth",
#     version="3.0.0",
#     lifespan=lifespan
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Static files
# static_dir = BASE_DIR / "static"
# static_dir.mkdir(parents=True, exist_ok=True)
# app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# # Templates
# templates_dir = BASE_DIR / "templates"
# templates_dir.mkdir(parents=True, exist_ok=True)
# templates = Jinja2Templates(directory=str(templates_dir))


# # ============================================================
# # AUTH ROUTES - /auth/*
# # ============================================================

# from fastapi import APIRouter

# auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# @auth_router.post("/login")
# async def login(request: LoginRequest):
#     """Login user with email and password"""
#     db = get_database()
    
#     user = await db.users.find_one({"email": request.email})
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password"
#         )
    
#     if not verify_password(request.password, user["password"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password"
#         )
    
#     # Skip email verification check for testing
#     # if not user.get("email_verified", False):
#     #     raise HTTPException(
#     #         status_code=status.HTTP_403_FORBIDDEN,
#     #         detail="Please verify your email before logging in"
#     #     )
    
#     await db.users.update_one(
#         {"_id": user["_id"]},
#         {"$set": {"last_login": datetime.utcnow()}}
#     )
    
#     return {
#         "success": True,
#         "message": "Login successful!",
#         "user": {
#             "id": str(user["_id"]),
#             "email": user["email"],
#             "first_name": user.get("first_name", ""),
#             "last_name": user.get("last_name", ""),
#             "employee_id": user.get("employee_id", ""),
#             "department": user.get("department", ""),
#             "job_title": user.get("job_title", "TRAVELER"),
#             "role": user.get("role", "TRAVELER"),
#         }
#     }


# @auth_router.post("/signup")
# async def signup(request: SignupRequest):
#     """Register a new user"""
#     db = get_database()
    
#     if request.password != request.confirm_password:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Passwords do not match"
#         )
    
#     existing_user = await db.users.find_one({"email": request.email})
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     existing_employee = await db.users.find_one({"employee_id": request.employee_id})
#     if existing_employee:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Employee ID already registered"
#         )
    
#     email_otp = generate_otp()
#     phone_otp = generate_otp()
    
#     await store_otp(f"email_{request.email}", email_otp)
#     await store_otp(f"phone_{request.phone}", phone_otp)
    
#     user_data = {
#         "first_name": request.first_name,
#         "last_name": request.last_name,
#         "email": request.email,
#         "password": hash_password(request.password),
#         "department": request.department,
#         "employee_id": request.employee_id,
#         "phone": request.phone,
#         "carrier": request.carrier,
#         "job_title": request.job_title or "TRAVELER",
#         "role": "TRAVELER",
#         "dob": request.dob,
#         "gender": request.gender,
#         "address": request.address,
#         "join_date": request.join_date,
#         "email_verified": True,  # Auto-verify for testing
#         "phone_verified": True,  # Auto-verify for testing
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }
    
#     result = await db.users.insert_one(user_data)
    
#     send_otp_email(request.email, email_otp)
#     send_otp_sms(request.phone, phone_otp)
    
#     return {
#         "success": True,
#         "message": "Registration successful! OTP sent to your email and phone.",
#         "user_id": str(result.inserted_id),
#         "email": request.email,
#         "phone": request.phone,
#         "email_otp": email_otp,  # For testing only - remove in production
#         "phone_otp": phone_otp   # For testing only - remove in production
#     }


# @auth_router.post("/verify-email-otp")
# async def verify_email_otp(request: OTPRequest):
#     """Verify email OTP"""
#     db = get_database()
    
#     if not request.email:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email is required"
#         )
    
#     if not await validate_otp(f"email_{request.email}", request.otp):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired OTP"
#         )
    
#     result = await db.users.update_one(
#         {"email": request.email},
#         {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}}
#     )
    
#     if result.modified_count == 0:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return {"success": True, "message": "Email verified successfully!"}


# @auth_router.post("/verify-phone-otp")
# async def verify_phone_otp(request: OTPRequest):
#     """Verify phone OTP"""
#     db = get_database()
    
#     if not request.phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Phone number is required"
#         )
    
#     if not await validate_otp(f"phone_{request.phone}", request.otp):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired OTP"
#         )
    
#     result = await db.users.update_one(
#         {"phone": request.phone},
#         {"$set": {"phone_verified": True, "updated_at": datetime.utcnow()}}
#     )
    
#     if result.modified_count == 0:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return {"success": True, "message": "Phone verified successfully!"}


# @auth_router.post("/resend-otp")
# async def resend_otp(
#     email: Optional[EmailStr] = Form(None),
#     phone: Optional[str] = Form(None)
# ):
#     """Resend OTP"""
#     if not email and not phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Either email or phone is required"
#         )
    
#     response = {"success": True, "messages": []}
    
#     if email:
#         email_otp = generate_otp()
#         await store_otp(f"email_{email}", email_otp)
#         send_otp_email(email, email_otp)
#         response["messages"].append("OTP sent to email")
#         response["email_otp"] = email_otp  # For testing
    
#     if phone:
#         phone_otp = generate_otp()
#         await store_otp(f"phone_{phone}", phone_otp)
#         send_otp_sms(phone, phone_otp)
#         response["messages"].append("OTP sent to phone")
#         response["phone_otp"] = phone_otp  # For testing
    
#     return response


# @auth_router.get("/profile/{email}")
# async def get_profile(email: EmailStr):
#     """Get user profile by email"""
#     db = get_database()
    
#     user = await db.users.find_one({"email": email}, {"password": 0})
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     user["_id"] = str(user["_id"])
#     return {"success": True, "user": user}


# @auth_router.get("/users")
# async def list_users(
#     search: Optional[str] = Query(None),
#     limit: int = Query(50, le=100)
# ):
#     """List all users - for testing"""
#     db = get_database()
    
#     query = {}
#     if search:
#         query["$or"] = [
#             {"first_name": {"$regex": search, "$options": "i"}},
#             {"last_name": {"$regex": search, "$options": "i"}},
#             {"email": {"$regex": search, "$options": "i"}},
#             {"employee_id": {"$regex": search, "$options": "i"}},
#         ]
    
#     cursor = db.users.find(query, {"password": 0}).limit(limit)
#     users = []
#     async for user in cursor:
#         user["_id"] = str(user["_id"])
#         users.append(user)
    
#     return {"success": True, "users": users, "total": len(users)}


# # Include auth router
# app.include_router(auth_router)


# # ============================================================
# # IMPORT AND INCLUDE OTHER ROUTERS
# # ============================================================

# # Import routers from routers folder
# try:
#     from routers import requests, approvals, reports, documents, admin
    
#     app.include_router(requests.router, prefix="/requests", tags=["Travel Requests"])
#     app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
#     app.include_router(reports.router, prefix="/reports", tags=["Post-Travel Reports"])
#     app.include_router(documents.router, prefix="/documents", tags=["Documents"])
#     app.include_router(admin.router, prefix="/admin", tags=["Admin"])
    
#     print("✅ All routers loaded successfully")
# except ImportError as e:
#     print(f"⚠️ Could not import some routers: {e}")
#     print("   Make sure you have the routers folder with all required files")


# # ============================================================
# # ROOT AND HEALTH ENDPOINTS
# # ============================================================

# @app.get("/")
# async def root():
#     """API root endpoint"""
#     return {
#         "message": "NTU Travel Management System API",
#         "version": "3.0.0",
#         "docs": "/docs",
#         "endpoints": {
#             "auth": "/auth - Login, Signup, OTP Verification",
#             "requests": "/requests - Travel Requests CRUD",
#             "approvals": "/approvals - Request Approvals",
#             "reports": "/reports - Post-Travel Reports",
#             "documents": "/documents - Document Management",
#             "admin": "/admin - Admin Functions"
#         }
#     }


# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     try:
#         db = get_database()
#         await db.command('ping')
#         db_status = "connected"
#     except:
#         db_status = "disconnected"
    
#     return {
#         "status": "healthy",
#         "database": db_status,
#         "timestamp": datetime.utcnow().isoformat()
#     }


# @app.get("/api/info")
# async def api_info():
#     """API information"""
#     return {
#         "name": "NTU Travel Management System",
#         "version": "3.0.0",
#         "description": "Complete Travel Authorization and Reimbursement System",
#         "modules": [
#             {"name": "Auth", "prefix": "/auth", "endpoints": ["login", "signup", "verify-email-otp", "verify-phone-otp", "resend-otp", "profile", "users"]},
#             {"name": "Requests", "prefix": "/requests", "endpoints": ["travelers", "new", "list", "view", "edit", "delete"]},
#             {"name": "Approvals", "prefix": "/approvals", "endpoints": ["approve", "reject", "pending", "post-travel"]},
#             {"name": "Reports", "prefix": "/reports", "endpoints": ["expense-report", "mileage-report", "trip-report", "post-travel"]},
#             {"name": "Documents", "prefix": "/documents", "endpoints": ["upload", "download", "list"]},
#             {"name": "Admin", "prefix": "/admin", "endpoints": ["users", "departments", "settings"]},
#         ]
#     }


# # ============================================================
# # RUN SERVER
# # ============================================================

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# """
# NTU Travel Management System - Unified FastAPI Application
# All modules in ONE server: Auth, Travel Requests, Approvals, Reports, Admin

# Run with: uvicorn main:app --reload --port 8000

# NOTE: Authentication DISABLED for testing. Re-enable for production!
# """

# from fastapi import FastAPI, Request, HTTPException, status, Form, Query
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from datetime import datetime, timedelta
# from bson import ObjectId
# import os
# import random
# import string
# import bcrypt
# from pathlib import Path

# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# # ============================================================
# # DATABASE CONFIGURATION
# # ============================================================

# MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
# MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ntu_travel")

# _client: Optional[AsyncIOMotorClient] = None
# _database: Optional[AsyncIOMotorDatabase] = None


# class Settings:
#     """Application settings"""
#     MONGODB_URI: str = MONGODB_URI
#     MONGODB_DATABASE: str = MONGODB_DATABASE
#     UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
#     MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))
#     SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24


# def get_settings() -> Settings:
#     return Settings()


# async def connect_to_mongo():
#     """Connect to MongoDB"""
#     global _client, _database
#     settings = get_settings()
#     _client = AsyncIOMotorClient(settings.MONGODB_URI)
#     _database = _client[settings.MONGODB_DATABASE]
    
#     # Test connection
#     await _client.admin.command('ping')
#     print(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}")
    
#     # Create indexes
#     try:
#         await _database.users.create_index("email", unique=True)
#         await _database.users.create_index("employee_id", unique=True)
#         await _database.otps.create_index("identifier")
#         await _database.otps.create_index("created_at", expireAfterSeconds=600)
#         await _database.travel_requests.create_index("traveler_id")
#         await _database.travel_requests.create_index("status")
#         await _database.travel_requests.create_index("ta_number")
#         print("✅ Database indexes created")
#     except Exception as e:
#         print(f"⚠️ Index warning: {e}")


# async def close_mongo_connection():
#     """Close MongoDB connection"""
#     global _client
#     if _client:
#         _client.close()
#         print("✅ MongoDB connection closed")


# def get_database() -> AsyncIOMotorDatabase:
#     """Get database instance"""
#     if _database is None:
#         raise RuntimeError("Database not initialized")
#     return _database


# # ============================================================
# # AUTH UTILITIES
# # ============================================================

# def hash_password(password: str) -> str:
#     """Hash password using bcrypt"""
#     password_bytes = password.encode('utf-8')[:72]
#     salt = bcrypt.gensalt()
#     hashed = bcrypt.hashpw(password_bytes, salt)
#     return hashed.decode('utf-8')


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify password against hash"""
#     try:
#         password_bytes = plain_password.encode('utf-8')[:72]
#         hashed_bytes = hashed_password.encode('utf-8')
#         return bcrypt.checkpw(password_bytes, hashed_bytes)
#     except Exception as e:
#         print(f"Password verification error: {e}")
#         return False


# def generate_otp(length: int = 6) -> str:
#     """Generate random OTP"""
#     return ''.join(random.choices(string.digits, k=length))


# async def store_otp(identifier: str, otp: str, expiration: int = 10):
#     """Store OTP in MongoDB"""
#     db = get_database()
#     await db.otps.update_one(
#         {"identifier": identifier},
#         {
#             "$set": {
#                 "otp": otp,
#                 "created_at": datetime.utcnow(),
#                 "expires_at": datetime.utcnow() + timedelta(minutes=expiration)
#             }
#         },
#         upsert=True
#     )


# async def validate_otp(identifier: str, otp: str) -> bool:
#     """Validate OTP"""
#     db = get_database()
#     otp_data = await db.otps.find_one({"identifier": identifier})
    
#     if not otp_data:
#         return False
    
#     if datetime.utcnow() > otp_data['expires_at']:
#         await db.otps.delete_one({"identifier": identifier})
#         return False
    
#     is_valid = otp_data['otp'] == otp
#     if is_valid:
#         await db.otps.delete_one({"identifier": identifier})
    
#     return is_valid


# def send_otp_email(email: str, otp: str):
#     """Simulate sending OTP via email"""
#     print(f"📧 Sending OTP to email: {email}. OTP: {otp}")


# def send_otp_sms(phone: str, otp: str):
#     """Simulate sending OTP via SMS"""
#     print(f"📱 Sending OTP to phone: {phone}. OTP: {otp}")


# # ============================================================
# # PYDANTIC MODELS FOR AUTH
# # ============================================================

# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str


# class SignupRequest(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#     password: str
#     confirm_password: str
#     department: str
#     employee_id: str
#     phone: str
#     carrier: Optional[str] = None
#     job_title: Optional[str] = 'TRAVELER'
#     dob: Optional[str] = None
#     gender: Optional[str] = None
#     address: Optional[str] = None
#     join_date: Optional[str] = None


# class OTPRequest(BaseModel):
#     email: Optional[EmailStr] = None
#     otp: str
#     phone: Optional[str] = None


# # ============================================================
# # FASTAPI APPLICATION SETUP
# # ============================================================

# BASE_DIR = Path(__file__).resolve().parent


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Startup and shutdown events"""
#     await connect_to_mongo()
#     yield
#     await close_mongo_connection()


# app = FastAPI(
#     title="NTU Travel Management System",
#     description="Complete Travel Authorization and Reimbursement System with Auth",
#     version="3.0.0",
#     lifespan=lifespan
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Static files
# static_dir = BASE_DIR / "static"
# static_dir.mkdir(parents=True, exist_ok=True)
# app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# # Templates
# templates_dir = BASE_DIR / "templates"
# templates_dir.mkdir(parents=True, exist_ok=True)
# templates = Jinja2Templates(directory=str(templates_dir))


# # ============================================================
# # AUTH ROUTES - /auth/*
# # ============================================================

# from fastapi import APIRouter

# auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# @auth_router.post("/login")
# async def login(request: LoginRequest):
#     """Login user with email and password"""
#     db = get_database()
    
#     user = await db.users.find_one({"email": request.email})
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password"
#         )
    
#     if not verify_password(request.password, user["password"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password"
#         )
    
#     # Skip email verification check for testing
#     # if not user.get("email_verified", False):
#     #     raise HTTPException(
#     #         status_code=status.HTTP_403_FORBIDDEN,
#     #         detail="Please verify your email before logging in"
#     #     )
    
#     await db.users.update_one(
#         {"_id": user["_id"]},
#         {"$set": {"last_login": datetime.utcnow()}}
#     )
    
#     return {
#         "success": True,
#         "message": "Login successful!",
#         "user": {
#             "id": str(user["_id"]),
#             "email": user["email"],
#             "first_name": user.get("first_name", ""),
#             "last_name": user.get("last_name", ""),
#             "employee_id": user.get("employee_id", ""),
#             "department": user.get("department", ""),
#             "job_title": user.get("job_title", "TRAVELER"),
#             "role": user.get("role", "TRAVELER"),
#         }
#     }


# @auth_router.post("/signup")
# async def signup(request: SignupRequest):
#     """Register a new user"""
#     db = get_database()
    
#     if request.password != request.confirm_password:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Passwords do not match"
#         )
    
#     existing_user = await db.users.find_one({"email": request.email})
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     existing_employee = await db.users.find_one({"employee_id": request.employee_id})
#     if existing_employee:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Employee ID already registered"
#         )
    
#     email_otp = generate_otp()
#     phone_otp = generate_otp()
    
#     await store_otp(f"email_{request.email}", email_otp)
#     await store_otp(f"phone_{request.phone}", phone_otp)
    
#     user_data = {
#         "first_name": request.first_name,
#         "last_name": request.last_name,
#         "email": request.email,
#         "password": hash_password(request.password),
#         "department": request.department,
#         "employee_id": request.employee_id,
#         "phone": request.phone,
#         "carrier": request.carrier,
#         "job_title": request.job_title or "TRAVELER",
#         "role": "TRAVELER",
#         "dob": request.dob,
#         "gender": request.gender,
#         "address": request.address,
#         "join_date": request.join_date,
#         "email_verified": True,  # Auto-verify for testing
#         "phone_verified": True,  # Auto-verify for testing
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }
    
#     result = await db.users.insert_one(user_data)
    
#     send_otp_email(request.email, email_otp)
#     send_otp_sms(request.phone, phone_otp)
    
#     return {
#         "success": True,
#         "message": "Registration successful! OTP sent to your email and phone.",
#         "user_id": str(result.inserted_id),
#         "email": request.email,
#         "phone": request.phone,
#         "email_otp": email_otp,  # For testing only - remove in production
#         "phone_otp": phone_otp   # For testing only - remove in production
#     }


# @auth_router.post("/verify-email-otp")
# async def verify_email_otp(request: OTPRequest):
#     """Verify email OTP"""
#     db = get_database()
    
#     if not request.email:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email is required"
#         )
    
#     if not await validate_otp(f"email_{request.email}", request.otp):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired OTP"
#         )
    
#     result = await db.users.update_one(
#         {"email": request.email},
#         {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}}
#     )
    
#     if result.modified_count == 0:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return {"success": True, "message": "Email verified successfully!"}


# @auth_router.post("/verify-phone-otp")
# async def verify_phone_otp(request: OTPRequest):
#     """Verify phone OTP"""
#     db = get_database()
    
#     if not request.phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Phone number is required"
#         )
    
#     if not await validate_otp(f"phone_{request.phone}", request.otp):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired OTP"
#         )
    
#     result = await db.users.update_one(
#         {"phone": request.phone},
#         {"$set": {"phone_verified": True, "updated_at": datetime.utcnow()}}
#     )
    
#     if result.modified_count == 0:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return {"success": True, "message": "Phone verified successfully!"}


# @auth_router.post("/resend-otp")
# async def resend_otp(
#     email: Optional[EmailStr] = Form(None),
#     phone: Optional[str] = Form(None)
# ):
#     """Resend OTP"""
#     if not email and not phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Either email or phone is required"
#         )
    
#     response = {"success": True, "messages": []}
    
#     if email:
#         email_otp = generate_otp()
#         await store_otp(f"email_{email}", email_otp)
#         send_otp_email(email, email_otp)
#         response["messages"].append("OTP sent to email")
#         response["email_otp"] = email_otp  # For testing
    
#     if phone:
#         phone_otp = generate_otp()
#         await store_otp(f"phone_{phone}", phone_otp)
#         send_otp_sms(phone, phone_otp)
#         response["messages"].append("OTP sent to phone")
#         response["phone_otp"] = phone_otp  # For testing
    
#     return response


# @auth_router.get("/profile/{email}")
# async def get_profile(email: EmailStr):
#     """Get user profile by email"""
#     db = get_database()
    
#     user = await db.users.find_one({"email": email}, {"password": 0})
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     user["_id"] = str(user["_id"])
#     return {"success": True, "user": user}


# @auth_router.get("/users")
# async def list_users(
#     search: Optional[str] = Query(None),
#     limit: int = Query(50, le=100)
# ):
#     """List all users - for testing"""
#     db = get_database()
    
#     query = {}
#     if search:
#         query["$or"] = [
#             {"first_name": {"$regex": search, "$options": "i"}},
#             {"last_name": {"$regex": search, "$options": "i"}},
#             {"email": {"$regex": search, "$options": "i"}},
#             {"employee_id": {"$regex": search, "$options": "i"}},
#         ]
    
#     cursor = db.users.find(query, {"password": 0}).limit(limit)
#     users = []
#     async for user in cursor:
#         user["_id"] = str(user["_id"])
#         users.append(user)
    
#     return {"success": True, "users": users, "total": len(users)}


# # Include auth router
# app.include_router(auth_router)


# # ============================================================
# # IMPORT AND INCLUDE OTHER ROUTERS
# # ============================================================

# # Import routers from routers folder
# try:
#     from routers import requests, approvals, reports, documents, admin
    
#     app.include_router(requests.router, prefix="/requests", tags=["Travel Requests"])
#     app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
#     app.include_router(reports.router, prefix="/reports", tags=["Post-Travel Reports"])
#     app.include_router(documents.router, prefix="/documents", tags=["Documents"])
#     app.include_router(admin.router, prefix="/admin", tags=["Admin"])
    
#     print("✅ All routers loaded successfully")
# except ImportError as e:
#     print(f"⚠️ Could not import some routers: {e}")
#     print("   Make sure you have the routers folder with all required files")


# # ============================================================
# # ROOT AND HEALTH ENDPOINTS
# # ============================================================

# @app.get("/")
# async def root():
#     """API root endpoint"""
#     return {
#         "message": "NTU Travel Management System API",
#         "version": "3.0.0",
#         "docs": "/docs",
#         "endpoints": {
#             "auth": "/auth - Login, Signup, OTP Verification",
#             "requests": "/requests - Travel Requests CRUD",
#             "approvals": "/approvals - Request Approvals",
#             "reports": "/reports - Post-Travel Reports",
#             "documents": "/documents - Document Management",
#             "admin": "/admin - Admin Functions"
#         }
#     }


# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     try:
#         db = get_database()
#         await db.command('ping')
#         db_status = "connected"
#     except:
#         db_status = "disconnected"
    
#     return {
#         "status": "healthy",
#         "database": db_status,
#         "timestamp": datetime.utcnow().isoformat()
#     }


# @app.get("/api/info")
# async def api_info():
#     """API information"""
#     return {
#         "name": "NTU Travel Management System",
#         "version": "3.0.0",
#         "description": "Complete Travel Authorization and Reimbursement System",
#         "modules": [
#             {"name": "Auth", "prefix": "/auth", "endpoints": ["login", "signup", "verify-email-otp", "verify-phone-otp", "resend-otp", "profile", "users"]},
#             {"name": "Requests", "prefix": "/requests", "endpoints": ["travelers", "new", "list", "view", "edit", "delete"]},
#             {"name": "Approvals", "prefix": "/approvals", "endpoints": ["approve", "reject", "pending", "post-travel"]},
#             {"name": "Reports", "prefix": "/reports", "endpoints": ["expense-report", "mileage-report", "trip-report", "post-travel"]},
#             {"name": "Documents", "prefix": "/documents", "endpoints": ["upload", "download", "list"]},
#             {"name": "Admin", "prefix": "/admin", "endpoints": ["users", "departments", "settings"]},
#         ]
#     }


# # ============================================================
# # RUN SERVER
# # ============================================================

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

"""
NTU Travel Management System - Unified FastAPI Application
All modules in ONE server: Auth, Travel Requests, Approvals, Reports, Admin

Run with: uvicorn main:app --reload --port 8000

NOTE: Authentication DISABLED for testing. Re-enable for production!
"""

# ============================================================
# LOAD ENVIRONMENT VARIABLES FIRST (before any other imports)
# ============================================================
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the same directory as main.py
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Debug: Print loaded email config
print(f"📧 Email Config Loaded:")
print(f"   MAIL_USERNAME: {os.getenv('MAIL_USERNAME', 'NOT SET')}")
print(f"   SMTP_SERVER: {os.getenv('SMTP_SERVER', 'NOT SET')}")

# ============================================================
# IMPORTS
# ============================================================
from fastapi import FastAPI, Request, HTTPException, status, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId
import random
import string
import bcrypt

# Import database module - this will be shared with routers
from dependencies.database import (
    connect_to_mongo, 
    close_mongo_connection, 
    get_database,
    get_settings
)

# ============================================================
# AUTH UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def generate_otp(length: int = 6) -> str:
    """Generate random OTP"""
    return ''.join(random.choices(string.digits, k=length))


async def store_otp(identifier: str, otp: str, expiration: int = 10):
    """Store OTP in MongoDB"""
    db = get_database()
    await db.otps.update_one(
        {"identifier": identifier},
        {
            "$set": {
                "otp": otp,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=expiration)
            }
        },
        upsert=True
    )


async def validate_otp(identifier: str, otp: str) -> bool:
    """Validate OTP"""
    db = get_database()
    otp_data = await db.otps.find_one({"identifier": identifier})
    
    if not otp_data:
        return False
    
    if datetime.utcnow() > otp_data['expires_at']:
        await db.otps.delete_one({"identifier": identifier})
        return False
    
    is_valid = otp_data['otp'] == otp
    if is_valid:
        await db.otps.delete_one({"identifier": identifier})
    
    return is_valid


def send_otp_email(email: str, otp: str) -> bool:
    """
    Send OTP via SMTP email (actual email delivery)
    Uses Gmail SMTP with app password from environment variables
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # SMTP Configuration from environment
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_ADDRESS = os.getenv("MAIL_USERNAME", os.getenv("EMAIL_ADDRESS", ""))
    EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))
    FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_ADDRESS)
    
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print(f"⚠️ SMTP credentials not configured. OTP for {email}: {otp}")
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NTU Travel Management - Your OTP Verification Code"
        msg["From"] = FROM_EMAIL
        msg["To"] = email
        
        # Plain text body
        text_body = f"""
NTU Travel Management System

Your OTP verification code is: {otp}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Thank you,
NTU Travel Desk Team
        """
        
        # HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; padding: 20px; background: #413178; border-radius: 5px 5px 0 0;">
                    <h1 style="color: white; margin: 0;">NTU Travel Management</h1>
                </div>
                <div style="padding: 30px; background: #f9f9f9; border: 1px solid #ddd; border-top: none;">
                    <h2 style="color: #413178;">Email Verification Code</h2>
                    <p>Hello,</p>
                    <p>Your OTP verification code is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #413178; 
                                     background: #e8e4f0; padding: 15px 30px; border-radius: 5px;
                                     letter-spacing: 5px;">{otp}</span>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        ⏱️ This code will expire in <strong>10 minutes</strong>.
                    </p>
                    <p style="color: #999; font-size: 12px;">
                        If you did not request this code, please ignore this email.
                    </p>
                </div>
                <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
                    <p>© 2025 NTU Travel Management System</p>
                    <p>Navajo Technical University</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(FROM_EMAIL, email, msg.as_string())
        
        print(f"✅ OTP email sent successfully to: {email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print(f"📧 [FALLBACK] OTP for {email}: {otp}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        print(f"📧 [FALLBACK] OTP for {email}: {otp}")
        return False
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        print(f"📧 [FALLBACK] OTP for {email}: {otp}")
        return False


def send_otp_sms(phone: str, otp: str):
    """
    Simulate sending OTP via SMS (kept as random code generation)
    Phone OTP remains in console/simulation mode
    """
    print(f"📱 Sending OTP to phone: {phone}. OTP: {otp}")


# ============================================================
# PYDANTIC MODELS FOR AUTH
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str
    department: str
    employee_id: str
    phone: str
    carrier: Optional[str] = None
    job_title: Optional[str] = 'TRAVELER'
    dob: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    join_date: Optional[str] = None


class OTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    otp: str
    phone: Optional[str] = None


# ============================================================
# FASTAPI APPLICATION SETUP
# ============================================================

# BASE_DIR is already defined at the top of the file when loading .env


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Connect to MongoDB on startup
    await connect_to_mongo()
    print("✅ Application started - all modules loaded")
    yield
    # Disconnect on shutdown
    await close_mongo_connection()
    print("✅ Application shutdown complete")


app = FastAPI(
    title="NTU Travel Management System",
    description="Complete Travel Authorization and Reimbursement System with Auth",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = BASE_DIR / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


# ============================================================
# AUTH ROUTES - /auth/*
# ============================================================

from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login")
async def login(request: LoginRequest):
    """Login user with email and password"""
    db = get_database()
    
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Skip email verification check for testing
    # if not user.get("email_verified", False):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Please verify your email before logging in"
    #     )
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "message": "Login successful!",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "employee_id": user.get("employee_id", ""),
            "department": user.get("department", ""),
            "job_title": user.get("job_title", "TRAVELER"),
            "role": user.get("role", "TRAVELER"),
        }
    }


@auth_router.post("/signup")
async def signup(request: SignupRequest):
    """Register a new user"""
    db = get_database()
    
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_employee = await db.users.find_one({"employee_id": request.employee_id})
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already registered"
        )
    
    email_otp = generate_otp()
    phone_otp = generate_otp()
    
    await store_otp(f"email_{request.email}", email_otp)
    await store_otp(f"phone_{request.phone}", phone_otp)
    
    user_data = {
        "first_name": request.first_name,
        "last_name": request.last_name,
        "email": request.email,
        "password": hash_password(request.password),
        "department": request.department,
        "employee_id": request.employee_id,
        "phone": request.phone,
        "carrier": request.carrier,
        "job_title": request.job_title or "TRAVELER",
        "role": "TRAVELER",
        "dob": request.dob,
        "gender": request.gender,
        "address": request.address,
        "join_date": request.join_date,
        "email_verified": True,  # Auto-verify for testing
        "phone_verified": True,  # Auto-verify for testing
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_data)
    
    send_otp_email(request.email, email_otp)
    send_otp_sms(request.phone, phone_otp)
    
    return {
        "success": True,
        "message": "Registration successful! OTP sent to your email and phone.",
        "user_id": str(result.inserted_id),
        "email": request.email,
        "phone": request.phone,
        "email_otp": email_otp,  # For testing only - remove in production
        "phone_otp": phone_otp   # For testing only - remove in production
    }


@auth_router.post("/verify-email-otp")
async def verify_email_otp(request: OTPRequest):
    """Verify email OTP"""
    db = get_database()
    
    if not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    if not await validate_otp(f"email_{request.email}", request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    result = await db.users.update_one(
        {"email": request.email},
        {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"success": True, "message": "Email verified successfully!"}


@auth_router.post("/verify-phone-otp")
async def verify_phone_otp(request: OTPRequest):
    """Verify phone OTP"""
    db = get_database()
    
    if not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    if not await validate_otp(f"phone_{request.phone}", request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    result = await db.users.update_one(
        {"phone": request.phone},
        {"$set": {"phone_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"success": True, "message": "Phone verified successfully!"}


@auth_router.post("/resend-otp")
async def resend_otp(
    email: Optional[EmailStr] = Form(None),
    phone: Optional[str] = Form(None)
):
    """Resend OTP"""
    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone is required"
        )
    
    response = {"success": True, "messages": []}
    
    if email:
        email_otp = generate_otp()
        await store_otp(f"email_{email}", email_otp)
        send_otp_email(email, email_otp)
        response["messages"].append("OTP sent to email")
        response["email_otp"] = email_otp  # For testing
    
    if phone:
        phone_otp = generate_otp()
        await store_otp(f"phone_{phone}", phone_otp)
        send_otp_sms(phone, phone_otp)
        response["messages"].append("OTP sent to phone")
        response["phone_otp"] = phone_otp  # For testing
    
    return response


@auth_router.get("/profile/{email}")
async def get_profile(email: EmailStr):
    """Get user profile by email"""
    db = get_database()
    
    user = await db.users.find_one({"email": email}, {"password": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    return {"success": True, "user": user}


@auth_router.get("/users")
async def list_users(
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """List all users - for testing"""
    db = get_database()
    
    query = {}
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}},
        ]
    
    cursor = db.users.find(query, {"password": 0}).limit(limit)
    users = []
    async for user in cursor:
        user["_id"] = str(user["_id"])
        users.append(user)
    
    return {"success": True, "users": users, "total": len(users)}


# Include auth router
app.include_router(auth_router)


# ============================================================
# IMPORT AND INCLUDE OTHER ROUTERS
# ============================================================

# Import routers from routers folder
try:
    from routers import requests, approvals, reports, documents, admin
    
    app.include_router(requests.router, prefix="/requests", tags=["Travel Requests"])
    app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
    app.include_router(reports.router, prefix="/reports", tags=["Post-Travel Reports"])
    app.include_router(documents.router, prefix="/documents", tags=["Documents"])
    app.include_router(admin.router, prefix="/admin", tags=["Admin"])
    
    print("✅ All routers loaded successfully")
except ImportError as e:
    print(f"⚠️ Could not import some routers: {e}")
    print("   Make sure you have the routers folder with all required files")


# ============================================================
# ROOT AND HEALTH ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "NTU Travel Management System API",
        "version": "3.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth - Login, Signup, OTP Verification",
            "requests": "/requests - Travel Requests CRUD",
            "approvals": "/approvals - Request Approvals",
            "reports": "/reports - Post-Travel Reports",
            "documents": "/documents - Document Management",
            "admin": "/admin - Admin Functions"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        await db.command('ping')
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/info")
async def api_info():
    """API information"""
    return {
        "name": "NTU Travel Management System",
        "version": "3.0.0",
        "description": "Complete Travel Authorization and Reimbursement System",
        "modules": [
            {"name": "Auth", "prefix": "/auth", "endpoints": ["login", "signup", "verify-email-otp", "verify-phone-otp", "resend-otp", "profile", "users"]},
            {"name": "Requests", "prefix": "/requests", "endpoints": ["travelers", "new", "list", "view", "edit", "delete"]},
            {"name": "Approvals", "prefix": "/approvals", "endpoints": ["approve", "reject", "pending", "post-travel"]},
            {"name": "Reports", "prefix": "/reports", "endpoints": ["expense-report", "mileage-report", "trip-report", "post-travel"]},
            {"name": "Documents", "prefix": "/documents", "endpoints": ["upload", "download", "list"]},
            {"name": "Admin", "prefix": "/admin", "endpoints": ["users", "departments", "settings"]},
        ]
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)# """
# NTU Travel Management System - Unified FastAPI Application
# All modules in ONE server: Auth, Travel Requests, Approvals, Reports, Admin

# Run with: uvicorn main:app --reload --port 8000

# NOTE: Authentication DISABLED for testing. Re-enable for production!
# """

# from fastapi import FastAPI, Request, HTTPException, status, Form, Query
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from datetime import datetime, timedelta
# from bson import ObjectId
# import os
# import random
# import string
# import bcrypt
# from pathlib import Path

# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# # ============================================================
# # DATABASE CONFIGURATION
# # ============================================================

# MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
# MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ntu_travel")

# _client: Optional[AsyncIOMotorClient] = None
# _database: Optional[AsyncIOMotorDatabase] = None


# class Settings:
#     """Application settings"""
#     MONGODB_URI: str = MONGODB_URI
#     MONGODB_DATABASE: str = MONGODB_DATABASE
#     UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
#     MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))
#     SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24


# def get_settings() -> Settings:
#     return Settings()


# async def connect_to_mongo():
#     """Connect to MongoDB"""
#     global _client, _database
#     settings = get_settings()
#     _client = AsyncIOMotorClient(settings.MONGODB_URI)
#     _database = _client[settings.MONGODB_DATABASE]
    
#     # Test connection
#     await _client.admin.command('ping')
#     print(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}")
    
#     # Create indexes
#     try:
#         await _database.users.create_index("email", unique=True)
#         await _database.users.create_index("employee_id", unique=True)
#         await _database.otps.create_index("identifier")
#         await _database.otps.create_index("created_at", expireAfterSeconds=600)
#         await _database.travel_requests.create_index("traveler_id")
#         await _database.travel_requests.create_index("status")
#         await _database.travel_requests.create_index("ta_number")
#         print("✅ Database indexes created")
#     except Exception as e:
#         print(f"⚠️ Index warning: {e}")


# async def close_mongo_connection():
#     """Close MongoDB connection"""
#     global _client
#     if _client:
#         _client.close()
#         print("✅ MongoDB connection closed")


# def get_database() -> AsyncIOMotorDatabase:
#     """Get database instance"""
#     if _database is None:
#         raise RuntimeError("Database not initialized")
#     return _database


# # ============================================================
# # AUTH UTILITIES
# # ============================================================

# def hash_password(password: str) -> str:
#     """Hash password using bcrypt"""
#     password_bytes = password.encode('utf-8')[:72]
#     salt = bcrypt.gensalt()
#     hashed = bcrypt.hashpw(password_bytes, salt)
#     return hashed.decode('utf-8')


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify password against hash"""
#     try:
#         password_bytes = plain_password.encode('utf-8')[:72]
#         hashed_bytes = hashed_password.encode('utf-8')
#         return bcrypt.checkpw(password_bytes, hashed_bytes)
#     except Exception as e:
#         print(f"Password verification error: {e}")
#         return False


# def generate_otp(length: int = 6) -> str:
#     """Generate random OTP"""
#     return ''.join(random.choices(string.digits, k=length))


# async def store_otp(identifier: str, otp: str, expiration: int = 10):
#     """Store OTP in MongoDB"""
#     db = get_database()
#     await db.otps.update_one(
#         {"identifier": identifier},
#         {
#             "$set": {
#                 "otp": otp,
#                 "created_at": datetime.utcnow(),
#                 "expires_at": datetime.utcnow() + timedelta(minutes=expiration)
#             }
#         },
#         upsert=True
#     )


# async def validate_otp(identifier: str, otp: str) -> bool:
#     """Validate OTP"""
#     db = get_database()
#     otp_data = await db.otps.find_one({"identifier": identifier})
    
#     if not otp_data:
#         return False
    
#     if datetime.utcnow() > otp_data['expires_at']:
#         await db.otps.delete_one({"identifier": identifier})
#         return False
    
#     is_valid = otp_data['otp'] == otp
#     if is_valid:
#         await db.otps.delete_one({"identifier": identifier})
    
#     return is_valid


# def send_otp_email(email: str, otp: str):
#     """Simulate sending OTP via email"""
#     print(f"📧 Sending OTP to email: {email}. OTP: {otp}")


# def send_otp_sms(phone: str, otp: str):
#     """Simulate sending OTP via SMS"""
#     print(f"📱 Sending OTP to phone: {phone}. OTP: {otp}")


# # ============================================================
# # PYDANTIC MODELS FOR AUTH
# # ============================================================

# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str


# class SignupRequest(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#     password: str
#     confirm_password: str
#     department: str
#     employee_id: str
#     phone: str
#     carrier: Optional[str] = None
#     job_title: Optional[str] = 'TRAVELER'
#     dob: Optional[str] = None
#     gender: Optional[str] = None
#     address: Optional[str] = None
#     join_date: Optional[str] = None


# class OTPRequest(BaseModel):
#     email: Optional[EmailStr] = None
#     otp: str
#     phone: Optional[str] = None


# # ============================================================
# # FASTAPI APPLICATION SETUP
# # ============================================================

# BASE_DIR = Path(__file__).resolve().parent


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Startup and shutdown events"""
#     await connect_to_mongo()
#     yield
#     await close_mongo_connection()


# app = FastAPI(
#     title="NTU Travel Management System",
#     description="Complete Travel Authorization and Reimbursement System with Auth",
#     version="3.0.0",
#     lifespan=lifespan
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Static files
# static_dir = BASE_DIR / "static"
# static_dir.mkdir(parents=True, exist_ok=True)
# app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# # Templates
# templates_dir = BASE_DIR / "templates"
# templates_dir.mkdir(parents=True, exist_ok=True)
# templates = Jinja2Templates(directory=str(templates_dir))


# # ============================================================
# # AUTH ROUTES - /auth/*
# # ============================================================

# from fastapi import APIRouter

# auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# @auth_router.post("/login")
# async def login(request: LoginRequest):
#     """Login user with email and password"""
#     db = get_database()
    
#     user = await db.users.find_one({"email": request.email})
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password"
#         )
    
#     if not verify_password(request.password, user["password"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password"
#         )
    
#     # Skip email verification check for testing
#     # if not user.get("email_verified", False):
#     #     raise HTTPException(
#     #         status_code=status.HTTP_403_FORBIDDEN,
#     #         detail="Please verify your email before logging in"
#     #     )
    
#     await db.users.update_one(
#         {"_id": user["_id"]},
#         {"$set": {"last_login": datetime.utcnow()}}
#     )
    
#     return {
#         "success": True,
#         "message": "Login successful!",
#         "user": {
#             "id": str(user["_id"]),
#             "email": user["email"],
#             "first_name": user.get("first_name", ""),
#             "last_name": user.get("last_name", ""),
#             "employee_id": user.get("employee_id", ""),
#             "department": user.get("department", ""),
#             "job_title": user.get("job_title", "TRAVELER"),
#             "role": user.get("role", "TRAVELER"),
#         }
#     }


# @auth_router.post("/signup")
# async def signup(request: SignupRequest):
#     """Register a new user"""
#     db = get_database()
    
#     if request.password != request.confirm_password:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Passwords do not match"
#         )
    
#     existing_user = await db.users.find_one({"email": request.email})
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     existing_employee = await db.users.find_one({"employee_id": request.employee_id})
#     if existing_employee:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Employee ID already registered"
#         )
    
#     email_otp = generate_otp()
#     phone_otp = generate_otp()
    
#     await store_otp(f"email_{request.email}", email_otp)
#     await store_otp(f"phone_{request.phone}", phone_otp)
    
#     user_data = {
#         "first_name": request.first_name,
#         "last_name": request.last_name,
#         "email": request.email,
#         "password": hash_password(request.password),
#         "department": request.department,
#         "employee_id": request.employee_id,
#         "phone": request.phone,
#         "carrier": request.carrier,
#         "job_title": request.job_title or "TRAVELER",
#         "role": "TRAVELER",
#         "dob": request.dob,
#         "gender": request.gender,
#         "address": request.address,
#         "join_date": request.join_date,
#         "email_verified": True,  # Auto-verify for testing
#         "phone_verified": True,  # Auto-verify for testing
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }
    
#     result = await db.users.insert_one(user_data)
    
#     send_otp_email(request.email, email_otp)
#     send_otp_sms(request.phone, phone_otp)
    
#     return {
#         "success": True,
#         "message": "Registration successful! OTP sent to your email and phone.",
#         "user_id": str(result.inserted_id),
#         "email": request.email,
#         "phone": request.phone,
#         "email_otp": email_otp,  # For testing only - remove in production
#         "phone_otp": phone_otp   # For testing only - remove in production
#     }


# @auth_router.post("/verify-email-otp")
# async def verify_email_otp(request: OTPRequest):
#     """Verify email OTP"""
#     db = get_database()
    
#     if not request.email:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email is required"
#         )
    
#     if not await validate_otp(f"email_{request.email}", request.otp):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired OTP"
#         )
    
#     result = await db.users.update_one(
#         {"email": request.email},
#         {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}}
#     )
    
#     if result.modified_count == 0:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return {"success": True, "message": "Email verified successfully!"}


# @auth_router.post("/verify-phone-otp")
# async def verify_phone_otp(request: OTPRequest):
#     """Verify phone OTP"""
#     db = get_database()
    
#     if not request.phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Phone number is required"
#         )
    
#     if not await validate_otp(f"phone_{request.phone}", request.otp):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired OTP"
#         )
    
#     result = await db.users.update_one(
#         {"phone": request.phone},
#         {"$set": {"phone_verified": True, "updated_at": datetime.utcnow()}}
#     )
    
#     if result.modified_count == 0:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return {"success": True, "message": "Phone verified successfully!"}


# @auth_router.post("/resend-otp")
# async def resend_otp(
#     email: Optional[EmailStr] = Form(None),
#     phone: Optional[str] = Form(None)
# ):
#     """Resend OTP"""
#     if not email and not phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Either email or phone is required"
#         )
    
#     response = {"success": True, "messages": []}
    
#     if email:
#         email_otp = generate_otp()
#         await store_otp(f"email_{email}", email_otp)
#         send_otp_email(email, email_otp)
#         response["messages"].append("OTP sent to email")
#         response["email_otp"] = email_otp  # For testing
    
#     if phone:
#         phone_otp = generate_otp()
#         await store_otp(f"phone_{phone}", phone_otp)
#         send_otp_sms(phone, phone_otp)
#         response["messages"].append("OTP sent to phone")
#         response["phone_otp"] = phone_otp  # For testing
    
#     return response


# @auth_router.get("/profile/{email}")
# async def get_profile(email: EmailStr):
#     """Get user profile by email"""
#     db = get_database()
    
#     user = await db.users.find_one({"email": email}, {"password": 0})
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     user["_id"] = str(user["_id"])
#     return {"success": True, "user": user}


# @auth_router.get("/users")
# async def list_users(
#     search: Optional[str] = Query(None),
#     limit: int = Query(50, le=100)
# ):
#     """List all users - for testing"""
#     db = get_database()
    
#     query = {}
#     if search:
#         query["$or"] = [
#             {"first_name": {"$regex": search, "$options": "i"}},
#             {"last_name": {"$regex": search, "$options": "i"}},
#             {"email": {"$regex": search, "$options": "i"}},
#             {"employee_id": {"$regex": search, "$options": "i"}},
#         ]
    
#     cursor = db.users.find(query, {"password": 0}).limit(limit)
#     users = []
#     async for user in cursor:
#         user["_id"] = str(user["_id"])
#         users.append(user)
    
#     return {"success": True, "users": users, "total": len(users)}


# # Include auth router
# app.include_router(auth_router)


# # ============================================================
# # IMPORT AND INCLUDE OTHER ROUTERS
# # ============================================================

# # Import routers from routers folder
# try:
#     from routers import requests, approvals, reports, documents, admin
    
#     app.include_router(requests.router, prefix="/requests", tags=["Travel Requests"])
#     app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
#     app.include_router(reports.router, prefix="/reports", tags=["Post-Travel Reports"])
#     app.include_router(documents.router, prefix="/documents", tags=["Documents"])
#     app.include_router(admin.router, prefix="/admin", tags=["Admin"])
    
#     print("✅ All routers loaded successfully")
# except ImportError as e:
#     print(f"⚠️ Could not import some routers: {e}")
#     print("   Make sure you have the routers folder with all required files")


# # ============================================================
# # ROOT AND HEALTH ENDPOINTS
# # ============================================================

# @app.get("/")
# async def root():
#     """API root endpoint"""
#     return {
#         "message": "NTU Travel Management System API",
#         "version": "3.0.0",
#         "docs": "/docs",
#         "endpoints": {
#             "auth": "/auth - Login, Signup, OTP Verification",
#             "requests": "/requests - Travel Requests CRUD",
#             "approvals": "/approvals - Request Approvals",
#             "reports": "/reports - Post-Travel Reports",
#             "documents": "/documents - Document Management",
#             "admin": "/admin - Admin Functions"
#         }
#     }


# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     try:
#         db = get_database()
#         await db.command('ping')
#         db_status = "connected"
#     except:
#         db_status = "disconnected"
    
#     return {
#         "status": "healthy",
#         "database": db_status,
#         "timestamp": datetime.utcnow().isoformat()
#     }


# @app.get("/api/info")
# async def api_info():
#     """API information"""
#     return {
#         "name": "NTU Travel Management System",
#         "version": "3.0.0",
#         "description": "Complete Travel Authorization and Reimbursement System",
#         "modules": [
#             {"name": "Auth", "prefix": "/auth", "endpoints": ["login", "signup", "verify-email-otp", "verify-phone-otp", "resend-otp", "profile", "users"]},
#             {"name": "Requests", "prefix": "/requests", "endpoints": ["travelers", "new", "list", "view", "edit", "delete"]},
#             {"name": "Approvals", "prefix": "/approvals", "endpoints": ["approve", "reject", "pending", "post-travel"]},
#             {"name": "Reports", "prefix": "/reports", "endpoints": ["expense-report", "mileage-report", "trip-report", "post-travel"]},
#             {"name": "Documents", "prefix": "/documents", "endpoints": ["upload", "download", "list"]},
#             {"name": "Admin", "prefix": "/admin", "endpoints": ["users", "departments", "settings"]},
#         ]
#     }


# # ============================================================
# # RUN SERVER
# # ============================================================

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

"""
NTU Travel Management System - Unified FastAPI Application
All modules in ONE server: Auth, Travel Requests, Approvals, Reports, Admin

Run with: uvicorn main:app --reload --port 8000

NOTE: Authentication DISABLED for testing. Re-enable for production!
"""

# ============================================================
# LOAD ENVIRONMENT VARIABLES FIRST (before any other imports)
# ============================================================
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the same directory as main.py
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Debug: Print loaded email config
print(f"📧 Email Config Loaded:")
print(f"   MAIL_USERNAME: {os.getenv('MAIL_USERNAME', 'NOT SET')}")
print(f"   SMTP_SERVER: {os.getenv('SMTP_SERVER', 'NOT SET')}")

# ============================================================
# IMPORTS
# ============================================================
from fastapi import FastAPI, Request, HTTPException, status, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId
import random
import string
import bcrypt

# Import database module - this will be shared with routers
from dependencies.database import (
    connect_to_mongo, 
    close_mongo_connection, 
    get_database,
    get_settings
)

# ============================================================
# AUTH UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def generate_otp(length: int = 6) -> str:
    """Generate random OTP"""
    return ''.join(random.choices(string.digits, k=length))


async def store_otp(identifier: str, otp: str, expiration: int = 10):
    """Store OTP in MongoDB"""
    db = get_database()
    await db.otps.update_one(
        {"identifier": identifier},
        {
            "$set": {
                "otp": otp,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=expiration)
            }
        },
        upsert=True
    )


async def validate_otp(identifier: str, otp: str) -> bool:
    """Validate OTP"""
    db = get_database()
    otp_data = await db.otps.find_one({"identifier": identifier})
    
    if not otp_data:
        return False
    
    if datetime.utcnow() > otp_data['expires_at']:
        await db.otps.delete_one({"identifier": identifier})
        return False
    
    is_valid = otp_data['otp'] == otp
    if is_valid:
        await db.otps.delete_one({"identifier": identifier})
    
    return is_valid


def send_otp_email(email: str, otp: str) -> bool:
    """
    Send OTP via SMTP email (actual email delivery)
    Uses Gmail SMTP with app password from environment variables
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # SMTP Configuration from environment
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_ADDRESS = os.getenv("MAIL_USERNAME", os.getenv("EMAIL_ADDRESS", ""))
    EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))
    FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_ADDRESS)
    
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print(f"⚠️ SMTP credentials not configured. OTP for {email}: {otp}")
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "NTU Travel Management - Your OTP Verification Code"
        msg["From"] = FROM_EMAIL
        msg["To"] = email
        
        # Plain text body
        text_body = f"""
NTU Travel Management System

Your OTP verification code is: {otp}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Thank you,
NTU Travel Desk Team
        """
        
        # HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; padding: 20px; background: #413178; border-radius: 5px 5px 0 0;">
                    <h1 style="color: white; margin: 0;">NTU Travel Management</h1>
                </div>
                <div style="padding: 30px; background: #f9f9f9; border: 1px solid #ddd; border-top: none;">
                    <h2 style="color: #413178;">Email Verification Code</h2>
                    <p>Hello,</p>
                    <p>Your OTP verification code is:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #413178; 
                                     background: #e8e4f0; padding: 15px 30px; border-radius: 5px;
                                     letter-spacing: 5px;">{otp}</span>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        ⏱️ This code will expire in <strong>10 minutes</strong>.
                    </p>
                    <p style="color: #999; font-size: 12px;">
                        If you did not request this code, please ignore this email.
                    </p>
                </div>
                <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
                    <p>© 2025 NTU Travel Management System</p>
                    <p>Navajo Technical University</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(FROM_EMAIL, email, msg.as_string())
        
        print(f"✅ OTP email sent successfully to: {email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print(f"📧 [FALLBACK] OTP for {email}: {otp}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        print(f"📧 [FALLBACK] OTP for {email}: {otp}")
        return False
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        print(f"📧 [FALLBACK] OTP for {email}: {otp}")
        return False


def send_otp_sms(phone: str, otp: str):
    """
    Simulate sending OTP via SMS (kept as random code generation)
    Phone OTP remains in console/simulation mode
    """
    print(f"📱 Sending OTP to phone: {phone}. OTP: {otp}")


# ============================================================
# PYDANTIC MODELS FOR AUTH
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str
    department: str
    employee_id: str
    phone: str
    carrier: Optional[str] = None
    job_title: Optional[str] = 'TRAVELER'
    dob: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    join_date: Optional[str] = None


class OTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    otp: str
    phone: Optional[str] = None


# ============================================================
# FASTAPI APPLICATION SETUP
# ============================================================

# BASE_DIR is already defined at the top of the file when loading .env


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Connect to MongoDB on startup
    await connect_to_mongo()
    print("✅ Application started - all modules loaded")
    yield
    # Disconnect on shutdown
    await close_mongo_connection()
    print("✅ Application shutdown complete")


app = FastAPI(
    title="NTU Travel Management System",
    description="Complete Travel Authorization and Reimbursement System with Auth",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = BASE_DIR / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


# ============================================================
# AUTH ROUTES - /auth/*
# ============================================================

from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login")
async def login(request: LoginRequest):
    """Login user with email and password"""
    db = get_database()
    
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Skip email verification check for testing
    # if not user.get("email_verified", False):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Please verify your email before logging in"
    #     )
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "message": "Login successful!",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "employee_id": user.get("employee_id", ""),
            "department": user.get("department", ""),
            "job_title": user.get("job_title", "TRAVELER"),
            "role": user.get("role", "TRAVELER"),
        }
    }


@auth_router.post("/signup")
async def signup(request: SignupRequest):
    """Register a new user"""
    db = get_database()
    
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_employee = await db.users.find_one({"employee_id": request.employee_id})
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already registered"
        )
    
    email_otp = generate_otp()
    phone_otp = generate_otp()
    
    await store_otp(f"email_{request.email}", email_otp)
    await store_otp(f"phone_{request.phone}", phone_otp)
    
    user_data = {
        "first_name": request.first_name,
        "last_name": request.last_name,
        "email": request.email,
        "password": hash_password(request.password),
        "department": request.department,
        "employee_id": request.employee_id,
        "phone": request.phone,
        "carrier": request.carrier,
        "job_title": request.job_title or "TRAVELER",
        "role": "TRAVELER",
        "dob": request.dob,
        "gender": request.gender,
        "address": request.address,
        "join_date": request.join_date,
        "email_verified": False,  # Will be verified after OTP confirmation
        "phone_verified": False,  # Will be verified after OTP confirmation
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_data)
    
    # Send OTPs
    email_sent = send_otp_email(request.email, email_otp)
    send_otp_sms(request.phone, phone_otp)
    
    return {
        "success": True,
        "message": "Registration successful! Please verify your email and phone.",
        "user_id": str(result.inserted_id),
        "email": request.email,
        "phone": request.phone,
        "email_message": "OTP has been sent to your email" if email_sent else "OTP sent to email (check console if not received)",
        "phone_message": "OTP has been sent to your phone"
    }


@auth_router.post("/verify-email-otp")
async def verify_email_otp(request: OTPRequest):
    """Verify email OTP"""
    db = get_database()
    
    if not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    if not await validate_otp(f"email_{request.email}", request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    result = await db.users.update_one(
        {"email": request.email},
        {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"success": True, "message": "Email verified successfully!"}


@auth_router.post("/verify-phone-otp")
async def verify_phone_otp(request: OTPRequest):
    """Verify phone OTP"""
    db = get_database()
    
    if not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    if not await validate_otp(f"phone_{request.phone}", request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    result = await db.users.update_one(
        {"phone": request.phone},
        {"$set": {"phone_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"success": True, "message": "Phone verified successfully!"}


@auth_router.post("/resend-otp")
async def resend_otp(
    email: Optional[EmailStr] = Form(None),
    phone: Optional[str] = Form(None)
):
    """Resend OTP"""
    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone is required"
        )
    
    response = {"success": True, "messages": []}
    
    if email:
        email_otp = generate_otp()
        await store_otp(f"email_{email}", email_otp)
        email_sent = send_otp_email(email, email_otp)
        response["messages"].append("OTP has been sent to your email" if email_sent else "OTP sent to email")
    
    if phone:
        phone_otp = generate_otp()
        await store_otp(f"phone_{phone}", phone_otp)
        send_otp_sms(phone, phone_otp)
        response["messages"].append("OTP has been sent to your phone")
    
    return response


@auth_router.get("/profile/{email}")
async def get_profile(email: EmailStr):
    """Get user profile by email"""
    db = get_database()
    
    user = await db.users.find_one({"email": email}, {"password": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    return {"success": True, "user": user}


@auth_router.get("/users")
async def list_users(
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """List all users - for testing"""
    db = get_database()
    
    query = {}
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}},
        ]
    
    cursor = db.users.find(query, {"password": 0}).limit(limit)
    users = []
    async for user in cursor:
        user["_id"] = str(user["_id"])
        users.append(user)
    
    return {"success": True, "users": users, "total": len(users)}


# Include auth router
app.include_router(auth_router)


# ============================================================
# IMPORT AND INCLUDE OTHER ROUTERS
# ============================================================

# Import routers from routers folder
try:
    from routers import requests, approvals, reports, documents, admin
    
    app.include_router(requests.router, prefix="/requests", tags=["Travel Requests"])
    app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
    app.include_router(reports.router, prefix="/reports", tags=["Post-Travel Reports"])
    app.include_router(documents.router, prefix="/documents", tags=["Documents"])
    app.include_router(admin.router, prefix="/admin", tags=["Admin"])
    
    print("✅ All routers loaded successfully")
except ImportError as e:
    print(f"⚠️ Could not import some routers: {e}")
    print("   Make sure you have the routers folder with all required files")


# ============================================================
# ROOT AND HEALTH ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "NTU Travel Management System API",
        "version": "3.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth - Login, Signup, OTP Verification",
            "requests": "/requests - Travel Requests CRUD",
            "approvals": "/approvals - Request Approvals",
            "reports": "/reports - Post-Travel Reports",
            "documents": "/documents - Document Management",
            "admin": "/admin - Admin Functions"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        await db.command('ping')
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/info")
async def api_info():
    """API information"""
    return {
        "name": "NTU Travel Management System",
        "version": "3.0.0",
        "description": "Complete Travel Authorization and Reimbursement System",
        "modules": [
            {"name": "Auth", "prefix": "/auth", "endpoints": ["login", "signup", "verify-email-otp", "verify-phone-otp", "resend-otp", "profile", "users"]},
            {"name": "Requests", "prefix": "/requests", "endpoints": ["travelers", "new", "list", "view", "edit", "delete"]},
            {"name": "Approvals", "prefix": "/approvals", "endpoints": ["approve", "reject", "pending", "post-travel"]},
            {"name": "Reports", "prefix": "/reports", "endpoints": ["expense-report", "mileage-report", "trip-report", "post-travel"]},
            {"name": "Documents", "prefix": "/documents", "endpoints": ["upload", "download", "list"]},
            {"name": "Admin", "prefix": "/admin", "endpoints": ["users", "departments", "settings"]},
        ]
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)