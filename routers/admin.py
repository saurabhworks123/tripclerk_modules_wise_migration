"""
Admin Router
Handles: Admin functions, debug endpoints, scheduler status
Converted from Flask Blueprint routes.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from dependencies.database import get_database
from dependencies.auth import get_current_user, get_admin_user, get_finance_user
from models.request import TravelStatus
from models.response import DataResponse, ListResponse, BaseResponse
from utils.helpers import safe_object_id, utc_now, paginate_query

router = APIRouter()


# ============ Dashboard / Stats Routes ============

@router.get("/dashboard", response_model=DataResponse)
async def admin_dashboard(
    current_user: dict = Depends(get_admin_user),
    db = Depends(get_database),
):
    """Get admin dashboard statistics"""
    
    # Count requests by status
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = {}
    async for doc in db.travel_requests.aggregate(pipeline):
        status_counts[doc["_id"]] = doc["count"]
    
    # Count pending approvals
    pending_supervisor = await db.travel_requests.count_documents({
        "status": TravelStatus.PENDING_SUPERVISOR.value
    })
    pending_president = await db.travel_requests.count_documents({
        "status": TravelStatus.PENDING_PRESIDENT.value
    })
    pending_post_travel = await db.travel_requests.count_documents({
        "status": TravelStatus.POST_TRAVEL_SUBMITTED.value
    })
    pending_finance = await db.travel_requests.count_documents({
        "status": TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value
    })
    
    # Recent activity (last 7 days)
    week_ago = utc_now() - timedelta(days=7)
    recent_submissions = await db.travel_requests.count_documents({
        "submitted_at": {"$gte": week_ago}
    })
    recent_completions = await db.travel_requests.count_documents({
        "completed_at": {"$gte": week_ago}
    })
    
    # Total users by role
    user_pipeline = [
        {"$group": {"_id": "$role", "count": {"$sum": 1}}}
    ]
    user_counts = {}
    async for doc in db.users.aggregate(user_pipeline):
        user_counts[doc["_id"]] = doc["count"]
    
    return DataResponse(
        success=True,
        message="Dashboard data retrieved",
        data={
            "status_counts": status_counts,
            "pending_approvals": {
                "supervisor": pending_supervisor,
                "president": pending_president,
                "post_travel": pending_post_travel,
                "finance": pending_finance,
                "total": pending_supervisor + pending_president + pending_post_travel + pending_finance,
            },
            "recent_activity": {
                "submissions": recent_submissions,
                "completions": recent_completions,
            },
            "user_counts": user_counts,
        }
    )


# ============ All Requests (Admin View) ============

@router.get("/requests", response_model=ListResponse)
async def list_all_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    department: Optional[str] = Query(None),
    traveler_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_admin_user),
    db = Depends(get_database),
):
    """List all travel requests with filters (admin only)"""
    skip, limit = paginate_query(page, per_page)
    
    # Build query
    query = {}
    
    if status_filter:
        query["status"] = status_filter.upper()
    
    if department:
        query["department"] = department
    
    if traveler_id:
        query["traveler_id"] = traveler_id
    
    if date_from:
        query["departure_date"] = {"$gte": date_from}
    
    if date_to:
        if "departure_date" in query:
            query["departure_date"]["$lte"] = date_to
        else:
            query["departure_date"] = {"$lte": date_to}
    
    if search:
        query["$or"] = [
            {"traveler_name": {"$regex": search, "$options": "i"}},
            {"destination": {"$regex": search, "$options": "i"}},
            {"ta_number": {"$regex": search, "$options": "i"}},
            {"purpose": {"$regex": search, "$options": "i"}},
        ]
    
    # Get total count
    total = await db.travel_requests.count_documents(query)
    
    # Get requests
    cursor = db.travel_requests.find(query).sort("created_at", -1).skip(skip).limit(limit)
    
    requests = []
    async for req in cursor:
        req["_id"] = str(req["_id"])
        requests.append(req)
    
    return ListResponse(
        success=True,
        message="Requests retrieved",
        data=requests,
        total=total,
        page=page,
        per_page=per_page,
    )


# ============ Post-Travel Reminders ============

@router.post("/send-post-travel-reminders", response_model=DataResponse)
async def send_post_travel_reminders(
    background_tasks: BackgroundTasks,
    days_since_return: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_admin_user),
    db = Depends(get_database),
):
    """
    Send reminders to travelers who haven't submitted post-travel reports.
    Targets requests with TA_ISSUED status where return_date is past.
    """
    cutoff_date = (utc_now() - timedelta(days=days_since_return)).date().isoformat()
    
    query = {
        "status": TravelStatus.TA_ISSUED.value,
        "return_date": {"$lt": cutoff_date},
    }
    
    cursor = db.travel_requests.find(query)
    
    reminders_sent = 0
    async for request in cursor:
        traveler_id = str(request.get("traveler_id"))
        request_id = str(request["_id"])
        destination = request.get("destination")
        return_date = request.get("return_date")
        
        notification = {
            "user_id": traveler_id,
            "title": "Post-Travel Report Reminder",
            "message": f"Please submit your post-travel report for your trip to {destination} (returned {return_date})",
            "notification_type": "warning",
            "link": f"/requests/{request_id}/view",
            "is_read": False,
            "created_at": utc_now(),
        }
        await db.notifications.insert_one(notification)
        
        await db.travel_requests.update_one(
            {"_id": request["_id"]},
            {"$set": {"last_reminder_sent": utc_now()}}
        )
        
        reminders_sent += 1
    
    return DataResponse(
        success=True,
        message=f"Sent {reminders_sent} post-travel reminders",
        data={"reminders_sent": reminders_sent}
    )


@router.get("/test-post-travel-reminders", response_model=DataResponse)
async def test_post_travel_reminders(
    days_since_return: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_admin_user),
    db = Depends(get_database),
):
    """Test/preview which requests would receive post-travel reminders."""
    cutoff_date = (utc_now() - timedelta(days=days_since_return)).date().isoformat()
    
    query = {
        "status": TravelStatus.TA_ISSUED.value,
        "return_date": {"$lt": cutoff_date},
    }
    
    cursor = db.travel_requests.find(query).limit(50)
    
    pending_reminders = []
    async for request in cursor:
        pending_reminders.append({
            "request_id": str(request["_id"]),
            "ta_number": request.get("ta_number"),
            "traveler_name": request.get("traveler_name"),
            "destination": request.get("destination"),
            "return_date": request.get("return_date"),
        })
    
    return DataResponse(
        success=True,
        message=f"Found {len(pending_reminders)} requests needing reminders",
        data=pending_reminders
    )


# ============ Debug Routes ============

@router.get("/debug/post-travel-visibility", response_model=DataResponse)
async def debug_post_travel_visibility(
    request_id: str = Query(...),
    current_user: dict = Depends(get_admin_user),
    db = Depends(get_database),
):
    """Debug endpoint to check post-travel report visibility"""
    obj_id = safe_object_id(request_id)
    if not obj_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request ID")
    
    travel_request = await db.travel_requests.find_one({"_id": obj_id})
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    debug_info = {
        "request_id": str(travel_request["_id"]),
        "ta_number": travel_request.get("ta_number"),
        "status": travel_request.get("status"),
        "has_expense_report": travel_request.get("expense_report") is not None,
        "has_mileage_report": travel_request.get("mileage_report") is not None,
        "has_trip_report": travel_request.get("trip_report") is not None,
        "has_post_travel_report": travel_request.get("post_travel_report") is not None,
        "approval_history": travel_request.get("approval_history", []),
    }
    
    return DataResponse(success=True, message="Debug info retrieved", data=debug_info)


@router.get("/scheduler-status", response_model=DataResponse)
async def scheduler_status(current_user: dict = Depends(get_admin_user)):
    """Check scheduler/background tasks status"""
    return DataResponse(
        success=True,
        message="Scheduler status",
        data={
            "scheduler_type": "FastAPI BackgroundTasks",
            "status": "active",
            "note": "For scheduled jobs, integrate with Celery or APScheduler.",
        }
    )


# ============ User Management ============

@router.get("/users", response_model=ListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_admin_user),
    db = Depends(get_database),
):
    """List all users (admin only)"""
    skip, limit = paginate_query(page, per_page)
    
    query = {}
    if role:
        query["role"] = role.upper()
    if department:
        query["department"] = department
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
        ]
    
    total = await db.users.count_documents(query)
    cursor = db.users.find(query, {"password_hash": 0}).sort("created_at", -1).skip(skip).limit(limit)
    
    users = []
    async for user in cursor:
        user["_id"] = str(user["_id"])
        users.append(user)
    
    return ListResponse(success=True, message="Users retrieved", data=users, total=total, page=page, per_page=per_page)


@router.get("/departments", response_model=DataResponse)
async def list_departments(current_user: dict = Depends(get_current_user), db = Depends(get_database)):
    """List all departments"""
    departments = await db.departments.find().to_list(100)
    for dept in departments:
        dept["_id"] = str(dept["_id"])
    return DataResponse(success=True, message="Departments retrieved", data=departments)


@router.get("/supervisors", response_model=DataResponse)
async def list_supervisors(
    department: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """List all users who can be supervisors"""
    query = {"role": {"$in": ["SUPERVISOR", "ADMIN", "PRESIDENT"]}, "is_active": True}
    if department:
        query["department"] = department
    
    cursor = db.users.find(query, {"password_hash": 0})
    supervisors = []
    async for user in cursor:
        supervisors.append({
            "id": str(user["_id"]),
            "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            "email": user.get("email"),
            "department": user.get("department"),
            "role": user.get("role"),
        })
    
    return DataResponse(success=True, message="Supervisors retrieved", data=supervisors)


# ============ Reports ============

@router.get("/reports/summary", response_model=DataResponse)
async def generate_summary_report(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    current_user: dict = Depends(get_finance_user),
    db = Depends(get_database),
):
    """Generate summary report of travel expenses"""
    match_stage = {}
    
    if date_from or date_to:
        match_stage["departure_date"] = {}
        if date_from:
            match_stage["departure_date"]["$gte"] = date_from
        if date_to:
            match_stage["departure_date"]["$lte"] = date_to
    
    if department:
        match_stage["department"] = department
    
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {
            "$group": {
                "_id": "$department",
                "total_requests": {"$sum": 1},
                "total_estimated": {"$sum": "$estimated_cost"},
                "total_spent": {"$sum": "$post_travel_report.total_spent"},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "COMPLETED"]}, 1, 0]}},
            }
        },
        {"$sort": {"total_requests": -1}}
    ]
    
    results = []
    async for doc in db.travel_requests.aggregate(pipeline):
        results.append(doc)
    
    grand_total = {
        "total_requests": sum(r["total_requests"] for r in results),
        "total_estimated": sum(r["total_estimated"] for r in results),
        "total_spent": sum(r.get("total_spent", 0) or 0 for r in results),
        "completed": sum(r["completed"] for r in results),
    }
    
    return DataResponse(
        success=True,
        message="Summary report generated",
        data={"by_department": results, "grand_total": grand_total}
    )
