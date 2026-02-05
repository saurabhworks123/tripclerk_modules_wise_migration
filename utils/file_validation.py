"""
File Upload Validation Utilities
Ported from Flask validate_file_upload and allowed_file functions
"""

import os
import re
import uuid
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException, status
from werkzeug.utils import secure_filename

# Allowed extensions by category
ALLOWED_EXTENSIONS = {
    'documents': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'rtf', 'odt', 'ods'},
    'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
    'archives': {'zip'},
}

# All allowed extensions
ALL_ALLOWED = set().union(*ALLOWED_EXTENSIONS.values())

# Dangerous extensions that should NEVER be allowed
DANGEROUS_EXTENSIONS = {
    'exe', 'bat', 'cmd', 'sh', 'bash', 'ps1', 'psm1',  # Executables
    'php', 'php3', 'php4', 'php5', 'phtml', 'phar',    # PHP
    'asp', 'aspx', 'asa', 'asax', 'ascx', 'ashx',      # ASP
    'jsp', 'jspx', 'jsw', 'jsv', 'jspf',               # JSP
    'cgi', 'pl', 'py', 'pyc', 'pyo', 'pyd',            # Scripts
    'rb', 'erb', 'rhtml',                               # Ruby
    'htaccess', 'htpasswd',                             # Apache
    'dll', 'so', 'dylib',                              # Libraries
    'msi', 'scr', 'hta', 'cpl',                        # Windows
    'jar', 'war', 'ear',                               # Java archives
    'svg',  # Can contain JavaScript - remove if needed
}

# Maximum file size (10MB default)
MAX_FILE_SIZE = 10 * 1024 * 1024

# MIME type mapping for validation
SAFE_MIME_TYPES = {
    'application/pdf': ['pdf'],
    'application/msword': ['doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
    'application/vnd.ms-excel': ['xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
    'text/plain': ['txt'],
    'application/rtf': ['rtf'],
    'application/vnd.oasis.opendocument.text': ['odt'],
    'application/vnd.oasis.opendocument.spreadsheet': ['ods'],
    'image/png': ['png'],
    'image/jpeg': ['jpg', 'jpeg'],
    'image/gif': ['gif'],
    'image/bmp': ['bmp'],
    'image/webp': ['webp'],
    'application/zip': ['zip'],
}


def get_file_extension(filename: str) -> str:
    """Extract file extension, handling double extensions"""
    if not filename:
        return ""
    
    # Handle double extensions like .tar.gz
    parts = filename.rsplit('.', 2)
    if len(parts) >= 2:
        ext = parts[-1].lower()
        # Check for double dangerous extensions
        if len(parts) >= 3:
            double_ext = f"{parts[-2]}.{parts[-1]}".lower()
            if parts[-2].lower() in DANGEROUS_EXTENSIONS:
                return double_ext
        return ext
    return ""


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """
    Check if file has allowed extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions (default: ALL_ALLOWED)
    
    Returns:
        True if extension is allowed, False otherwise
    """
    if not filename:
        return False
    
    if allowed_extensions is None:
        allowed_extensions = ALL_ALLOWED
    
    ext = get_file_extension(filename)
    
    # Block dangerous extensions regardless of allowed list
    if ext in DANGEROUS_EXTENSIONS:
        return False
    
    return ext in allowed_extensions


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Use werkzeug's secure_filename
    safe_name = secure_filename(filename)
    
    # Additional sanitization
    # Remove any remaining path separators
    safe_name = safe_name.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    safe_name = safe_name.replace('\x00', '')
    
    # Limit length
    if len(safe_name) > 200:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:200 - len(ext)] + ext
    
    # Ensure filename is not empty after sanitization
    if not safe_name or safe_name == '.':
        safe_name = f"file_{uuid.uuid4().hex[:8]}"
    
    return safe_name


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving extension.
    
    Args:
        original_filename: Original filename
    
    Returns:
        Unique filename with UUID prefix
    """
    safe_name = sanitize_filename(original_filename)
    name, ext = os.path.splitext(safe_name)
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}_{name}{ext}"


async def validate_file_upload(
    file: UploadFile,
    allowed_extensions: set = None,
    max_size: int = MAX_FILE_SIZE,
    validate_mime: bool = True
) -> Tuple[bool, str]:
    """
    Comprehensive file upload validation.
    
    Args:
        file: FastAPI UploadFile object
        allowed_extensions: Set of allowed extensions
        max_size: Maximum file size in bytes
        validate_mime: Whether to validate MIME type
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file provided"
    
    filename = file.filename
    
    # Check extension
    if not allowed_file(filename, allowed_extensions):
        ext = get_file_extension(filename)
        return False, f"File type '.{ext}' is not allowed"
    
    # Check for dangerous double extensions
    ext = get_file_extension(filename)
    if '.' in filename[:-len(ext)-1] if ext else filename:
        parts = filename.rsplit('.', 2)
        if len(parts) >= 3 and parts[-2].lower() in DANGEROUS_EXTENSIONS:
            return False, f"Dangerous file type detected"
    
    # Check file size
    # Read file to get size (and rewind)
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Rewind for later use
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File too large. Maximum size is {max_mb:.1f}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Validate MIME type
    if validate_mime:
        content_type = file.content_type or mimetypes.guess_type(filename)[0]
        if content_type:
            ext = get_file_extension(filename)
            if content_type in SAFE_MIME_TYPES:
                allowed_exts = SAFE_MIME_TYPES[content_type]
                if ext not in allowed_exts:
                    return False, f"File extension doesn't match content type"
    
    return True, ""


async def validate_and_save_file(
    file: UploadFile,
    upload_dir: str,
    allowed_extensions: set = None,
    max_size: int = MAX_FILE_SIZE,
    preserve_filename: bool = False
) -> Tuple[bool, str, Optional[str]]:
    """
    Validate and save uploaded file.
    
    Args:
        file: FastAPI UploadFile object
        upload_dir: Directory to save file
        allowed_extensions: Set of allowed extensions
        max_size: Maximum file size in bytes
        preserve_filename: If True, use original filename; otherwise generate unique
    
    Returns:
        Tuple of (success, message/error, saved_filename or None)
    """
    # Validate
    is_valid, error = await validate_file_upload(file, allowed_extensions, max_size)
    if not is_valid:
        return False, error, None
    
    # Create upload directory if needed
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    if preserve_filename:
        filename = sanitize_filename(file.filename)
    else:
        filename = generate_unique_filename(file.filename)
    
    # Save file
    file_path = os.path.join(upload_dir, filename)
    
    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        return True, "File uploaded successfully", filename
    except Exception as e:
        return False, f"Failed to save file: {str(e)}", None


def delete_file(file_path: str) -> bool:
    """
    Safely delete a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def get_file_info(file_path: str) -> Optional[dict]:
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Dict with file info or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    stat = os.stat(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    
    return {
        'filename': os.path.basename(file_path),
        'size': stat.st_size,
        'mime_type': mime_type,
        'created_at': stat.st_ctime,
        'modified_at': stat.st_mtime,
    }
