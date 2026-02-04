"""
Excel Writer - Saves filtered jobs to formatted Excel file
"""

from pathlib import Path
from typing import List
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from loguru import logger


def write_to_excel(filtered_jobs: List, output_path: str) -> str:
    """
    Write filtered jobs to an Excel file with formatting.
    
    Args:
        filtered_jobs: List of FilteredJob objects
        output_path: Path to save the Excel file
        
    Returns:
        Absolute path to the saved file
    """
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Freelance Gigs"
    
    # Headers
    headers = [
        "Title",
        "Company",
        "Location",
        "Type",
        "Posted",
        "AI Score",
        "AI Analysis",
        "Job URL",
        "Scraped At"
    ]
    
    # Styles
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = border
    
    # Write data
    for row, fj in enumerate(filtered_jobs, 2):
        job = fj.job
        
        data = [
            job.title,
            job.company,
            job.location,
            job.job_type,
            job.posted_date,
            fj.quality_score if fj.quality_score > 0 else "N/A",
            fj.reason,
            job.job_url,
            job.scraped_at
        ]
        
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = border
            
            # Color code AI scores
            if col == 6 and isinstance(value, int):
                if value >= 8:
                    cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif value >= 6:
                    cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    
    # Auto-width columns
    column_widths = [40, 25, 20, 15, 12, 10, 40, 50, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    
    # Freeze header row
    ws.freeze_panes = 'A2'
    
    # Save
    wb.save(output_path)
    logger.info(f"Saved {len(filtered_jobs)} jobs to {output_path}")
    
    return str(Path(output_path).absolute())
