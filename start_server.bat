@echo off
echo ========================================
echo NTU Travel Management System
echo Starting unified server on port 8000...
echo ========================================
echo.
echo API Docs: http://localhost:8000/docs
echo Endpoints:
echo   - Auth:      http://localhost:8000/auth
echo   - Requests:  http://localhost:8000/requests
echo   - Approvals: http://localhost:8000/approvals
echo   - Reports:   http://localhost:8000/reports
echo   - Documents: http://localhost:8000/documents
echo   - Admin:     http://localhost:8000/admin
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
