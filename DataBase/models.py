from pydantic import BaseModel, EmailStr
from typing import Optional

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
    email: EmailStr = None
    otp: str
    phone: str = None

class OTPResponse(BaseModel):
    success: bool
    message: str
