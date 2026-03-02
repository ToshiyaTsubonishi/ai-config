import zipfile
import xml.etree.ElementTree as ET
import sys
import re

namespaces = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
}

def extract_raw_content(docx_path):
    """Wordファイルからテキストと画像の出現順を抽出するスクリプト"""
    try:
        z = zipfile.ZipFile(docx_path, 'r')
    except Exception as e:
        print(f"Error reading docx: {e}")
        return

    doc_xml = z.read('word/document.xml')
    root = ET.fromstring(doc_xml)
    body = root.find('w:body', namespaces)
    
    output = []
    image_counter = 1

    for elem in body:
        if elem.tag == f"{{{namespaces['w']}}}p":
            para_data, image_counter_new = process_paragraph(elem, image_counter)
            
            # Extract plain text to check for early termination rules
            text_to_check = ""
            if para_data:
                if isinstance(para_data, list):
                    text_to_check = "".join(para_data)
                else:
                    text_to_check = para_data
                    
            if "執筆時に参考にしたURL" in text_to_check:
                output.append("[この段落以降は『執筆時に参考にしたURL』のため削除対象]")
                break
                
            if para_data:
                if isinstance(para_data, list):
                    output.extend(para_data)
                else:
                    output.append(para_data)
            image_counter = image_counter_new
                
        elif elem.tag == f"{{{namespaces['w']}}}tbl":
            output.append("[テーブル発見: AIにてHTML化してください]")
            # テーブル内のテキストも最低限抽出しておく
            for tr in elem.findall('.//w:tr', namespaces):
                row_text = []
                for tc in tr.findall('.//w:tc', namespaces):
                     cell_text = "".join([t.text for t in tc.findall('.//w:t', namespaces) if t.text]).strip()
                     row_text.append(cell_text)
                if any(row_text):
                     output.append(f"  行: {' | '.join(row_text)}")

    print("=== Word 原稿抽出結果 ===")
    for line in output:
        print(line)
    print("=========================")

def process_paragraph(p_elem, image_counter):
    parts = []
    
    # 画像の抽出
    drawings = p_elem.findall('.//w:drawing', namespaces)
    for d in drawings:
        alt_text = "キャプション不明"
        docPr = d.find('.//wp:docPr', namespaces)
        if docPr is not None:
            descr = docPr.get('descr')
            title = docPr.get('title')
            if descr:
                 alt_text = descr
            elif title:
                 alt_text = title
                
        img_name = f"{image_counter:02d}.jpg"
        parts.append(f"[画像ファイル: {img_name}] (内部Altテキスト: {alt_text})")
        image_counter += 1

    # テキストと太字の抽出
    para_text = ""
    is_all_bold = True
    has_text = False
    raw_text_only = ""

    runs = p_elem.findall('.//w:r', namespaces)
    for r in runs:
        text_elems = r.findall('.//w:t', namespaces)
        if not text_elems:
            continue
            
        rPr = r.find('w:rPr', namespaces)
        is_bold = rPr is not None and rPr.find('w:b', namespaces) is not None
        
        for t in text_elems:
            if t.text:
                has_text = True
                clean_text = t.text.replace('\u3000', '')
                raw_text_only += clean_text
                
                if not is_bold and clean_text.strip():
                     is_all_bold = False
                     
                if is_bold:
                    para_text += f"*{clean_text}*" # マークダウンの太字で表現
                else:
                    para_text += clean_text
                    
    if has_text:
        # 見出し判定（すべて太字のアスタリスク囲み）
        if is_all_bold and raw_text_only.strip():
             parts.append(f"[見出し候補] {raw_text_only}")
        else:
             parts.append(para_text)
             
    if not parts:
        return None, image_counter
    elif len(parts) == 1:
        return parts[0], image_counter
    else:
        return parts, image_counter

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <input.docx> [output.txt]")
        sys.exit(1)
    
    import io
    # Forcing UTF-8 for everything
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) >= 3:
        # Redirect stdout to the specified file with utf-8 encoding
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            sys.stdout = f
            extract_raw_content(sys.argv[1])
    else:
        extract_raw_content(sys.argv[1])
