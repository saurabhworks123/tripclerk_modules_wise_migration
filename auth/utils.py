# app/auth/utils.py
import random
import string
import hashlib
from datetime import datetime, timedelta
import bcrypt
from app.DataBase.mongodb import get_database

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with Python 3.14 compatibility
    Truncates password to 72 bytes as per bcrypt limitation
    """
    # Convert password to bytes and truncate to 72 bytes (bcrypt limitation)
    password_bytes = password.encode('utf-8')[:72]
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash with Python 3.14 compatibility
    """
    try:
        # Convert password to bytes and truncate to 72 bytes
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP."""
    return ''.join(random.choices(string.digits, k=length))

async def store_otp(identifier: str, otp: str, expiration: int = 10):
    """Store OTP in MongoDB with expiration time."""
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
    """Validate OTP from MongoDB."""
    db = get_database()
    otp_data = await db.otps.find_one({"identifier": identifier})
    
    if not otp_data:
        return False
    
    # Check if OTP is expired
    if datetime.utcnow() > otp_data['expires_at']:
        # Delete expired OTP
        await db.otps.delete_one({"identifier": identifier})
        return False
    
    # Validate OTP
    is_valid = otp_data['otp'] == otp
    
    # Delete OTP after successful validation
    if is_valid:
        await db.otps.delete_one({"identifier": identifier})
    
    return is_valid

def send_otp_email(email: str, otp: str):
    """Simulate sending OTP via email."""
    # In production, use an email service like SendGrid or AWS SES
    print(f"📧 Sending OTP to email: {email}. OTP: {otp}")

def send_otp_sms(phone: str, otp: str):
    """Simulate sending OTP via SMS."""
    # In production, use Twilio or another SMS service
    print(f"📱 Sending OTP to phone: {phone}. OTP: {otp}")