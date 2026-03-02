import sys
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
import argparse

# Force UTF-8 output for Windows Console if writing to stdout
sys.stdout.reconfigure(encoding='utf-8')

def decode_html(html_bytes):
    # List of encodings to try
    encodings = ['utf-8', 'cp932', 'euc-jp', 'shift_jis']
    
    # 1. Try to detect from header/meta (fast path)
    head = html_bytes[:1024].decode('ascii', errors='ignore')
    match = re.search(r"""charset=["']?([a-zA-Z0-9_-]+)""", head, re.IGNORECASE)
    if match:
        declared = match.group(1).lower()
        if declared in ['shift_jis', 'shift-jis', 'sjis']: declared = 'cp932'
        if declared not in encodings:
            encodings.insert(0, declared)
        else:
            encodings.remove(declared)
            encodings.insert(0, declared)

    for enc in encodings:
        try:
            decoded = html_bytes.decode(enc)
            if enc != 'utf-8':
                if re.search(r'[\u3040-\u309F]', decoded):
                    return decoded
            else:
                return decoded
        except UnicodeDecodeError:
            continue
            
    return html_bytes.decode('utf-8', errors='ignore')

class LinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.title = ""
        self.description = ""
        self.in_title = False
        self.in_a = False
        self.current_a_href = None
        self.current_a_text = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'title':
            self.in_title = True
        elif tag == 'meta':
            if attrs_dict.get('name', '').lower() == 'description':
                self.description = attrs_dict.get('content', '')
        elif tag == 'a':
            self.in_a = True
            self.current_a_href = attrs_dict.get('href')
            self.current_a_text = []

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag == 'a':
            if self.current_a_href:
                text = "".join(self.current_a_text).strip()
                text = re.sub(r'\s+', ' ', text)
                full_url = urllib.parse.urljoin(self.base_url, self.current_a_href)
                self.links.append((text, full_url))
            self.in_a = False
            self.current_a_href = None

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_a:
            self.current_a_text.append(data)

def generate_llms_txt(url, output_file=None):
    output_buffer = []
    
    def out(text):
        if output_file:
            output_buffer.append(text)
        else:
            print(text)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req) as response:
            html_bytes = response.read()
            html = decode_html(html_bytes)

        parser = LinkParser(url)
        parser.feed(html)

        domain = urllib.parse.urlparse(url).netloc
        unique_links = {}
        
        sections = {
            "Core": ["company", "about", "corporate", "profile", "会社", "企業", "概要"],
            "Business": ["service", "business", "solution", "product", "事業", "サービス", "商品"],
            "Investors": ["investor", "ir", "stock", "finance", "library", "投資", "株主", "決算"],
            "News": ["news", "press", "release", "topic", "info", "ニュース", "お知らせ"],
            "Sustainability": ["csr", "sustainability", "esg", "sdgs", "サステナ", "環境"],
            "Recruit": ["recruit", "career", "job", "採用"],
            "Contact": ["contact", "inquiry", "support", "faq", "お問い合わせ"]
        }
        
        categorized_links = {k: [] for k in sections}
        uncategorized = []

        for text, link in parser.links:
            if not text or len(text) < 2: continue
            if urllib.parse.urlparse(link).netloc != domain: continue 
            
            if link in unique_links:
                if len(text) > len(unique_links[link]):
                    unique_links[link] = text
            else:
                unique_links[link] = text

        for link, text in unique_links.items():
            assigned = False
            link_lower = link.lower()
            text_lower = text.lower()
            
            for cat, keywords in sections.items():
                if any(k in link_lower or k in text_lower for k in keywords):
                    categorized_links[cat].append((text, link))
                    assigned = True
                    break 
            
            if not assigned:
                uncategorized.append((text, link))

        out(f"# {parser.title.strip()}")
        out("")
        if parser.description:
            out(f"> {parser.description.strip()}")
        out("")
        out(f"- [Top]({url})")

        for cat, links_list in categorized_links.items():
            if links_list:
                out("")
                out(f"## {cat}")
                links_list.sort(key=lambda x: len(x[1])) 
                for text, link in links_list[:12]:
                    out(f"- [{text}]({link})")

        if uncategorized:
             uncategorized.sort(key=lambda x: len(x[1]))
             out("")
             out(f"## Other")
             for text, link in uncategorized[:8]:
                 out(f"- [{text}]({link})")

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(chr(10).join(output_buffer))
            print(f"Successfully wrote to {output_file}")

    except Exception as e:
        print(f"Error processing {url}: {e}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate llms.txt from a URL')
    parser.add_argument('url', help='Target URL')
    parser.add_argument('-o', '--output', help='Output file path')
    args = parser.parse_args()
    
    generate_llms_txt(args.url, args.output)
