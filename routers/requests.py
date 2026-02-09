"""
Travel Requests Router
Handles: CRUD operations, request submission, editing, viewing
Updated to match NTU Travel Form fields

NOTE: Authentication DISABLED for testing. Re-enable for production!
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime, timezone, date
from bson import ObjectId
from enum import Enum
import os

from dependencies.database import get_database, get_settings
# Auth imports kept but not used
# from dependencies.auth import (
#     get_current_user,
#     can_view_request,
#     can_edit_request,
# )
from models.request import (
    TravelRequestResponse,
    TravelStatus,
    TravelType,
    TravelDestinationType,
    VehicleSelection,
    PurposeOfTravel,
    BookingDetails,
    AdditionalFundsRequest,
    AdditionalFundsResponse,
    TravelerInfo,
    TravelerListResponse,
    TravelerDetailResponse,
    SupervisorInfo,
)
from models.response import ListResponse, DataResponse
from utils.file_validation import validate_and_save_file, delete_file, ALLOWED_EXTENSIONS
from utils.helpers import (
    generate_ta_number_async,
    safe_parse_date,
    safe_float,
    safe_object_id,
    get_user_full_name,
    paginate_query,
    build_sort_query,
    utc_now,
)
from services.email_service import EmailService

router = APIRouter()


# ============ Helper Functions ============

async def get_request_by_id(db, request_id: str) -> Optional[dict]:
    """Get travel request by ID"""
    obj_id = safe_object_id(request_id)
    if not obj_id:
        return None
    return await db.travel_requests.find_one({"_id": obj_id})


async def send_notification_with_sms(
    db,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    link: Optional[str] = None,
    send_sms: bool = True
):
    """Send in-app notification and optionally SMS"""
    notification = {
        "user_id": user_id,
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "link": link,
        "is_read": False,
        "created_at": utc_now(),
    }
    await db.notifications.insert_one(notification)


# ============ Traveler Selection Routes ============

@router.get("/travelers", response_model=TravelerListResponse)
async def get_travelers(
    search: Optional[str] = Query(None, description="Search by name, email, or employee ID"),
    include_students: bool = Query(True, description="Include student travelers"),
    include_visiting: bool = Query(False, description="Include visiting members"),
    db = Depends(get_database),
):
    """
    Get list of travelers for dropdown selection.
    Users can create travel requests for themselves, on behalf of others, or for visiting members.
    
    Search Parameters:
    - search: Search by first name, last name, full name, email, or employee ID
    - include_students: Include users with user_type='student'
    - include_visiting: Include users with user_type='visiting'
    
    Returns traveler details including: name, email, employee_id, department, phone, job_title
    """
    print(f"\n{'='*60}")
    print(f"🔍 GET /travelers called")
    print(f"   search: {search}")
    print(f"   include_students: {include_students}")
    print(f"   include_visiting: {include_visiting}")
    print(f"{'='*60}")
    
    # Build query
    query = {}
    
    # Add search filter if provided
    if search:
        search = search.strip()
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"job_title": {"$regex": search, "$options": "i"}},
        ]
    
    print(f"   MongoDB Query: {query}")
    
    # Define projection - exclude only password
    projection = {
        "password": 0,
        "password_hash": 0,
        "reset_token": 0,
        "reset_token_expiry": 0
    }
    
    try:
        # Execute query with sorting (by first_name, last_name)
        cursor = db.users.find(query, projection).sort([
            ("first_name", 1),
            ("last_name", 1)
        ]).limit(100)
        
        travelers = []
        async for user in cursor:
            # Build full name from first_name + last_name
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            
            # If no name, use email
            if not full_name:
                full_name = user.get("email", "Unknown User")
            
            # Determine user type (default to employee if not set)
            user_type = user.get("user_type", "employee")
            job_title = user.get("job_title", "")
            
            # Filter by user type based on flags
            if user_type == "student" and not include_students:
                continue
            if user_type == "visiting" and not include_visiting:
                continue
            
            # Build traveler info with all available fields
            traveler_data = TravelerInfo(
                id=str(user["_id"]),
                name=full_name,
                email=user.get("email", ""),
                employee_id=user.get("employee_id"),
                department=user.get("department"),
                phone=user.get("phone"),
                role=user.get("role") or job_title,
                user_type=user_type,
                is_employee=user_type == "employee" or user_type is None,
                is_student=user_type == "student",
                is_visiting=user_type == "visiting",
                supervisor_id=str(user.get("supervisor_id")) if user.get("supervisor_id") else None,
            )
            
            travelers.append(traveler_data)
        
        print(f"   ✅ Found {len(travelers)} travelers")
        for t in travelers[:5]:
            print(f"      - {t.name} | {t.email} | {t.department} | {t.employee_id}")
        
        return TravelerListResponse(success=True, travelers=travelers, total=len(travelers))
    
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return TravelerListResponse(success=False, travelers=[], total=0)


@router.get("/travelers/{traveler_id}", response_model=DataResponse)
async def get_traveler_details(
    traveler_id: str,
    db = Depends(get_database),
):
    """
    Get detailed information for a specific traveler by ID.
    Returns full traveler profile including all fields from MongoDB.
    """
    print(f"\n🔍 GET /travelers/{traveler_id} called")
    
    obj_id = safe_object_id(traveler_id)
    if not obj_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid traveler ID format"
        )
    
    # Get traveler from database
    traveler = await db.users.find_one(
        {"_id": obj_id},
        {
            "password": 0,
            "password_hash": 0,
            "reset_token": 0,
            "reset_token_expiry": 0
        }
    )
    
    if not traveler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Traveler not found"
        )
    
    # Build full name
    first_name = traveler.get("first_name", "")
    last_name = traveler.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    
    # Get supervisor info if available
    supervisor_id = traveler.get("supervisor_id")
    supervisor_info = None
    if supervisor_id:
        try:
            sup_obj_id = ObjectId(supervisor_id) if isinstance(supervisor_id, str) else supervisor_id
            supervisor = await db.users.find_one(
                {"_id": sup_obj_id},
                {"first_name": 1, "last_name": 1, "email": 1, "department": 1, "job_title": 1}
            )
            if supervisor:
                sup_name = f"{supervisor.get('first_name', '')} {supervisor.get('last_name', '')}".strip()
                supervisor_info = {
                    "id": str(supervisor["_id"]),
                    "name": sup_name,
                    "email": supervisor.get("email"),
                    "department": supervisor.get("department"),
                    "job_title": supervisor.get("job_title")
                }
        except Exception as e:
            print(f"   ⚠️ Error fetching supervisor: {e}")
    
    # Get travel statistics
    travel_count = await db.travel_requests.count_documents({
        "$or": [
            {"traveler_id": traveler_id},
            {"traveler_id": str(obj_id)}
        ]
    })
    
    # Get last travel request
    last_travel = await db.travel_requests.find_one(
        {"$or": [{"traveler_id": traveler_id}, {"traveler_id": str(obj_id)}]},
        sort=[("created_at", -1)]
    )
    
    # Build complete response with ALL fields from MongoDB
    traveler_data = {
        "id": str(traveler["_id"]),
        "first_name": first_name,
        "last_name": last_name,
        "name": full_name,
        "email": traveler.get("email", ""),
        "employee_id": traveler.get("employee_id"),
        "department": traveler.get("department"),
        "phone": traveler.get("phone"),
        "carrier": traveler.get("carrier"),
        "job_title": traveler.get("job_title"),
        "dob": traveler.get("dob"),
        "gender": traveler.get("gender"),
        "address": traveler.get("address"),
        "join_date": traveler.get("join_date"),
        "email_verified": traveler.get("email_verified"),
        "phone_verified": traveler.get("phone_verified"),
        "user_type": traveler.get("user_type", "employee"),
        "is_employee": traveler.get("user_type", "employee") == "employee",
        "is_student": traveler.get("user_type") == "student",
        "is_visiting": traveler.get("user_type") == "visiting",
        "supervisor": supervisor_info,
        "supervisor_id": str(supervisor_id) if supervisor_id else None,
        "travel_stats": {
            "total_requests": travel_count,
            "last_travel_date": last_travel.get("departure_date") if last_travel else None,
            "last_destination": last_travel.get("destination_city") if last_travel else None
        },
        "created_at": traveler.get("created_at"),
        "updated_at": traveler.get("updated_at"),
        "last_login": traveler.get("last_login")
    }
    
    print(f"   ✅ Found traveler: {full_name} ({traveler.get('email')})")
    
    return DataResponse(
        success=True,
        message="Traveler details retrieved successfully",
        data=traveler_data
    )


# ============ Form Options Routes ============

@router.get("/supervisors")
async def get_supervisors(
    search: Optional[str] = Query(None, description="Search by name or email"),
    db = Depends(get_database),
):
    """
    Get list of supervisors for dropdown selection.
    Returns supervisors with role SUPERVISOR, PRESIDENT, ADMIN, or FINANCE.
    """
    print(f"\n{'='*60}")
    print(f"🔍 GET /supervisors called")
    print(f"   search: {search}")
    print(f"{'='*60}")
    
    # Build query for supervisors (users with supervisor-like roles)
    query = {
        "$or": [
            {"role": {"$in": ["SUPERVISOR", "PRESIDENT", "ADMIN", "FINANCE", "DEPARTMENT_HEAD"]}},
            {"job_title": {"$regex": "supervisor|president|manager|director|head|dean", "$options": "i"}},
            {"is_supervisor": True}
        ]
    }
    
    # Add search filter if provided
    if search:
        search = search.strip()
        query = {
            "$and": [
                query,
                {
                    "$or": [
                        {"first_name": {"$regex": search, "$options": "i"}},
                        {"last_name": {"$regex": search, "$options": "i"}},
                        {"email": {"$regex": search, "$options": "i"}},
                        {"department": {"$regex": search, "$options": "i"}},
                    ]
                }
            ]
        }
    
    try:
        cursor = db.users.find(query, {
            "password": 0,
            "password_hash": 0,
            "reset_token": 0
        }).sort([("first_name", 1), ("last_name", 1)]).limit(50)
        
        supervisors = []
        async for user in cursor:
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            
            if not full_name:
                full_name = user.get("email", "Unknown")
            
            role = user.get("role", user.get("job_title", "Supervisor"))
            
            supervisors.append({
                "id": str(user["_id"]),
                "name": full_name,
                "email": user.get("email", ""),
                "role": role,
                "department": user.get("department", ""),
                "phone": user.get("phone", ""),
                "label": f"{full_name} ({role})",  # For dropdown display
                "value": user.get("email", "")  # Use email as value for selection
            })
        
        print(f"   ✅ Found {len(supervisors)} supervisors")
        for s in supervisors[:5]:
            print(f"      - {s['name']} | {s['email']} | {s['role']}")
        
        return {
            "success": True,
            "supervisors": supervisors,
            "total": len(supervisors)
        }
    
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "supervisors": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/purpose-options")
async def get_purpose_options():
    """Get purpose of travel options for dropdown"""
    return {
        "success": True,
        "options": [
            {"value": "conference", "label": "Conference"},
            {"value": "training", "label": "Training"},
            {"value": "workshop", "label": "Workshop"},
            {"value": "meeting", "label": "Meeting"},
            {"value": "field_work", "label": "Field Work"},
            {"value": "student_travel", "label": "Student Travel"},
            {"value": "athletic_event", "label": "Athletic Event"},
            {"value": "recruitment", "label": "Recruitment"},
            {"value": "other", "label": "Other"},
        ]
    }


@router.get("/travel-type-options")
async def get_travel_type_options():
    """Get travel type options for radio buttons"""
    return {
        "success": True,
        "options": [
            {"value": "one_day", "label": "One Day Travel"},
            {"value": "overnight", "label": "Overnight Travel"},
            {"value": "per_diem", "label": "Per Diem (2 wks. prior)"},
            {"value": "31_days", "label": "31 Days Travel"},
            {"value": "actual_receipts", "label": "Actual (Receipts)"},
        ]
    }


@router.get("/vehicle-options")
async def get_vehicle_options():
    """Get vehicle selection options for radio buttons"""
    return {
        "success": True,
        "options": [
            {"value": "not_using", "label": "Not Using Vehicle"},
            {"value": "ntu_vehicle", "label": "Using NTU Vehicle"},
            {"value": "private_vehicle", "label": "Using Private Vehicle"},
        ]
    }


@router.get("/destination-type-options")
async def get_destination_type_options():
    """Get destination type options for radio buttons"""
    return {
        "success": True,
        "options": [
            {"value": "domestic", "label": "Domestic (USA)", "icon": "flag"},
            {"value": "international", "label": "International", "icon": "globe"},
        ]
    }


# ============ Request CRUD Routes ============

@router.post("/new", response_model=TravelRequestResponse)
async def create_request(
    background_tasks: BackgroundTasks,
    # Employee/Student Information
    traveler_id: str = Form(...),
    
    # Travel Itinerary Information  
    travel_type: str = Form(...),
    travel_destination_type: str = Form(...),
    
    # Destination Information
    destination_city: str = Form(...),
    destination_state: Optional[str] = Form(None),
    destination_country: str = Form("United States"),
    place_id: Optional[str] = Form(None),
    
    # Date Information
    date_of_request: str = Form(...),
    departure_date: str = Form(...),
    return_date: str = Form(...),
    
    # Purpose Information
    purpose_of_travel: str = Form(...),
    event_activity_name: str = Form(...),
    detailed_purpose: str = Form(...),
    travel_itinerary: str = Form(...),
    
    # Vehicle Selection
    vehicle_selection: str = Form("not_using"),
    pov_mileage_estimate: Optional[float] = Form(None),
    pov_rate_per_mile: float = Form(0.67),
    
    # Supervisor - Select from available supervisors
    # Call GET /requests/supervisors to see all available options
    supervisor: str = Form(
        ..., 
        description="Supervisor email. Call GET /requests/supervisors to get available supervisors.",
        example="himanshu.bansal@harshwal.com"
    ),
    
    # Department
    department: Optional[str] = Form(None),
    
    # Estimated costs
    estimated_cost: float = Form(0),
    
    # Draft or Submit
    is_draft: bool = Form(False),
    
    # File uploads
    agenda_file: Optional[UploadFile] = File(None),
    budget_file: Optional[UploadFile] = File(None),
    registration_file: Optional[UploadFile] = File(None),
    pov_insurance_file: Optional[UploadFile] = File(None),
    
    # Optional: Specify who is creating this request (for testing "create on behalf")
    created_by: Optional[str] = Form(
        None, 
        description="User ID or email of person creating this request. Leave empty if creating for yourself."
    ),
    
    # NO AUTH - removed current_user dependency
    db = Depends(get_database),
):
    """
    Create a new travel request.
    Can be saved as draft or submitted for approval.
    
    NOTE: Authentication disabled for testing!
    
    Supervisor Selection:
    - First call GET /requests/supervisors to get list of supervisors
    - Select supervisor from dropdown (shows name and role)
    - Pass supervisor name or email in this field
    """
    print(f"\n{'='*60}")
    print(f"📝 POST /requests/new called")
    print(f"   traveler_id: {traveler_id}")
    print(f"   supervisor: {supervisor}")
    print(f"   destination: {destination_city}, {destination_state}")
    print(f"{'='*60}")
    
    settings = get_settings()
    
    # Validate traveler exists
    traveler = await db.users.find_one({"_id": ObjectId(traveler_id)})
    if not traveler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid traveler selected"
        )
    
    # ============ DETERMINE WHO IS CREATING THIS REQUEST ============
    # If created_by is provided, lookup that user; otherwise, traveler is creating for themselves
    
    if created_by:
        # Someone specified - lookup by ID or email
        creator_doc = None
        
        # Try by ID first (ObjectId)
        try:
            creator_doc = await db.users.find_one({"_id": ObjectId(created_by)})
        except:
            pass
        
        # If not found, try by email
        if not creator_doc:
            creator_doc = await db.users.find_one({"email": created_by})
        
        if not creator_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Creator not found: {created_by}"
            )
        
        creator_id = str(creator_doc["_id"])
        creator_name = f"{creator_doc.get('first_name', '')} {creator_doc.get('last_name', '')}".strip()
    else:
        # No creator specified - traveler is creating for themselves
        creator_doc = traveler
        creator_id = traveler_id
        creator_name = f"{traveler.get('first_name', '')} {traveler.get('last_name', '')}".strip()
    
    # Get creator's effective role (check job_title)
    creator_role = creator_doc.get("role", "TRAVELER")
    creator_job_title = creator_doc.get("job_title", "").upper()
    
    effective_creator_role = creator_role
    if "PRESIDENT" in creator_job_title:
        effective_creator_role = "PRESIDENT"
    elif "SUPERVISOR" in creator_job_title:
        effective_creator_role = "SUPERVISOR"
    elif "FINANCE" in creator_job_title or "FINANCE HEAD" in creator_job_title:
        effective_creator_role = "FINANCE"
    elif "ADMIN" in creator_job_title:
        effective_creator_role = "ADMIN"
    
    # ============ CREATE ON BEHALF PERMISSION CHECK ============
    is_proxy_request = (creator_id != traveler_id)
    
    if is_proxy_request:
        # Someone is creating on behalf of someone else
        traveler_name = f"{traveler.get('first_name', '')} {traveler.get('last_name', '')}".strip()
        
        # Define who can create on behalf of others
        can_create_for_others = ["SUPERVISOR", "PRESIDENT", "ADMIN"]
        
        if effective_creator_role not in can_create_for_others:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"❌ Permission Denied: {effective_creator_role} cannot create travel requests on behalf of others. {effective_creator_role} can only create requests for themselves."
            )
        
        print(f"✅ Proxy request: {creator_name} ({effective_creator_role}) creating for {traveler_name}")
    else:
        print(f"✅ Self request: {creator_name} creating for themselves")
    
    # ============ END CREATE ON BEHALF VALIDATION ============
    
    
    # Find supervisor by email OR by name (flexible lookup)
    supervisor_query = supervisor.strip()
    supervisor_doc = None
    
    # Try to find by email first
    if "@" in supervisor_query:
        supervisor_doc = await db.users.find_one({"email": supervisor_query})
    
    # If not found by email, try by name
    if not supervisor_doc:
        # Try exact match on full name
        supervisor_doc = await db.users.find_one({
            "$or": [
                {"$expr": {"$eq": [{"$concat": ["$first_name", " ", "$last_name"]}, supervisor_query]}},
                {"name": supervisor_query},
                {"first_name": supervisor_query},
            ]
        })
    
    # If still not found, try partial match
    if not supervisor_doc:
        # Split name and search
        name_parts = supervisor_query.split()
        if len(name_parts) >= 2:
            supervisor_doc = await db.users.find_one({
                "first_name": {"$regex": f"^{name_parts[0]}", "$options": "i"},
                "last_name": {"$regex": f"^{name_parts[-1]}", "$options": "i"}
            })
        else:
            supervisor_doc = await db.users.find_one({
                "$or": [
                    {"first_name": {"$regex": supervisor_query, "$options": "i"}},
                    {"last_name": {"$regex": supervisor_query, "$options": "i"}},
                    {"email": {"$regex": supervisor_query, "$options": "i"}}
                ]
            })
    
    if not supervisor_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supervisor '{supervisor}' not found. Please select from the supervisors list."
        )
    
    # Get supervisor_id from the found supervisor
    supervisor_id = str(supervisor_doc["_id"])
    
    # ============ SUPERVISOR SELECTION VALIDATION ============
    # Validate supervisor selection based on traveler role and destination type
    
    # Get traveler role - check both 'role' and 'job_title' fields
    traveler_role = traveler.get("role", "TRAVELER")
    traveler_job_title = traveler.get("job_title", "").upper()
    
    # Determine effective traveler role (prioritize job_title for President/Supervisor detection)
    effective_traveler_role = traveler_role
    if "PRESIDENT" in traveler_job_title:
        effective_traveler_role = "PRESIDENT"
    elif "SUPERVISOR" in traveler_job_title:
        effective_traveler_role = "SUPERVISOR"
    elif "FINANCE" in traveler_job_title or "FINANCE HEAD" in traveler_job_title:
        effective_traveler_role = "FINANCE"
    elif "ADMIN" in traveler_job_title:
        effective_traveler_role = "ADMIN"
    
    # Get supervisor role - check both 'role' and 'job_title' fields
    supervisor_role = supervisor_doc.get("role", "TRAVELER")
    supervisor_job_title = supervisor_doc.get("job_title", "").upper()
    
    # Determine effective supervisor role (prioritize job_title for President/Supervisor detection)
    effective_supervisor_role = supervisor_role
    if "PRESIDENT" in supervisor_job_title:
        effective_supervisor_role = "PRESIDENT"
    elif "SUPERVISOR" in supervisor_job_title:
        effective_supervisor_role = "SUPERVISOR"
    elif "FINANCE" in supervisor_job_title or "FINANCE HEAD" in supervisor_job_title:
        effective_supervisor_role = "FINANCE"
    elif "ADMIN" in supervisor_job_title:
        effective_supervisor_role = "ADMIN"
    
    supervisor_name = f"{supervisor_doc.get('first_name', '')} {supervisor_doc.get('last_name', '')}".strip()
    
    # Check if international travel
    is_international = (travel_destination_type == "international")
    
    if is_international:
        # INTERNATIONAL TRAVEL: Only PRESIDENTS allowed as supervisors
        if effective_supervisor_role != "PRESIDENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"❌ Invalid Supervisor for International Travel: Only PRESIDENTS can be selected as supervisors for international travel. You selected: {supervisor_name} ({effective_supervisor_role}). Please select a PRESIDENT."
            )
        print(f"✅ International travel: {supervisor_name} (PRESIDENT) is valid supervisor")
    else:
        # DOMESTIC TRAVEL: Role-based validation
        
        # Define allowed supervisor roles for each traveler role
        allowed_supervisor_roles = {
            "TRAVELER": ["SUPERVISOR", "PRESIDENT"],
            "SUPERVISOR": ["SUPERVISOR", "PRESIDENT"],
            "PRESIDENT": ["SUPERVISOR", "PRESIDENT"],
            "FINANCE": ["SUPERVISOR", "PRESIDENT"],
            "ADMIN": ["SUPERVISOR", "PRESIDENT"]
        }
        
        # Get allowed roles for this traveler (use effective role)
        allowed_roles = allowed_supervisor_roles.get(effective_traveler_role, ["SUPERVISOR", "PRESIDENT"])
        
        # Check if supervisor role is allowed
        if effective_supervisor_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"❌ Invalid Supervisor: {effective_traveler_role} cannot select {effective_supervisor_role} as supervisor. You selected: {supervisor_name} ({effective_supervisor_role}). Allowed supervisor roles: {', '.join(allowed_roles)}."
            )
        
        # Special case: TRAVELER cannot select themselves
        if effective_traveler_role == "TRAVELER" and traveler_id == supervisor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"❌ Invalid Supervisor: TRAVELER cannot select themselves as supervisor. Please select a SUPERVISOR or PRESIDENT."
            )
        
        # Special case: FINANCE cannot select themselves
        if effective_traveler_role == "FINANCE" and traveler_id == supervisor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"❌ Invalid Supervisor: FINANCE cannot select themselves as supervisor. Please select a SUPERVISOR or PRESIDENT."
            )
        
        # Special case: ADMIN cannot select themselves
        if effective_traveler_role == "ADMIN" and traveler_id == supervisor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"❌ Invalid Supervisor: ADMIN cannot select themselves as supervisor. Please select a SUPERVISOR or PRESIDENT."
            )
        
        print(f"✅ Domestic travel: {effective_traveler_role} selecting {supervisor_name} ({effective_supervisor_role}) is valid")
    
    # ============ END SUPERVISOR VALIDATION ============
    
    
    # Parse dates
    req_date = safe_parse_date(date_of_request)
    dep_date = safe_parse_date(departure_date)
    ret_date = safe_parse_date(return_date)
    
    if not dep_date or not ret_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use MM/DD/YYYY or YYYY-MM-DD"
        )
    
    if ret_date < dep_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Return date must be after departure date"
        )
    
    # Handle file uploads
    upload_dir = os.path.join(settings.UPLOAD_FOLDER, "travel_requests")
    os.makedirs(upload_dir, exist_ok=True)
    saved_files = {}
    
    file_fields = [
        ("agenda_file", agenda_file),
        ("budget_file", budget_file),
        ("registration_file", registration_file),
        ("pov_insurance_file", pov_insurance_file),
    ]
    
    for field_name, file in file_fields:
        if file and file.filename:
            success, msg, filename = await validate_and_save_file(
                file, upload_dir, ALLOWED_EXTENSIONS['documents']
            )
            if success:
                saved_files[field_name] = filename
            else:
                for saved_name in saved_files.values():
                    delete_file(os.path.join(upload_dir, saved_name))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File upload error ({field_name}): {msg}"
                )
    
    # Determine status
    if is_draft:
        request_status = TravelStatus.DRAFT.value
    else:
        if travel_destination_type == "international":
            request_status = TravelStatus.PENDING_PRESIDENT.value
        else:
            request_status = TravelStatus.PENDING_SUPERVISOR.value
    
    # Create request document
    now = utc_now()
    traveler_name = get_user_full_name(traveler)
    
    travel_request = {
        # Traveler Info
        "traveler_id": traveler_id,
        "traveler_name": traveler_name,
        "traveler_email": traveler.get("email"),
        "traveler_phone": traveler.get("phone"),
        "traveler_employee_id": traveler.get("employee_id"),
        "department": department or traveler.get("department"),
        
        # Created by (same as traveler since no auth)
        "created_by_id": traveler_id,
        "created_by_name": traveler_name,
        "is_proxy_request": False,
        
        # Travel Type & Destination
        "travel_type": travel_type,
        "travel_destination_type": travel_destination_type,
        "destination_city": destination_city,
        "destination_state": destination_state,
        "destination_country": destination_country,
        "place_id": place_id,
        
        # Dates
        "date_of_request": req_date.isoformat() if req_date else date.today().isoformat(),
        "departure_date": dep_date.isoformat(),
        "return_date": ret_date.isoformat(),
        
        # Purpose
        "purpose_of_travel": purpose_of_travel,
        "event_activity_name": event_activity_name,
        "detailed_purpose": detailed_purpose,
        "travel_itinerary": travel_itinerary,
        
        # Vehicle
        "vehicle_selection": vehicle_selection,
        "pov_mileage_estimate": safe_float(pov_mileage_estimate) if vehicle_selection == "private_vehicle" else None,
        "pov_rate_per_mile": safe_float(pov_rate_per_mile),
        
        # Supervisor
        "supervisor_id": supervisor_id,
        "supervisor_name": get_user_full_name(supervisor_doc),
        
        # Status
        "status": request_status,
        
        # Files
        "agenda_file": saved_files.get("agenda_file"),
        "budget_file": saved_files.get("budget_file"),
        "registration_file": saved_files.get("registration_file"),
        "pov_insurance_file": saved_files.get("pov_insurance_file"),
        "other_documents": [],
        
        # Budget tracking
        "estimated_cost": safe_float(estimated_cost),
        "original_budget": safe_float(estimated_cost),
        "additional_funds": 0,
        "total_approved_budget": safe_float(estimated_cost),
        "travel_advance": 0,
        
        # Timestamps
        "created_at": now,
        "updated_at": now,
        "submitted_at": None if is_draft else now,
    }
    
    # Insert into database
    result = await db.travel_requests.insert_one(travel_request)
    request_id = str(result.inserted_id)
    
    print(f"   ✅ Created request: {request_id}")
    print(f"   Status: {request_status}")
    
    # Send notifications if submitted (not draft)
    if not is_draft:
        background_tasks.add_task(
            send_notification_with_sms,
            db,
            supervisor_id,
            "New Travel Request Pending Approval",
            f"{traveler_name} has submitted a travel request to {destination_city}",
            "warning",
            f"/requests/{request_id}/view"
        )
        
        # Send email to supervisor about pending request
        if supervisor_doc and supervisor_doc.get("email"):
            email_data = {
                "supervisor_name": get_user_full_name(supervisor_doc),
                "traveler_name": traveler_name,
                "employee_id": traveler.get("employee_id", "N/A"),
                "department": department or traveler.get("department", "N/A"),
                "destination": destination_city,
                "departure_date": dep_date.strftime("%B %d, %Y") if dep_date else "N/A",
                "return_date": ret_date.strftime("%B %d, %Y") if ret_date else "N/A",
                "purpose": purpose_of_travel or event_activity_name or "N/A",
                "estimated_cost": f"{safe_float(estimated_cost):.2f}" if estimated_cost else "0.00",
                "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
            }
            background_tasks.add_task(
                EmailService.send_new_request_to_supervisor,
                supervisor_doc.get("email"),
                email_data
            )
            print(f"   📧 Pending approval email queued for supervisor: {supervisor_doc.get('email')}")
    
    return TravelRequestResponse(
        success=True,
        message="Travel request saved as draft" if is_draft else "Travel request submitted successfully",
        request_id=request_id,
    )


@router.get("/{request_id}", response_model=DataResponse)
async def view_request(
    request_id: str,
    db = Depends(get_database),
):
    """Get travel request details - NO AUTH"""
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    travel_request["_id"] = str(travel_request["_id"])
    
    # Get supervisor details
    if travel_request.get("supervisor_id"):
        supervisor = await db.users.find_one({"_id": ObjectId(travel_request["supervisor_id"])})
        if supervisor:
            travel_request["supervisor_name"] = get_user_full_name(supervisor)
            travel_request["supervisor_email"] = supervisor.get("email")
    
    # Get traveler details
    if travel_request.get("traveler_id"):
        traveler = await db.users.find_one({"_id": ObjectId(travel_request["traveler_id"])})
        if traveler:
            travel_request["traveler_details"] = {
                "name": get_user_full_name(traveler),
                "email": traveler.get("email"),
                "phone": traveler.get("phone"),
                "employee_id": traveler.get("employee_id"),
                "department": traveler.get("department"),
            }
    
    return DataResponse(
        success=True,
        message="Request retrieved successfully",
        data=travel_request
    )


@router.put("/{request_id}", response_model=TravelRequestResponse)
async def edit_request(
    request_id: str,
    background_tasks: BackgroundTasks,
    traveler_id: Optional[str] = Form(None),
    travel_type: Optional[str] = Form(None),
    travel_destination_type: Optional[str] = Form(None),
    destination_city: Optional[str] = Form(None),
    destination_state: Optional[str] = Form(None),
    destination_country: Optional[str] = Form(None),
    departure_date: Optional[str] = Form(None),
    return_date: Optional[str] = Form(None),
    purpose_of_travel: Optional[str] = Form(None),
    event_activity_name: Optional[str] = Form(None),
    detailed_purpose: Optional[str] = Form(None),
    travel_itinerary: Optional[str] = Form(None),
    vehicle_selection: Optional[str] = Form(None),
    pov_mileage_estimate: Optional[float] = Form(None),
    supervisor_id: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    estimated_cost: Optional[float] = Form(None),
    submit: bool = Form(False),
    agenda_file: Optional[UploadFile] = File(None),
    budget_file: Optional[UploadFile] = File(None),
    registration_file: Optional[UploadFile] = File(None),
    pov_insurance_file: Optional[UploadFile] = File(None),
    db = Depends(get_database),
):
    """Edit an existing travel request - NO AUTH"""
    settings = get_settings()
    
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    update_data = {"updated_at": utc_now()}
    
    # Update simple fields
    field_mapping = {
        "traveler_id": traveler_id,
        "travel_type": travel_type,
        "travel_destination_type": travel_destination_type,
        "destination_city": destination_city,
        "destination_state": destination_state,
        "destination_country": destination_country,
        "purpose_of_travel": purpose_of_travel,
        "event_activity_name": event_activity_name,
        "detailed_purpose": detailed_purpose,
        "travel_itinerary": travel_itinerary,
        "vehicle_selection": vehicle_selection,
        "department": department,
    }
    
    for field, value in field_mapping.items():
        if value is not None:
            update_data[field] = value
    
    # Parse dates
    if departure_date:
        dep_date = safe_parse_date(departure_date)
        if dep_date:
            update_data["departure_date"] = dep_date.isoformat()
    
    if return_date:
        ret_date = safe_parse_date(return_date)
        if ret_date:
            update_data["return_date"] = ret_date.isoformat()
    
    # Update supervisor
    if supervisor_id:
        supervisor = await db.users.find_one({"_id": ObjectId(supervisor_id)})
        if supervisor:
            update_data["supervisor_id"] = supervisor_id
            update_data["supervisor_name"] = get_user_full_name(supervisor)
    
    if pov_mileage_estimate is not None:
        update_data["pov_mileage_estimate"] = safe_float(pov_mileage_estimate)
    
    if estimated_cost is not None:
        update_data["estimated_cost"] = safe_float(estimated_cost)
        update_data["original_budget"] = safe_float(estimated_cost)
        update_data["total_approved_budget"] = safe_float(estimated_cost) + travel_request.get("additional_funds", 0)
    
    # Handle file uploads
    upload_dir = os.path.join(settings.UPLOAD_FOLDER, "travel_requests")
    os.makedirs(upload_dir, exist_ok=True)
    
    for field_name, file in [("agenda_file", agenda_file), ("budget_file", budget_file), 
                              ("registration_file", registration_file), ("pov_insurance_file", pov_insurance_file)]:
        if file and file.filename:
            success, msg, filename = await validate_and_save_file(file, upload_dir, ALLOWED_EXTENSIONS['documents'])
            if success:
                old_file = travel_request.get(field_name)
                if old_file:
                    delete_file(os.path.join(upload_dir, old_file))
                update_data[field_name] = filename
    
    # Handle submit
    current_status = travel_request.get("status")
    if submit and current_status == TravelStatus.DRAFT.value:
        dest_type = update_data.get("travel_destination_type", travel_request.get("travel_destination_type"))
        update_data["status"] = TravelStatus.PENDING_PRESIDENT.value if dest_type == "international" else TravelStatus.PENDING_SUPERVISOR.value
        update_data["submitted_at"] = utc_now()
    
    await db.travel_requests.update_one({"_id": ObjectId(request_id)}, {"$set": update_data})
    
    return TravelRequestResponse(
        success=True,
        message="Travel request updated and submitted" if submit else "Travel request updated",
        request_id=request_id,
    )


@router.delete("/{request_id}", response_model=TravelRequestResponse)
async def delete_draft(
    request_id: str,
    db = Depends(get_database),
):
    """Delete a draft travel request - NO AUTH"""
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    if travel_request.get("status") != TravelStatus.DRAFT.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft requests can be deleted")
    
    await db.travel_requests.delete_one({"_id": ObjectId(request_id)})
    
    return TravelRequestResponse(success=True, message="Draft request deleted successfully", request_id=request_id)


@router.post("/{request_id}/cancel", response_model=TravelRequestResponse)
async def cancel_request(
    request_id: str,
    reason: str = Form(None),
    db = Depends(get_database),
):
    """Cancel a submitted travel request - NO AUTH"""
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    if travel_request.get("status") in [TravelStatus.COMPLETED.value, TravelStatus.CANCELLED.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel this request")
    
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": TravelStatus.CANCELLED.value, "cancelled_at": utc_now(), 
                  "cancellation_reason": reason, "updated_at": utc_now()}}
    )
    
    return TravelRequestResponse(success=True, message="Travel request cancelled", request_id=request_id)


# ============ List Routes ============

@router.get("/", response_model=ListResponse)
async def list_all_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    traveler_id: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db = Depends(get_database),
):
    """List all travel requests - NO AUTH (returns all requests)"""
    skip, limit = paginate_query(page, per_page)
    
    query = {}
    if status_filter:
        query["status"] = status_filter.upper()
    if traveler_id:
        query["traveler_id"] = traveler_id
    
    total = await db.travel_requests.count_documents(query)
    sort = build_sort_query(sort_by, sort_order)
    cursor = db.travel_requests.find(query).sort(sort).skip(skip).limit(limit)
    
    requests = []
    async for req in cursor:
        req["_id"] = str(req["_id"])
        requests.append(req)
    
    return ListResponse(success=True, message="Requests retrieved", data=requests, total=total, page=page, per_page=per_page)


# ============ Booking & Additional Funds ============

@router.put("/{request_id}/booking", response_model=TravelRequestResponse)
async def update_booking(
    request_id: str,
    booking: BookingDetails,
    db = Depends(get_database),
):
    """Update booking details - NO AUTH"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    if travel_request.get("status") not in [TravelStatus.TA_ISSUED.value, TravelStatus.SUPERVISOR_APPROVED.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking can only be updated after TA is issued")
    
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"booking_details": booking.model_dump(exclude_none=True), "updated_at": utc_now()}}
    )
    
    return TravelRequestResponse(success=True, message="Booking details updated", request_id=request_id)


@router.post("/{request_id}/additional-funds", response_model=AdditionalFundsResponse)
async def request_additional_funds(
    request_id: str,
    funds_request: AdditionalFundsRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_database),
):
    """Request additional funds - NO AUTH"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    if travel_request.get("status") != TravelStatus.TA_ISSUED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Additional funds can only be requested after TA is issued")
    
    current_additional = safe_float(travel_request.get("additional_funds", 0))
    original_budget = safe_float(travel_request.get("original_budget", 0))
    new_additional = current_additional + funds_request.amount
    new_total = original_budget + new_additional
    
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"additional_funds": new_additional, "total_approved_budget": new_total, "updated_at": utc_now()},
         "$push": {"additional_funds_history": {"amount": funds_request.amount, "reason": funds_request.reason, 
                                                 "requested_at": utc_now()}}}
    )
    
    return AdditionalFundsResponse(success=True, message=f"Additional funds of ${funds_request.amount:.2f} approved",
                                   new_total_budget=new_total, additional_funds_total=new_additional)