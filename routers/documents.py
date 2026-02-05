"""
Documents Router
Handles: File uploads, downloads, document management
Converted from Flask Blueprint routes.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import os
import io
import zipfile
import mimetypes

from dependencies.database import get_database, get_settings
from dependencies.auth import get_current_user, can_view_request
from models.response import DataResponse, BaseResponse, FileUploadResponse
from utils.file_validation import (
    validate_and_save_file,
    delete_file,
    get_file_info,
    ALLOWED_EXTENSIONS,
    sanitize_filename,
)
from utils.helpers import safe_object_id, utc_now

router = APIRouter()


# ============ Helper Functions ============

async def get_request_by_id(db, request_id: str) -> Optional[dict]:
    """Get travel request by ID"""
    obj_id = safe_object_id(request_id)
    if not obj_id:
        return None
    return await db.travel_requests.find_one({"_id": obj_id})


def get_file_path(request_id: str, filename: str, file_type: str = "requests") -> str:
    """Get full file path for a document"""
    settings = get_settings()
    
    if file_type == "requests":
        return os.path.join(settings.UPLOAD_FOLDER, "travel_requests", filename)
    elif file_type == "receipts":
        return os.path.join(settings.UPLOAD_FOLDER, "receipts", request_id, filename)
    elif file_type == "trip_reports":
        return os.path.join(settings.UPLOAD_FOLDER, "trip_reports", request_id, filename)
    else:
        return os.path.join(settings.UPLOAD_FOLDER, file_type, filename)


def find_document_file(request_id: str, filename: str) -> Optional[str]:
    """Find document file in possible locations"""
    settings = get_settings()
    
    # Possible locations
    paths = [
        os.path.join(settings.UPLOAD_FOLDER, "travel_requests", filename),
        os.path.join(settings.UPLOAD_FOLDER, "receipts", request_id, filename),
        os.path.join(settings.UPLOAD_FOLDER, "trip_reports", request_id, filename),
        os.path.join(settings.UPLOAD_FOLDER, filename),
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


# ============ Upload Routes ============

@router.post("/{request_id}/upload", response_model=FileUploadResponse)
async def upload_document(
    request_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),  # agenda, budget, registration, pov_insurance, receipt, other
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """Upload a document for a travel request"""
    settings = get_settings()
    
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    # Check permission
    is_owner = str(travel_request.get("traveler_id")) == current_user["_id"]
    is_admin = current_user.get("role") == "ADMIN"
    
    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to upload documents"
        )
    
    # Determine upload directory and allowed types
    if document_type == "receipt":
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, "receipts", request_id)
        allowed = set().union(ALLOWED_EXTENSIONS['documents'], ALLOWED_EXTENSIONS['images'])
    elif document_type in ["agenda", "budget", "registration", "pov_insurance"]:
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, "travel_requests")
        allowed = ALLOWED_EXTENSIONS['documents']
    else:  # other
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, "travel_requests")
        allowed = set().union(ALLOWED_EXTENSIONS['documents'], ALLOWED_EXTENSIONS['images'])
    
    # Validate and save file
    success, msg, filename = await validate_and_save_file(file, upload_dir, allowed)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Update request document
    if document_type in ["agenda", "budget", "registration", "pov_insurance"]:
        field_name = f"{document_type}_file"
        
        # Delete old file if exists
        old_file = travel_request.get(field_name)
        if old_file:
            old_path = os.path.join(upload_dir, old_file)
            delete_file(old_path)
        
        await db.travel_requests.update_one(
            {"_id": ObjectId(request_id)},
            {
                "$set": {
                    field_name: filename,
                    "updated_at": utc_now(),
                }
            }
        )
    else:  # other or receipt
        await db.travel_requests.update_one(
            {"_id": ObjectId(request_id)},
            {
                "$push": {"other_documents": filename},
                "$set": {"updated_at": utc_now()},
            }
        )
    
    file_info = get_file_info(os.path.join(upload_dir, filename))
    
    return FileUploadResponse(
        success=True,
        message="Document uploaded successfully",
        filename=filename,
        file_path=f"/documents/{request_id}/{filename}",
        file_size=file_info.get("size") if file_info else None,
        content_type=file_info.get("mime_type") if file_info else None,
    )


@router.post("/{request_id}/upload-multiple", response_model=DataResponse)
async def upload_multiple_documents(
    request_id: str,
    files: List[UploadFile] = File(...),
    document_type: str = Form("other"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """Upload multiple documents at once"""
    settings = get_settings()
    
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    # Check permission
    is_owner = str(travel_request.get("traveler_id")) == current_user["_id"]
    is_admin = current_user.get("role") == "ADMIN"
    
    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to upload documents"
        )
    
    # Determine upload directory
    if document_type == "receipt":
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, "receipts", request_id)
    else:
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, "travel_requests")
    
    allowed = set().union(ALLOWED_EXTENSIONS['documents'], ALLOWED_EXTENSIONS['images'])
    
    uploaded = []
    errors = []
    
    for file in files:
        if file and file.filename:
            success, msg, filename = await validate_and_save_file(file, upload_dir, allowed)
            if success:
                uploaded.append(filename)
            else:
                errors.append({"filename": file.filename, "error": msg})
    
    # Update request with uploaded files
    if uploaded:
        await db.travel_requests.update_one(
            {"_id": ObjectId(request_id)},
            {
                "$push": {"other_documents": {"$each": uploaded}},
                "$set": {"updated_at": utc_now()},
            }
        )
    
    return DataResponse(
        success=len(uploaded) > 0,
        message=f"Uploaded {len(uploaded)} files" + (f", {len(errors)} failed" if errors else ""),
        data={
            "uploaded": uploaded,
            "errors": errors,
        }
    )


# ============ Download Routes ============

@router.get("/{request_id}/{filename}")
async def download_document(
    request_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """Download a specific document"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    # Check permission
    if not can_view_request(current_user, travel_request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this document"
        )
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Find file
    file_path = find_document_file(request_id, safe_filename)
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Determine content type
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=content_type,
    )


@router.get("/{request_id}/view/{filename}")
async def view_document(
    request_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """View a document inline (for PDFs and images)"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    # Check permission
    if not can_view_request(current_user, travel_request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this document"
        )
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Find file
    file_path = find_document_file(request_id, safe_filename)
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Determine content type
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    
    # Return with inline disposition for viewing
    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=content_type,
        headers={"Content-Disposition": f"inline; filename={safe_filename}"}
    )


@router.get("/{request_id}/download-all")
async def download_all_documents(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """Download all documents as a ZIP file"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    # Check permission
    if not can_view_request(current_user, travel_request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download documents"
        )
    
    # Collect all document files
    documents = []
    
    # Main document fields
    for field in ["agenda_file", "budget_file", "registration_file", "pov_insurance_file"]:
        filename = travel_request.get(field)
        if filename:
            file_path = find_document_file(request_id, filename)
            if file_path:
                documents.append((filename, file_path))
    
    # Other documents
    for filename in travel_request.get("other_documents", []):
        file_path = find_document_file(request_id, filename)
        if file_path:
            documents.append((filename, file_path))
    
    # Receipts
    expense_report = travel_request.get("expense_report", {})
    for filename in expense_report.get("receipt_files", []):
        file_path = find_document_file(request_id, filename)
        if file_path:
            documents.append((f"receipts/{filename}", file_path))
    
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No documents found"
        )
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, path in documents:
            zip_file.write(path, name)
    
    zip_buffer.seek(0)
    
    ta_number = travel_request.get("ta_number", request_id)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=documents_{ta_number}.zip"
        }
    )


# ============ Delete Routes ============

@router.delete("/{request_id}/{filename}", response_model=BaseResponse)
async def delete_document(
    request_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """Delete a document from a travel request"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    # Check permission - only owner or admin can delete
    is_owner = str(travel_request.get("traveler_id")) == current_user["_id"]
    is_admin = current_user.get("role") == "ADMIN"
    
    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete documents"
        )
    
    # Can't delete documents after certain statuses
    protected_statuses = ["COMPLETED", "POST_TRAVEL_FINANCE_APPROVED"]
    if travel_request.get("status") in protected_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete documents from completed requests"
        )
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Find and delete file
    file_path = find_document_file(request_id, safe_filename)
    
    if file_path:
        delete_file(file_path)
    
    # Update database
    update_ops = {"$set": {"updated_at": utc_now()}}
    
    # Check which field contains this file
    for field in ["agenda_file", "budget_file", "registration_file", "pov_insurance_file"]:
        if travel_request.get(field) == safe_filename:
            update_ops["$set"][field] = None
            break
    else:
        # Check in other_documents array
        update_ops["$pull"] = {"other_documents": safe_filename}
    
    await db.travel_requests.update_one(
        {"_id": ObjectId(request_id)},
        update_ops
    )
    
    return BaseResponse(
        success=True,
        message="Document deleted successfully"
    )


# ============ List Documents ============

@router.get("/{request_id}/list", response_model=DataResponse)
async def list_documents(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database),
):
    """List all documents for a travel request"""
    travel_request = await get_request_by_id(db, request_id)
    if not travel_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel request not found"
        )
    
    # Check permission
    if not can_view_request(current_user, travel_request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view documents"
        )
    
    documents = []
    
    # Main document fields
    doc_fields = [
        ("agenda_file", "Agenda", True),
        ("budget_file", "Budget", False),
        ("registration_file", "Registration", False),
        ("pov_insurance_file", "POV Insurance", False),
    ]
    
    for field, label, required in doc_fields:
        filename = travel_request.get(field)
        if filename:
            file_path = find_document_file(request_id, filename)
            info = get_file_info(file_path) if file_path else None
            documents.append({
                "type": field.replace("_file", ""),
                "label": label,
                "filename": filename,
                "required": required,
                "exists": file_path is not None,
                "size": info.get("size") if info else None,
                "download_url": f"/documents/{request_id}/{filename}",
            })
        elif required:
            documents.append({
                "type": field.replace("_file", ""),
                "label": label,
                "filename": None,
                "required": required,
                "exists": False,
            })
    
    # Other documents
    for filename in travel_request.get("other_documents", []):
        file_path = find_document_file(request_id, filename)
        info = get_file_info(file_path) if file_path else None
        documents.append({
            "type": "other",
            "label": "Other Document",
            "filename": filename,
            "required": False,
            "exists": file_path is not None,
            "size": info.get("size") if info else None,
            "download_url": f"/documents/{request_id}/{filename}",
        })
    
    # Receipts
    expense_report = travel_request.get("expense_report", {})
    for filename in expense_report.get("receipt_files", []):
        file_path = find_document_file(request_id, filename)
        info = get_file_info(file_path) if file_path else None
        documents.append({
            "type": "receipt",
            "label": "Receipt",
            "filename": filename,
            "required": False,
            "exists": file_path is not None,
            "size": info.get("size") if info else None,
            "download_url": f"/documents/{request_id}/{filename}",
        })
    
    return DataResponse(
        success=True,
        message=f"Found {len(documents)} documents",
        data=documents
    )
