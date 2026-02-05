# """
# Approvals Router
# Handles: Supervisor approval, President approval, Post-travel approvals

# NOTE: Authentication DISABLED for testing. Re-enable for production!
# """

# from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Form, Query
# from typing import Optional, List
# from datetime import datetime, timezone
# from bson import ObjectId

# from dependencies.database import get_database
# # Auth imports disabled for testing
# # from dependencies.auth import (
# #     get_current_user,
# #     get_supervisor_user,
# #     get_finance_user,
# #     get_president_user,
# #     can_approve_request,
# # )
# from models.request import (
#     TravelStatus,
#     ApprovalAction,
#     ApprovalResponse,
# )
# from models.response import ListResponse, DataResponse
# from utils.helpers import (
#     generate_ta_number_async,
#     safe_object_id,
#     get_user_full_name,
#     paginate_query,
#     build_sort_query,
#     utc_now,
# )
# from services.notification_service import NotificationService
# from services.email_service import EmailService

# router = APIRouter()


# # ============ Helper Functions ============

# async def get_request_by_id(db, request_id: str) -> Optional[dict]:
#     """Get travel request by ID"""
#     obj_id = safe_object_id(request_id)
#     if not obj_id:
#         return None
#     return await db.travel_requests.find_one({"_id": obj_id})


# async def send_notification_with_sms(
#     db,
#     user_id: str,
#     title: str,
#     message: str,
#     notification_type: str = "info",
#     link: Optional[str] = None,
# ):
#     """Send in-app notification"""
#     notification = {
#         "user_id": user_id,
#         "title": title,
#         "message": message,
#         "notification_type": notification_type,
#         "link": link,
#         "is_read": False,
#         "created_at": utc_now(),
#     }
#     await db.notifications.insert_one(notification)


# # ============ Supervisor Approval Routes ============

# @router.post("/{request_id}/approve", response_model=ApprovalResponse)
# async def approve_request(
#     request_id: str,
#     background_tasks: BackgroundTasks,
#     comments: Optional[str] = Form(None),
#     approver_name: Optional[str] = Form(None),  # Optional signature name
#     approver_id: Optional[str] = Form(None),  # Optional - not required from frontend
#     db = Depends(get_database),
# ):
#     """
#     Approve a travel request.
#     Supervisor approval for domestic, President approval for international.
    
#     Frontend only needs to send: comments (optional), approver_name (optional)
#     """
#     print(f"\n{'='*60}")
#     print(f"✅ POST /approvals/{request_id}/approve called")
#     print(f"   approver_name: {approver_name}")
#     print(f"   comments: {comments}")
#     print(f"{'='*60}")
    
#     travel_request = await get_request_by_id(db, request_id)
    
#     if not travel_request:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Travel request not found"
#         )
    
#     current_status = travel_request.get("status")
    
#     # Get approver info - use provided name or "System Approved"
#     approver = None
#     user_id = "system"
#     final_approver_name = approver_name or "System Approved"
    
#     # Only try to fetch user if approver_id is valid
#     if approver_id and safe_object_id(approver_id):
#         approver_obj_id = safe_object_id(approver_id)
#         if approver_obj_id:
#             approver = await db.users.find_one({"_id": approver_obj_id})
#             user_id = approver_id
#             if approver:
#                 final_approver_name = get_user_full_name(approver)
    
#     # Validate current status allows approval
#     if current_status == TravelStatus.PENDING_SUPERVISOR.value:
#         new_status = TravelStatus.SUPERVISOR_APPROVED.value
#     elif current_status == TravelStatus.PENDING_PRESIDENT.value:
#         new_status = TravelStatus.SUPERVISOR_APPROVED.value
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Request cannot be approved in current status: {current_status}"
#         )
    
#     # Generate TA number if moving to approved
#     ta_number = None
#     if new_status == TravelStatus.SUPERVISOR_APPROVED.value:
#         ta_number = await generate_ta_number_async(db)
#         new_status = TravelStatus.TA_ISSUED.value
    
#     # Update request
#     update_data = {
#         "status": new_status,
#         "updated_at": utc_now(),
#         "supervisor_approved_at": utc_now(),
#         "supervisor_approved_by": user_id,
#         "approval_comments": comments,
#     }
    
#     if ta_number:
#         update_data["ta_number"] = ta_number
    
#     if current_status == TravelStatus.PENDING_PRESIDENT.value:
#         update_data["president_approved_at"] = utc_now()
#         update_data["president_approved_by"] = user_id
    
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {"$set": update_data}
#     )
    
#     # Add to approval history
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {
#             "$push": {
#                 "approval_history": {
#                     "action": "approved",
#                     "by_user_id": user_id,
#                     "by_user_name": final_approver_name,
#                     "comments": comments,
#                     "timestamp": utc_now(),
#                     "previous_status": current_status,
#                     "new_status": new_status,
#                 }
#             }
#         }
#     )
    
#     # Notify traveler
#     traveler_id = str(travel_request.get("traveler_id"))
#     destination = travel_request.get("destination_city", "destination")
    
#     notification_msg = f"Your travel request to {destination} has been approved"
#     if ta_number:
#         notification_msg += f". TA Number: {ta_number}"
    
#     background_tasks.add_task(
#         send_notification_with_sms,
#         db,
#         traveler_id,
#         "Travel Request Approved",
#         notification_msg,
#         "success",
#         f"/requests/{request_id}/view"
#     )
    
#     # Send approval email to traveler
#     traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
#     if traveler and traveler.get("email"):
#         # Check if this is President approval (international travel)
#         is_president_approval = current_status == TravelStatus.PENDING_PRESIDENT.value
        
#         email_data = {
#             "traveler_name": get_user_full_name(traveler),
#             "ta_number": ta_number or "N/A",
#             "destination": destination,
#             "country": travel_request.get("destination_country", "N/A"),
#             "departure_date": str(travel_request.get("departure_date", "N/A")),
#             "return_date": str(travel_request.get("return_date", "N/A")),
#             "approved_by": final_approver_name,
#             "approved_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
#             "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
#         }
        
#         if is_president_approval:
#             # Use President approval template for international travel
#             background_tasks.add_task(
#                 EmailService.send_president_approval_notification,
#                 traveler.get("email"),
#                 email_data
#             )
#             print(f"   📧 President approval email queued for: {traveler.get('email')}")
#         else:
#             # Use regular supervisor approval template
#             background_tasks.add_task(
#                 EmailService.send_approval_notification,
#                 traveler.get("email"),
#                 email_data
#             )
#             print(f"   📧 Supervisor approval email queued for: {traveler.get('email')}")
    
#     print(f"   ✅ Approved! New status: {new_status}, TA: {ta_number}")
    
#     return ApprovalResponse(
#         success=True,
#         message="Travel request approved successfully",
#         new_status=new_status,
#         ta_number=ta_number,
#     )


# @router.post("/{request_id}/reject", response_model=ApprovalResponse)
# async def reject_request(
#     request_id: str,
#     background_tasks: BackgroundTasks,
#     reason: str = Form(..., min_length=10),
#     rejector_name: Optional[str] = Form(None),  # Optional signature name
#     rejector_id: Optional[str] = Form(None),  # Optional - not required from frontend
#     db = Depends(get_database),
# ):
#     """
#     Reject a travel request.
    
#     Frontend only needs to send: reason (required), rejector_name (optional)
#     """
#     print(f"\n{'='*60}")
#     print(f"❌ POST /approvals/{request_id}/reject called")
#     print(f"   rejector_name: {rejector_name}")
#     print(f"   reason: {reason}")
#     print(f"{'='*60}")
    
#     travel_request = await get_request_by_id(db, request_id)
    
#     if not travel_request:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Travel request not found"
#         )
    
#     current_status = travel_request.get("status")
    
#     # Get rejector info - use provided name or "System Rejected"
#     rejector = None
#     user_id = "system"
#     final_rejector_name = rejector_name or "System Rejected"
    
#     # Only try to fetch user if rejector_id is valid
#     if rejector_id and safe_object_id(rejector_id):
#         rejector_obj_id = safe_object_id(rejector_id)
#         if rejector_obj_id:
#             rejector = await db.users.find_one({"_id": rejector_obj_id})
#             user_id = rejector_id
#             if rejector:
#                 final_rejector_name = get_user_full_name(rejector)
    
#     # Validate rejection permission
#     allowed_statuses = [
#         TravelStatus.PENDING_SUPERVISOR.value,
#         TravelStatus.PENDING_PRESIDENT.value,
#     ]
    
#     if current_status not in allowed_statuses:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Request cannot be rejected in current status: {current_status}"
#         )
    
#     # Update request
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {
#             "$set": {
#                 "status": TravelStatus.REJECTED.value,
#                 "updated_at": utc_now(),
#                 "rejected_at": utc_now(),
#                 "rejected_by": user_id,
#                 "rejection_reason": reason,
#             },
#             "$push": {
#                 "approval_history": {
#                     "action": "rejected",
#                     "by_user_id": user_id,
#                     "by_user_name": final_rejector_name,
#                     "reason": reason,
#                     "timestamp": utc_now(),
#                     "previous_status": current_status,
#                     "new_status": TravelStatus.REJECTED.value,
#                 }
#             }
#         }
#     )
    
#     # Notify traveler
#     traveler_id = str(travel_request.get("traveler_id"))
#     destination = travel_request.get("destination_city", "destination")
    
#     background_tasks.add_task(
#         send_notification_with_sms,
#         db,
#         traveler_id,
#         "Travel Request Rejected",
#         f"Your travel request to {destination} has been rejected. Reason: {reason}",
#         "error",
#         f"/requests/{request_id}/view"
#     )
    
#     # Send rejection email to traveler
#     traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
#     if traveler and traveler.get("email"):
#         # Check if this is President rejection (international travel)
#         is_president_rejection = current_status == TravelStatus.PENDING_PRESIDENT.value
        
#         email_data = {
#             "traveler_name": get_user_full_name(traveler),
#             "destination": destination,
#             "country": travel_request.get("destination_country", "N/A"),
#             "departure_date": str(travel_request.get("departure_date", "N/A")),
#             "return_date": str(travel_request.get("return_date", "N/A")),
#             "rejected_by": final_rejector_name,
#             "reason": reason,
#             "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
#         }
        
#         if is_president_rejection:
#             # Use President rejection template for international travel
#             background_tasks.add_task(
#                 EmailService.send_president_rejection_notification,
#                 traveler.get("email"),
#                 email_data
#             )
#             print(f"   📧 President rejection email queued for: {traveler.get('email')}")
#         else:
#             # Use regular supervisor rejection template
#             background_tasks.add_task(
#                 EmailService.send_rejection_notification,
#                 traveler.get("email"),
#                 email_data
#             )
#             print(f"   📧 Supervisor rejection email queued for: {traveler.get('email')}")
    
#     print(f"   ❌ Rejected! Reason: {reason}")
    
#     return ApprovalResponse(
#         success=True,
#         message="Travel request rejected",
#         new_status=TravelStatus.REJECTED.value,
#     )


# # ============ Post-Travel Approval Routes ============

# @router.post("/{request_id}/post-travel/supervisor-approve", response_model=ApprovalResponse)
# async def supervisor_approve_post_travel(
#     request_id: str,
#     background_tasks: BackgroundTasks,
#     comments: Optional[str] = Form(None),
#     approver_name: Optional[str] = Form(None),  # Optional signature name
#     approver_id: Optional[str] = Form(None),  # Optional - not required from frontend
#     db = Depends(get_database),
# ):
#     """
#     Supervisor approval for post-travel report.
#     Frontend only needs to send: comments (optional), approver_name (optional)
#     """
#     travel_request = await get_request_by_id(db, request_id)
    
#     if not travel_request:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Travel request not found"
#         )
    
#     current_status = travel_request.get("status")
    
#     # Get approver info - use provided name or "System Approved"
#     approver = None
#     user_id = "system"
#     final_approver_name = approver_name or "System Approved"
    
#     # Only try to fetch user if approver_id is valid
#     if approver_id and safe_object_id(approver_id):
#         approver_obj_id = safe_object_id(approver_id)
#         if approver_obj_id:
#             approver = await db.users.find_one({"_id": approver_obj_id})
#             user_id = approver_id
#             if approver:
#                 final_approver_name = get_user_full_name(approver)
    
#     if current_status != TravelStatus.POST_TRAVEL_SUBMITTED.value:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Post-travel report not submitted or already reviewed"
#         )
    
#     # Update status
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {
#             "$set": {
#                 "status": TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
#                 "updated_at": utc_now(),
#                 "post_travel_supervisor_approved_at": utc_now(),
#                 "post_travel_supervisor_approved_by": user_id,
#                 "post_travel_supervisor_comments": comments,
#             },
#             "$push": {
#                 "approval_history": {
#                     "action": "post_travel_supervisor_approved",
#                     "by_user_id": user_id,
#                     "by_user_name": final_approver_name,
#                     "comments": comments,
#                     "timestamp": utc_now(),
#                 }
#             }
#         }
#     )
    
#     # Notify finance team
#     finance_users = await db.users.find({"role": "FINANCE"}).to_list(100)
#     for finance_user in finance_users:
#         background_tasks.add_task(
#             send_notification_with_sms,
#             db,
#             str(finance_user["_id"]),
#             "Post-Travel Report Ready for Finance Review",
#             f"Post-travel report for {travel_request.get('traveler_name')} needs finance approval",
#             "warning",
#             f"/requests/{request_id}/view"
#         )
        
#         # Send email to finance team
#         if finance_user.get("email"):
#             post_travel_data = travel_request.get("post_travel_report", {})
#             email_data = {
#                 "traveler_name": travel_request.get("traveler_name", "N/A"),
#                 "ta_number": travel_request.get("ta_number", "N/A"),
#                 "destination": travel_request.get("destination_city", "N/A"),
#                 "departure_date": str(travel_request.get("departure_date", "N/A")),
#                 "return_date": str(travel_request.get("return_date", "N/A")),
#                 "total_expenses": f"{float(post_travel_data.get('total_spent', 0)):.2f}",
#                 "travel_advance": f"{float(travel_request.get('travel_advance', 0)):.2f}",
#                 "supervisor_approved_by": approver_name,
#                 "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
#             }
#             background_tasks.add_task(
#                 EmailService.send_post_travel_to_finance_notification,
#                 finance_user.get("email"),
#                 email_data
#             )
#             print(f"   📧 Finance notification email queued for: {finance_user.get('email')}")
    
#     return ApprovalResponse(
#         success=True,
#         message="Post-travel report approved by supervisor, sent to finance",
#         new_status=TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
#     )


# @router.post("/{request_id}/post-travel/finance-approve", response_model=ApprovalResponse)
# async def finance_approve_post_travel(
#     request_id: str,
#     background_tasks: BackgroundTasks,
#     comments: Optional[str] = Form(None),
#     approved_amount: Optional[float] = Form(None),
#     approver_name: Optional[str] = Form(None),  # Optional signature name
#     approver_id: Optional[str] = Form(None),  # Optional - not required from frontend
#     db = Depends(get_database),
# ):
#     """
#     Finance approval for post-travel report - finalizes reimbursement.
#     Frontend only needs to send: comments (optional), approved_amount (optional), approver_name (optional)
#     """
#     travel_request = await get_request_by_id(db, request_id)
    
#     if not travel_request:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Travel request not found"
#         )
    
#     current_status = travel_request.get("status")
    
#     # Get approver info - use provided name or "System Approved"
#     approver = None
#     user_id = "system"
#     final_approver_name = approver_name or "System Approved"
    
#     # Only try to fetch user if approver_id is valid
#     if approver_id and safe_object_id(approver_id):
#         approver_obj_id = safe_object_id(approver_id)
#         if approver_obj_id:
#             approver = await db.users.find_one({"_id": approver_obj_id})
#             user_id = approver_id
#             if approver:
#                 final_approver_name = get_user_full_name(approver)
    
#     if current_status != TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Post-travel report must be supervisor-approved first"
#         )
    
#     # Calculate settlement
#     travel_advance = float(travel_request.get("travel_advance", 0))
#     additional_funds = float(travel_request.get("additional_funds", 0))
#     total_given = travel_advance + additional_funds
    
#     post_travel = travel_request.get("post_travel_report", {})
#     total_spent = float(post_travel.get("total_spent", 0))
    
#     if approved_amount is not None:
#         total_spent = approved_amount
    
#     settlement = total_given - total_spent
#     settlement_type = "TRAVELER_OWES" if settlement > 0 else "UNIVERSITY_OWES" if settlement < 0 else "BALANCED"
    
#     # Update status to completed
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {
#             "$set": {
#                 "status": TravelStatus.COMPLETED.value,
#                 "updated_at": utc_now(),
#                 "completed_at": utc_now(),
#                 "finance_approved_at": utc_now(),
#                 "finance_approved_by": user_id,
#                 "finance_comments": comments,
#                 "final_approved_amount": total_spent,
#                 "settlement": {
#                     "total_given": total_given,
#                     "total_spent": total_spent,
#                     "settlement_amount": abs(settlement),
#                     "settlement_type": settlement_type,
#                     "calculated_at": utc_now(),
#                 }
#             },
#             "$push": {
#                 "approval_history": {
#                     "action": "finance_approved",
#                     "by_user_id": user_id,
#                     "by_user_name": final_approver_name,
#                     "comments": comments,
#                     "approved_amount": total_spent,
#                     "timestamp": utc_now(),
#                 }
#             }
#         }
#     )
    
#     # Notify traveler
#     traveler_id = str(travel_request.get("traveler_id"))
#     settlement_msg = f"Amount: ${abs(settlement):.2f}"
#     if settlement_type == "TRAVELER_OWES":
#         settlement_msg = f"Please return ${abs(settlement):.2f} to the university"
#     elif settlement_type == "UNIVERSITY_OWES":
#         settlement_msg = f"You will receive ${abs(settlement):.2f} reimbursement"
    
#     background_tasks.add_task(
#         send_notification_with_sms,
#         db,
#         traveler_id,
#         "Travel Request Completed",
#         f"Your travel request has been finalized. {settlement_msg}",
#         "success",
#         f"/requests/{request_id}/view"
#     )
    
#     # Send finance approval email to traveler
#     traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
#     if traveler and traveler.get("email"):
#         email_data = {
#             "traveler_name": get_user_full_name(traveler),
#             "ta_number": travel_request.get("ta_number", "N/A"),
#             "destination": travel_request.get("destination_city", "N/A"),
#             "total_advance": f"{total_given:.2f}",
#             "total_expenses": f"{total_spent:.2f}",
#             "settlement_type": settlement_type,
#             "settlement_amount": f"{abs(settlement):.2f}",
#             "approved_by": final_approver_name,
#             "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
#         }
#         background_tasks.add_task(
#             EmailService.send_finance_approval_notification,
#             traveler.get("email"),
#             email_data
#         )
#         print(f"   📧 Finance approval email queued for: {traveler.get('email')}")
    
#     return ApprovalResponse(
#         success=True,
#         message=f"Post-travel approved. Settlement: {settlement_type}",
#         new_status=TravelStatus.COMPLETED.value,
#     )


# @router.post("/{request_id}/post-travel/reject", response_model=ApprovalResponse)
# async def reject_post_travel(
#     request_id: str,
#     background_tasks: BackgroundTasks,
#     reason: str = Form(..., min_length=10),
#     rejector_name: Optional[str] = Form(None),  # Optional signature name
#     rejector_id: Optional[str] = Form(None),  # Optional - not required from frontend
#     db = Depends(get_database),
# ):
#     """
#     Reject post-travel report and request revisions.
#     Frontend only needs to send: reason (required), rejector_name (optional)
#     """
#     travel_request = await get_request_by_id(db, request_id)
    
#     if not travel_request:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Travel request not found"
#         )
    
#     current_status = travel_request.get("status")
    
#     # Get rejector info - use provided name or "System Rejected"
#     rejector = None
#     user_id = "system"
#     final_rejector_name = rejector_name or "System Rejected"
    
#     # Only try to fetch user if rejector_id is valid
#     if rejector_id and safe_object_id(rejector_id):
#         rejector_obj_id = safe_object_id(rejector_id)
#         if rejector_obj_id:
#             rejector = await db.users.find_one({"_id": rejector_obj_id})
#             user_id = rejector_id
#             if rejector:
#                 final_rejector_name = get_user_full_name(rejector)
    
#     allowed_statuses = [
#         TravelStatus.POST_TRAVEL_SUBMITTED.value,
#         TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
#     ]
    
#     if current_status not in allowed_statuses:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="No post-travel report to reject"
#         )
    
#     # Revert to TA_ISSUED to allow resubmission
#     await db.travel_requests.update_one(
#         {"_id": ObjectId(request_id)},
#         {
#             "$set": {
#                 "status": TravelStatus.TA_ISSUED.value,
#                 "updated_at": utc_now(),
#                 "post_travel_rejected_at": utc_now(),
#                 "post_travel_rejected_by": user_id,
#                 "post_travel_rejection_reason": reason,
#             },
#             "$push": {
#                 "approval_history": {
#                     "action": "post_travel_rejected",
#                     "by_user_id": user_id,
#                     "by_user_name": final_rejector_name,
#                     "reason": reason,
#                     "timestamp": utc_now(),
#                 }
#             }
#         }
#     )
    
#     # Notify traveler
#     traveler_id = str(travel_request.get("traveler_id"))
    
#     background_tasks.add_task(
#         send_notification_with_sms,
#         db,
#         traveler_id,
#         "Post-Travel Report Needs Revision",
#         f"Please revise your post-travel report. Reason: {reason}",
#         "warning",
#         f"/requests/{request_id}/view"
#     )
    
#     # Send revision email to traveler
#     traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
#     if traveler and traveler.get("email"):
#         email_data = {
#             "traveler_name": get_user_full_name(traveler),
#             "ta_number": travel_request.get("ta_number", "N/A"),
#             "destination": travel_request.get("destination_city", "N/A"),
#             "rejected_by": final_rejector_name,
#             "reason": reason,
#             "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
#         }
#         background_tasks.add_task(
#             EmailService.send_post_travel_revision_notification,
#             traveler.get("email"),
#             email_data
#         )
#         print(f"   📧 Post-travel revision email queued for: {traveler.get('email')}")
    
#     return ApprovalResponse(
#         success=True,
#         message="Post-travel report rejected, traveler notified to revise",
#         new_status=TravelStatus.TA_ISSUED.value,
#     )


# # ============ List Pending Approvals ============

# @router.get("/pending", response_model=ListResponse)
# async def list_pending_approvals(
#     page: int = Query(1, ge=1),
#     per_page: int = Query(20, ge=1, le=100),
#     approval_type: Optional[str] = Query(None),  # supervisor, post_travel, finance
#     supervisor_id: Optional[str] = Query(None),  # Filter by supervisor
#     db = Depends(get_database),
# ):
#     """
#     List requests pending approval - NO AUTH
    
#     Pass supervisor_id to filter by specific supervisor's pending requests.
#     """
#     skip, limit = paginate_query(page, per_page)
    
#     # Build query
#     query = {}
    
#     if approval_type == "supervisor":
#         query["status"] = TravelStatus.PENDING_SUPERVISOR.value
#         if supervisor_id:
#             query["supervisor_id"] = supervisor_id
#     elif approval_type == "president":
#         query["status"] = TravelStatus.PENDING_PRESIDENT.value
#     elif approval_type == "post_travel":
#         query["status"] = TravelStatus.POST_TRAVEL_SUBMITTED.value
#         if supervisor_id:
#             query["supervisor_id"] = supervisor_id
#     elif approval_type == "finance":
#         query["status"] = TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value
#     else:
#         # Return all pending requests
#         query["status"] = {"$in": [
#             TravelStatus.PENDING_SUPERVISOR.value,
#             TravelStatus.PENDING_PRESIDENT.value,
#             TravelStatus.POST_TRAVEL_SUBMITTED.value,
#             TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
#         ]}
    
#     # Get total count
#     total = await db.travel_requests.count_documents(query)
    
#     # Get requests
#     cursor = db.travel_requests.find(query).sort("submitted_at", -1).skip(skip).limit(limit)
    
#     requests = []
#     async for req in cursor:
#         req["_id"] = str(req["_id"])
#         requests.append(req)
    
#     return ListResponse(
#         success=True,
#         message="Pending approvals retrieved",
#         data=requests,
#         total=total,
#         page=page,
#         per_page=per_page,
#     )


# @router.get("/all", response_model=ListResponse)
# async def list_all_approvals(
#     page: int = Query(1, ge=1),
#     per_page: int = Query(20, ge=1, le=100),
#     status_filter: Optional[str] = Query(None),
#     db = Depends(get_database),
# ):
#     """List all travel requests regardless of status - NO AUTH"""
#     skip, limit = paginate_query(page, per_page)
    
#     query = {}
#     if status_filter:
#         query["status"] = status_filter.upper()
    
#     total = await db.travel_requests.count_documents(query)
#     cursor = db.travel_requests.find(query).sort("created_at", -1).skip(skip).limit(limit)
    
#     requests = []
#     async for req in cursor:
#         req["_id"] = str(req["_id"])
#         requests.append(req)
    
#     return ListResponse(
#         success=True,
#         message="Requests retrieved",
#         data=requests,
#         total=total,
#         page=page,
#         per_page=per_page,
#     )

"""
Approvals Router
Handles: Supervisor approval, President approval, Post-travel approvals

NOTE: Authentication DISABLED for testing. Re-enable for production!
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Form, Query
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId

from dependencies.database import get_database
# Auth imports disabled for testing
# from dependencies.auth import (
#     get_current_user,
#     get_supervisor_user,
#     get_finance_user,
#     get_president_user,
#     can_approve_request,
# )
from models.request import (
    TravelStatus,
    ApprovalAction,
    ApprovalResponse,
)
from models.response import ListResponse, DataResponse
from utils.helpers import (
    generate_ta_number_async,
    safe_object_id,
    get_user_full_name,
    paginate_query,
    build_sort_query,
    utc_now,
)
from services.notification_service import NotificationService
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
):
    """Send in-app notification"""
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


# ============ Supervisor Approval Routes ============

@router.post("/{request_id}/approve", response_model=ApprovalResponse)
async def approve_request(
    request_id: str,
    background_tasks: BackgroundTasks,
    comments: Optional[str] = Form(None),
    approver_name: Optional[str] = Form(None),  # Optional signature name
    approver_id: Optional[str] = Form(None),  # Optional - not required from frontend
    db = Depends(get_database),
):
    """
    Approve a travel request.
    Supervisor approval for domestic, President approval for international.
    
    Frontend only needs to send: comments (optional), approver_name (optional)
    """
    print(f"\n{'='*60}")
    print(f"✅ POST /approvals/{request_id}/approve called")
    print(f"   approver_name: {approver_name}")
    print(f"   comments: {comments}")
    print(f"{'='*60}")
    
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    current_status = travel_request.get("status")
    
    # Get approver info - use provided name or "System Approved"
    approver = None
    user_id = "system"
    final_approver_name = approver_name or "System Approved"
    
    # Only try to fetch user if approver_id is valid
    if approver_id and safe_object_id(approver_id):
        approver_obj_id = safe_object_id(approver_id)
        if approver_obj_id:
            approver = await db.users.find_one({"_id": approver_obj_id})
            user_id = approver_id
            if approver:
                final_approver_name = get_user_full_name(approver)
    
    # Validate current status allows approval
    if current_status == TravelStatus.PENDING_SUPERVISOR.value:
        new_status = TravelStatus.SUPERVISOR_APPROVED.value
    elif current_status == TravelStatus.PENDING_PRESIDENT.value:
        new_status = TravelStatus.SUPERVISOR_APPROVED.value
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request cannot be approved in current status: {current_status}"
        )
    
    # Generate TA number if moving to approved
    ta_number = None
    if new_status == TravelStatus.SUPERVISOR_APPROVED.value:
        ta_number = await generate_ta_number_async(db)
        new_status = TravelStatus.TA_ISSUED.value
    
    # Update request
    update_data = {
        "status": new_status,
        "updated_at": utc_now(),
        "supervisor_approved_at": utc_now(),
        "supervisor_approved_by": user_id,
        "approval_comments": comments,
    }
    
    if ta_number:
        update_data["ta_number"] = ta_number
    
    if current_status == TravelStatus.PENDING_PRESIDENT.value:
        update_data["president_approved_at"] = utc_now()
        update_data["president_approved_by"] = user_id
    
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": update_data}
    )
    
    # Add to approval history
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$push": {
                "approval_history": {
                    "action": "approved",
                    "by_user_id": user_id,
                    "by_user_name": final_approver_name,
                    "comments": comments,
                    "timestamp": utc_now(),
                    "previous_status": current_status,
                    "new_status": new_status,
                }
            }
        }
    )
    
    # Notify traveler
    traveler_id = str(travel_request.get("traveler_id"))
    destination = travel_request.get("destination_city", "destination")
    
    notification_msg = f"Your travel request to {destination} has been approved"
    if ta_number:
        notification_msg += f". TA Number: {ta_number}"
    
    background_tasks.add_task(
        send_notification_with_sms,
        db,
        traveler_id,
        "Travel Request Approved",
        notification_msg,
        "success",
        f"/requests/{request_id}/view"
    )
    
    # Send approval email to traveler
    traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
    if traveler and traveler.get("email"):
        # Check if this is President approval (international travel)
        is_president_approval = current_status == TravelStatus.PENDING_PRESIDENT.value
        
        email_data = {
            "traveler_name": get_user_full_name(traveler),
            "ta_number": ta_number or "N/A",
            "destination": destination,
            "country": travel_request.get("destination_country", "N/A"),
            "departure_date": str(travel_request.get("departure_date", "N/A")),
            "return_date": str(travel_request.get("return_date", "N/A")),
            "approved_by": final_approver_name,
            "approved_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
        }
        
        if is_president_approval:
            # Use President approval template for international travel
            background_tasks.add_task(
                EmailService.send_president_approval_notification,
                traveler.get("email"),
                email_data
            )
            print(f"   📧 President approval email queued for: {traveler.get('email')}")
        else:
            # Use regular supervisor approval template
            background_tasks.add_task(
                EmailService.send_approval_notification,
                traveler.get("email"),
                email_data
            )
            print(f"   📧 Supervisor approval email queued for: {traveler.get('email')}")
    
    print(f"   ✅ Approved! New status: {new_status}, TA: {ta_number}")
    
    return ApprovalResponse(
        success=True,
        message="Travel request approved successfully",
        new_status=new_status,
        ta_number=ta_number,
    )


@router.post("/{request_id}/reject", response_model=ApprovalResponse)
async def reject_request(
    request_id: str,
    background_tasks: BackgroundTasks,
    reason: str = Form(..., min_length=10),
    rejector_name: Optional[str] = Form(None),  # Optional signature name
    rejector_id: Optional[str] = Form(None),  # Optional - not required from frontend
    db = Depends(get_database),
):
    """
    Reject a travel request.
    
    Frontend only needs to send: reason (required), rejector_name (optional)
    """
    print(f"\n{'='*60}")
    print(f"❌ POST /approvals/{request_id}/reject called")
    print(f"   rejector_name: {rejector_name}")
    print(f"   reason: {reason}")
    print(f"{'='*60}")
    
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    current_status = travel_request.get("status")
    
    # Get rejector info - use provided name or "System Rejected"
    rejector = None
    user_id = "system"
    final_rejector_name = rejector_name or "System Rejected"
    
    # Only try to fetch user if rejector_id is valid
    if rejector_id and safe_object_id(rejector_id):
        rejector_obj_id = safe_object_id(rejector_id)
        if rejector_obj_id:
            rejector = await db.users.find_one({"_id": rejector_obj_id})
            user_id = rejector_id
            if rejector:
                final_rejector_name = get_user_full_name(rejector)
    
    # Validate rejection permission
    allowed_statuses = [
        TravelStatus.PENDING_SUPERVISOR.value,
        TravelStatus.PENDING_PRESIDENT.value,
    ]
    
    if current_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request cannot be rejected in current status: {current_status}"
        )
    
    # Update request
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                "status": TravelStatus.REJECTED.value,
                "updated_at": utc_now(),
                "rejected_at": utc_now(),
                "rejected_by": user_id,
                "rejection_reason": reason,
            },
            "$push": {
                "approval_history": {
                    "action": "rejected",
                    "by_user_id": user_id,
                    "by_user_name": final_rejector_name,
                    "reason": reason,
                    "timestamp": utc_now(),
                    "previous_status": current_status,
                    "new_status": TravelStatus.REJECTED.value,
                }
            }
        }
    )
    
    # Notify traveler
    traveler_id = str(travel_request.get("traveler_id"))
    destination = travel_request.get("destination_city", "destination")
    
    background_tasks.add_task(
        send_notification_with_sms,
        db,
        traveler_id,
        "Travel Request Rejected",
        f"Your travel request to {destination} has been rejected. Reason: {reason}",
        "error",
        f"/requests/{request_id}/view"
    )
    
    # Send rejection email to traveler
    traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
    if traveler and traveler.get("email"):
        # Check if this is President rejection (international travel)
        is_president_rejection = current_status == TravelStatus.PENDING_PRESIDENT.value
        
        email_data = {
            "traveler_name": get_user_full_name(traveler),
            "destination": destination,
            "country": travel_request.get("destination_country", "N/A"),
            "departure_date": str(travel_request.get("departure_date", "N/A")),
            "return_date": str(travel_request.get("return_date", "N/A")),
            "rejected_by": final_rejector_name,
            "reason": reason,
            "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
        }
        
        if is_president_rejection:
            # Use President rejection template for international travel
            background_tasks.add_task(
                EmailService.send_president_rejection_notification,
                traveler.get("email"),
                email_data
            )
            print(f"   📧 President rejection email queued for: {traveler.get('email')}")
        else:
            # Use regular supervisor rejection template
            background_tasks.add_task(
                EmailService.send_rejection_notification,
                traveler.get("email"),
                email_data
            )
            print(f"   📧 Supervisor rejection email queued for: {traveler.get('email')}")
    
    print(f"   ❌ Rejected! Reason: {reason}")
    
    return ApprovalResponse(
        success=True,
        message="Travel request rejected",
        new_status=TravelStatus.REJECTED.value,
    )


# ============ Post-Travel Approval Routes ============

@router.post("/{request_id}/post-travel/supervisor-approve", response_model=ApprovalResponse)
async def supervisor_approve_post_travel(
    request_id: str,
    background_tasks: BackgroundTasks,
    comments: Optional[str] = Form(None),
    approver_name: Optional[str] = Form(None),  # Optional signature name
    approver_id: Optional[str] = Form(None),  # Optional - not required from frontend
    db = Depends(get_database),
):
    """
    Supervisor approval for post-travel report.
    Frontend only needs to send: comments (optional), approver_name (optional)
    """
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    current_status = travel_request.get("status")
    
    # Get approver info - use provided name or "System Approved"
    approver = None
    user_id = "system"
    final_approver_name = approver_name or "System Approved"
    
    # Only try to fetch user if approver_id is valid
    if approver_id and safe_object_id(approver_id):
        approver_obj_id = safe_object_id(approver_id)
        if approver_obj_id:
            approver = await db.users.find_one({"_id": approver_obj_id})
            user_id = approver_id
            if approver:
                final_approver_name = get_user_full_name(approver)
    
    if current_status != TravelStatus.POST_TRAVEL_SUBMITTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post-travel report not submitted or already reviewed"
        )
    
    # Update status
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                "status": TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
                "updated_at": utc_now(),
                "post_travel_supervisor_approved_at": utc_now(),
                "post_travel_supervisor_approved_by": user_id,
                "post_travel_supervisor_comments": comments,
            },
            "$push": {
                "approval_history": {
                    "action": "post_travel_supervisor_approved",
                    "by_user_id": user_id,
                    "by_user_name": final_approver_name,
                    "comments": comments,
                    "timestamp": utc_now(),
                }
            }
        }
    )
    
    # Notify finance team
    finance_users = await db.users.find({"role": "FINANCE"}).to_list(100)
    for finance_user in finance_users:
        background_tasks.add_task(
            send_notification_with_sms,
            db,
            str(finance_user["_id"]),
            "Post-Travel Report Ready for Finance Review",
            f"Post-travel report for {travel_request.get('traveler_name')} needs finance approval",
            "warning",
            f"/requests/{request_id}/view"
        )
        
        # Send email to finance team
        if finance_user.get("email"):
            post_travel_data = travel_request.get("post_travel_report", {})
            email_data = {
                "traveler_name": travel_request.get("traveler_name", "N/A"),
                "ta_number": travel_request.get("ta_number", "N/A"),
                "destination": travel_request.get("destination_city", "N/A"),
                "departure_date": str(travel_request.get("departure_date", "N/A")),
                "return_date": str(travel_request.get("return_date", "N/A")),
                "total_expenses": f"{float(post_travel_data.get('total_spent', 0)):.2f}",
                "travel_advance": f"{float(travel_request.get('travel_advance', 0)):.2f}",
                "supervisor_approved_by": approver_name,
                "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
            }
            background_tasks.add_task(
                EmailService.send_post_travel_to_finance_notification,
                finance_user.get("email"),
                email_data
            )
            print(f"   📧 Finance notification email queued for: {finance_user.get('email')}")
    
    return ApprovalResponse(
        success=True,
        message="Post-travel report approved by supervisor, sent to finance",
        new_status=TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
    )


@router.post("/{request_id}/post-travel/finance-approve", response_model=ApprovalResponse)
async def finance_approve_post_travel(
    request_id: str,
    background_tasks: BackgroundTasks,
    comments: Optional[str] = Form(None),
    approved_amount: Optional[float] = Form(None),
    approver_name: Optional[str] = Form(None),  # Optional signature name
    approver_id: Optional[str] = Form(None),  # Optional - not required from frontend
    db = Depends(get_database),
):
    """
    Finance approval for post-travel report - finalizes reimbursement.
    Frontend only needs to send: comments (optional), approved_amount (optional), approver_name (optional)
    """
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    current_status = travel_request.get("status")
    
    # Get approver info - use provided name or "System Approved"
    approver = None
    user_id = "system"
    final_approver_name = approver_name or "System Approved"
    
    # Only try to fetch user if approver_id is valid
    if approver_id and safe_object_id(approver_id):
        approver_obj_id = safe_object_id(approver_id)
        if approver_obj_id:
            approver = await db.users.find_one({"_id": approver_obj_id})
            user_id = approver_id
            if approver:
                final_approver_name = get_user_full_name(approver)
    
    if current_status != TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post-travel report must be supervisor-approved first"
        )
    
    # Calculate settlement
    travel_advance = float(travel_request.get("travel_advance", 0))
    additional_funds = float(travel_request.get("additional_funds", 0))
    total_given = travel_advance + additional_funds
    
    post_travel = travel_request.get("post_travel_report", {})
    total_spent = float(post_travel.get("total_spent", 0))
    
    if approved_amount is not None:
        total_spent = approved_amount
    
    settlement = total_given - total_spent
    settlement_type = "TRAVELER_OWES" if settlement > 0 else "UNIVERSITY_OWES" if settlement < 0 else "BALANCED"
    
    # Update status to completed
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                "status": TravelStatus.COMPLETED.value,
                "updated_at": utc_now(),
                "completed_at": utc_now(),
                "finance_approved_at": utc_now(),
                "finance_approved_by": user_id,
                "finance_comments": comments,
                "final_approved_amount": total_spent,
                "settlement": {
                    "total_given": total_given,
                    "total_spent": total_spent,
                    "settlement_amount": abs(settlement),
                    "settlement_type": settlement_type,
                    "calculated_at": utc_now(),
                }
            },
            "$push": {
                "approval_history": {
                    "action": "finance_approved",
                    "by_user_id": user_id,
                    "by_user_name": final_approver_name,
                    "comments": comments,
                    "approved_amount": total_spent,
                    "timestamp": utc_now(),
                }
            }
        }
    )
    
    # Notify traveler
    traveler_id = str(travel_request.get("traveler_id"))
    settlement_msg = f"Amount: ${abs(settlement):.2f}"
    if settlement_type == "TRAVELER_OWES":
        settlement_msg = f"Please return ${abs(settlement):.2f} to the university"
    elif settlement_type == "UNIVERSITY_OWES":
        settlement_msg = f"You will receive ${abs(settlement):.2f} reimbursement"
    
    background_tasks.add_task(
        send_notification_with_sms,
        db,
        traveler_id,
        "Travel Request Completed",
        f"Your travel request has been finalized. {settlement_msg}",
        "success",
        f"/requests/{request_id}/view"
    )
    
    # Send finance approval email to traveler
    traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
    if traveler and traveler.get("email"):
        email_data = {
            "traveler_name": get_user_full_name(traveler),
            "ta_number": travel_request.get("ta_number", "N/A"),
            "destination": travel_request.get("destination_city", "N/A"),
            "total_advance": f"{total_given:.2f}",
            "total_expenses": f"{total_spent:.2f}",
            "settlement_type": settlement_type,
            "settlement_amount": f"{abs(settlement):.2f}",
            "approved_by": final_approver_name,
            "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
        }
        background_tasks.add_task(
            EmailService.send_finance_approval_notification,
            traveler.get("email"),
            email_data
        )
        print(f"   📧 Finance approval email queued for: {traveler.get('email')}")
    
    return ApprovalResponse(
        success=True,
        message=f"Post-travel approved. Settlement: {settlement_type}",
        new_status=TravelStatus.COMPLETED.value,
    )


@router.post("/{request_id}/post-travel/reject", response_model=ApprovalResponse)
async def reject_post_travel(
    request_id: str,
    background_tasks: BackgroundTasks,
    reason: str = Form(..., min_length=10),
    rejector_name: Optional[str] = Form(None),  # Optional signature name
    rejector_id: Optional[str] = Form(None),  # Optional - not required from frontend
    db = Depends(get_database),
):
    """
    Reject post-travel report and request revisions.
    Frontend only needs to send: reason (required), rejector_name (optional)
    """
    travel_request = await get_request_by_id(db, request_id)
    
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    current_status = travel_request.get("status")
    
    # Get rejector info - use provided name or "System Rejected"
    rejector = None
    user_id = "system"
    final_rejector_name = rejector_name or "System Rejected"
    
    # Only try to fetch user if rejector_id is valid
    if rejector_id and safe_object_id(rejector_id):
        rejector_obj_id = safe_object_id(rejector_id)
        if rejector_obj_id:
            rejector = await db.users.find_one({"_id": rejector_obj_id})
            user_id = rejector_id
            if rejector:
                final_rejector_name = get_user_full_name(rejector)
    
    allowed_statuses = [
        TravelStatus.POST_TRAVEL_SUBMITTED.value,
        TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
    ]
    
    if current_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No post-travel report to reject"
        )
    
    # Revert to TA_ISSUED to allow resubmission
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                "status": TravelStatus.TA_ISSUED.value,
                "updated_at": utc_now(),
                "post_travel_rejected_at": utc_now(),
                "post_travel_rejected_by": user_id,
                "post_travel_rejection_reason": reason,
            },
            "$push": {
                "approval_history": {
                    "action": "post_travel_rejected",
                    "by_user_id": user_id,
                    "by_user_name": final_rejector_name,
                    "reason": reason,
                    "timestamp": utc_now(),
                }
            }
        }
    )
    
    # Notify traveler
    traveler_id = str(travel_request.get("traveler_id"))
    
    background_tasks.add_task(
        send_notification_with_sms,
        db,
        traveler_id,
        "Post-Travel Report Needs Revision",
        f"Please revise your post-travel report. Reason: {reason}",
        "warning",
        f"/requests/{request_id}/view"
    )
    
    # Send revision email to traveler
    traveler = await db.users.find_one({"_id": ObjectId(traveler_id)}) if ObjectId.is_valid(traveler_id) else None
    if traveler and traveler.get("email"):
        email_data = {
            "traveler_name": get_user_full_name(traveler),
            "ta_number": travel_request.get("ta_number", "N/A"),
            "destination": travel_request.get("destination_city", "N/A"),
            "rejected_by": final_rejector_name,
            "reason": reason,
            "link": f"{EmailService.APP_BASE_URL}/requests/{request_id}/view"
        }
        background_tasks.add_task(
            EmailService.send_post_travel_revision_notification,
            traveler.get("email"),
            email_data
        )
        print(f"   📧 Post-travel revision email queued for: {traveler.get('email')}")
    
    return ApprovalResponse(
        success=True,
        message="Post-travel report rejected, traveler notified to revise",
        new_status=TravelStatus.TA_ISSUED.value,
    )


# ============ List Pending Approvals ============

@router.get("/pending", response_model=ListResponse)
async def list_pending_approvals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    approval_type: Optional[str] = Query(None),  # supervisor, post_travel, finance
    supervisor_id: Optional[str] = Query(None),  # Filter by supervisor
    db = Depends(get_database),
):
    """
    List requests pending approval - NO AUTH
    
    Pass supervisor_id to filter by specific supervisor's pending requests.
    """
    skip, limit = paginate_query(page, per_page)
    
    # Build query
    query = {}
    
    if approval_type == "supervisor":
        query["status"] = TravelStatus.PENDING_SUPERVISOR.value
        if supervisor_id:
            query["supervisor_id"] = supervisor_id
    elif approval_type == "president":
        query["status"] = TravelStatus.PENDING_PRESIDENT.value
    elif approval_type == "post_travel":
        query["status"] = TravelStatus.POST_TRAVEL_SUBMITTED.value
        if supervisor_id:
            query["supervisor_id"] = supervisor_id
    elif approval_type == "finance":
        query["status"] = TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value
    else:
        # Return all pending requests
        query["status"] = {"$in": [
            TravelStatus.PENDING_SUPERVISOR.value,
            TravelStatus.PENDING_PRESIDENT.value,
            TravelStatus.POST_TRAVEL_SUBMITTED.value,
            TravelStatus.POST_TRAVEL_SUPERVISOR_APPROVED.value,
        ]}
    
    # Get total count
    total = await db.travel_requests.count_documents(query)
    
    # Get requests
    cursor = db.travel_requests.find(query).sort("submitted_at", -1).skip(skip).limit(limit)
    
    requests = []
    async for req in cursor:
        req["_id"] = str(req["_id"])
        requests.append(req)
    
    return ListResponse(
        success=True,
        message="Pending approvals retrieved",
        data=requests,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/all", response_model=ListResponse)
async def list_all_approvals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    db = Depends(get_database),
):
    """List all travel requests regardless of status - NO AUTH"""
    skip, limit = paginate_query(page, per_page)
    
    query = {}
    if status_filter:
        query["status"] = status_filter.upper()
    
    total = await db.travel_requests.count_documents(query)
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