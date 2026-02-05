# app/auth/routes.py
from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr
from datetime import datetime
from app.auth.models import LoginRequest, SignupRequest, OTPRequest
from app.auth.utils import (
    generate_otp, store_otp, validate_otp, 
    send_otp_email, send_otp_sms,
    hash_password, verify_password
)
from app.DataBase.mongodb import get_database

router = APIRouter()

# =====================
# 1. Login Route
# =====================
@router.post("/login")
async def login(request: LoginRequest):
    """Login user with email and password"""
    db = get_database()
    
    # Find user by email
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if email is verified
    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return {
        "message": "Login successful!",
        "user": {
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "employee_id": user["employee_id"],
            "job_title": user.get("job_title", "TRAVELER")
        }
    }

# =====================
# 2. Signup Route
# =====================
@router.post("/signup")
async def signup(request: SignupRequest):
    """Register a new user"""
    db = get_database()
    
    # Validate passwords match
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if employee_id already exists
    existing_employee = await db.users.find_one({"employee_id": request.employee_id})
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already registered"
        )
    
    # Generate OTP for email and phone
    email_otp = generate_otp()
    phone_otp = generate_otp()
    
    # Store OTPs in MongoDB
    await store_otp(f"email_{request.email}", email_otp)
    await store_otp(f"phone_{request.phone}", phone_otp)
    
    # Store user data temporarily (unverified)
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
        "dob": request.dob,
        "gender": request.gender,
        "address": request.address,
        "join_date": request.join_date,
        "email_verified": False,
        "phone_verified": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_data)
    
    # Send OTP via email and SMS
    send_otp_email(request.email, email_otp)
    send_otp_sms(request.phone, phone_otp)

    return {
        "message": "OTP sent to your email and phone for verification.",
        "email": request.email,
        "phone": request.phone
    }

# =====================
# 3. Email OTP Verification
# =====================
@router.post("/verify-email-otp")
async def verify_email_otp(request: OTPRequest):
    """Verify email OTP"""
    db = get_database()
    
    if not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Validate OTP
    if not await validate_otp(f"email_{request.email}", request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Update user email verification status
    result = await db.users.update_one(
        {"email": request.email},
        {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Email verified successfully!"}

# =====================
# 4. Phone OTP Verification
# =====================
@router.post("/verify-phone-otp")
async def verify_phone_otp(request: OTPRequest):
    """Verify phone OTP"""
    db = get_database()
    
    if not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is required"
        )
    
    # Validate OTP
    if not await validate_otp(f"phone_{request.phone}", request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Update user phone verification status
    result = await db.users.update_one(
        {"phone": request.phone},
        {"$set": {"phone_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Phone verified successfully!"}

# =====================
# 5. Resend OTP
# =====================
@router.post("/resend-otp")
async def resend_otp(email: EmailStr = None, phone: str = None):
    """Resend OTP to email and/or phone"""
    
    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone is required"
        )
    
    response_messages = []
    
    # Resend email OTP
    if email:
        email_otp = generate_otp()
        await store_otp(f"email_{email}", email_otp)
        send_otp_email(email, email_otp)
        response_messages.append("OTP sent to email")
    
    # Resend phone OTP
    if phone:
        phone_otp = generate_otp()
        await store_otp(f"phone_{phone}", phone_otp)
        send_otp_sms(phone, phone_otp)
        response_messages.append("OTP sent to phone")
    
    return {"message": " and ".join(response_messages)}

# =====================
# 6. Get User Profile
# =====================
@router.get("/profile/{email}")
async def get_profile(email: EmailStr):
    """Get user profile by email"""
    db = get_database()
    
    user = await db.users.find_one({"email": email}, {"password": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert ObjectId to string
    user["_id"] = str(user["_id"])
    
    return user
