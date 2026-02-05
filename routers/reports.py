# """
# Reports Router - Post-Travel Reports
# 3 Main Routes:
# 1. Expense Report - Daily expenses, Account Distribution, Reconciliation, Certification
# 2. Mileage Report - Mileage entries with locations
# 3. Trip Report - Trip summary, objectives, outcomes

# NOTE: Authentication DISABLED for testing. Re-enable for production!
# """

# from fastapi import APIRouter, Depends, HTTPException, status, Form, BackgroundTasks, Query
# from typing import Optional
# from datetime import datetime
# from bson import ObjectId

# from dependencies.database import get_database, get_settings
# from models.request import TravelStatus
# from models.response import DataResponse
# from utils.helpers import safe_object_id, safe_float, utc_now

# router = APIRouter()


# # ============ Helper Functions ============

# async def get_request_by_id(db, request_id: str) -> Optional[dict]:
#     """Get travel request by ID"""
#     obj_id = safe_object_id(request_id)
#     if not obj_id:
#         return None
#     return await db.travel_requests.find_one({"_id": obj_id})


# async def send_notification(db, user_id: str, title: str, message: str, 
#                             notification_type: str = "info", link: Optional[str] = None):
#     """Send in-app notification"""
#     notification = {
#         "user_id": user_id, "title": title, "message": message,
#         "notification_type": notification_type, "link": link,
#         "is_read": False, "created_at": utc_now(),
#     }
#     await db.notifications.insert_one(notification)


# def calculate_settlement(travel_advance: float, additional_funds: float, total_spent: float) -> dict:
#     """Calculate settlement between traveler and university"""
#     total_given = travel_advance + additional_funds
#     difference = total_given - total_spent
    
#     if difference > 0:
#         return {"settlement_type": "TRAVELER_OWES", "amount_due_to_ntu": difference, "amount_due_to_employee": 0}
#     elif difference < 0:
#         return {"settlement_type": "UNIVERSITY_OWES", "amount_due_to_employee": abs(difference), "amount_due_to_ntu": 0}
#     else:
#         return {"settlement_type": "BALANCED", "amount_due_to_ntu": 0, "amount_due_to_employee": 0}


# # ============================================================
# # 1. EXPENSE REPORT - Daily Expenses, Account Distribution, Reconciliation, Certification
# # ============================================================

# @router.post("/{request_id}/expense-report", response_model=DataResponse)
# async def submit_expense_report(
#     request_id: str,
#     background_tasks: BackgroundTasks,
    
#     # ===== TRAVELER INFO (Display Only) =====
#     employee_id: Optional[str] = Form(None, description="Employee ID (e.g., EMP011)"),
#     traveler_name: Optional[str] = Form(None, description="Traveler Name"),
#     position: Optional[str] = Form(None, description="Position (e.g., TRAVELER)"),
#     department: Optional[str] = Form(None, description="Department (e.g., Computer Science)"),
#     travel_period_start: Optional[str] = Form(None, description="Travel Period Start (MM/DD/YYYY)"),
#     travel_period_end: Optional[str] = Form(None, description="Travel Period End (MM/DD/YYYY)"),
    
#     # ===== DAY 1 EXPENSES =====
#     day1_date: Optional[str] = Form(None, description="Day 1 Date (MM/DD/YYYY)"),
#     day1_lodging: float = Form(0.0, description="Day 1 - Lodging ($)"),
#     day1_breakfast: float = Form(0.0, description="Day 1 - Breakfast ($)"),
#     day1_lunch: float = Form(0.0, description="Day 1 - Lunch ($)"),
#     day1_dinner: float = Form(0.0, description="Day 1 - Dinner ($)"),
#     day1_misc: float = Form(0.0, description="Day 1 - Misc ($)"),
#     day1_pov_mileage: float = Form(0.0, description="Day 1 - POV Mileage ($)"),
#     day1_fuel: float = Form(0.0, description="Day 1 - Fuel ($)"),
#     day1_car_rental: float = Form(0.0, description="Day 1 - Car Rental ($)"),
#     day1_airfare: float = Form(0.0, description="Day 1 - Airfare ($)"),
#     day1_inner_city_fares: float = Form(0.0, description="Day 1 - Inner-City Fares ($)"),
#     day1_parking_fees: float = Form(0.0, description="Day 1 - Parking Fees ($)"),
#     day1_internet_service: float = Form(0.0, description="Day 1 - Internet Service ($)"),
#     # Day 1 Emburse Card
#     day1_lodging_emburse: float = Form(0.0, description="Day 1 - Lodging Emburse Card ($)"),
#     day1_breakfast_emburse: float = Form(0.0, description="Day 1 - Breakfast Emburse Card ($)"),
#     day1_lunch_emburse: float = Form(0.0, description="Day 1 - Lunch Emburse Card ($)"),
#     day1_dinner_emburse: float = Form(0.0, description="Day 1 - Dinner Emburse Card ($)"),
#     day1_misc_emburse: float = Form(0.0, description="Day 1 - Misc Emburse Card ($)"),
#     day1_pov_mileage_emburse: float = Form(0.0, description="Day 1 - POV Mileage Emburse Card ($)"),
#     day1_fuel_emburse: float = Form(0.0, description="Day 1 - Fuel Emburse Card ($)"),
#     day1_car_rental_emburse: float = Form(0.0, description="Day 1 - Car Rental Emburse Card ($)"),
#     day1_airfare_emburse: float = Form(0.0, description="Day 1 - Airfare Emburse Card ($)"),
#     day1_inner_city_fares_emburse: float = Form(0.0, description="Day 1 - Inner-City Fares Emburse Card ($)"),
#     day1_parking_fees_emburse: float = Form(0.0, description="Day 1 - Parking Fees Emburse Card ($)"),
#     day1_internet_service_emburse: float = Form(0.0, description="Day 1 - Internet Service Emburse Card ($)"),
    
#     # ===== CATEGORY TOTALS =====
#     total_lodging: float = Form(0.0, description="TOTAL - Lodging ($)"),
#     total_breakfast: float = Form(0.0, description="TOTAL - Breakfast ($)"),
#     total_lunch: float = Form(0.0, description="TOTAL - Lunch ($)"),
#     total_dinner: float = Form(0.0, description="TOTAL - Dinner ($)"),
#     total_misc: float = Form(0.0, description="TOTAL - Misc ($)"),
#     total_pov_mileage: float = Form(0.0, description="TOTAL - POV Mileage ($)"),
#     total_fuel: float = Form(0.0, description="TOTAL - Fuel ($)"),
#     total_car_rental: float = Form(0.0, description="TOTAL - Car Rental ($)"),
#     total_airfare: float = Form(0.0, description="TOTAL - Airfare ($)"),
#     total_inner_city_fares: float = Form(0.0, description="TOTAL - Inner-City Fares ($)"),
#     total_parking_fees: float = Form(0.0, description="TOTAL - Parking Fees ($)"),
#     total_internet_service: float = Form(0.0, description="TOTAL - Internet Service ($)"),
    
#     # ===== EMBURSE CARD TOTALS =====
#     total_lodging_emburse: float = Form(0.0, description="TOTAL Emburse - Lodging ($)"),
#     total_breakfast_emburse: float = Form(0.0, description="TOTAL Emburse - Breakfast ($)"),
#     total_lunch_emburse: float = Form(0.0, description="TOTAL Emburse - Lunch ($)"),
#     total_dinner_emburse: float = Form(0.0, description="TOTAL Emburse - Dinner ($)"),
#     total_misc_emburse: float = Form(0.0, description="TOTAL Emburse - Misc ($)"),
#     total_pov_mileage_emburse: float = Form(0.0, description="TOTAL Emburse - POV Mileage ($)"),
#     total_fuel_emburse: float = Form(0.0, description="TOTAL Emburse - Fuel ($)"),
#     total_car_rental_emburse: float = Form(0.0, description="TOTAL Emburse - Car Rental ($)"),
#     total_airfare_emburse: float = Form(0.0, description="TOTAL Emburse - Airfare ($)"),
#     total_inner_city_fares_emburse: float = Form(0.0, description="TOTAL Emburse - Inner-City Fares ($)"),
#     total_parking_fees_emburse: float = Form(0.0, description="TOTAL Emburse - Parking Fees ($)"),
#     total_internet_service_emburse: float = Form(0.0, description="TOTAL Emburse - Internet Service ($)"),
    
#     # ===== ACCOUNT DISTRIBUTION =====
#     dist_meals: float = Form(0.0, description="Account Distribution - Meals ($)"),
#     dist_mileage: float = Form(0.0, description="Account Distribution - Mileage ($)"),
#     dist_lodging: float = Form(0.0, description="Account Distribution - Lodging ($)"),
#     dist_other_expenses: float = Form(0.0, description="Account Distribution - Other Expenses ($)"),
    
#     # ===== EXPENSE RECONCILIATION =====
#     total_expenditure: float = Form(0.0, description="Total Expenditure This Report ($)"),
#     advance_this_report: float = Form(0.0, description="Advance This Report ($)"),
#     emburse_expense: float = Form(0.0, description="Emburse Expense ($)"),
#     out_of_pocket_expense: float = Form(0.0, description="Out of Pocket Expense ($)"),
#     amount_due_to_employee: float = Form(0.0, description="Amount Due to Employee ($)"),
#     amount_due_to_ntu: float = Form(0.0, description="Amount Due to NTU ($)"),
    
#     # ===== CERTIFICATION =====
#     traveler_signature: str = Form(..., description="Traveler's Signature (Type Full Name) *REQUIRED*"),
#     certification_date: str = Form(..., description="Certification Date (MM/DD/YYYY) *REQUIRED*"),
    
#     db = Depends(get_database),
# ):
#     """
#     📋 EXPENSE REPORT - Submit complete expense report with:
    
#     - Traveler Information (Employee ID, Name, Position, Department, Travel Period)
#     - Daily Expense Breakdown (Day 1-5) with 12 categories each
#     - Emburse Card amounts for each category
#     - Category Totals
#     - Account Distribution (Meals, Mileage, Lodging, Other)
#     - Expense Reconciliation (Total Expenditure, Advance, Due amounts)
#     - Certification (Signature and Date - REQUIRED)
    
#     NO AUTH - for testing
#     """
#     print(f"\n{'='*60}")
#     print(f"📋 EXPENSE REPORT - POST /reports/{request_id}/expense-report")
#     print(f"   Signature: {traveler_signature} | Date: {certification_date}")
#     print(f"{'='*60}")
    
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     # Build daily expenses
#     daily_expenses = []
#     days_data = [
#         (1, day1_date, day1_lodging, day1_breakfast, day1_lunch, day1_dinner, day1_misc, day1_pov_mileage, day1_fuel, day1_car_rental, day1_airfare, day1_inner_city_fares, day1_parking_fees, day1_internet_service, day1_lodging_emburse, day1_breakfast_emburse, day1_lunch_emburse, day1_dinner_emburse, day1_misc_emburse, day1_pov_mileage_emburse, day1_fuel_emburse, day1_car_rental_emburse, day1_airfare_emburse, day1_inner_city_fares_emburse, day1_parking_fees_emburse, day1_internet_service_emburse)
#     ]
    
#     for d in days_data:
#         if d[1]:  # If date is provided
#             daily_expenses.append({
#                 "day_number": d[0], "date": d[1],
#                 "lodging": safe_float(d[2]), "breakfast": safe_float(d[3]), "lunch": safe_float(d[4]),
#                 "dinner": safe_float(d[5]), "misc": safe_float(d[6]), "pov_mileage": safe_float(d[7]),
#                 "fuel": safe_float(d[8]), "car_rental": safe_float(d[9]), "airfare": safe_float(d[10]),
#                 "inner_city_fares": safe_float(d[11]), "parking_fees": safe_float(d[12]), "internet_service": safe_float(d[13]),
#                 "lodging_emburse": safe_float(d[14]), "breakfast_emburse": safe_float(d[15]), "lunch_emburse": safe_float(d[16]),
#                 "dinner_emburse": safe_float(d[17]), "misc_emburse": safe_float(d[18]), "pov_mileage_emburse": safe_float(d[19]),
#                 "fuel_emburse": safe_float(d[20]), "car_rental_emburse": safe_float(d[21]), "airfare_emburse": safe_float(d[22]),
#                 "inner_city_fares_emburse": safe_float(d[23]), "parking_fees_emburse": safe_float(d[24]), "internet_service_emburse": safe_float(d[25]),
#             })
    
#     # Category totals
#     category_totals = {
#         "lodging": safe_float(total_lodging), "breakfast": safe_float(total_breakfast),
#         "lunch": safe_float(total_lunch), "dinner": safe_float(total_dinner),
#         "misc": safe_float(total_misc), "pov_mileage": safe_float(total_pov_mileage),
#         "fuel": safe_float(total_fuel), "car_rental": safe_float(total_car_rental),
#         "airfare": safe_float(total_airfare), "inner_city_fares": safe_float(total_inner_city_fares),
#         "parking_fees": safe_float(total_parking_fees), "internet_service": safe_float(total_internet_service),
#     }
    
#     emburse_totals = {
#         "lodging": safe_float(total_lodging_emburse), "breakfast": safe_float(total_breakfast_emburse),
#         "lunch": safe_float(total_lunch_emburse), "dinner": safe_float(total_dinner_emburse),
#         "misc": safe_float(total_misc_emburse), "pov_mileage": safe_float(total_pov_mileage_emburse),
#         "fuel": safe_float(total_fuel_emburse), "car_rental": safe_float(total_car_rental_emburse),
#         "airfare": safe_float(total_airfare_emburse), "inner_city_fares": safe_float(total_inner_city_fares_emburse),
#         "parking_fees": safe_float(total_parking_fees_emburse), "internet_service": safe_float(total_internet_service_emburse),
#     }
    
#     grand_total = sum(category_totals.values())
#     grand_emburse = sum(emburse_totals.values())
    
#     # Account Distribution
#     account_distribution = {
#         "meals": safe_float(dist_meals), "mileage": safe_float(dist_mileage),
#         "lodging": safe_float(dist_lodging), "other_expenses": safe_float(dist_other_expenses),
#         "total": safe_float(dist_meals) + safe_float(dist_mileage) + safe_float(dist_lodging) + safe_float(dist_other_expenses),
#     }
    
#     # Expense Reconciliation
#     expense_reconciliation = {
#         "total_expenditure": safe_float(total_expenditure) or grand_total,
#         "advance_this_report": safe_float(advance_this_report),
#         "emburse_expense": safe_float(emburse_expense) or grand_emburse,
#         "out_of_pocket_expense": safe_float(out_of_pocket_expense),
#         "amount_due_to_employee": safe_float(amount_due_to_employee),
#         "amount_due_to_ntu": safe_float(amount_due_to_ntu),
#     }
    
#     # Certification
#     certification = {
#         "statement": "I CERTIFY THAT THIS TRAVEL REPORT IS ACCURATE, COMPLETE AND ALL EXPENSES REQUESTED FOR REIMBURSEMENT AND CLAIMED HEREIN WERE ON NAVAJO TECHNICAL UNIVERSITY OFFICIAL TRAVEL FOR THE PURPOSE SET FORTH IN THIS TRAVEL AUTHORIZATION",
#         "traveler_signature": traveler_signature,
#         "certification_date": certification_date,
#         "certified_at": utc_now(),
#     }
    
#     # Build expense report
#     expense_report = {
#         "traveler_info": {
#             "employee_id": employee_id or travel_request.get("traveler_employee_id"),
#             "name": traveler_name or travel_request.get("traveler_name"),
#             "position": position or travel_request.get("position", "TRAVELER"),
#             "department": department or travel_request.get("department"),
#             "travel_period_start": travel_period_start or travel_request.get("departure_date"),
#             "travel_period_end": travel_period_end or travel_request.get("return_date"),
#         },
#         "daily_expenses": daily_expenses,
#         "category_totals": category_totals,
#         "emburse_totals": emburse_totals,
#         "grand_total": grand_total,
#         "grand_emburse": grand_emburse,
#         "account_distribution": account_distribution,
#         "expense_reconciliation": expense_reconciliation,
#         "certification": certification,
#         "submitted_at": utc_now(),
#         "status": "SUBMITTED",
#     }
    
#     # Update database
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {"$set": {
#             "expense_report": expense_report,
#             "daily_expense_breakdown": {"daily_expenses": daily_expenses, "category_totals": category_totals, "emburse_totals": emburse_totals},
#             "account_distribution": account_distribution,
#             "expense_reconciliation": expense_reconciliation,
#             "certification": certification,
#             "updated_at": utc_now(),
#         }}
#     )
    
#     print(f"   ✅ Expense Report Saved - Total: ${grand_total:.2f}, Emburse: ${grand_emburse:.2f}")
    
#     return DataResponse(
#         success=True,
#         message="Expense Report submitted successfully",
#         data={
#             "grand_total": grand_total,
#             "grand_emburse": grand_emburse,
#             "days_reported": len(daily_expenses),
#             "account_distribution": account_distribution,
#             "expense_reconciliation": expense_reconciliation,
#             "certification": {"signature": traveler_signature, "date": certification_date},
#         }
#     )


# # ============================================================
# # 2. MILEAGE REPORT - Mileage entries with from/to locations
# # ============================================================

# # ============================================================
# # 2. MILEAGE REPORT/LOG - With Odometer Readings
# # REPLACE your existing mileage-report section with this
# # ============================================================

# @router.post("/{request_id}/mileage-report", response_model=DataResponse)
# async def submit_mileage_report(
#     request_id: str,
    
#     # ===== TRAVELER INFORMATION =====
#     traveler_name: Optional[str] = Form(None, description="TRAVELER'S NAME"),
#     ta_number: Optional[str] = Form(None, description="TRAVEL AUTHORIZATION NO."),
    
#     # ===== MILEAGE LOG ENTRY 1 =====
#     entry1_travel_date: Optional[str] = Form(None, description="Entry 1 - Travel Date (MM/DD/YYYY)"),
#     entry1_purpose_of_travel: Optional[str] = Form(None, description="Entry 1 - Purpose of Travel"),
#     entry1_city_from: Optional[str] = Form(None, description="Entry 1 - City From"),
#     entry1_city_to: Optional[str] = Form(None, description="Entry 1 - City To"),
#     entry1_odometer_begin: float = Form(0.0, description="Entry 1 - Odometer Begin"),
#     entry1_odometer_end: float = Form(0.0, description="Entry 1 - Odometer End"),
#     entry1_total_miles: float = Form(0.0, description="Entry 1 - Total Miles"),
    
#     # ===== TOTALS =====
#     grand_total_miles: float = Form(0.0, description="TOTAL MILES"),
#     rate_per_mile: float = Form(0.67, description="Rate per Mile ($)"),
#     total_reimbursement: float = Form(0.0, description="Total Reimbursement ($)"),
    
#     # ===== CERTIFICATION =====
#     traveler_signature: str = Form(..., description="Traveler's Signature (Type Full Name) *REQUIRED*"),
#     certification_date: str = Form(..., description="Certification Date (MM/DD/YYYY) *REQUIRED*"),
    
#     db = Depends(get_database),
# ):
#     """
#     🚗 MILEAGE REPORT/LOG
    
#     Required for Monthly Blanket TA or POV Mileage Claims.
#     Must be accompanied with a Trip Report.
    
#     Traveler Information:
#     - TRAVELER'S NAME
#     - TRAVEL AUTHORIZATION NO.
    
#     Mileage Log Entries (up to 10):
#     - Travel Date (MM/DD/YYYY)
#     - Purpose of Travel
#     - City From
#     - City To
#     - Odometer Begin
#     - Odometer End
#     - Total Miles
    
#     Certification:
#     "I certify that this mileage report represents actual mileage incurred by me on official travel as herein stated."
    
#     NO AUTH - for testing
#     """
#     print(f"\n{'='*60}")
#     print(f"🚗 MILEAGE REPORT - POST /reports/{request_id}/mileage-report")
#     print(f"   Traveler: {traveler_name} | TA#: {ta_number}")
#     print(f"   Signature: {traveler_signature} | Date: {certification_date}")
#     print(f"{'='*60}")
    
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     # Build mileage entries
#     entries = []
#     all_entries = [
#         (1, entry1_travel_date, entry1_purpose_of_travel, entry1_city_from, entry1_city_to, entry1_odometer_begin, entry1_odometer_end, entry1_total_miles)
#     ]
    
#     for entry_num, travel_date, purpose, city_from, city_to, odo_begin, odo_end, miles in all_entries:
#         if travel_date or city_from:
#             calculated_miles = safe_float(miles)
#             if calculated_miles == 0 and safe_float(odo_end) > safe_float(odo_begin):
#                 calculated_miles = safe_float(odo_end) - safe_float(odo_begin)
            
#             entries.append({
#                 "entry_number": entry_num,
#                 "travel_date": travel_date,
#                 "purpose_of_travel": purpose,
#                 "city_from": city_from,
#                 "city_to": city_to,
#                 "odometer_begin": safe_float(odo_begin),
#                 "odometer_end": safe_float(odo_end),
#                 "total_miles": calculated_miles,
#             })
    
#     calculated_total_miles = sum(e["total_miles"] for e in entries) if entries else safe_float(grand_total_miles)
#     rate = safe_float(rate_per_mile) or 0.67
#     calculated_reimbursement = calculated_total_miles * rate
    
#     traveler_info = {
#         "traveler_name": traveler_name or travel_request.get("traveler_name"),
#         "ta_number": ta_number or travel_request.get("ta_number"),
#     }
    
#     certification = {
#         "statement": "I certify that this mileage report represents actual mileage incurred by me on official travel as herein stated.",
#         "traveler_signature": traveler_signature,
#         "certification_date": certification_date,
#         "certified_at": utc_now(),
#     }
    
#     mileage_report = {
#         "traveler_info": traveler_info,
#         "mileage_log_entries": entries,
#         "grand_total_miles": calculated_total_miles,
#         "rate_per_mile": rate,
#         "total_reimbursement": safe_float(total_reimbursement) or calculated_reimbursement,
#         "certification": certification,
#         "submitted_at": utc_now(),
#         "status": "SUBMITTED",
#     }
    
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {"$set": {"mileage_report": mileage_report, "updated_at": utc_now()}}
#     )
    
#     print(f"   ✅ Mileage Report Saved - {len(entries)} entries, {calculated_total_miles} miles, ${calculated_reimbursement:.2f}")
    
#     return DataResponse(
#         success=True,
#         message="Mileage Report submitted successfully",
#         data={
#             "traveler_info": traveler_info,
#             "entries_count": len(entries),
#             "grand_total_miles": calculated_total_miles,
#             "rate_per_mile": rate,
#             "total_reimbursement": calculated_reimbursement,
#             "certification": {"signature": traveler_signature, "date": certification_date},
#         }
#     )

# # ============================================================
# # 3. TRIP REPORT - Trip summary, objectives, outcomes
# # ============================================================

# @router.post("/{request_id}/trip-report", response_model=DataResponse)
# async def submit_trip_report(
#     request_id: str,
    
#     # ===== TRAVELER INFORMATION =====
#     traveler_name: Optional[str] = Form(None, description="TRAVELER NAME"),
#     ta_number: Optional[str] = Form(None, description="TA NUMBER"),
#     department: Optional[str] = Form(None, description="DEPARTMENT"),
    
#     # ===== TRAVEL DETAILS =====
#     report_date: str = Form(..., description="Report Date (MM/DD/YYYY) *REQUIRED*"),
#     travel_start_date: str = Form(..., description="Travel Start Date (MM/DD/YYYY) *REQUIRED*"),
#     travel_end_date: str = Form(..., description="Travel End Date (MM/DD/YYYY) *REQUIRED*"),
#     departure_time: Optional[str] = Form(None, description="Departure Time (e.g., 07:00 AM)"),
#     return_time: Optional[str] = Form(None, description="Return Time (e.g., 08:00 PM)"),
    
#     # ===== VEHICLE INFORMATION =====
#     type_of_vehicle: Optional[str] = Form(None, description="Type of Vehicle (Private Vehicle, Rental, University Vehicle)"),
#     odometer_beginning: float = Form(0.0, description="Odometer Beginning"),
#     odometer_ending: float = Form(0.0, description="Odometer Ending"),
#     total_miles: float = Form(0.0, description="Total Miles (Auto-calculated from odometer)"),
    
#     # ===== PURPOSE OF TRAVEL =====
#     purpose_of_travel: str = Form(..., description="Describe the purpose of your travel *REQUIRED*"),
    
#     # ===== PERSON(S) CONTACTED =====
#     persons_contacted: str = Form(..., description="List people you met with or contacted *REQUIRED* (e.g., John Smith (ABC Company, CEO), Jane Doe (XYZ Organization, Director))"),
    
#     # ===== ACCOMPLISHMENTS (Note: XVII.2) =====
#     accomplishments: str = Form(..., description="Describe your accomplishments *REQUIRED* - What you accomplished during this travel and how it benefits NTU"),
    
#     # ===== UNAUTHORIZED EXPENSES (Optional) =====
#     unauthorized_expenses_justification: Optional[str] = Form(None, description="Justification for any unauthorized expenses (Leave blank if not applicable)"),
    
#     # ===== CERTIFICATION & SIGNATURE =====
#     traveler_signature: str = Form(..., description="Traveler Signature (Type Full Name) *REQUIRED*"),
#     signature_date: str = Form(..., description="Signature Date (MM/DD/YYYY) *REQUIRED*"),
    
#     db = Depends(get_database),
# ):
#     """
#     ✈️ TRIP REPORT - Submit trip report with all sections:
    
#     1. Traveler Information
#        - Traveler Name, TA Number, Department
    
#     2. Travel Details
#        - Report Date, Travel Start/End Date, Departure/Return Time
    
#     3. Vehicle Information
#        - Type of Vehicle, Odometer Beginning/Ending, Total Miles
    
#     4. Purpose of Travel
#        - Describe the purpose of your travel
    
#     5. Person(s) Contacted
#        - List people you met with or contacted
    
#     6. Accomplishments (Note: XVII.2)
#        - Describe what you accomplished and how it benefits NTU
    
#     7. Unauthorized Expenses (Optional)
#        - Justification for any unauthorized expenses
    
#     8. Certification & Signature
#        - "I certify that this trip report represents all claims incurred by me on official travel as herein stated."
#        - Traveler Signature, Signature Date
    
#     NO AUTH - for testing
#     """
#     print(f"\n{'='*60}")
#     print(f"✈️ TRIP REPORT - POST /reports/{request_id}/trip-report")
#     print(f"   Traveler: {traveler_name} | TA#: {ta_number}")
#     print(f"   Travel: {travel_start_date} to {travel_end_date}")
#     print(f"   Signature: {traveler_signature} | Date: {signature_date}")
#     print(f"{'='*60}")
    
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     # Calculate total miles from odometer if not provided
#     calculated_miles = safe_float(total_miles)
#     if calculated_miles == 0 and safe_float(odometer_ending) > safe_float(odometer_beginning):
#         calculated_miles = safe_float(odometer_ending) - safe_float(odometer_beginning)
    
#     # Build trip report
#     trip_report = {
#         # Traveler Information
#         "traveler_info": {
#             "traveler_name": traveler_name or travel_request.get("traveler_name"),
#             "ta_number": ta_number or travel_request.get("ta_number"),
#             "department": department or travel_request.get("department"),
#         },
        
#         # Travel Details
#         "travel_details": {
#             "report_date": report_date,
#             "travel_start_date": travel_start_date,
#             "travel_end_date": travel_end_date,
#             "departure_time": departure_time,
#             "return_time": return_time,
#         },
        
#         # Vehicle Information
#         "vehicle_info": {
#             "type_of_vehicle": type_of_vehicle,
#             "odometer_beginning": safe_float(odometer_beginning),
#             "odometer_ending": safe_float(odometer_ending),
#             "total_miles": calculated_miles,
#         },
        
#         # Purpose of Travel
#         "purpose_of_travel": purpose_of_travel,
        
#         # Person(s) Contacted
#         "persons_contacted": persons_contacted,
        
#         # Accomplishments
#         "accomplishments": accomplishments,
        
#         # Unauthorized Expenses
#         "unauthorized_expenses": {
#             "has_unauthorized": bool(unauthorized_expenses_justification),
#             "justification": unauthorized_expenses_justification,
#         },
        
#         # Certification
#         "certification": {
#             "statement": "I certify that this trip report represents all claims incurred by me on official travel as herein stated.",
#             "traveler_signature": traveler_signature,
#             "signature_date": signature_date,
#             "certified_at": utc_now(),
#         },
        
#         "submitted_at": utc_now(),
#         "status": "SUBMITTED",
#     }
    
#     # Update database
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {"$set": {"trip_report": trip_report, "updated_at": utc_now()}}
#     )
    
#     print(f"   ✅ Trip Report Saved - Miles: {calculated_miles}")
    
#     return DataResponse(
#         success=True,
#         message="Trip Report submitted successfully",
#         data={
#             "traveler_info": trip_report["traveler_info"],
#             "travel_details": trip_report["travel_details"],
#             "vehicle_info": trip_report["vehicle_info"],
#             "total_miles": calculated_miles,
#             "certification": {"signature": traveler_signature, "date": signature_date},
#         }
#     )


# # ============================================================
# # VIEW ENDPOINTS - Get submitted reports
# # ============================================================

# @router.get("/{request_id}/expense-report", response_model=DataResponse)
# async def get_expense_report(request_id: str, db = Depends(get_database)):
#     """📋 View submitted Expense Report"""
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     expense_report = travel_request.get("expense_report")
#     if not expense_report:
#         return DataResponse(success=False, message="Expense Report not submitted yet", data=None)
    
#     return DataResponse(success=True, message="Expense Report retrieved", data=expense_report)


# @router.get("/{request_id}/mileage-report", response_model=DataResponse)
# async def get_mileage_report(request_id: str, db = Depends(get_database)):
#     """🚗 View submitted Mileage Report"""
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     mileage_report = travel_request.get("mileage_report")
#     if not mileage_report:
#         return DataResponse(success=False, message="Mileage Report not submitted yet", data=None)
    
#     return DataResponse(success=True, message="Mileage Report retrieved", data=mileage_report)


# @router.get("/{request_id}/trip-report", response_model=DataResponse)
# async def get_trip_report(request_id: str, db = Depends(get_database)):
#     """✈️ View submitted Trip Report"""
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     trip_report = travel_request.get("trip_report")
#     if not trip_report:
#         return DataResponse(success=False, message="Trip Report not submitted yet", data=None)
    
#     return DataResponse(success=True, message="Trip Report retrieved", data=trip_report)


# # ============================================================
# # SUBMIT ALL POST-TRAVEL - Final submission
# # ============================================================

# @router.post("/{request_id}/post-travel/submit", response_model=DataResponse)
# async def submit_post_travel(
#     request_id: str,
#     background_tasks: BackgroundTasks,
#     traveler_signature: str = Form(..., description="Final Signature *REQUIRED*"),
#     certification_date: str = Form(..., description="Final Date (MM/DD/YYYY) *REQUIRED*"),
#     db = Depends(get_database),
# ):
#     """
#     ✅ SUBMIT ALL POST-TRAVEL - Final submission after all 3 reports are filled
    
#     This changes status to POST_TRAVEL_SUBMITTED and notifies supervisor.
#     Make sure Expense Report, Mileage Report, and Trip Report are submitted first!
#     """
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     # Check if reports are submitted
#     expense_report = travel_request.get("expense_report")
#     mileage_report = travel_request.get("mileage_report")
#     trip_report = travel_request.get("trip_report")
    
#     missing = []
#     if not expense_report: missing.append("Expense Report")
#     if not trip_report: missing.append("Trip Report")
#     # Mileage is optional
    
#     if missing:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Please submit these reports first: {', '.join(missing)}"
#         )
    
#     # Final certification
#     final_certification = {
#         "traveler_signature": traveler_signature,
#         "certification_date": certification_date,
#         "certified_at": utc_now(),
#     }
    
#     # Calculate settlement
#     travel_advance = safe_float(travel_request.get("travel_advance", 0))
#     additional_funds = safe_float(travel_request.get("additional_funds", 0))
#     total_spent = safe_float(expense_report.get("grand_total", 0))
#     settlement = calculate_settlement(travel_advance, additional_funds, total_spent)
    
#     # Update status
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {"$set": {
#             "status": TravelStatus.POST_TRAVEL_SUBMITTED.value,
#             "post_travel_final_certification": final_certification,
#             "settlement": settlement,
#             "updated_at": utc_now(),
#         }}
#     )
    
#     # Notify supervisor
#     supervisor_id = travel_request.get("supervisor_id")
#     traveler_name = travel_request.get("traveler_name", "Traveler")
    
#     if supervisor_id:
#         background_tasks.add_task(
#             send_notification, db, supervisor_id,
#             "Post-Travel Report Submitted",
#             f"{traveler_name} has submitted all post-travel reports for review",
#             "warning", f"/requests/{request_id}/view"
#         )
    
#     return DataResponse(
#         success=True,
#         message="All Post-Travel reports submitted for approval!",
#         data={
#             "status": "POST_TRAVEL_SUBMITTED",
#             "expense_report": "✅ Submitted",
#             "mileage_report": "✅ Submitted" if mileage_report else "⏭️ Skipped",
#             "trip_report": "✅ Submitted",
#             "settlement": settlement,
#         }
#     )


# # ============================================================
# # SETTLEMENT CALCULATION
# # ============================================================

# @router.get("/{request_id}/settlement", response_model=DataResponse)
# async def get_settlement(request_id: str, db = Depends(get_database)):
#     """💰 Get settlement calculation"""
#     travel_request = await get_request_by_id(db, request_id)
#     if not travel_request:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
#     travel_advance = safe_float(travel_request.get("travel_advance", 0))
#     additional_funds = safe_float(travel_request.get("additional_funds", 0))
    
#     expense_report = travel_request.get("expense_report", {})
#     total_spent = safe_float(expense_report.get("grand_total", 0))
    
#     settlement = calculate_settlement(travel_advance, additional_funds, total_spent)
    
#     return DataResponse(
#         success=True,
#         message="Settlement calculated",
#         data={
#             "travel_advance": travel_advance,
#             "additional_funds": additional_funds,
#             "total_given": travel_advance + additional_funds,
#             "total_spent": total_spent,
#             **settlement,
#         }
#     )

"""
Reports Router - Post-Travel Reports
3 Main Routes:
1. Expense Report - Daily expenses, Account Distribution, Reconciliation, Certification
2. Mileage Report - Mileage entries with locations
3. Trip Report - Trip summary, objectives, outcomes

NOTE: Authentication DISABLED for testing. Re-enable for production!
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form, BackgroundTasks, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId

from dependencies.database import get_database, get_settings
from models.request import TravelStatus
from models.response import DataResponse
from utils.helpers import safe_object_id, safe_float, utc_now

router = APIRouter()


# ============ Helper Functions ============

async def get_request_by_id(db, request_id: str) -> Optional[dict]:
    """Get travel request by ID"""
    obj_id = safe_object_id(request_id)
    if not obj_id:
        return None
    return await db.travel_requests.find_one({"_id": obj_id})


async def send_notification(db, user_id: str, title: str, message: str, 
                            notification_type: str = "info", link: Optional[str] = None):
    """Send in-app notification"""
    notification = {
        "user_id": user_id, "title": title, "message": message,
        "notification_type": notification_type, "link": link,
        "is_read": False, "created_at": utc_now(),
    }
    await db.notifications.insert_one(notification)


def calculate_settlement(travel_advance: float, additional_funds: float, total_spent: float) -> dict:
    """Calculate settlement between traveler and university"""
    total_given = travel_advance + additional_funds
    difference = total_given - total_spent
    
    if difference > 0:
        return {"settlement_type": "TRAVELER_OWES", "amount_due_to_ntu": difference, "amount_due_to_employee": 0}
    elif difference < 0:
        return {"settlement_type": "UNIVERSITY_OWES", "amount_due_to_employee": abs(difference), "amount_due_to_ntu": 0}
    else:
        return {"settlement_type": "BALANCED", "amount_due_to_ntu": 0, "amount_due_to_employee": 0}


# ============================================================
# 1. EXPENSE REPORT - Daily Expenses, Account Distribution, Reconciliation, Certification
# ============================================================

@router.post("/{request_id}/expense-report", response_model=DataResponse)
async def submit_expense_report(
    request_id: str,
    background_tasks: BackgroundTasks,
    
    # ===== TRAVELER INFO (Display Only) =====
    employee_id: Optional[str] = Form(None, description="Employee ID (e.g., EMP011)"),
    traveler_name: Optional[str] = Form(None, description="Traveler Name"),
    position: Optional[str] = Form(None, description="Position (e.g., TRAVELER)"),
    department: Optional[str] = Form(None, description="Department (e.g., Computer Science)"),
    travel_period_start: Optional[str] = Form(None, description="Travel Period Start (MM/DD/YYYY)"),
    travel_period_end: Optional[str] = Form(None, description="Travel Period End (MM/DD/YYYY)"),
    
    # ===== DAY 1 EXPENSES =====
    day1_date: Optional[str] = Form(None, description="Day 1 Date (MM/DD/YYYY)"),
    day1_lodging: float = Form(0.0, description="Day 1 - Lodging ($)"),
    day1_breakfast: float = Form(0.0, description="Day 1 - Breakfast ($)"),
    day1_lunch: float = Form(0.0, description="Day 1 - Lunch ($)"),
    day1_dinner: float = Form(0.0, description="Day 1 - Dinner ($)"),
    day1_misc: float = Form(0.0, description="Day 1 - Misc ($)"),
    day1_pov_mileage: float = Form(0.0, description="Day 1 - POV Mileage ($)"),
    day1_fuel: float = Form(0.0, description="Day 1 - Fuel ($)"),
    day1_car_rental: float = Form(0.0, description="Day 1 - Car Rental ($)"),
    day1_airfare: float = Form(0.0, description="Day 1 - Airfare ($)"),
    day1_inner_city_fares: float = Form(0.0, description="Day 1 - Inner-City Fares ($)"),
    day1_parking_fees: float = Form(0.0, description="Day 1 - Parking Fees ($)"),
    day1_internet_service: float = Form(0.0, description="Day 1 - Internet Service ($)"),
    # Day 1 Emburse Card
    day1_lodging_emburse: float = Form(0.0, description="Day 1 - Lodging Emburse Card ($)"),
    day1_breakfast_emburse: float = Form(0.0, description="Day 1 - Breakfast Emburse Card ($)"),
    day1_lunch_emburse: float = Form(0.0, description="Day 1 - Lunch Emburse Card ($)"),
    day1_dinner_emburse: float = Form(0.0, description="Day 1 - Dinner Emburse Card ($)"),
    day1_misc_emburse: float = Form(0.0, description="Day 1 - Misc Emburse Card ($)"),
    day1_pov_mileage_emburse: float = Form(0.0, description="Day 1 - POV Mileage Emburse Card ($)"),
    day1_fuel_emburse: float = Form(0.0, description="Day 1 - Fuel Emburse Card ($)"),
    day1_car_rental_emburse: float = Form(0.0, description="Day 1 - Car Rental Emburse Card ($)"),
    day1_airfare_emburse: float = Form(0.0, description="Day 1 - Airfare Emburse Card ($)"),
    day1_inner_city_fares_emburse: float = Form(0.0, description="Day 1 - Inner-City Fares Emburse Card ($)"),
    day1_parking_fees_emburse: float = Form(0.0, description="Day 1 - Parking Fees Emburse Card ($)"),
    day1_internet_service_emburse: float = Form(0.0, description="Day 1 - Internet Service Emburse Card ($)"),
    
   
    # ===== CATEGORY TOTALS =====
    total_lodging: float = Form(0.0, description="TOTAL - Lodging ($)"),
    total_breakfast: float = Form(0.0, description="TOTAL - Breakfast ($)"),
    total_lunch: float = Form(0.0, description="TOTAL - Lunch ($)"),
    total_dinner: float = Form(0.0, description="TOTAL - Dinner ($)"),
    total_misc: float = Form(0.0, description="TOTAL - Misc ($)"),
    total_pov_mileage: float = Form(0.0, description="TOTAL - POV Mileage ($)"),
    total_fuel: float = Form(0.0, description="TOTAL - Fuel ($)"),
    total_car_rental: float = Form(0.0, description="TOTAL - Car Rental ($)"),
    total_airfare: float = Form(0.0, description="TOTAL - Airfare ($)"),
    total_inner_city_fares: float = Form(0.0, description="TOTAL - Inner-City Fares ($)"),
    total_parking_fees: float = Form(0.0, description="TOTAL - Parking Fees ($)"),
    total_internet_service: float = Form(0.0, description="TOTAL - Internet Service ($)"),
    
    # ===== EMBURSE CARD TOTALS =====
    total_lodging_emburse: float = Form(0.0, description="TOTAL Emburse - Lodging ($)"),
    total_breakfast_emburse: float = Form(0.0, description="TOTAL Emburse - Breakfast ($)"),
    total_lunch_emburse: float = Form(0.0, description="TOTAL Emburse - Lunch ($)"),
    total_dinner_emburse: float = Form(0.0, description="TOTAL Emburse - Dinner ($)"),
    total_misc_emburse: float = Form(0.0, description="TOTAL Emburse - Misc ($)"),
    total_pov_mileage_emburse: float = Form(0.0, description="TOTAL Emburse - POV Mileage ($)"),
    total_fuel_emburse: float = Form(0.0, description="TOTAL Emburse - Fuel ($)"),
    total_car_rental_emburse: float = Form(0.0, description="TOTAL Emburse - Car Rental ($)"),
    total_airfare_emburse: float = Form(0.0, description="TOTAL Emburse - Airfare ($)"),
    total_inner_city_fares_emburse: float = Form(0.0, description="TOTAL Emburse - Inner-City Fares ($)"),
    total_parking_fees_emburse: float = Form(0.0, description="TOTAL Emburse - Parking Fees ($)"),
    total_internet_service_emburse: float = Form(0.0, description="TOTAL Emburse - Internet Service ($)"),
    
    # ===== ACCOUNT DISTRIBUTION =====
    dist_meals: float = Form(0.0, description="Account Distribution - Meals ($)"),
    dist_mileage: float = Form(0.0, description="Account Distribution - Mileage ($)"),
    dist_lodging: float = Form(0.0, description="Account Distribution - Lodging ($)"),
    dist_other_expenses: float = Form(0.0, description="Account Distribution - Other Expenses ($)"),
    
    # ===== EXPENSE RECONCILIATION =====
    total_expenditure: float = Form(0.0, description="Total Expenditure This Report ($)"),
    advance_this_report: float = Form(0.0, description="Advance This Report ($)"),
    emburse_expense: float = Form(0.0, description="Emburse Expense ($)"),
    out_of_pocket_expense: float = Form(0.0, description="Out of Pocket Expense ($)"),
    amount_due_to_employee: float = Form(0.0, description="Amount Due to Employee ($)"),
    amount_due_to_ntu: float = Form(0.0, description="Amount Due to NTU ($)"),
    
    # ===== CERTIFICATION =====
    traveler_signature: str = Form(..., description="Traveler's Signature (Type Full Name) *REQUIRED*"),
    certification_date: str = Form(..., description="Certification Date (MM/DD/YYYY) *REQUIRED*"),
    
    db = Depends(get_database),
):
    """
    📋 EXPENSE REPORT - Submit complete expense report with:
    
    - Traveler Information (Employee ID, Name, Position, Department, Travel Period)
    - Daily Expense Breakdown (Day 1-5) with 12 categories each
    - Emburse Card amounts for each category
    - Category Totals
    - Account Distribution (Meals, Mileage, Lodging, Other)
    - Expense Reconciliation (Total Expenditure, Advance, Due amounts)
    - Certification (Signature and Date - REQUIRED)
    
    NO AUTH - for testing
    """
    print(f"\n{'='*60}")
    print(f"📋 EXPENSE REPORT - POST /reports/{request_id}/expense-report")
    print(f"   Signature: {traveler_signature} | Date: {certification_date}")
    print(f"{'='*60}")
    
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    # Build daily expenses
    daily_expenses = []
    days_data = [
        (1, day1_date, day1_lodging, day1_breakfast, day1_lunch, day1_dinner, day1_misc, day1_pov_mileage, day1_fuel, day1_car_rental, day1_airfare, day1_inner_city_fares, day1_parking_fees, day1_internet_service, day1_lodging_emburse, day1_breakfast_emburse, day1_lunch_emburse, day1_dinner_emburse, day1_misc_emburse, day1_pov_mileage_emburse, day1_fuel_emburse, day1_car_rental_emburse, day1_airfare_emburse, day1_inner_city_fares_emburse, day1_parking_fees_emburse, day1_internet_service_emburse)
    ]
    
    for d in days_data:
        if d[1]:  # If date is provided
            daily_expenses.append({
                "day_number": d[0], "date": d[1],
                "lodging": safe_float(d[2]), "breakfast": safe_float(d[3]), "lunch": safe_float(d[4]),
                "dinner": safe_float(d[5]), "misc": safe_float(d[6]), "pov_mileage": safe_float(d[7]),
                "fuel": safe_float(d[8]), "car_rental": safe_float(d[9]), "airfare": safe_float(d[10]),
                "inner_city_fares": safe_float(d[11]), "parking_fees": safe_float(d[12]), "internet_service": safe_float(d[13]),
                "lodging_emburse": safe_float(d[14]), "breakfast_emburse": safe_float(d[15]), "lunch_emburse": safe_float(d[16]),
                "dinner_emburse": safe_float(d[17]), "misc_emburse": safe_float(d[18]), "pov_mileage_emburse": safe_float(d[19]),
                "fuel_emburse": safe_float(d[20]), "car_rental_emburse": safe_float(d[21]), "airfare_emburse": safe_float(d[22]),
                "inner_city_fares_emburse": safe_float(d[23]), "parking_fees_emburse": safe_float(d[24]), "internet_service_emburse": safe_float(d[25]),
            })
    
    # Category totals - Calculate from daily expenses instead of using form totals
    calculated_category_totals = {
        "lodging": 0, "breakfast": 0, "lunch": 0, "dinner": 0,
        "misc": 0, "pov_mileage": 0, "fuel": 0, "car_rental": 0,
        "airfare": 0, "inner_city_fares": 0, "parking_fees": 0, "internet_service": 0,
    }
    
    calculated_emburse_totals = {
        "lodging": 0, "breakfast": 0, "lunch": 0, "dinner": 0,
        "misc": 0, "pov_mileage": 0, "fuel": 0, "car_rental": 0,
        "airfare": 0, "inner_city_fares": 0, "parking_fees": 0, "internet_service": 0,
    }
    
    # Sum up all daily expenses to get totals
    for day in daily_expenses:
        calculated_category_totals["lodging"] += day["lodging"]
        calculated_category_totals["breakfast"] += day["breakfast"]
        calculated_category_totals["lunch"] += day["lunch"]
        calculated_category_totals["dinner"] += day["dinner"]
        calculated_category_totals["misc"] += day["misc"]
        calculated_category_totals["pov_mileage"] += day["pov_mileage"]
        calculated_category_totals["fuel"] += day["fuel"]
        calculated_category_totals["car_rental"] += day["car_rental"]
        calculated_category_totals["airfare"] += day["airfare"]
        calculated_category_totals["inner_city_fares"] += day["inner_city_fares"]
        calculated_category_totals["parking_fees"] += day["parking_fees"]
        calculated_category_totals["internet_service"] += day["internet_service"]
        
        calculated_emburse_totals["lodging"] += day["lodging_emburse"]
        calculated_emburse_totals["breakfast"] += day["breakfast_emburse"]
        calculated_emburse_totals["lunch"] += day["lunch_emburse"]
        calculated_emburse_totals["dinner"] += day["dinner_emburse"]
        calculated_emburse_totals["misc"] += day["misc_emburse"]
        calculated_emburse_totals["pov_mileage"] += day["pov_mileage_emburse"]
        calculated_emburse_totals["fuel"] += day["fuel_emburse"]
        calculated_emburse_totals["car_rental"] += day["car_rental_emburse"]
        calculated_emburse_totals["airfare"] += day["airfare_emburse"]
        calculated_emburse_totals["inner_city_fares"] += day["inner_city_fares_emburse"]
        calculated_emburse_totals["parking_fees"] += day["parking_fees_emburse"]
        calculated_emburse_totals["internet_service"] += day["internet_service_emburse"]
    
    # Use calculated totals (or form totals if provided and non-zero)
    # FIXED: Always prioritize calculated totals since they're accurate
    category_totals = {
        "lodging": calculated_category_totals["lodging"] if calculated_category_totals["lodging"] > 0 else safe_float(total_lodging),
        "breakfast": calculated_category_totals["breakfast"] if calculated_category_totals["breakfast"] > 0 else safe_float(total_breakfast),
        "lunch": calculated_category_totals["lunch"] if calculated_category_totals["lunch"] > 0 else safe_float(total_lunch),
        "dinner": calculated_category_totals["dinner"] if calculated_category_totals["dinner"] > 0 else safe_float(total_dinner),
        "misc": calculated_category_totals["misc"] if calculated_category_totals["misc"] > 0 else safe_float(total_misc),
        "pov_mileage": calculated_category_totals["pov_mileage"] if calculated_category_totals["pov_mileage"] > 0 else safe_float(total_pov_mileage),
        "fuel": calculated_category_totals["fuel"] if calculated_category_totals["fuel"] > 0 else safe_float(total_fuel),
        "car_rental": calculated_category_totals["car_rental"] if calculated_category_totals["car_rental"] > 0 else safe_float(total_car_rental),
        "airfare": calculated_category_totals["airfare"] if calculated_category_totals["airfare"] > 0 else safe_float(total_airfare),
        "inner_city_fares": calculated_category_totals["inner_city_fares"] if calculated_category_totals["inner_city_fares"] > 0 else safe_float(total_inner_city_fares),
        "parking_fees": calculated_category_totals["parking_fees"] if calculated_category_totals["parking_fees"] > 0 else safe_float(total_parking_fees),
        "internet_service": calculated_category_totals["internet_service"] if calculated_category_totals["internet_service"] > 0 else safe_float(total_internet_service),
    }
    
    emburse_totals = {
        "lodging": calculated_emburse_totals["lodging"] if calculated_emburse_totals["lodging"] > 0 else safe_float(total_lodging_emburse),
        "breakfast": calculated_emburse_totals["breakfast"] if calculated_emburse_totals["breakfast"] > 0 else safe_float(total_breakfast_emburse),
        "lunch": calculated_emburse_totals["lunch"] if calculated_emburse_totals["lunch"] > 0 else safe_float(total_lunch_emburse),
        "dinner": calculated_emburse_totals["dinner"] if calculated_emburse_totals["dinner"] > 0 else safe_float(total_dinner_emburse),
        "misc": calculated_emburse_totals["misc"] if calculated_emburse_totals["misc"] > 0 else safe_float(total_misc_emburse),
        "pov_mileage": calculated_emburse_totals["pov_mileage"] if calculated_emburse_totals["pov_mileage"] > 0 else safe_float(total_pov_mileage_emburse),
        "fuel": calculated_emburse_totals["fuel"] if calculated_emburse_totals["fuel"] > 0 else safe_float(total_fuel_emburse),
        "car_rental": calculated_emburse_totals["car_rental"] if calculated_emburse_totals["car_rental"] > 0 else safe_float(total_car_rental_emburse),
        "airfare": calculated_emburse_totals["airfare"] if calculated_emburse_totals["airfare"] > 0 else safe_float(total_airfare_emburse),
        "inner_city_fares": calculated_emburse_totals["inner_city_fares"] if calculated_emburse_totals["inner_city_fares"] > 0 else safe_float(total_inner_city_fares_emburse),
        "parking_fees": calculated_emburse_totals["parking_fees"] if calculated_emburse_totals["parking_fees"] > 0 else safe_float(total_parking_fees_emburse),
        "internet_service": calculated_emburse_totals["internet_service"] if calculated_emburse_totals["internet_service"] > 0 else safe_float(total_internet_service_emburse),
    }
    
    grand_total = sum(category_totals.values())
    grand_emburse = sum(emburse_totals.values())
    
    # Calculate Account Distribution automatically
    meals_total = category_totals["breakfast"] + category_totals["lunch"] + category_totals["dinner"]
    mileage_total = category_totals["pov_mileage"]
    lodging_total = category_totals["lodging"]
    other_total = category_totals["misc"] + category_totals["fuel"] + category_totals["car_rental"] + category_totals["airfare"] + category_totals["inner_city_fares"] + category_totals["parking_fees"] + category_totals["internet_service"]
    
    # Account Distribution - use provided or calculate
    account_distribution = {
        "meals": safe_float(dist_meals) or meals_total,
        "mileage": safe_float(dist_mileage) or mileage_total,
        "lodging": safe_float(dist_lodging) or lodging_total,
        "other_expenses": safe_float(dist_other_expenses) or other_total,
        "total": 0,  # Will be calculated below
    }
    account_distribution["total"] = sum([
        account_distribution["meals"],
        account_distribution["mileage"],
        account_distribution["lodging"],
        account_distribution["other_expenses"]
    ])
    
    # Expense Reconciliation - Calculate automatically
    calc_total_expenditure = grand_total  # Total from category totals
    calc_advance = safe_float(advance_this_report) or safe_float(travel_request.get("travel_advance", 0))
    calc_emburse = grand_emburse  # Total emburse card expenses
    calc_out_of_pocket = calc_total_expenditure - calc_emburse  # What traveler paid themselves
    
    # Calculate settlement
    calc_amount_due_to_employee = 0
    calc_amount_due_to_ntu = 0
    
    if calc_out_of_pocket > calc_advance:
        # Traveler spent more than advance - university owes them
        calc_amount_due_to_employee = calc_out_of_pocket - calc_advance
    elif calc_advance > calc_out_of_pocket:
        # Traveler spent less than advance - they owe university
        calc_amount_due_to_ntu = calc_advance - calc_out_of_pocket
    
    expense_reconciliation = {
        "total_expenditure": safe_float(total_expenditure) or calc_total_expenditure,
        "advance_this_report": safe_float(advance_this_report) or calc_advance,
        "emburse_expense": safe_float(emburse_expense) or calc_emburse,
        "out_of_pocket_expense": safe_float(out_of_pocket_expense) or calc_out_of_pocket,
        "amount_due_to_employee": safe_float(amount_due_to_employee) or calc_amount_due_to_employee,
        "amount_due_to_ntu": safe_float(amount_due_to_ntu) or calc_amount_due_to_ntu,
    }
    
    # Debug logging
    print(f"   📊 CALCULATIONS:")
    print(f"      Daily Expenses: {len(daily_expenses)} days")
    print(f"      Grand Total: ${grand_total:.2f}")
    print(f"      Grand Emburse: ${grand_emburse:.2f}")
    print(f"      Account Distribution Total: ${account_distribution['total']:.2f}")
    print(f"      Settlement: Employee Owes=${expense_reconciliation['amount_due_to_ntu']:.2f}, NTU Owes=${expense_reconciliation['amount_due_to_employee']:.2f}")
    
    # Certification
    certification = {
        "statement": "I CERTIFY THAT THIS TRAVEL REPORT IS ACCURATE, COMPLETE AND ALL EXPENSES REQUESTED FOR REIMBURSEMENT AND CLAIMED HEREIN WERE ON NAVAJO TECHNICAL UNIVERSITY OFFICIAL TRAVEL FOR THE PURPOSE SET FORTH IN THIS TRAVEL AUTHORIZATION",
        "traveler_signature": traveler_signature,
        "certification_date": certification_date,
        "certified_at": utc_now(),
    }
    
    # Build expense report
    expense_report = {
        "traveler_info": {
            "employee_id": employee_id or travel_request.get("traveler_employee_id"),
            "name": traveler_name or travel_request.get("traveler_name"),
            "position": position or travel_request.get("position", "TRAVELER"),
            "department": department or travel_request.get("department"),
            "travel_period_start": travel_period_start or travel_request.get("departure_date"),
            "travel_period_end": travel_period_end or travel_request.get("return_date"),
        },
        "daily_expenses": daily_expenses,
        "category_totals": category_totals,
        "emburse_totals": emburse_totals,
        "grand_total": grand_total,
        "grand_emburse": grand_emburse,
        "account_distribution": account_distribution,
        "expense_reconciliation": expense_reconciliation,
        "certification": certification,
        "submitted_at": utc_now(),
        "status": "SUBMITTED",
    }
    
    # Update database
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "expense_report": expense_report,
            "daily_expense_breakdown": {"daily_expenses": daily_expenses, "category_totals": category_totals, "emburse_totals": emburse_totals},
            "account_distribution": account_distribution,
            "expense_reconciliation": expense_reconciliation,
            "certification": certification,
            "updated_at": utc_now(),
        }}
    )
    
    print(f"   ✅ Expense Report Saved - Total: ${grand_total:.2f}, Emburse: ${grand_emburse:.2f}")
    
    return DataResponse(
        success=True,
        message="Expense Report submitted successfully",
        data={
            "grand_total": grand_total,
            "grand_emburse": grand_emburse,
            "days_reported": len(daily_expenses),
            "account_distribution": account_distribution,
            "expense_reconciliation": expense_reconciliation,
            "certification": {"signature": traveler_signature, "date": certification_date},
        }
    )


# ============================================================
# 2. MILEAGE REPORT - Mileage entries with from/to locations
# ============================================================

# ============================================================
# 2. MILEAGE REPORT/LOG - With Odometer Readings
# REPLACE your existing mileage-report section with this
# ============================================================

@router.post("/{request_id}/mileage-report", response_model=DataResponse)
async def submit_mileage_report(
    request_id: str,
    
    # ===== TRAVELER INFORMATION =====
    traveler_name: Optional[str] = Form(None, description="TRAVELER'S NAME"),
    ta_number: Optional[str] = Form(None, description="TRAVEL AUTHORIZATION NO."),
    
    # ===== MILEAGE LOG ENTRY 1 =====
    entry1_travel_date: Optional[str] = Form(None, description="Entry 1 - Travel Date (MM/DD/YYYY)"),
    entry1_purpose_of_travel: Optional[str] = Form(None, description="Entry 1 - Purpose of Travel"),
    entry1_city_from: Optional[str] = Form(None, description="Entry 1 - City From"),
    entry1_city_to: Optional[str] = Form(None, description="Entry 1 - City To"),
    entry1_odometer_begin: float = Form(0.0, description="Entry 1 - Odometer Begin"),
    entry1_odometer_end: float = Form(0.0, description="Entry 1 - Odometer End"),
    entry1_total_miles: float = Form(0.0, description="Entry 1 - Total Miles"),
    
    # ===== TOTALS =====
    grand_total_miles: float = Form(0.0, description="TOTAL MILES"),
    rate_per_mile: float = Form(0.67, description="Rate per Mile ($)"),
    total_reimbursement: float = Form(0.0, description="Total Reimbursement ($)"),
    
    # ===== CERTIFICATION =====
    traveler_signature: str = Form(..., description="Traveler's Signature (Type Full Name) *REQUIRED*"),
    certification_date: str = Form(..., description="Certification Date (MM/DD/YYYY) *REQUIRED*"),
    
    db = Depends(get_database),
):
    """
    🚗 MILEAGE REPORT/LOG
    
    Required for Monthly Blanket TA or POV Mileage Claims.
    Must be accompanied with a Trip Report.
    
    Traveler Information:
    - TRAVELER'S NAME
    - TRAVEL AUTHORIZATION NO.
    
    Mileage Log Entries (up to 10):
    - Travel Date (MM/DD/YYYY)
    - Purpose of Travel
    - City From
    - City To
    - Odometer Begin
    - Odometer End
    - Total Miles
    
    Certification:
    "I certify that this mileage report represents actual mileage incurred by me on official travel as herein stated."
    
    NO AUTH - for testing
    """
    print(f"\n{'='*60}")
    print(f"🚗 MILEAGE REPORT - POST /reports/{request_id}/mileage-report")
    print(f"   Traveler: {traveler_name} | TA#: {ta_number}")
    print(f"   Signature: {traveler_signature} | Date: {certification_date}")
    print(f"{'='*60}")
    
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    # Build mileage entries
    entries = []
    all_entries = [
        (1, entry1_travel_date, entry1_purpose_of_travel, entry1_city_from, entry1_city_to, entry1_odometer_begin, entry1_odometer_end, entry1_total_miles)
    ]
    
    for entry_num, travel_date, purpose, city_from, city_to, odo_begin, odo_end, miles in all_entries:
        if travel_date or city_from:
            calculated_miles = safe_float(miles)
            if calculated_miles == 0 and safe_float(odo_end) > safe_float(odo_begin):
                calculated_miles = safe_float(odo_end) - safe_float(odo_begin)
            
            entries.append({
                "entry_number": entry_num,
                "travel_date": travel_date,
                "purpose_of_travel": purpose,
                "city_from": city_from,
                "city_to": city_to,
                "odometer_begin": safe_float(odo_begin),
                "odometer_end": safe_float(odo_end),
                "total_miles": calculated_miles,
            })
    
    calculated_total_miles = sum(e["total_miles"] for e in entries) if entries else safe_float(grand_total_miles)
    rate = safe_float(rate_per_mile) or 0.67
    calculated_reimbursement = calculated_total_miles * rate
    
    traveler_info = {
        "traveler_name": traveler_name or travel_request.get("traveler_name"),
        "ta_number": ta_number or travel_request.get("ta_number"),
    }
    
    certification = {
        "statement": "I certify that this mileage report represents actual mileage incurred by me on official travel as herein stated.",
        "traveler_signature": traveler_signature,
        "certification_date": certification_date,
        "certified_at": utc_now(),
    }
    
    mileage_report = {
        "traveler_info": traveler_info,
        "mileage_log_entries": entries,
        "grand_total_miles": calculated_total_miles,
        "rate_per_mile": rate,
        "total_reimbursement": safe_float(total_reimbursement) or calculated_reimbursement,
        "certification": certification,
        "submitted_at": utc_now(),
        "status": "SUBMITTED",
    }
    
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"mileage_report": mileage_report, "updated_at": utc_now()}}
    )
    
    print(f"   ✅ Mileage Report Saved - {len(entries)} entries, {calculated_total_miles} miles, ${calculated_reimbursement:.2f}")
    
    return DataResponse(
        success=True,
        message="Mileage Report submitted successfully",
        data={
            "traveler_info": traveler_info,
            "entries_count": len(entries),
            "grand_total_miles": calculated_total_miles,
            "rate_per_mile": rate,
            "total_reimbursement": calculated_reimbursement,
            "certification": {"signature": traveler_signature, "date": certification_date},
        }
    )

# ============================================================
# 3. TRIP REPORT - Trip summary, objectives, outcomes
# ============================================================

@router.post("/{request_id}/trip-report", response_model=DataResponse)
async def submit_trip_report(
    request_id: str,
    
    # ===== TRAVELER INFORMATION =====
    traveler_name: Optional[str] = Form(None, description="TRAVELER NAME"),
    ta_number: Optional[str] = Form(None, description="TA NUMBER"),
    department: Optional[str] = Form(None, description="DEPARTMENT"),
    
    # ===== TRAVEL DETAILS =====
    report_date: str = Form(..., description="Report Date (MM/DD/YYYY) *REQUIRED*"),
    travel_start_date: str = Form(..., description="Travel Start Date (MM/DD/YYYY) *REQUIRED*"),
    travel_end_date: str = Form(..., description="Travel End Date (MM/DD/YYYY) *REQUIRED*"),
    departure_time: Optional[str] = Form(None, description="Departure Time (e.g., 07:00 AM)"),
    return_time: Optional[str] = Form(None, description="Return Time (e.g., 08:00 PM)"),
    
    # ===== VEHICLE INFORMATION =====
    type_of_vehicle: Optional[str] = Form(None, description="Type of Vehicle (Private Vehicle, Rental, University Vehicle)"),
    odometer_beginning: float = Form(0.0, description="Odometer Beginning"),
    odometer_ending: float = Form(0.0, description="Odometer Ending"),
    total_miles: float = Form(0.0, description="Total Miles (Auto-calculated from odometer)"),
    
    # ===== PURPOSE OF TRAVEL =====
    purpose_of_travel: str = Form(..., description="Describe the purpose of your travel *REQUIRED*"),
    
    # ===== PERSON(S) CONTACTED =====
    persons_contacted: str = Form(..., description="List people you met with or contacted *REQUIRED* (e.g., John Smith (ABC Company, CEO), Jane Doe (XYZ Organization, Director))"),
    
    # ===== ACCOMPLISHMENTS (Note: XVII.2) =====
    accomplishments: str = Form(..., description="Describe your accomplishments *REQUIRED* - What you accomplished during this travel and how it benefits NTU"),
    
    # ===== UNAUTHORIZED EXPENSES (Optional) =====
    unauthorized_expenses_justification: Optional[str] = Form(None, description="Justification for any unauthorized expenses (Leave blank if not applicable)"),
    
    # ===== CERTIFICATION & SIGNATURE =====
    traveler_signature: str = Form(..., description="Traveler Signature (Type Full Name) *REQUIRED*"),
    signature_date: str = Form(..., description="Signature Date (MM/DD/YYYY) *REQUIRED*"),
    
    db = Depends(get_database),
):
    """
    ✈️ TRIP REPORT - Submit trip report with all sections:
    
    1. Traveler Information
       - Traveler Name, TA Number, Department
    
    2. Travel Details
       - Report Date, Travel Start/End Date, Departure/Return Time
    
    3. Vehicle Information
       - Type of Vehicle, Odometer Beginning/Ending, Total Miles
    
    4. Purpose of Travel
       - Describe the purpose of your travel
    
    5. Person(s) Contacted
       - List people you met with or contacted
    
    6. Accomplishments (Note: XVII.2)
       - Describe what you accomplished and how it benefits NTU
    
    7. Unauthorized Expenses (Optional)
       - Justification for any unauthorized expenses
    
    8. Certification & Signature
       - "I certify that this trip report represents all claims incurred by me on official travel as herein stated."
       - Traveler Signature, Signature Date
    
    NO AUTH - for testing
    """
    print(f"\n{'='*60}")
    print(f"✈️ TRIP REPORT - POST /reports/{request_id}/trip-report")
    print(f"   Traveler: {traveler_name} | TA#: {ta_number}")
    print(f"   Travel: {travel_start_date} to {travel_end_date}")
    print(f"   Signature: {traveler_signature} | Date: {signature_date}")
    print(f"{'='*60}")
    
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    # Calculate total miles from odometer if not provided
    calculated_miles = safe_float(total_miles)
    if calculated_miles == 0 and safe_float(odometer_ending) > safe_float(odometer_beginning):
        calculated_miles = safe_float(odometer_ending) - safe_float(odometer_beginning)
    
    # Build trip report
    trip_report = {
        # Traveler Information
        "traveler_info": {
            "traveler_name": traveler_name or travel_request.get("traveler_name"),
            "ta_number": ta_number or travel_request.get("ta_number"),
            "department": department or travel_request.get("department"),
        },
        
        # Travel Details
        "travel_details": {
            "report_date": report_date,
            "travel_start_date": travel_start_date,
            "travel_end_date": travel_end_date,
            "departure_time": departure_time,
            "return_time": return_time,
        },
        
        # Vehicle Information
        "vehicle_info": {
            "type_of_vehicle": type_of_vehicle,
            "odometer_beginning": safe_float(odometer_beginning),
            "odometer_ending": safe_float(odometer_ending),
            "total_miles": calculated_miles,
        },
        
        # Purpose of Travel
        "purpose_of_travel": purpose_of_travel,
        
        # Person(s) Contacted
        "persons_contacted": persons_contacted,
        
        # Accomplishments
        "accomplishments": accomplishments,
        
        # Unauthorized Expenses
        "unauthorized_expenses": {
            "has_unauthorized": bool(unauthorized_expenses_justification),
            "justification": unauthorized_expenses_justification,
        },
        
        # Certification
        "certification": {
            "statement": "I certify that this trip report represents all claims incurred by me on official travel as herein stated.",
            "traveler_signature": traveler_signature,
            "signature_date": signature_date,
            "certified_at": utc_now(),
        },
        
        "submitted_at": utc_now(),
        "status": "SUBMITTED",
    }
    
    # Update database
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"trip_report": trip_report, "updated_at": utc_now()}}
    )
    
    print(f"   ✅ Trip Report Saved - Miles: {calculated_miles}")
    
    return DataResponse(
        success=True,
        message="Trip Report submitted successfully",
        data={
            "traveler_info": trip_report["traveler_info"],
            "travel_details": trip_report["travel_details"],
            "vehicle_info": trip_report["vehicle_info"],
            "total_miles": calculated_miles,
            "certification": {"signature": traveler_signature, "date": signature_date},
        }
    )


# ============================================================
# VIEW ENDPOINTS - Get submitted reports
# ============================================================

@router.get("/{request_id}/expense-report", response_model=DataResponse)
async def get_expense_report(request_id: str, db = Depends(get_database)):
    """📋 View submitted Expense Report"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    expense_report = travel_request.get("expense_report")
    if not expense_report:
        return DataResponse(success=False, message="Expense Report not submitted yet", data=None)
    
    return DataResponse(success=True, message="Expense Report retrieved", data=expense_report)


@router.get("/{request_id}/mileage-report", response_model=DataResponse)
async def get_mileage_report(request_id: str, db = Depends(get_database)):
    """🚗 View submitted Mileage Report"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    mileage_report = travel_request.get("mileage_report")
    if not mileage_report:
        return DataResponse(success=False, message="Mileage Report not submitted yet", data=None)
    
    return DataResponse(success=True, message="Mileage Report retrieved", data=mileage_report)


@router.get("/{request_id}/trip-report", response_model=DataResponse)
async def get_trip_report(request_id: str, db = Depends(get_database)):
    """✈️ View submitted Trip Report"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    trip_report = travel_request.get("trip_report")
    if not trip_report:
        return DataResponse(success=False, message="Trip Report not submitted yet", data=None)
    
    return DataResponse(success=True, message="Trip Report retrieved", data=trip_report)


# ============================================================
# SUBMIT ALL POST-TRAVEL - Final submission
# ============================================================

@router.post("/{request_id}/post-travel/submit", response_model=DataResponse)
async def submit_post_travel(
    request_id: str,
    background_tasks: BackgroundTasks,
    traveler_signature: str = Form(..., description="Final Signature *REQUIRED*"),
    certification_date: str = Form(..., description="Final Date (MM/DD/YYYY) *REQUIRED*"),
    db = Depends(get_database),
):
    """
    ✅ SUBMIT ALL POST-TRAVEL - Final submission after all 3 reports are filled
    
    This changes status to POST_TRAVEL_SUBMITTED and notifies supervisor.
    Make sure Expense Report, Mileage Report, and Trip Report are submitted first!
    """
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    # Check if reports are submitted
    expense_report = travel_request.get("expense_report")
    mileage_report = travel_request.get("mileage_report")
    trip_report = travel_request.get("trip_report")
    
    missing = []
    if not expense_report: missing.append("Expense Report")
    if not trip_report: missing.append("Trip Report")
    # Mileage is optional
    
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Please submit these reports first: {', '.join(missing)}"
        )
    
    # Final certification
    final_certification = {
        "traveler_signature": traveler_signature,
        "certification_date": certification_date,
        "certified_at": utc_now(),
    }
    
    # Calculate settlement
    travel_advance = safe_float(travel_request.get("travel_advance", 0))
    additional_funds = safe_float(travel_request.get("additional_funds", 0))
    total_spent = safe_float(expense_report.get("grand_total", 0))
    settlement = calculate_settlement(travel_advance, additional_funds, total_spent)
    
    # Update status
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": TravelStatus.POST_TRAVEL_SUBMITTED.value,
            "post_travel_final_certification": final_certification,
            "settlement": settlement,
            "updated_at": utc_now(),
        }}
    )
    
    # Notify supervisor
    supervisor_id = travel_request.get("supervisor_id")
    traveler_name = travel_request.get("traveler_name", "Traveler")
    
    if supervisor_id:
        background_tasks.add_task(
            send_notification, db, supervisor_id,
            "Post-Travel Report Submitted",
            f"{traveler_name} has submitted all post-travel reports for review",
            "warning", f"/requests/{request_id}/view"
        )
    
    return DataResponse(
        success=True,
        message="All Post-Travel reports submitted for approval!",
        data={
            "status": "POST_TRAVEL_SUBMITTED",
            "expense_report": "✅ Submitted",
            "mileage_report": "✅ Submitted" if mileage_report else "⏭️ Skipped",
            "trip_report": "✅ Submitted",
            "settlement": settlement,
        }
    )


# ============================================================
# SETTLEMENT CALCULATION
# ============================================================

@router.get("/{request_id}/settlement", response_model=DataResponse)
async def get_settlement(request_id: str, db = Depends(get_database)):
    """💰 Get settlement calculation"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")
    
    travel_advance = safe_float(travel_request.get("travel_advance", 0))
    additional_funds = safe_float(travel_request.get("additional_funds", 0))
    
    expense_report = travel_request.get("expense_report", {})
    total_spent = safe_float(expense_report.get("grand_total", 0))
    
    settlement = calculate_settlement(travel_advance, additional_funds, total_spent)
    
    return DataResponse(
        success=True,
        message="Settlement calculated",
        data={
            "travel_advance": travel_advance,
            "additional_funds": additional_funds,
            "total_given": travel_advance + additional_funds,
            "total_spent": total_spent,
            **settlement,
        }
    )