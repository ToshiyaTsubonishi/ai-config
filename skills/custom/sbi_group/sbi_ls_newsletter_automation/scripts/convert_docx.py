import os
import sys
import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
import shutil
from PIL import Image
import io

# Set up paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'resources', 'template.html')

def convert_image_to_png(image_bytes, output_path):
    """
    Converts image bytes to PNG and saves to output_path.
    Handles WMF/EMF via Pillow.
    """
    try:
        # Load image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ('CMYK', 'P'):
            img = img.convert('RGB')
        img.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"Error converting image to PNG: {e}")
        return False

def extract_image_from_xml(element, doc, images_dir, image_counter):
    """
    Extracts a single image from a w:drawing or w:pict element.
    """
    blips = element.xpath('.//a:blip')
    if not blips:
        return None, image_counter
    
    blip = blips[0]
    embed_attr = blip.get(qn('r:embed'))
    if not embed_attr:
        return None, image_counter
        
    try:
        part = doc.part.related_parts[embed_attr]
        image_bytes = part.blob
        image_filename = f"image_{image_counter:03d}.png"
        image_path = os.path.join(images_dir, image_filename)
        
        if convert_image_to_png(image_bytes, image_path):
            return image_filename, image_counter + 1
    except Exception as e:
        print(f"Error extracting image: {e}")
        
    return None, image_counter

def get_paragraph_alignment(para):
    alignment = para.alignment
    if alignment == WD_ALIGN_PARAGRAPH.CENTER:
        return 'center'
    elif alignment == WD_ALIGN_PARAGRAPH.RIGHT:
        return 'right'
    else:
        return 'left'

def generate_html_block(content_html, align='left', is_heading=False, has_block_image=False, is_attribution=False):
    wrapper_start = f"""
        <table width="600" border="0" align="center" cellpadding="0" cellspacing="0" style="background: #FFF; margin: 0 auto;">
          <tbody>"""
    wrapper_end = """
          </tbody>
        </table>
"""
    if has_block_image and not is_heading:
        # Full-width block images with more generous spacing (20px) after and 10px before
        inner_content = f"""
            <tr><td height="10"></td></tr>
            <tr>
              <td align="center" style="padding: 0 20px;">{content_html}</td>
            </tr>
            <tr><td height="20"></td></tr>"""
    elif is_heading:
        # Standard headings with generous top padding
        inner_content = f"""
            <tr>
              <td height="50" align="left"></td>
            </tr>
            <tr>
              <td align="{align}" style="padding: 0 20px;"><div style="font-size:20px; color: #333;">
                <strong>{content_html}</strong>
              </div></td>
            </tr>
            <tr>
              <td height="20" align="left"></td>
            </tr>"""
    elif is_attribution:
        # Attribution/Source lines (12px)
        inner_content = f"""
            <tr>
              <td align="{align}" style="padding: 0 20px;">
                <div style="font-size: 12px; line-height:1.4; color:#333;">{content_html}</div>
              </td>
            </tr>
            <tr>
               <td height="10"></td>
            </tr>"""
    else:
        # Standard text with standard line height 1.6
        inner_content = f"""
            <tr>
              <td align="{align}" style="padding: 0 20px;">
                <div style="font-size: 16px; line-height:1.6; color:#333;">{content_html}</div>
              </td>
            </tr>
            <tr>
               <td height="10"></td>
            </tr>"""
            
    return wrapper_start + inner_content + wrapper_end

def convert_docx_to_html(docx_path):
    if not os.path.exists(docx_path):
        return None

    doc = docx.Document(docx_path)
    output_dir = os.path.join(os.path.dirname(docx_path), 'output')
    images_dir = os.path.join(output_dir, 'images')
    if not os.path.exists(images_dir): os.makedirs(images_dir)
    
    # Copy static assets from resources/images to output/images
    static_images_src = os.path.join(BASE_DIR, 'resources', 'images')
    if os.path.exists(static_images_src):
        for img_file in os.listdir(static_images_src):
            src_path = os.path.join(static_images_src, img_file)
            dst_path = os.path.join(images_dir, img_file)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)

    html_parts = []
    # Add top spacer (20px) to separate from banner
    html_parts.append('<table width="600" border="0" align="center" cellpadding="0" cellspacing="0" style="background: #FFF; margin: 0 auto;"><tbody><tr><td height="20"></td></tr></tbody></table>')
    image_counter = 0

    for para in doc.paragraphs:
        text_content = para.text.strip()
        is_heading = False
        if para.style.name.startswith('Heading') or (text_content.startswith('【') and text_content.endswith('】')):
            is_heading = True

        # Attribution detection
        is_attribution = False
        if text_content.startswith('(出所') or text_content.startswith('（出所') or text_content.startswith('(*'):
            is_attribution = True

        runs_data = []

        for run in para.runs:
            run_html = ""
            has_img = False
            run_text = ""
            
            for child in run._element.iterchildren():
                if child.tag == qn('w:t'):
                    txt = child.text
                    if txt:
                        run_text += txt
                        escaped = txt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        
                        styles = []
                        # Base font size is 16px. Only apply if different or if heading/attribution.
                        if run.font.size and not is_heading and not is_attribution:
                            pt = run.font.size.pt
                            # If it's the standard 10.5pt, we don't need a span because the parent div handles it (16px)
                            if pt > 10.5:
                                styles.append(f"font-size: {int(pt * 1.5)}px")
                            elif pt < 10.0:
                                styles.append(f"font-size: {int(pt * 1.5)}px")
                        
                        is_bold = run.bold
                        if is_bold is None and para.style.font and para.style.font.bold:
                            is_bold = True
                        
                        if is_bold:
                            styles.append("font-weight: bold")
                        
                        if styles:
                            run_html += f'<span style="{"; ".join(styles)}">{escaped}</span>'
                        else:
                            run_html += escaped
                        
                elif child.tag == qn('w:drawing') or child.tag == qn('w:pict'):
                    img_file, image_counter = extract_image_from_xml(child, doc, images_dir, image_counter)
                    if img_file:
                        has_img = True
                        # For aesthetic beauty, we ensure inline logos align well
                        run_html += f'<img src="images/{img_file}" style="max-width: 100%; height: auto; vertical-align: middle; margin: 0 5px; display: inline-block;">'

            if run_html:
                runs_data.append({'html': run_html, 'has_img': has_img, 'text': run_text})

        if not runs_data:
            continue

        # Logo-label heuristic (maintain sequence fix)
        # We move the image to the end if the first run is an image and the subsequent text looks like a label or caption
        if len(runs_data) >= 2:
            r0 = runs_data[0]
            if r0['has_img'] and not r0['text'].strip():
                # Join all remaining text in the paragraph to check for labels/captions
                total_text_after = "".join([r['text'] for r in runs_data[1:]]).strip()
                # Case 1: Airline logo (e.g., "デルタ航空:")
                # Case 2: Graph caption (e.g., "<2025年通期...>")
                if total_text_after.endswith(':') or (total_text_after.startswith('<') and total_text_after.endswith('>')):
                    img_run = runs_data.pop(0)
                    runs_data.append(img_run)

        para_html = "".join([r['html'] for r in runs_data])
        align = get_paragraph_alignment(para)
        
        # Attribution detection
        is_attribution = False
        if text_content.startswith('(出所') or text_content.startswith('（出所'):
            is_attribution = True

        paragraph_all_images = all(r['has_img'] and not r['text'].strip() for r in runs_data)
        has_text = any(r['text'].strip() for r in runs_data)
        is_block_image = paragraph_all_images and not has_text

        # If it's a block image, ensure it has the correct width for the design
        if is_block_image:
             para_html = para_html.replace('style="', 'width="560" style="')

        html_parts.append(generate_html_block(para_html, align=align, is_heading=is_heading, has_block_image=is_block_image, is_attribution=is_attribution))

    # Append standard closing statement (100-year company)
    closing_text = "当社は、「100年企業への挑戦」を経営理念とし、今後も、優良な案件に取り組んでいくとともに、税務や法務の専門家、金融機関などのパートナーが持つ高い専門性を組み合わせ、投資家には付加価値の高い金融ソリューションを、航空・海運会社等の 借り手（レッシー）である資金需要者には競争力のあるファイナンスの提供を行うことで、投資家、パートナー、借り手（レッシー）とともに 100年企業を目指してまいります。"
    html_parts.append(generate_html_block(closing_text, align='left', is_attribution=False))

    return "\n".join(html_parts)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert DOCX to HTML for newsletter.')
    parser.add_argument('docx_path', help='Path to the Word document.')
    parser.add_argument('--vol', help='Volume number (e.g., 46)', default='')
    parser.add_argument('--date', help='Date (e.g., FEBRUARY 2026)', default='')

    args = parser.parse_args()
    docx_path = os.path.abspath(args.docx_path)

    if not os.path.exists(docx_path):
        print(f"Error: File not found at {docx_path}")
        sys.exit(1)

    print(f"Converting with refined layout: {docx_path}")
    content_html = convert_docx_to_html(docx_path)

    if content_html:
        # Load template
        try:
            with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
                template = f.read()
        except Exception as e:
            print(f"Error loading template: {e}")
            return

        # Format header volume/date in professional style: VOL.46 DECEMBER 2025
        vol_str = f"VOL.{args.vol}" if args.vol else "VOL.XX"
        date_str = args.date.upper() if args.date else "MONTH YYYY"
        date_volume = f"{vol_str} {date_str}".strip()

        # Replace placeholders using robust regex
        import re
        # Content replacement
        final_html = re.sub(r'\{\{\s*content\s*\}\}', content_html, template)
        # Date Volume replacement (handles potential multi-line in template)
        final_html = re.sub(r'\{\{\s*date_volume\s*\}\}', date_volume, final_html, flags=re.DOTALL)

        # Output path
        output_dir = os.path.join(os.path.dirname(docx_path), 'output')
        output_path = os.path.join(output_dir, 'newsletter.html')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print(f"Done! Created {output_path}")

if __name__ == "__main__":
    main()
