"""
Dependencies Package
"""

from .database import (
    get_database,
    get_db,
    get_settings,
    connect_to_mongo,
    close_mongo_connection,
    get_collection,
)

from .auth import (
    get_current_user,
    get_current_user_optional,
    require_roles,
    get_supervisor_user,
    get_finance_user,
    get_admin_user,
    get_president_user,
    create_access_token,
    verify_password,
    hash_password,
    authenticate_user,
    can_approve_request,
    can_view_request,
    can_edit_request,
)

__all__ = [
    # Database
    "get_database",
    "get_db",
    "get_settings",
    "connect_to_mongo",
    "close_mongo_connection",
    "get_collection",
    # Auth
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
    "get_supervisor_user",
    "get_finance_user",
    "get_admin_user",
    "get_president_user",
    "create_access_token",
    "verify_password",
    "hash_password",
    "authenticate_user",
    "can_approve_request",
    "can_view_request",
    "can_edit_request",
]
