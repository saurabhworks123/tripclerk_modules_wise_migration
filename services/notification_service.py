"""
Notification Service
Handles in-app notifications
"""

from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    async def create_notification(
        db,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        link: Optional[str] = None,
    ) -> str:
        """
        Create a new notification.
        
        Args:
            db: Database instance
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_type: Type (info, warning, success, error)
            link: Optional link to related resource
        
        Returns:
            Notification ID
        """
        notification = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "link": link,
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
        }
        
        result = await db.notifications.insert_one(notification)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_user_notifications(
        db,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list:
        """Get notifications for a user"""
        query = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        
        cursor = db.notifications.find(query).sort("created_at", -1).limit(limit)
        
        notifications = []
        async for notif in cursor:
            notif["_id"] = str(notif["_id"])
            notifications.append(notif)
        
        return notifications
    
    @staticmethod
    async def mark_as_read(db, notification_id: str) -> bool:
        """Mark a notification as read"""
        result = await db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def mark_all_as_read(db, user_id: str) -> int:
        """Mark all user notifications as read"""
        result = await db.notifications.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count
    
    @staticmethod
    async def get_unread_count(db, user_id: str) -> int:
        """Get count of unread notifications"""
        return await db.notifications.count_documents({
            "user_id": user_id,
            "is_read": False
        })
    
    @staticmethod
    async def delete_notification(db, notification_id: str) -> bool:
        """Delete a notification"""
        result = await db.notifications.delete_one({"_id": ObjectId(notification_id)})
        return result.deleted_count > 0
    
    @staticmethod
    async def delete_old_notifications(db, days: int = 30) -> int:
        """Delete notifications older than specified days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.notifications.delete_many({
            "created_at": {"$lt": cutoff},
            "is_read": True
        })
        return result.deleted_count
