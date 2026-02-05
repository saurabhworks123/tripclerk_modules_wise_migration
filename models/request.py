# """
# Pydantic Models for Travel Request System
# Updated to match actual NTU Travel form fields
# """

# from pydantic import BaseModel, Field, field_validator
# from typing import Optional, List, Any
# from datetime import datetime, date
# from enum import Enum
# from bson import ObjectId


# class PyObjectId(str):
#     """Custom type for MongoDB ObjectId"""
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v, info):
#         if isinstance(v, ObjectId):
#             return str(v)
#         if isinstance(v, str) and ObjectId.is_valid(v):
#             return v
#         raise ValueError("Invalid ObjectId")


# class TravelStatus(str, Enum):
#     DRAFT = "DRAFT"
#     PENDING_SUPERVISOR = "PENDING_SUPERVISOR"
#     PENDING_PRESIDENT = "PENDING_PRESIDENT"
#     SUPERVISOR_APPROVED = "SUPERVISOR_APPROVED"
#     TA_ISSUED = "TA_ISSUED"
#     REJECTED = "REJECTED"
#     CANCELLED = "CANCELLED"
#     POST_TRAVEL_SUBMITTED = "POST_TRAVEL_SUBMITTED"
#     POST_TRAVEL_SUPERVISOR_APPROVED = "POST_TRAVEL_SUPERVISOR_APPROVED"
#     POST_TRAVEL_FINANCE_APPROVED = "POST_TRAVEL_FINANCE_APPROVED"
#     COMPLETED = "COMPLETED"


# class TravelDestinationType(str, Enum):
#     DOMESTIC = "domestic"
#     INTERNATIONAL = "international"


# class TravelType(str, Enum):
#     ONE_DAY = "one_day"
#     OVERNIGHT = "overnight"
#     PER_DIEM = "per_diem"  # 2 weeks prior
#     THIRTY_ONE_DAYS = "31_days"
#     ACTUAL_RECEIPTS = "actual_receipts"


# class VehicleSelection(str, Enum):
#     NOT_USING = "not_using"
#     NTU_VEHICLE = "ntu_vehicle"
#     PRIVATE_VEHICLE = "private_vehicle"


# class PurposeOfTravel(str, Enum):
#     CONFERENCE = "conference"
#     TRAINING = "training"
#     WORKSHOP = "workshop"
#     MEETING = "meeting"
#     FIELD_WORK = "field_work"
#     STUDENT_TRAVEL = "student_travel"
#     ATHLETIC_EVENT = "athletic_event"
#     RECRUITMENT = "recruitment"
#     OTHER = "other"


# class TransportMode(str, Enum):
#     AIR = "air"
#     GROUND = "ground"
#     POV = "pov"
#     RENTAL = "rental"
#     NTU_VEHICLE = "ntu_vehicle"


# # ============ Request Models ============

# class TravelRequestCreate(BaseModel):
#     """Model for creating new travel requests - matches NTU form"""
    
#     # Employee/Student Information
#     traveler_id: str  # Selected traveler (can create for self, others, or visiting members)
    
#     # Travel Itinerary Information
#     travel_type: TravelType  # One Day, Overnight, Per Diem, 31 Days, Actual
#     travel_destination_type: TravelDestinationType  # Domestic or International
    
#     # Destination Information
#     destination_city: str = Field(..., min_length=1, max_length=200)
#     destination_state: Optional[str] = None  # Auto-filled from city
#     destination_country: str = "United States"  # Based on destination type
    
#     # Date Information
#     date_of_request: date  # Auto-filled with today's date
#     departure_date: date
#     return_date: date
    
#     # Purpose Information
#     purpose_of_travel: PurposeOfTravel
#     event_activity_name: str = Field(..., min_length=1, max_length=500)  # e.g., AISES National Conference 2025
#     detailed_purpose: str = Field(..., min_length=10, max_length=2000)
#     travel_itinerary: str = Field(..., min_length=5, max_length=1000)  # e.g., Crownpoint, ABQ - Minneapolis - Return
    
#     # Vehicle Selection
#     vehicle_selection: VehicleSelection = VehicleSelection.NOT_USING
    
#     # If using private vehicle
#     pov_mileage_estimate: Optional[float] = None
#     pov_rate_per_mile: float = 0.67  # IRS rate
    
#     # Supervisor
#     supervisor_id: str
    
#     # Department
#     department: Optional[str] = None
    
#     # Draft or Submit
#     is_draft: bool = False
    
#     @field_validator('return_date')
#     @classmethod
#     def return_after_departure(cls, v, info):
#         if 'departure_date' in info.data and v < info.data['departure_date']:
#             raise ValueError('Return date must be after departure date')
#         return v


# class TravelRequestUpdate(BaseModel):
#     """Model for updating travel requests"""
#     # All fields optional for partial updates
#     traveler_id: Optional[str] = None
#     travel_type: Optional[TravelType] = None
#     travel_destination_type: Optional[TravelDestinationType] = None
#     destination_city: Optional[str] = None
#     destination_state: Optional[str] = None
#     destination_country: Optional[str] = None
#     departure_date: Optional[date] = None
#     return_date: Optional[date] = None
#     purpose_of_travel: Optional[PurposeOfTravel] = None
#     event_activity_name: Optional[str] = None
#     detailed_purpose: Optional[str] = None
#     travel_itinerary: Optional[str] = None
#     vehicle_selection: Optional[VehicleSelection] = None
#     pov_mileage_estimate: Optional[float] = None
#     supervisor_id: Optional[str] = None
#     department: Optional[str] = None


# class DestinationInfo(BaseModel):
#     """Destination information sub-model"""
#     city: str
#     state: Optional[str] = None
#     country: str = "United States"
#     # For Google Places autocomplete
#     place_id: Optional[str] = None
#     formatted_address: Optional[str] = None


# class TravelRequestInDB(BaseModel):
#     """Model for travel request stored in database"""
#     id: PyObjectId = Field(alias="_id")
    
#     # TA Number (generated on approval)
#     ta_number: Optional[str] = None
    
#     # Employee/Traveler Info
#     traveler_id: str
#     traveler_name: str
#     traveler_email: str
#     traveler_phone: Optional[str] = None
#     traveler_employee_id: Optional[str] = None
#     department: Optional[str] = None
    
#     # Travel Type & Destination
#     travel_type: TravelType
#     travel_destination_type: TravelDestinationType
#     destination_city: str
#     destination_state: Optional[str] = None
#     destination_country: str
    
#     # Dates
#     date_of_request: date
#     departure_date: date
#     return_date: date
    
#     # Purpose
#     purpose_of_travel: PurposeOfTravel
#     event_activity_name: str
#     detailed_purpose: str
#     travel_itinerary: str
    
#     # Vehicle
#     vehicle_selection: VehicleSelection
#     pov_mileage_estimate: Optional[float] = None
#     pov_rate_per_mile: float = 0.67
    
#     # Supervisor
#     supervisor_id: str
#     supervisor_name: Optional[str] = None
    
#     # Status
#     status: TravelStatus = TravelStatus.DRAFT
    
#     # Timestamps
#     created_at: datetime
#     updated_at: datetime
#     submitted_at: Optional[datetime] = None
    
#     # Approval tracking
#     supervisor_approved_at: Optional[datetime] = None
#     supervisor_approved_by: Optional[str] = None
#     president_approved_at: Optional[datetime] = None
#     president_approved_by: Optional[str] = None
    
#     # Documents
#     agenda_file: Optional[str] = None
#     budget_file: Optional[str] = None
#     registration_file: Optional[str] = None
#     pov_insurance_file: Optional[str] = None
#     other_documents: List[str] = []
    
#     # Booking details
#     booking_details: Optional[dict] = None
    
#     # Budget tracking
#     estimated_cost: float = 0
#     original_budget: float = 0
#     additional_funds: float = 0
#     total_approved_budget: float = 0
#     travel_advance: float = 0
    
#     class Config:
#         populate_by_name = True
#         json_encoders = {ObjectId: str}


# class TravelRequestResponse(BaseModel):
#     """Response model for travel requests"""
#     success: bool
#     message: str
#     request_id: Optional[str] = None
#     ta_number: Optional[str] = None
#     data: Optional[dict] = None


# # ============ Traveler Selection Models ============

# class TravelerInfo(BaseModel):
#     """Traveler information for dropdown"""
#     id: str
#     name: str
#     email: str
#     employee_id: Optional[str] = None
#     department: Optional[str] = None
#     phone: Optional[str] = None
#     is_employee: bool = True
#     is_student: bool = False
#     is_visiting: bool = False


# class TravelerListResponse(BaseModel):
#     """Response with list of travelers"""
#     success: bool
#     travelers: List[TravelerInfo]


# # ============ Booking Models ============

# class BookingDetails(BaseModel):
#     """Model for booking details"""
#     flight_confirmation: Optional[str] = None
#     flight_details: Optional[str] = None
#     hotel_confirmation: Optional[str] = None
#     hotel_name: Optional[str] = None
#     hotel_address: Optional[str] = None
#     rental_car_confirmation: Optional[str] = None
#     rental_car_company: Optional[str] = None
#     notes: Optional[str] = None


# # ============ Additional Funds Models ============

# class AdditionalFundsRequest(BaseModel):
#     """Model for requesting additional funds"""
#     amount: float = Field(..., gt=0)
#     reason: str = Field(..., min_length=10, max_length=1000)


# class AdditionalFundsResponse(BaseModel):
#     """Response for additional funds request"""
#     success: bool
#     message: str
#     new_total_budget: Optional[float] = None
#     additional_funds_total: Optional[float] = None


# # ============ Expense Models ============

# class ExpenseCategory(str, Enum):
#     AIRFARE = "airfare"
#     LODGING = "lodging"
#     MEALS = "meals"
#     GROUND_TRANSPORT = "ground_transport"
#     PARKING = "parking"
#     REGISTRATION = "registration"
#     MILEAGE = "mileage"
#     OTHER = "other"


# class ExpenseItem(BaseModel):
#     """Individual expense item"""
#     date: date
#     description: str
#     category: ExpenseCategory
#     amount: float = Field(..., ge=0)
#     receipt_file: Optional[str] = None


# class ExpenseReport(BaseModel):
#     """Expense report submission"""
#     expenses: List[ExpenseItem]
#     total_claimed: float
#     notes: Optional[str] = None


# # ============ Mileage Models ============

# class MileageEntry(BaseModel):
#     """Individual mileage entry"""
#     date: date
#     from_location: str
#     to_location: str
#     miles: float = Field(..., ge=0)
#     purpose: str


# class MileageReport(BaseModel):
#     """Mileage report submission"""
#     entries: List[MileageEntry]
#     total_miles: float
#     rate_per_mile: float = 0.67  # IRS rate
#     total_reimbursement: float


# # ============ Trip Report Models ============

# class TripReport(BaseModel):
#     """Trip report submission"""
#     summary: str = Field(..., min_length=50, max_length=5000)
#     objectives_met: bool
#     outcomes: str = Field(..., min_length=20, max_length=2000)
#     recommendations: Optional[str] = None
#     follow_up_actions: Optional[str] = None
#     attachments: List[str] = []


# # ============ Post-Travel Models ============

# class PostTravelSubmission(BaseModel):
#     """Complete post-travel submission"""
#     expense_report: Optional[ExpenseReport] = None
#     mileage_report: Optional[MileageReport] = None
#     trip_report: TripReport
#     total_spent: float
#     receipts: List[str] = []


# class PostTravelReview(BaseModel):
#     """Post-travel review by supervisor/finance"""
#     approved: bool
#     comments: Optional[str] = None
#     adjustments: Optional[dict] = None


# # ============ Settlement Models ============

# class SettlementCalculation(BaseModel):
#     """Settlement calculation result"""
#     travel_advance: float = 0
#     additional_funds: float = 0
#     total_given: float = 0
#     total_spent: float = 0
#     settlement_amount: float = 0  # Positive = owes university, Negative = university owes
#     settlement_type: str  # "TRAVELER_OWES" or "UNIVERSITY_OWES"


# # ============ Approval Models ============

# class ApprovalAction(BaseModel):
#     """Model for approval/rejection actions"""
#     action: str = Field(..., pattern="^(approve|reject)$")
#     comments: Optional[str] = None


# class ApprovalResponse(BaseModel):
#     """Response for approval actions"""
#     success: bool
#     message: str
#     new_status: Optional[str] = None
#     ta_number: Optional[str] = None

"""
Pydantic Models for Travel Request System
Updated to match actual NTU Travel form fields
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime, date
from enum import Enum
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid ObjectId")


class TravelStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_SUPERVISOR = "PENDING_SUPERVISOR"
    PENDING_PRESIDENT = "PENDING_PRESIDENT"
    SUPERVISOR_APPROVED = "SUPERVISOR_APPROVED"
    TA_ISSUED = "TA_ISSUED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    POST_TRAVEL_SUBMITTED = "POST_TRAVEL_SUBMITTED"
    POST_TRAVEL_SUPERVISOR_APPROVED = "POST_TRAVEL_SUPERVISOR_APPROVED"
    POST_TRAVEL_FINANCE_APPROVED = "POST_TRAVEL_FINANCE_APPROVED"
    COMPLETED = "COMPLETED"


class TravelDestinationType(str, Enum):
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"


class TravelType(str, Enum):
    ONE_DAY = "one_day"
    OVERNIGHT = "overnight"
    PER_DIEM = "per_diem"  # 2 weeks prior
    THIRTY_ONE_DAYS = "31_days"
    ACTUAL_RECEIPTS = "actual_receipts"


class VehicleSelection(str, Enum):
    NOT_USING = "not_using"
    NTU_VEHICLE = "ntu_vehicle"
    PRIVATE_VEHICLE = "private_vehicle"


class PurposeOfTravel(str, Enum):
    CONFERENCE = "conference"
    TRAINING = "training"
    WORKSHOP = "workshop"
    MEETING = "meeting"
    FIELD_WORK = "field_work"
    STUDENT_TRAVEL = "student_travel"
    ATHLETIC_EVENT = "athletic_event"
    RECRUITMENT = "recruitment"
    OTHER = "other"


class TransportMode(str, Enum):
    AIR = "air"
    GROUND = "ground"
    POV = "pov"
    RENTAL = "rental"
    NTU_VEHICLE = "ntu_vehicle"


# ============ Request Models ============

class TravelRequestCreate(BaseModel):
    """Model for creating new travel requests - matches NTU form"""
    
    # Employee/Student Information
    traveler_id: str  # Selected traveler (can create for self, others, or visiting members)
    
    # Travel Itinerary Information
    travel_type: TravelType  # One Day, Overnight, Per Diem, 31 Days, Actual
    travel_destination_type: TravelDestinationType  # Domestic or International
    
    # Destination Information
    destination_city: str = Field(..., min_length=1, max_length=200)
    destination_state: Optional[str] = None  # Auto-filled from city
    destination_country: str = "United States"  # Based on destination type
    
    # Date Information
    date_of_request: date  # Auto-filled with today's date
    departure_date: date
    return_date: date
    
    # Purpose Information
    purpose_of_travel: PurposeOfTravel
    event_activity_name: str = Field(..., min_length=1, max_length=500)  # e.g., AISES National Conference 2025
    detailed_purpose: str = Field(..., min_length=10, max_length=2000)
    travel_itinerary: str = Field(..., min_length=5, max_length=1000)  # e.g., Crownpoint, ABQ - Minneapolis - Return
    
    # Vehicle Selection
    vehicle_selection: VehicleSelection = VehicleSelection.NOT_USING
    
    # If using private vehicle
    pov_mileage_estimate: Optional[float] = None
    pov_rate_per_mile: float = 0.67  # IRS rate
    
    # Supervisor
    supervisor_id: str
    
    # Department
    department: Optional[str] = None
    
    # Draft or Submit
    is_draft: bool = False
    
    @field_validator('return_date')
    @classmethod
    def return_after_departure(cls, v, info):
        if 'departure_date' in info.data and v < info.data['departure_date']:
            raise ValueError('Return date must be after departure date')
        return v


class TravelRequestUpdate(BaseModel):
    """Model for updating travel requests"""
    # All fields optional for partial updates
    traveler_id: Optional[str] = None
    travel_type: Optional[TravelType] = None
    travel_destination_type: Optional[TravelDestinationType] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None
    destination_country: Optional[str] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    purpose_of_travel: Optional[PurposeOfTravel] = None
    event_activity_name: Optional[str] = None
    detailed_purpose: Optional[str] = None
    travel_itinerary: Optional[str] = None
    vehicle_selection: Optional[VehicleSelection] = None
    pov_mileage_estimate: Optional[float] = None
    supervisor_id: Optional[str] = None
    department: Optional[str] = None


class DestinationInfo(BaseModel):
    """Destination information sub-model"""
    city: str
    state: Optional[str] = None
    country: str = "United States"
    # For Google Places autocomplete
    place_id: Optional[str] = None
    formatted_address: Optional[str] = None


class TravelRequestInDB(BaseModel):
    """Model for travel request stored in database"""
    id: PyObjectId = Field(alias="_id")
    
    # TA Number (generated on approval)
    ta_number: Optional[str] = None
    
    # Employee/Traveler Info
    traveler_id: str
    traveler_name: str
    traveler_email: str
    traveler_phone: Optional[str] = None
    traveler_employee_id: Optional[str] = None
    department: Optional[str] = None
    
    # Travel Type & Destination
    travel_type: TravelType
    travel_destination_type: TravelDestinationType
    destination_city: str
    destination_state: Optional[str] = None
    destination_country: str
    
    # Dates
    date_of_request: date
    departure_date: date
    return_date: date
    
    # Purpose
    purpose_of_travel: PurposeOfTravel
    event_activity_name: str
    detailed_purpose: str
    travel_itinerary: str
    
    # Vehicle
    vehicle_selection: VehicleSelection
    pov_mileage_estimate: Optional[float] = None
    pov_rate_per_mile: float = 0.67
    
    # Supervisor
    supervisor_id: str
    supervisor_name: Optional[str] = None
    
    # Status
    status: TravelStatus = TravelStatus.DRAFT
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    
    # Approval tracking
    supervisor_approved_at: Optional[datetime] = None
    supervisor_approved_by: Optional[str] = None
    president_approved_at: Optional[datetime] = None
    president_approved_by: Optional[str] = None
    
    # Documents
    agenda_file: Optional[str] = None
    budget_file: Optional[str] = None
    registration_file: Optional[str] = None
    pov_insurance_file: Optional[str] = None
    other_documents: List[str] = []
    
    # Booking details
    booking_details: Optional[dict] = None
    
    # Budget tracking
    estimated_cost: float = 0
    original_budget: float = 0
    additional_funds: float = 0
    total_approved_budget: float = 0
    travel_advance: float = 0
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class TravelRequestResponse(BaseModel):
    """Response model for travel requests"""
    success: bool
    message: str
    request_id: Optional[str] = None
    ta_number: Optional[str] = None
    data: Optional[dict] = None


# ============ Traveler Selection Models ============

class SupervisorInfo(BaseModel):
    """Supervisor information sub-model"""
    id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = None


class TravelerInfo(BaseModel):
    """Traveler information for dropdown"""
    id: str
    name: str
    email: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    user_type: Optional[str] = None
    is_employee: bool = True
    is_student: bool = False
    is_visiting: bool = False
    supervisor_id: Optional[str] = None
    supervisor: Optional[SupervisorInfo] = None


class TravelerDetailResponse(BaseModel):
    """Detailed traveler information response"""
    success: bool
    traveler: Optional[TravelerInfo] = None
    travel_stats: Optional[dict] = None


class TravelerListResponse(BaseModel):
    """Response with list of travelers"""
    success: bool
    travelers: List[TravelerInfo]
    total: Optional[int] = None


# ============ Booking Models ============

class BookingDetails(BaseModel):
    """Model for booking details"""
    flight_confirmation: Optional[str] = None
    flight_details: Optional[str] = None
    hotel_confirmation: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_address: Optional[str] = None
    rental_car_confirmation: Optional[str] = None
    rental_car_company: Optional[str] = None
    notes: Optional[str] = None


# ============ Additional Funds Models ============

class AdditionalFundsRequest(BaseModel):
    """Model for requesting additional funds"""
    amount: float = Field(..., gt=0)
    reason: str = Field(..., min_length=10, max_length=1000)


class AdditionalFundsResponse(BaseModel):
    """Response for additional funds request"""
    success: bool
    message: str
    new_total_budget: Optional[float] = None
    additional_funds_total: Optional[float] = None


# ============ Expense Models ============

class ExpenseCategory(str, Enum):
    AIRFARE = "airfare"
    LODGING = "lodging"
    MEALS = "meals"
    GROUND_TRANSPORT = "ground_transport"
    PARKING = "parking"
    REGISTRATION = "registration"
    MILEAGE = "mileage"
    OTHER = "other"


class ExpenseItem(BaseModel):
    """Individual expense item"""
    date: date
    description: str
    category: ExpenseCategory
    amount: float = Field(..., ge=0)
    receipt_file: Optional[str] = None


class ExpenseReport(BaseModel):
    """Expense report submission"""
    expenses: List[ExpenseItem]
    total_claimed: float
    notes: Optional[str] = None


# ============ Mileage Models ============

class MileageEntry(BaseModel):
    """Individual mileage entry"""
    date: date
    from_location: str
    to_location: str
    miles: float = Field(..., ge=0)
    purpose: str


class MileageReport(BaseModel):
    """Mileage report submission"""
    entries: List[MileageEntry]
    total_miles: float
    rate_per_mile: float = 0.67  # IRS rate
    total_reimbursement: float


# ============ Trip Report Models ============

class TripReport(BaseModel):
    """Trip report submission"""
    summary: str = Field(..., min_length=50, max_length=5000)
    objectives_met: bool
    outcomes: str = Field(..., min_length=20, max_length=2000)
    recommendations: Optional[str] = None
    follow_up_actions: Optional[str] = None
    attachments: List[str] = []


# ============ Post-Travel Models ============

class PostTravelSubmission(BaseModel):
    """Complete post-travel submission"""
    expense_report: Optional[ExpenseReport] = None
    mileage_report: Optional[MileageReport] = None
    trip_report: TripReport
    total_spent: float
    receipts: List[str] = []


class PostTravelReview(BaseModel):
    """Post-travel review by supervisor/finance"""
    approved: bool
    comments: Optional[str] = None
    adjustments: Optional[dict] = None


# ============ Settlement Models ============

class SettlementCalculation(BaseModel):
    """Settlement calculation result"""
    travel_advance: float = 0
    additional_funds: float = 0
    total_given: float = 0
    total_spent: float = 0
    settlement_amount: float = 0  # Positive = owes university, Negative = university owes
    settlement_type: str  # "TRAVELER_OWES" or "UNIVERSITY_OWES"


# ============ Approval Models ============

class ApprovalAction(BaseModel):
    """Model for approval/rejection actions"""
    action: str = Field(..., pattern="^(approve|reject)$")
    comments: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response for approval actions"""
    success: bool
    message: str
    new_status: Optional[str] = None
    ta_number: Optional[str] = None