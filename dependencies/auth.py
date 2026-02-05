"""
Authentication Dependency
JWT-based authentication replacing Flask-Login
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from bson import ObjectId
import bcrypt

from dependencies.database import get_database, get_settings
from models.user import UserRole, UserInDB, TokenData, Token

security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def hash_password(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user from database by ID"""
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return user


async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user from database by email"""
    db = get_database()
    user = await db.users.find_one({"email": email.lower()})
    return user


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate user with email and password"""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return user


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token.
    This replaces Flask-Login's current_user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check for token in header
    token = None
    if credentials:
        token = credentials.credentials
    
    # Also check for session-based auth (for web interface)
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise credentials_exception
    
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Convert ObjectId to string
    user["_id"] = str(user["_id"])
    return user


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """Get current user if authenticated, None otherwise"""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory to require specific roles.
    Usage: Depends(require_roles([UserRole.ADMIN, UserRole.SUPERVISOR]))
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = UserRole(current_user.get("role", "EMPLOYEE"))
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


# Convenience dependencies for common role checks
async def get_supervisor_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Require supervisor or higher role"""
    allowed = [UserRole.SUPERVISOR, UserRole.FINANCE, UserRole.TA, UserRole.ADMIN, UserRole.PRESIDENT]
    if UserRole(current_user.get("role")) not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor access required"
        )
    return current_user


async def get_finance_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Require finance or admin role"""
    allowed = [UserRole.FINANCE, UserRole.ADMIN]
    if UserRole(current_user.get("role")) not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Finance access required"
        )
    return current_user


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role"""
    if UserRole(current_user.get("role")) != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_president_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Require president or admin role"""
    allowed = [UserRole.PRESIDENT, UserRole.ADMIN]
    if UserRole(current_user.get("role")) not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="President access required"
        )
    return current_user


def can_approve_request(user: dict, request_data: dict) -> bool:
    """Check if user can approve a specific request"""
    user_id = str(user.get("_id"))
    user_role = UserRole(user.get("role", "EMPLOYEE"))
    
    # Admin can approve anything
    if user_role == UserRole.ADMIN:
        return True
    
    # Supervisor can approve their team's requests
    if user_role in [UserRole.SUPERVISOR, UserRole.TA]:
        supervisor_id = request_data.get("supervisor_id")
        if supervisor_id and str(supervisor_id) == user_id:
            return True
    
    # President can approve international travel
    if user_role == UserRole.PRESIDENT:
        if request_data.get("travel_type") == "international":
            return True
    
    # Finance can approve post-travel
    if user_role == UserRole.FINANCE:
        status = request_data.get("status")
        if status in ["POST_TRAVEL_SUPERVISOR_APPROVED"]:
            return True
    
    return False


def can_view_request(user: dict, request_data: dict) -> bool:
    """Check if user can view a specific request"""
    user_id = str(user.get("_id"))
    user_role = UserRole(user.get("role", "EMPLOYEE"))
    
    # Admin can view anything
    if user_role == UserRole.ADMIN:
        return True
    
    # Finance can view all requests
    if user_role == UserRole.FINANCE:
        return True
    
    # Traveler can view their own requests
    if str(request_data.get("traveler_id")) == user_id:
        return True
    
    # Supervisor can view their team's requests
    if str(request_data.get("supervisor_id")) == user_id:
        return True
    
    # President can view international requests
    if user_role == UserRole.PRESIDENT and request_data.get("travel_type") == "international":
        return True
    
    return False


def can_edit_request(user: dict, request_data: dict) -> bool:
    """Check if user can edit a specific request"""
    user_id = str(user.get("_id"))
    user_role = UserRole(user.get("role", "EMPLOYEE"))
    status = request_data.get("status", "")
    
    # Admin can always edit
    if user_role == UserRole.ADMIN:
        return True
    
    # Traveler can edit their own drafts
    if str(request_data.get("traveler_id")) == user_id:
        if status in ["DRAFT", "PENDING_SUPERVISOR"]:
            return True
    
    # Supervisor can edit pending requests
    if str(request_data.get("supervisor_id")) == user_id:
        if status in ["PENDING_SUPERVISOR"]:
            return True
    
    return False
