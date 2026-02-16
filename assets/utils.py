import qrcode
from io import BytesIO
from django.core.files import File
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.db.models import Q
from assets.models import Category, StatusOption, AssignmentHistory
from maintenance.models import MaintenanceLog, ActionTakenOption


def generate_qr_code(asset):
    """Generate QR code for an asset"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"Asset ID: {asset.asset_id}\nSerial: {asset.serial_number}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    asset.qr_code.save(
        f'qr_{asset.asset_id}.png',
        File(buffer),
        save=False
    )
    asset.save()


def export_assets_excel(assets):
    """Export comprehensive Excel workbook with 5 sheets, formulas, and dropdowns"""
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Get all data for dropdowns and formulas
    categories = Category.objects.all().order_by('name')
    statuses = StatusOption.objects.filter(is_active=True).order_by('name')
    action_taken_options = ActionTakenOption.objects.filter(is_active=True).order_by('name')
    
    # ========== SHEET 1: ASSET Inventory ==========
    ws_inventory = wb.create_sheet("ASSET Inventory", 0)
    
    # Headers
    headers_inventory = [
        'Asset_ID', 'Category item', 'Model/Description', 'Purchase Date',
        'Serial Number', 'Assigned to', 'Last Known User', 'Current Status', 'Admin Comments'
    ]
    ws_inventory.append(headers_inventory)
    
    # Style headers
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for cell in ws_inventory[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    
    # Data rows
    for asset in assets:
        purchase_date = asset.purchase_date.strftime('%d/%m/%Y') if asset.purchase_date else ''
        ws_inventory.append([
            asset.asset_id,
            asset.category.name if asset.category else '',
            asset.model_description,
            purchase_date,
            asset.serial_number,
            asset.assigned_to.username if asset.assigned_to else '',
            asset.last_known_user.username if asset.last_known_user else '',
            asset.status.name if asset.status else '',
            asset.admin_comments,
        ])
    
    # Add data validation (dropdowns) for Category (column B) - reference LISTS sheet
    if categories.exists():
        max_cat_row = len(categories) + 1
        dv_category = DataValidation(
            type="list",
            formula1=f'LISTS!$A$2:$A${max_cat_row}',
            allow_blank=True
        )
        dv_category.error = 'Please select from the dropdown list'
        dv_category.errorTitle = 'Invalid Entry'
        ws_inventory.add_data_validation(dv_category)
        dv_category.add(f'B2:B{ws_inventory.max_row + 1000}')  # Allow for future entries
    
    # Add data validation for Current Status (column H) - reference LISTS sheet
    if statuses.exists():
        max_status_row = len(statuses) + 1
        dv_status = DataValidation(
            type="list",
            formula1=f'LISTS!$B$2:$B${max_status_row}',
            allow_blank=True
        )
        dv_status.error = 'Please select from the dropdown list'
        dv_status.errorTitle = 'Invalid Entry'
        ws_inventory.add_data_validation(dv_status)
        dv_status.add(f'H2:H{ws_inventory.max_row + 1000}')  # Allow for future entries
    
    # Set column widths
    ws_inventory.column_dimensions['A'].width = 15  # Asset_ID
    ws_inventory.column_dimensions['B'].width = 20  # Category
    ws_inventory.column_dimensions['C'].width = 30  # Model/Description
    ws_inventory.column_dimensions['D'].width = 15  # Purchase Date
    ws_inventory.column_dimensions['E'].width = 20  # Serial Number
    ws_inventory.column_dimensions['F'].width = 20  # Assigned to
    ws_inventory.column_dimensions['G'].width = 20  # Last Known User
    ws_inventory.column_dimensions['H'].width = 20  # Current Status
    ws_inventory.column_dimensions['I'].width = 40  # Admin Comments
    
    # Freeze header row
    ws_inventory.freeze_panes = 'A2'
    
    # Add note about Asset_ID uniqueness (Excel can't enforce this, but we can add a comment)
    if ws_inventory.max_row > 1:
        note_cell = ws_inventory['A1']
        note_cell.comment = Comment("Each Asset_ID must be unique. Duplicate IDs will cause errors.", "System")
    
    # ========== SHEET 2: QUANTITIES ==========
    ws_quantities = wb.create_sheet("QUANTITIES", 1)
    
    headers_quantities = ['Asset Category', 'In Use', 'Available', 'Under Maintenance', 'Missing', 'Retired', 'Grand Total']
    ws_quantities.append(headers_quantities)
    
    # Style headers
    for cell in ws_quantities[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    
    # Add data rows with formulas
    for idx, category in enumerate(categories, start=2):
        row_num = idx
        
        # Category name
        ws_quantities.cell(row=row_num, column=1, value=category.name)
        
        # Formulas for each status count - using proper sheet reference
        # In Use
        ws_quantities.cell(row=row_num, column=2).value = f'=COUNTIFS(\'ASSET Inventory\'!$B:$B,A{row_num},\'ASSET Inventory\'!$H:$H,"In Use")'
        
        # Available
        ws_quantities.cell(row=row_num, column=3).value = f'=COUNTIFS(\'ASSET Inventory\'!$B:$B,A{row_num},\'ASSET Inventory\'!$H:$H,"Available")'
        
        # Under Maintenance
        ws_quantities.cell(row=row_num, column=4).value = f'=COUNTIFS(\'ASSET Inventory\'!$B:$B,A{row_num},\'ASSET Inventory\'!$H:$H,"Under Maintenance")'
        
        # Missing
        ws_quantities.cell(row=row_num, column=5).value = f'=COUNTIFS(\'ASSET Inventory\'!$B:$B,A{row_num},\'ASSET Inventory\'!$H:$H,"Missing")'
        
        # Retired
        ws_quantities.cell(row=row_num, column=6).value = f'=COUNTIFS(\'ASSET Inventory\'!$B:$B,A{row_num},\'ASSET Inventory\'!$H:$H,"Retired")'
        
        # Grand Total
        ws_quantities.cell(row=row_num, column=7).value = f'=SUM(B{row_num}:F{row_num})'
    
    # Add Total row
    if categories.exists():
        total_row = ws_quantities.max_row + 1
        total_cell = ws_quantities.cell(row=total_row, column=1, value='TOTAL')
        total_cell.font = Font(bold=True)
        total_cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        
        ws_quantities.cell(row=total_row, column=2).value = f'=SUM(B2:B{total_row-1})'
        ws_quantities.cell(row=total_row, column=3).value = f'=SUM(C2:C{total_row-1})'
        ws_quantities.cell(row=total_row, column=4).value = f'=SUM(D2:D{total_row-1})'
        ws_quantities.cell(row=total_row, column=5).value = f'=SUM(E2:E{total_row-1})'
        ws_quantities.cell(row=total_row, column=6).value = f'=SUM(F2:F{total_row-1})'
        ws_quantities.cell(row=total_row, column=7).value = f'=SUM(G2:G{total_row-1})'
    
    # Set column widths
    for col in range(1, 8):
        ws_quantities.column_dimensions[get_column_letter(col)].width = 18
    
    # Format number cells
    for row in range(2, ws_quantities.max_row + 1):
        for col in range(2, 8):  # Columns B-G
            cell = ws_quantities.cell(row=row, column=col)
            cell.number_format = '0'  # Integer format
            cell.alignment = Alignment(horizontal="center")
    
    # ========== SHEET 3: MAINTENANCE LOG ==========
    ws_maintenance = wb.create_sheet("MAINTENANCE LOG", 2)
    
    headers_maintenance = [
        'Timestamp', 'Asset ID', 'Describe Issue', 'Action Taken',
        'Date Reported', 'Cost of Repair', 'Date Completed'
    ]
    ws_maintenance.append(headers_maintenance)
    
    # Style headers
    for cell in ws_maintenance[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    
    # Get maintenance logs
    maintenance_logs = MaintenanceLog.objects.select_related('asset', 'action_taken').order_by('-timestamp')
    
    for log in maintenance_logs:
        timestamp = log.timestamp.strftime('%d/%m/%Y %H:%M') if log.timestamp else ''
        date_reported = log.date_reported.strftime('%d/%m/%Y') if log.date_reported else ''
        date_completed = log.date_completed.strftime('%d/%m/%Y') if log.date_completed else ''
        
        ws_maintenance.append([
            timestamp,
            log.asset.asset_id if log.asset else '',
            log.description,
            log.action_taken.name if log.action_taken else '',
            date_reported,
            log.cost_of_repair if log.cost_of_repair else '',
            date_completed,
        ])
    
    # Add data validation for Action Taken (column D) - reference LISTS sheet
    if action_taken_options.exists():
        # Use dynamic reference to LISTS sheet column C
        max_list_row = len(action_taken_options) + 1
        dv_action = DataValidation(
            type="list",
            formula1=f'LISTS!$C$2:$C${max_list_row}',
            allow_blank=True
        )
        dv_action.error = 'Please select from the dropdown list'
        dv_action.errorTitle = 'Invalid Entry'
        ws_maintenance.add_data_validation(dv_action)
        if ws_maintenance.max_row > 1:
            dv_action.add(f'D2:D{ws_maintenance.max_row + 100}')  # Allow for future entries
    
    # Set column widths
    ws_maintenance.column_dimensions['A'].width = 18  # Timestamp
    ws_maintenance.column_dimensions['B'].width = 15  # Asset ID
    ws_maintenance.column_dimensions['C'].width = 40  # Describe Issue
    ws_maintenance.column_dimensions['D'].width = 20  # Action Taken
    ws_maintenance.column_dimensions['E'].width = 15  # Date Reported
    ws_maintenance.column_dimensions['F'].width = 15  # Cost of Repair
    ws_maintenance.column_dimensions['G'].width = 15  # Date Completed
    
    # ========== SHEET 4: LISTS (Dropdown Source Data) ==========
    ws_lists = wb.create_sheet("LISTS", 3)
    
    headers_lists = ['Category Items', 'Current status', 'Action Taken']
    ws_lists.append(headers_lists)
    
    # Style headers
    for cell in ws_lists[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    
    # Get max length for each column
    max_len = max(len(categories), len(statuses), len(action_taken_options))
    
    # Fill Category Items (column A)
    for idx, category in enumerate(categories, start=2):
        ws_lists.cell(row=idx, column=1, value=category.name)
    
    # Fill Current status (column B)
    for idx, status in enumerate(statuses, start=2):
        ws_lists.cell(row=idx, column=2, value=status.name)
    
    # Fill Action Taken (column C)
    for idx, action in enumerate(action_taken_options, start=2):
        ws_lists.cell(row=idx, column=3, value=action.name)
    
    # Set column widths
    ws_lists.column_dimensions['A'].width = 25
    ws_lists.column_dimensions['B'].width = 25
    ws_lists.column_dimensions['C'].width = 25
    
    # ========== SHEET 5: Past Users ==========
    ws_past_users = wb.create_sheet("Past Users", 4)
    
    headers_past_users = ['Asset_ID', 'User', 'Start Date', 'End Date']
    ws_past_users.append(headers_past_users)
    
    # Style headers
    for cell in ws_past_users[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    
    # Get assignment history
    assignment_history = AssignmentHistory.objects.select_related('asset', 'user').order_by('-start_date')
    
    for assignment in assignment_history:
        start_date = assignment.start_date.strftime('%d/%m/%Y') if assignment.start_date else ''
        end_date = assignment.end_date.strftime('%d/%m/%Y') if assignment.end_date else ''
        
        ws_past_users.append([
            assignment.asset.asset_id if assignment.asset else '',
            assignment.user.username if assignment.user else '',
            start_date,
            end_date,
        ])
    
    # Set column widths
    ws_past_users.column_dimensions['A'].width = 15  # Asset_ID
    ws_past_users.column_dimensions['B'].width = 25  # User
    ws_past_users.column_dimensions['C'].width = 15  # Start Date
    ws_past_users.column_dimensions['D'].width = 15  # End Date
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Inventory_Export.xlsx"'
    wb.save(response)
    return response


def export_assets_pdf(assets):
    """Export assets to PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("Assets Export", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Table data
    data = [['Asset ID', 'Category', 'Model', 'Serial', 'Assigned To', 'Status']]
    
    for asset in assets[:100]:  # Limit to 100 for PDF
        data.append([
            asset.asset_id,
            asset.category.name if asset.category else '',
            asset.model_description[:30],
            asset.serial_number[:20],
            asset.assigned_to.username if asset.assigned_to else 'Unassigned',
            asset.status.name if asset.status else '',
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="assets_export.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response
