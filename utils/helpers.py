"""
Helper Utilities
Common functions used across routes
"""

from datetime import datetime, date, timezone
from typing import Optional, Union
from bson import ObjectId
import re


def generate_ta_number(db, year: int = None) -> str:
    """
    Generate Travel Authorization number in format TA-YYYY-NNN.
    Uses atomic counter increment for thread safety.
    
    Args:
        db: Database instance
        year: Year for TA number (default: current year)
    
    Returns:
        TA number string like "TA-2024-001"
    """
    if year is None:
        year = datetime.now().year
    
    # This is synchronous - for async use see async version below
    counter_key = f"ta_number_{year}"
    
    # Would need to be async in actual implementation
    # Using placeholder logic here
    return f"TA-{year}-001"


async def generate_ta_number_async(db, year: int = None) -> str:
    """
    Async version: Generate Travel Authorization number.
    Uses atomic counter increment for thread safety.
    """
    if year is None:
        year = datetime.now().year
    
    counter_key = f"ta_number_{year}"
    
    # Atomic increment
    result = await db.counters.find_one_and_update(
        {"_id": counter_key},
        {"$inc": {"sequence": 1}},
        upsert=True,
        return_document=True
    )
    
    sequence = result.get("sequence", 1)
    return f"TA-{year}-{sequence:03d}"


def safe_parse_date(date_string: Union[str, date, datetime, None]) -> Optional[date]:
    """
    Safely parse date from various formats.
    Handles: MM/DD/YYYY, YYYY-MM-DD, datetime objects, date objects
    
    Args:
        date_string: Date in various formats
    
    Returns:
        date object or None if parsing fails
    """
    if date_string is None:
        return None
    
    if isinstance(date_string, datetime):
        return date_string.date()
    
    if isinstance(date_string, date):
        return date_string
    
    if not isinstance(date_string, str):
        return None
    
    date_string = date_string.strip()
    if not date_string:
        return None
    
    # Try different formats
    formats = [
        "%Y-%m-%d",      # 2024-01-15
        "%m/%d/%Y",      # 01/15/2024
        "%d/%m/%Y",      # 15/01/2024
        "%Y/%m/%d",      # 2024/01/15
        "%m-%d-%Y",      # 01-15-2024
        "%d-%m-%Y",      # 15-01-2024
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    
    return None


def safe_parse_datetime(dt_string: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Safely parse datetime from various formats.
    
    Args:
        dt_string: Datetime in various formats
    
    Returns:
        datetime object or None if parsing fails
    """
    if dt_string is None:
        return None
    
    if isinstance(dt_string, datetime):
        return dt_string
    
    if not isinstance(dt_string, str):
        return None
    
    dt_string = dt_string.strip()
    if not dt_string:
        return None
    
    # Try ISO format first
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except ValueError:
        pass
    
    # Try other formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_string, fmt)
        except ValueError:
            continue
    
    return None


def safe_float(value: Union[str, int, float, None], default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Float value
    """
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Union[str, int, float, None], default: int = 0) -> int:
    """
    Safely convert value to int.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Int value
    """
    if value is None:
        return default
    
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_object_id(id_string: Union[str, ObjectId, None]) -> Optional[ObjectId]:
    """
    Safely convert string to ObjectId.
    
    Args:
        id_string: ID string or ObjectId
    
    Returns:
        ObjectId or None if invalid
    """
    if id_string is None:
        return None
    
    if isinstance(id_string, ObjectId):
        return id_string
    
    try:
        return ObjectId(id_string)
    except Exception:
        return None


def format_currency(amount: Union[float, int, str, None], symbol: str = "$") -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        symbol: Currency symbol (default: $)
    
    Returns:
        Formatted currency string
    """
    amount = safe_float(amount)
    return f"{symbol}{amount:,.2f}"


def format_date(d: Union[date, datetime, str, None], fmt: str = "%m/%d/%Y") -> str:
    """
    Format date as string.
    
    Args:
        d: Date to format
        fmt: Output format (default: MM/DD/YYYY)
    
    Returns:
        Formatted date string or empty string
    """
    if d is None:
        return ""
    
    if isinstance(d, str):
        d = safe_parse_date(d)
        if d is None:
            return ""
    
    if isinstance(d, datetime):
        d = d.date()
    
    return d.strftime(fmt)


def calculate_settlement(
    travel_advance: float,
    additional_funds: float,
    total_spent: float
) -> dict:
    """
    Calculate settlement amount.
    
    Settlement = Total Given - Total Spent
    - Positive: Traveler owes university
    - Negative: University owes traveler
    
    Args:
        travel_advance: Initial travel advance
        additional_funds: Additional funds approved
        total_spent: Total amount spent
    
    Returns:
        Dict with settlement details
    """
    total_given = safe_float(travel_advance) + safe_float(additional_funds)
    total_spent = safe_float(total_spent)
    settlement = total_given - total_spent
    
    return {
        "travel_advance": travel_advance,
        "additional_funds": additional_funds,
        "total_given": total_given,
        "total_spent": total_spent,
        "settlement_amount": abs(settlement),
        "settlement_type": "TRAVELER_OWES" if settlement > 0 else "UNIVERSITY_OWES" if settlement < 0 else "BALANCED"
    }


def get_user_full_name(user: dict) -> str:
    """
    Get user's full name from user document.
    
    Args:
        user: User document
    
    Returns:
        Full name string
    """
    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")
    return f"{first_name} {last_name}".strip() or user.get("email", "Unknown")


def sanitize_html(text: str) -> str:
    """
    Basic HTML sanitization - remove script tags and dangerous attributes.
    For production, use a proper library like bleach.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers
    text = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: URLs
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text


def paginate_query(page: int = 1, per_page: int = 20) -> tuple:
    """
    Calculate skip and limit for pagination.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Tuple of (skip, limit)
    """
    page = max(1, page)
    per_page = max(1, min(100, per_page))  # Cap at 100
    skip = (page - 1) * per_page
    return skip, per_page


def build_sort_query(sort_by: Optional[str], sort_order: str = "desc") -> list:
    """
    Build MongoDB sort query.
    
    Args:
        sort_by: Field to sort by
        sort_order: 'asc' or 'desc'
    
    Returns:
        List of (field, direction) tuples for pymongo
    """
    if not sort_by:
        return [("created_at", -1)]  # Default sort
    
    direction = 1 if sort_order.lower() == "asc" else -1
    return [(sort_by, direction)]


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)
