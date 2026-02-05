"""
Email Service
Handles email notifications for NTU Travel Management System
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from string import Template
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class EmailService:
    """Service for sending email notifications"""
    
    # Configuration from environment
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_ADDRESS = os.getenv("MAIL_USERNAME", os.getenv("EMAIL_ADDRESS", ""))
    EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))
    FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_ADDRESS)
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
    
    @classmethod
    def _get_smtp_connection(cls):
        """Get SMTP connection"""
        server = smtplib.SMTP(cls.SMTP_SERVER, cls.SMTP_PORT)
        server.starttls()
        server.login(cls.EMAIL_ADDRESS, cls.EMAIL_PASSWORD)
        return server
    
    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not cls.EMAIL_ADDRESS or not cls.EMAIL_PASSWORD:
            print(f"⚠️ [EMAIL] SMTP credentials not configured. Would send to {to_email}: {subject}")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = cls.FROM_EMAIL
            msg["To"] = to_email
            
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))
            
            with smtplib.SMTP(cls.SMTP_SERVER, cls.SMTP_PORT) as server:
                server.starttls()
                server.login(cls.EMAIL_ADDRESS, cls.EMAIL_PASSWORD)
                server.sendmail(cls.FROM_EMAIL, to_email, msg.as_string())
            
            print(f"✅ [EMAIL] Sent to {to_email}: {subject}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ [EMAIL] SMTP Authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ [EMAIL] SMTP Error: {e}")
            return False
        except Exception as e:
            print(f"❌ [EMAIL] Error sending to {to_email}: {e}")
            return False
    
    @classmethod
    def _get_email_header(cls) -> str:
        """Get common email header HTML"""
        return """
        <div style="text-align: center; padding: 20px; background: #413178; border-radius: 5px 5px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">NTU Travel Management</h1>
            <p style="color: #e8e4f0; margin: 5px 0 0 0; font-size: 14px;">Navajo Technical University</p>
        </div>
        """
    
    @classmethod
    def _get_email_footer(cls) -> str:
        """Get common email footer HTML"""
        return """
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px; border-top: 1px solid #ddd;">
            <p style="margin: 5px 0;">This is an automated message from the NTU Travel Management System.</p>
            <p style="margin: 5px 0;">© 2025 Navajo Technical University</p>
        </div>
        """
    
    # ============================================================
    # TRAVEL REQUEST SUBMISSION - Notify Supervisor
    # ============================================================
    
    @classmethod
    def send_new_request_to_supervisor(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send notification to supervisor about new pending travel request"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #413178; margin-top: 0;">🔔 New Travel Request Pending Approval</h2>
                    <p>Hello ${supervisor_name},</p>
                    <p>A new travel request has been submitted and requires your approval:</p>
                    
                    <div style="background: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p style="margin: 8px 0;"><strong>Traveler:</strong> ${traveler_name}</p>
                        <p style="margin: 8px 0;"><strong>Employee ID:</strong> ${employee_id}</p>
                        <p style="margin: 8px 0;"><strong>Department:</strong> ${department}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Travel Dates:</strong> ${departure_date} - ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Purpose:</strong> ${purpose}</p>
                        <p style="margin: 8px 0;"><strong>Estimated Cost:</strong> $${estimated_cost}</p>
                    </div>
                    
                    <p>Please review and take action on this request.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #413178; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Review Request
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        return cls.send_email(to_email, "🔔 Action Required: New Travel Request Pending", html)
    
    # ============================================================
    # APPROVAL NOTIFICATION - Notify Traveler
    # ============================================================
    
    @classmethod
    def send_approval_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send approval notification email to traveler"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #28a745; margin-top: 0;">✅ Travel Request Approved!</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Great news! Your travel request has been <strong style="color: #28a745;">approved</strong>.</p>
                    
                    <div style="background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> <span style="font-size: 18px; color: #155724;">${ta_number}</span></p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Travel Dates:</strong> ${departure_date} - ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Approved By:</strong> ${approved_by}</p>
                        <p style="margin: 8px 0;"><strong>Approved On:</strong> ${approved_date}</p>
                    </div>
                    
                    <p>You may now proceed with your travel arrangements. Please remember to:</p>
                    <ul style="color: #666;">
                        <li>Keep all receipts for reimbursement</li>
                        <li>Submit your post-travel report within 10 days of return</li>
                        <li>Follow university travel policies</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #28a745; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            View Approval Details
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"✅ Travel Request Approved - TA#{ta_num}", html)
    
    # ============================================================
    # REJECTION NOTIFICATION - Notify Traveler
    # ============================================================
    
    @classmethod
    def send_rejection_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send rejection notification email to traveler"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #dc3545; margin-top: 0;">❌ Travel Request Not Approved</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Unfortunately, your travel request has been <strong style="color: #dc3545;">not approved</strong>.</p>
                    
                    <div style="background: #f8d7da; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Travel Dates:</strong> ${departure_date} - ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Rejected By:</strong> ${rejected_by}</p>
                        <p style="margin: 8px 0;"><strong>Reason:</strong></p>
                        <p style="margin: 8px 0; padding: 10px; background: #fff; border-radius: 3px;">${reason}</p>
                    </div>
                    
                    <p>If you have questions about this decision, please contact your supervisor or the Travel Office.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #6c757d; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            View Details
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        return cls.send_email(to_email, "❌ Travel Request Not Approved", html)
    
    # ============================================================
    # PENDING REMINDER - Notify Supervisor
    # ============================================================
    
    @classmethod
    def send_pending_reminder(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send reminder to supervisor about pending requests"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #ffc107; margin-top: 0;">⏳ Reminder: Pending Travel Request</h2>
                    <p>Hello ${supervisor_name},</p>
                    <p>This is a reminder that you have a travel request pending your approval:</p>
                    
                    <div style="background: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p style="margin: 8px 0;"><strong>Traveler:</strong> ${traveler_name}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Travel Dates:</strong> ${departure_date} - ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Submitted:</strong> ${submitted_date}</p>
                        <p style="margin: 8px 0;"><strong>Days Pending:</strong> <span style="color: #856404;">${days_pending} days</span></p>
                    </div>
                    
                    <p>Please review and take action on this request at your earliest convenience.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #ffc107; color: #212529; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Review Now
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        return cls.send_email(to_email, "⏳ Reminder: Travel Request Pending Your Approval", html)
    
    # ============================================================
    # POST-TRAVEL REPORT REMINDER - Notify Traveler
    # ============================================================
    
    @classmethod
    def send_post_travel_reminder(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send reminder to traveler about post-travel report submission"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #17a2b8; margin-top: 0;">📝 Post-Travel Report Reminder</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>This is a reminder to submit your post-travel report for your recent trip:</p>
                    
                    <div style="background: #d1ecf1; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #17a2b8;">
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> ${ta_number}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Return Date:</strong> ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Days Since Return:</strong> ${days_since_return} days</p>
                    </div>
                    
                    <p>Please submit your:</p>
                    <ul style="color: #666;">
                        <li>Expense Report with all receipts</li>
                        <li>Mileage Log (if applicable)</li>
                        <li>Trip Report</li>
                    </ul>
                    
                    <p style="color: #dc3545;"><strong>Note:</strong> Reports must be submitted within 10 days of return.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #17a2b8; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Submit Report
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"📝 Reminder: Submit Post-Travel Report - TA#{ta_num}", html)
    
    # ============================================================
    # POST-TRAVEL SUBMITTED - Notify Supervisor
    # ============================================================
    
    @classmethod
    def send_post_travel_submitted_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send notification to supervisor that post-travel report was submitted"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #413178; margin-top: 0;">📋 Post-Travel Report Submitted</h2>
                    <p>Hello ${supervisor_name},</p>
                    <p>A post-travel report has been submitted and requires your review:</p>
                    
                    <div style="background: #e8e4f0; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #413178;">
                        <p style="margin: 8px 0;"><strong>Traveler:</strong> ${traveler_name}</p>
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> ${ta_number}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Total Expenses:</strong> $${total_expenses}</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #413178; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Review Report
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"📋 Post-Travel Report Submitted - TA#{ta_num}", html)
    
    # ============================================================
    # TRAVEL COMPLETED - Final Notification to Traveler
    # ============================================================
    
    @classmethod
    def send_completion_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send final completion notification to traveler"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        settlement_type = data.get('settlement_type', 'BALANCED')
        
        if settlement_type == "TRAVELER_OWES":
            settlement_message = f"<p style='color: #dc3545;'><strong>Amount to Return:</strong> ${data.get('settlement_amount', '0.00')}</p>"
        elif settlement_type == "UNIVERSITY_OWES":
            settlement_message = f"<p style='color: #28a745;'><strong>Reimbursement Due:</strong> ${data.get('settlement_amount', '0.00')}</p>"
        else:
            settlement_message = "<p style='color: #28a745;'><strong>Settlement:</strong> Balanced - No additional payment required</p>"
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #28a745; margin-top: 0;">🎉 Travel Request Completed!</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Your travel request has been fully processed and closed.</p>
                    
                    <div style="background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> ${ta_number}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Total Advance:</strong> $${total_advance}</p>
                        <p style="margin: 8px 0;"><strong>Total Expenses:</strong> $${total_expenses}</p>
                        """ + settlement_message + """
                    </div>
                    
                    <p>Thank you for using the NTU Travel Management System!</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #28a745; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            View Summary
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"🎉 Travel Request Completed - TA#{ta_num}", html)
    
    # ============================================================
    # PRESIDENT APPROVAL - Notify Traveler (International Travel)
    # ============================================================
    
    @classmethod
    def send_president_approval_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send president approval notification for international travel"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #28a745; margin-top: 0;">✅ International Travel Approved by President!</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Great news! Your <strong>international travel request</strong> has been approved by the President.</p>
                    
                    <div style="background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> <span style="font-size: 18px; color: #155724;">${ta_number}</span></p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Country:</strong> ${country}</p>
                        <p style="margin: 8px 0;"><strong>Travel Dates:</strong> ${departure_date} - ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Approved By:</strong> ${approved_by} (President)</p>
                        <p style="margin: 8px 0;"><strong>Approved On:</strong> ${approved_date}</p>
                    </div>
                    
                    <p>You may now proceed with your international travel arrangements. Please ensure:</p>
                    <ul style="color: #666;">
                        <li>Valid passport and required visas</li>
                        <li>Travel insurance coverage</li>
                        <li>University travel policies compliance</li>
                        <li>Submit post-travel report within 10 days of return</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #28a745; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            View Approval Details
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"✅ International Travel Approved by President - TA#{ta_num}", html)
    
    # ============================================================
    # PRESIDENT REJECTION - Notify Traveler (International Travel)
    # ============================================================
    
    @classmethod
    def send_president_rejection_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send president rejection notification for international travel"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #dc3545; margin-top: 0;">❌ International Travel Not Approved</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Unfortunately, your <strong>international travel request</strong> has not been approved by the President.</p>
                    
                    <div style="background: #f8d7da; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Country:</strong> ${country}</p>
                        <p style="margin: 8px 0;"><strong>Travel Dates:</strong> ${departure_date} - ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Rejected By:</strong> ${rejected_by} (President)</p>
                        <p style="margin: 8px 0;"><strong>Reason:</strong></p>
                        <p style="margin: 8px 0; padding: 10px; background: #fff; border-radius: 3px;">${reason}</p>
                    </div>
                    
                    <p>If you have questions, please contact the President's Office or your supervisor.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #6c757d; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            View Details
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        return cls.send_email(to_email, "❌ International Travel Not Approved by President", html)
    
    # ============================================================
    # FINANCE APPROVAL - Notify Traveler (Final Settlement)
    # ============================================================
    
    @classmethod
    def send_finance_approval_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send finance approval notification with settlement details"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        settlement_type = data.get('settlement_type', 'BALANCED')
        
        if settlement_type == "TRAVELER_OWES":
            settlement_html = f"""
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0; color: #856404;"><strong>⚠️ Amount to Return:</strong> ${data.get('settlement_amount', '0.00')}</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #856404;">Please return this amount to the Finance Office.</p>
            </div>
            """
        elif settlement_type == "UNIVERSITY_OWES":
            settlement_html = f"""
            <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0; color: #155724;"><strong>💰 Reimbursement Due:</strong> ${data.get('settlement_amount', '0.00')}</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #155724;">This amount will be processed for reimbursement.</p>
            </div>
            """
        else:
            settlement_html = """
            <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0; color: #155724;"><strong>✅ Balanced:</strong> No additional payment required</p>
            </div>
            """
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #28a745; margin-top: 0;">💰 Finance Approved - Travel Completed!</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Your post-travel expenses have been reviewed and approved by Finance. Your travel request is now <strong style="color: #28a745;">completed</strong>.</p>
                    
                    <div style="background: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> ${ta_number}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Total Advance Given:</strong> $${total_advance}</p>
                        <p style="margin: 8px 0;"><strong>Total Expenses Approved:</strong> $${total_expenses}</p>
                        <p style="margin: 8px 0;"><strong>Approved By:</strong> ${approved_by} (Finance)</p>
                    </div>
                    
                    """ + settlement_html + """
                    
                    <p>Thank you for using the NTU Travel Management System!</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #28a745; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            View Final Summary
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"💰 Finance Approved - Travel Completed - TA#{ta_num}", html)
    
    # ============================================================
    # FINANCE REJECTION - Notify Traveler
    # ============================================================
    
    @classmethod
    def send_finance_rejection_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send finance rejection notification"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #dc3545; margin-top: 0;">❌ Post-Travel Report Rejected by Finance</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Your post-travel expense report has been <strong style="color: #dc3545;">rejected</strong> by Finance and requires revision.</p>
                    
                    <div style="background: #f8d7da; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> ${ta_number}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Rejected By:</strong> ${rejected_by} (Finance)</p>
                        <p style="margin: 8px 0;"><strong>Reason:</strong></p>
                        <p style="margin: 8px 0; padding: 10px; background: #fff; border-radius: 3px;">${reason}</p>
                    </div>
                    
                    <p>Please review the feedback and resubmit your post-travel report with the necessary corrections.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #dc3545; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Revise Report
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"❌ Post-Travel Report Rejected by Finance - TA#{ta_num}", html)
    
    # ============================================================
    # POST-TRAVEL SUPERVISOR APPROVAL - Notify Finance Team
    # ============================================================
    
    @classmethod
    def send_post_travel_to_finance_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send notification to finance that post-travel is ready for review"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #413178; margin-top: 0;">📊 Post-Travel Report Ready for Finance Review</h2>
                    <p>Hello Finance Team,</p>
                    <p>A post-travel expense report has been approved by the supervisor and is now ready for finance review:</p>
                    
                    <div style="background: #e8e4f0; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #413178;">
                        <p style="margin: 8px 0;"><strong>Traveler:</strong> ${traveler_name}</p>
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> ${ta_number}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Travel Dates:</strong> ${departure_date} - ${return_date}</p>
                        <p style="margin: 8px 0;"><strong>Total Expenses Claimed:</strong> $${total_expenses}</p>
                        <p style="margin: 8px 0;"><strong>Travel Advance Given:</strong> $${travel_advance}</p>
                        <p style="margin: 8px 0;"><strong>Supervisor Approved:</strong> ${supervisor_approved_by}</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #413178; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Review & Approve
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"📊 Action Required: Post-Travel Finance Review - TA#{ta_num}", html)
    
    # ============================================================
    # POST-TRAVEL REJECTION - Notify Traveler to Revise
    # ============================================================
    
    @classmethod
    def send_post_travel_revision_notification(
        cls,
        to_email: str,
        data: Dict[str, Any],
    ) -> bool:
        """Send notification to traveler that post-travel report needs revision"""
        header = cls._get_email_header()
        footer = cls._get_email_footer()
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff;">
                """ + header + """
                <div style="padding: 30px;">
                    <h2 style="color: #ffc107; margin-top: 0;">⚠️ Post-Travel Report Needs Revision</h2>
                    <p>Hello ${traveler_name},</p>
                    <p>Your post-travel report has been reviewed and requires some revisions before it can be approved.</p>
                    
                    <div style="background: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <p style="margin: 8px 0;"><strong>TA Number:</strong> ${ta_number}</p>
                        <p style="margin: 8px 0;"><strong>Destination:</strong> ${destination}</p>
                        <p style="margin: 8px 0;"><strong>Reviewed By:</strong> ${rejected_by}</p>
                        <p style="margin: 8px 0;"><strong>Revision Required:</strong></p>
                        <p style="margin: 8px 0; padding: 10px; background: #fff; border-radius: 3px;">${reason}</p>
                    </div>
                    
                    <p>Please make the necessary corrections and resubmit your post-travel report.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="${link}" style="background: #ffc107; color: #212529; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Revise Report
                        </a>
                    </div>
                </div>
                """ + footer + """
            </div>
        </body>
        </html>
        """
        
        html = Template(template).safe_substitute(data)
        ta_num = data.get('ta_number', 'N/A')
        return cls.send_email(to_email, f"⚠️ Post-Travel Report Needs Revision - TA#{ta_num}", html)