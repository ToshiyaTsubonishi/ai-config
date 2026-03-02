import openpyxl
from openpyxl.cell import MergedCell
import json
import sys
import os

def safe_write(sheet, cell_coord, value):
    """
    Writes to a cell, or the top-left cell of a merged range if it belongs to one.
    """
    for merged_range in sheet.merged_cells.ranges:
        if cell_coord in merged_range:
            start_cell = merged_range.start_cell
            sheet.cell(row=start_cell.row, column=start_cell.column).value = value
            return
    sheet[cell_coord] = value

def process_excel(template_path, output_path, json_data_file):
    try:
        with open(json_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Invalid JSON file. {e}", file=sys.stderr)
        return False

    try:
        workbook = openpyxl.load_workbook(template_path)
    except Exception as e:
        print(f"Error loading Excel template: {e}", file=sys.stderr)
        return False

    sheet = workbook.worksheets[0]
    is_periodic = "定期評価" in template_path

    # Vendor basic info (Mapping is the same for both based on layout check)
    if "vendor_name" in data:
        safe_write(sheet, 'D5', data["vendor_name"])
    if "location" in data:
        safe_write(sheet, 'D6', data["location"])
    if "phone_number" in data:
        safe_write(sheet, 'D7', data["phone_number"])
    if "representative_name" in data:
        safe_write(sheet, 'D8', data["representative_name"])
    if "capital_stock" in data:
        safe_write(sheet, 'D9', data["capital_stock"])
    if "establishment_date" in data:
        safe_write(sheet, 'D10', data["establishment_date"])
    if "entrusted_work_content" in data:
        safe_write(sheet, 'D11', data["entrusted_work_content"])
    if "transaction_type" in data:
        safe_write(sheet, 'D12', data["transaction_type"])
    
    # Selection Criteria
    desc_data = data.get("evaluation_descriptions", {})
    
    if is_periodic:
        # Periodic Evaluation Mapping (9 items)
        score_mapping = {
            "reporting": "I15",
            "quality": "I20",
            "price": "I25",
            "timeliness": "I30",
            "financial": "I34",
            "information": "I39",
            "anti_social": "I48",
            "compliance": "I53",
            "other": "I58"
        }
        desc_mapping = {
            "reporting": "B17",    # 15 + 2
            "quality": "B22",      # 20 + 2
            "price": "B27",        # 25 + 2
            "timeliness": "B32",   # 30 + 2
            "financial": "B36",    # 34 + 2
            "information": "B45",  # 39 + 6
            "anti_social": "B50",  # 48 + 2
            "compliance": "B55",   # 53 + 2
            "other": "B60"         # 58 + 2
        }
    else:
        # New Evaluation Mapping (10 items)
        score_mapping = {
            "business_execution": "I15",
            "internal_control": "I20",
            "reporting": "I25",
            "quality": "I30",
            "price": "I35",
            "financial": "I40",
            "information": "I45",
            "anti_social": "I54",
            "compliance": "I59",
            "other": "I64"
        }
        desc_mapping = {
            "business_execution": "B17",
            "internal_control": "B22",
            "reporting": "B27",
            "quality": "B32",
            "price": "B37",
            "financial": "B42",
            "information": "B51",
            "anti_social": "B56",
            "compliance": "B61",
            "other": "B66"
        }

    # Initialize all scores to "-"
    for cell in score_mapping.values():
        safe_write(sheet, cell, "-")

    # Write descriptions from JSON if available
    for key, cell in desc_mapping.items():
        if key in desc_data:
            safe_write(sheet, cell, desc_data[key])
        else:
            safe_write(sheet, cell, "-")

    # 2. Personal Information
    if data.get("include_personal_info", False) and len(workbook.worksheets) > 1:
        pi_sheet = workbook.worksheets[1]
        if "personal_info_details" in data:
            safe_write(pi_sheet, 'C7', data["personal_info_details"])

    # 3. IT業務
    if data.get("is_it_outsourcing", False) and data.get("it_handles_sensitive_data", False) and len(workbook.worksheets) > 2:
        it_sheet = workbook.worksheets[2]
        if "it_outsourcing_details" in data:
            safe_write(it_sheet, 'C9', data["it_outsourcing_details"])

    try:
        workbook.save(output_path)
        print(f"Successfully created '{output_path}' with evaluation data.", file=sys.stdout)
        return True
    except Exception as e:
        print(f"Error saving Excel file: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python excel_processor.py <template_path> <output_path> <json_file_path>", file=sys.stderr)
        sys.exit(1)

    template_path = sys.argv[1]
    output_path = sys.argv[2]
    json_file_path = sys.argv[3]

    if not process_excel(template_path, output_path, json_file_path):
        sys.exit(1)
