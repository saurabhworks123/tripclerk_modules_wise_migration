"""
PDF Service
Handles PDF generation for reports
"""

from typing import Dict, Any, Optional
from datetime import datetime
from io import BytesIO

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFService:
    """Service for generating PDF reports"""
    
    # Styles
    HEADER_COLOR = colors.HexColor("#413178")
    
    @classmethod
    def _get_styles(cls):
        """Get custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            textColor=cls.HEADER_COLOR,
            spaceAfter=20,
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=cls.HEADER_COLOR,
            spaceBefore=15,
            spaceAfter=10,
        ))
        
        styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
        ))
        
        return styles
    
    @classmethod
    def generate_expense_report(cls, travel_request: Dict[str, Any]) -> bytes:
        """Generate expense report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = cls._get_styles()
        elements = []
        
        # Title
        elements.append(Paragraph("Expense Report", styles['CustomTitle']))
        elements.append(Spacer(1, 10))
        
        # Request Info
        ta_number = travel_request.get("ta_number", "N/A")
        traveler = travel_request.get("traveler_name", "N/A")
        destination = travel_request.get("destination", "N/A")
        
        info_data = [
            ["TA Number:", ta_number, "Traveler:", traveler],
            ["Destination:", destination, "Department:", travel_request.get("department", "N/A")],
            ["Travel Dates:", f"{travel_request.get('departure_date')} - {travel_request.get('return_date')}", "", ""],
        ]
        
        info_table = Table(info_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.gray),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Expenses Section
        elements.append(Paragraph("Expense Details", styles['SectionHeader']))
        
        expense_report = travel_request.get("expense_report", {})
        expenses = expense_report.get("expenses", [])
        
        if expenses:
            expense_data = [["Date", "Description", "Category", "Amount"]]
            for exp in expenses:
                expense_data.append([
                    exp.get("date", ""),
                    exp.get("description", ""),
                    exp.get("category", ""),
                    f"${exp.get('amount', 0):.2f}",
                ])
            
            # Total row
            total = expense_report.get("total_claimed", sum(e.get("amount", 0) for e in expenses))
            expense_data.append(["", "", "Total:", f"${total:.2f}"])
            
            expense_table = Table(expense_data, colWidths=[1.2*inch, 2.5*inch, 1.5*inch, 1.2*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), cls.HEADER_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.gray),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('TOPPADDING', (0, -1), (-1, -1), 10),
            ]))
            elements.append(expense_table)
        else:
            elements.append(Paragraph("No expenses recorded.", styles['Normal']))
        
        # Notes
        notes = expense_report.get("notes")
        if notes:
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("Notes:", styles['FieldLabel']))
            elements.append(Paragraph(notes, styles['Normal']))
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            ParagraphStyle('Footer', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
        ))
        
        doc.build(elements)
        return buffer.getvalue()
    
    @classmethod
    def generate_mileage_log(cls, travel_request: Dict[str, Any]) -> bytes:
        """Generate mileage log PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = cls._get_styles()
        elements = []
        
        # Title
        elements.append(Paragraph("Mileage Log", styles['CustomTitle']))
        elements.append(Spacer(1, 10))
        
        # Request Info
        ta_number = travel_request.get("ta_number", "N/A")
        traveler = travel_request.get("traveler_name", "N/A")
        
        info_data = [
            ["TA Number:", ta_number, "Traveler:", traveler],
        ]
        info_table = Table(info_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.gray),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Mileage Entries
        elements.append(Paragraph("Mileage Entries", styles['SectionHeader']))
        
        mileage_report = travel_request.get("mileage_report", {})
        entries = mileage_report.get("entries", [])
        
        if entries:
            mileage_data = [["Date", "From", "To", "Purpose", "Miles"]]
            for entry in entries:
                mileage_data.append([
                    entry.get("date", ""),
                    entry.get("from_location", ""),
                    entry.get("to_location", ""),
                    entry.get("purpose", ""),
                    f"{entry.get('miles', 0):.1f}",
                ])
            
            # Totals
            total_miles = mileage_report.get("total_miles", sum(e.get("miles", 0) for e in entries))
            rate = mileage_report.get("rate_per_mile", 0.67)
            total_reimbursement = mileage_report.get("total_reimbursement", total_miles * rate)
            
            mileage_data.append(["", "", "", "Total Miles:", f"{total_miles:.1f}"])
            mileage_data.append(["", "", "", f"Rate (${rate}/mile):", f"${total_reimbursement:.2f}"])
            
            mileage_table = Table(mileage_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.8*inch, 0.8*inch])
            mileage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), cls.HEADER_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -3), 0.5, colors.gray),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(mileage_table)
        else:
            elements.append(Paragraph("No mileage entries recorded.", styles['Normal']))
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            ParagraphStyle('Footer', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
        ))
        
        doc.build(elements)
        return buffer.getvalue()
    
    @classmethod
    def generate_trip_report(cls, travel_request: Dict[str, Any]) -> bytes:
        """Generate trip report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = cls._get_styles()
        elements = []
        
        # Title
        elements.append(Paragraph("Trip Report", styles['CustomTitle']))
        elements.append(Spacer(1, 10))
        
        # Request Info
        ta_number = travel_request.get("ta_number", "N/A")
        traveler = travel_request.get("traveler_name", "N/A")
        destination = travel_request.get("destination", "N/A")
        
        info_data = [
            ["TA Number:", ta_number, "Traveler:", traveler],
            ["Destination:", destination, "Dates:", f"{travel_request.get('departure_date')} - {travel_request.get('return_date')}"],
        ]
        info_table = Table(info_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.gray),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Trip Report Content
        trip_report = travel_request.get("trip_report", {})
        
        # Summary
        elements.append(Paragraph("Trip Summary", styles['SectionHeader']))
        elements.append(Paragraph(trip_report.get("summary", "No summary provided."), styles['Normal']))
        elements.append(Spacer(1, 10))
        
        # Objectives
        objectives_met = trip_report.get("objectives_met", False)
        status_text = "✓ Objectives Met" if objectives_met else "✗ Objectives Not Met"
        status_color = colors.green if objectives_met else colors.red
        elements.append(Paragraph(status_text, ParagraphStyle('Status', fontSize=12, textColor=status_color)))
        elements.append(Spacer(1, 10))
        
        # Outcomes
        elements.append(Paragraph("Outcomes", styles['SectionHeader']))
        elements.append(Paragraph(trip_report.get("outcomes", "No outcomes documented."), styles['Normal']))
        
        # Recommendations
        recommendations = trip_report.get("recommendations")
        if recommendations:
            elements.append(Paragraph("Recommendations", styles['SectionHeader']))
            elements.append(Paragraph(recommendations, styles['Normal']))
        
        # Follow-up Actions
        follow_up = trip_report.get("follow_up_actions")
        if follow_up:
            elements.append(Paragraph("Follow-up Actions", styles['SectionHeader']))
            elements.append(Paragraph(follow_up, styles['Normal']))
        
        # Footer
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            ParagraphStyle('Footer', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
        ))
        
        doc.build(elements)
        return buffer.getvalue()
    
    @classmethod
    def generate_complete_package(cls, travel_request: Dict[str, Any]) -> bytes:
        """Generate complete travel package PDF with all reports"""
        from PyPDF2 import PdfMerger
        
        merger = PdfMerger()
        
        # Add expense report
        if travel_request.get("expense_report"):
            expense_pdf = BytesIO(cls.generate_expense_report(travel_request))
            merger.append(expense_pdf)
        
        # Add mileage log
        if travel_request.get("mileage_report"):
            mileage_pdf = BytesIO(cls.generate_mileage_log(travel_request))
            merger.append(mileage_pdf)
        
        # Add trip report
        if travel_request.get("trip_report"):
            trip_pdf = BytesIO(cls.generate_trip_report(travel_request))
            merger.append(trip_pdf)
        
        # Output merged PDF
        output = BytesIO()
        merger.write(output)
        merger.close()
        
        return output.getvalue()
