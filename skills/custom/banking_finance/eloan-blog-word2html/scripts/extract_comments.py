import zipfile
import xml.etree.ElementTree as ET
import sys

namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def extract_comments(docx_path):
    try:
        z = zipfile.ZipFile(docx_path, 'r')
        if 'word/comments.xml' in z.namelist():
            comments_xml = z.read('word/comments.xml')
            root = ET.fromstring(comments_xml)
            for comment in root.findall('w:comment', namespaces):
                cid = comment.get(f"{{{namespaces['w']}}}id")
                text = "".join([t.text for t in comment.findall('.//w:t', namespaces) if t.text])
                print(f"Comment ID {cid}: {text}")
        else:
            print("No comments.xml found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_comments(sys.argv[1])
