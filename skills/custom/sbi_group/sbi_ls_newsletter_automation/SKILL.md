---
name: sbi_ls_newsletter_automation
description: Automates the creation of HTML newsletters from Word documents. SBIリーシングサービシーズのメルマガ作成専用。
---
#重要

このスキルはSBIリーシングサービシーズのメルマガ作成専用です。最初にユーザーにSBIリーシングサービシーズのメルマガ作成目的であるか確認してください。

# Newsletter Automation Skill

This skill converts a Word document (`.docx`) into an HTML newsletter based on the SBI Leasing Services design template.

## Usage

1.  **Collect Metadata**:
    - **First, ask the user for the `vol.` number and the `date` (e.g., "FEBRUARY 2026").**
    - Ensure the header format follows this pattern when inserting into HTML: `VOL.[Number] [MONTH] [YEAR]` (e.g., `VOL.46 DECEMBER 2025`).

2.  **Verify Word Document**:
    - Check if the target `.docx` file exists in the directory.
    - If it is missing, notify the user and ask them to provide the file.

3.  **Prepare your Word Document**:
    - Use **Bold** or `Heading 1` styles for section headers.
    - Insert images directly into the Word document.
    - "【Title】" style text is also recognized as a header.

4.  **Run the Conversion Script**:
    Run the script from the command line, passing the path to the Word document, volume, and date.

    ```powershell
    python sbi_ls_newsletter_automation/scripts/convert_docx.py "path/to/your/newsletter.docx" --vol "46" --date "DECEMBER 2025"
    ```

5.  **Automated Features**:
    - **Header Spacing**: Automatically inserts a 20px gap between the banner and content.
    - **Closing Statement**: Automatically appends the "100-year company" disclaimer at the end.
    - **Image Layout**: Refined spacing (10px top / 20px bottom) for graphs and block images.

6.  **Check the Output**:
    - The HTML file will be generated at `output/newsletter.html` (relative to the **Word document's location**).
    - Extracted images will be in `output/images/`.

## Directory Structure

- `scripts/`: Contains the conversion logic.
- `resources/`: Contains the HTML template and static assets.
    - `resources/images/`: Logos and buttons (automatically copied to output).

## Portability Note

This skill is now self-contained. All required static assets (logos, buttons) are included in the `resources/images/` folder and will be automatically copied to the output directory during conversion. No external dependencies on local image paths are required.
