"""
Pydantic Models for User System
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    SUPERVISOR = "SUPERVISOR"
    FINANCE = "FINANCE"
    TA = "TA"  # Travel Administrator
    ADMIN = "ADMIN"
    PRESIDENT = "PRESIDENT"


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    first_name: str
    last_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Model for creating new users"""
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.EMPLOYEE
    supervisor_id: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating users"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    supervisor_id: Optional[str] = None


class UserInDB(UserBase):
    """User model as stored in database"""
    id: str = Field(alias="_id")
    role: UserRole
    supervisor_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)"""
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    role: UserRole
    is_active: bool


class TokenData(BaseModel):
    """JWT Token payload"""
    user_id: str
    email: str
    role: UserRole
    exp: datetime


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    message: str
    token: Optional[Token] = None
    user: Optional[UserResponse] = None
