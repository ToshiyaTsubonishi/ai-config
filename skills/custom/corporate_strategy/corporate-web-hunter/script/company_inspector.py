import re
import urllib.request
import urllib.error
from html.parser import HTMLParser
import csv
import sys
import time
import random

# --- 簡易HTMLパーサー ---
class CompanyInfoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.is_collecting = False

    def handle_starttag(self, tag, attrs):
        if tag in ['p', 'td', 'th', 'div', 'span', 'li']:
            self.is_collecting = True

    def handle_endtag(self, tag):
        if tag in ['p', 'td', 'th', 'div', 'span', 'li']:
            self.is_collecting = False

    def handle_data(self, data):
        if self.is_collecting:
            self.text_content.append(data.strip())

    def get_text(self):
        return ' '.join([t for t in self.text_content if t])

def fetch_and_analyze(url):
    """
    指定されたURL（会社概要ページ想定）を取得し、
    企業規模や代表者名を推測して返す
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        parser = CompanyInfoParser()
        parser.feed(html)
        text = parser.get_text()
        
        # --- 正規表現による情報抽出 ---
        # 1. 従業員数（"従業員 〇〇名" などのパターン）
        emp_match = re.search(r'従業員(?:数)?[:\s\u3000]*([0-9０-９]+)名', text)
        emp_count = emp_match.group(1) if emp_match else "不明"
        
        # 2. 代表者名（"代表取締役 〇〇 〇〇" パターン）
        rep_match = re.search(r'代表取締役(?:社長)?[:\s\u3000]*([一-龠ぁ-んァ-ン]{2,4}[\s\u3000]*[一-龠ぁ-んァ-ン]{2,4})', text)
        rep_name = rep_match.group(1) if rep_match else "不明"
        
        # 3. 資本金
        cap_match = re.search(r'資本金[:\s\u3000]*([0-9０-９,]+(?:万|億)?円)', text)
        capital = cap_match.group(1) if cap_match else "不明"

        return {
            "URL": url,
            "従業員数": emp_count,
            "代表者": rep_name,
            "資本金": capital,
            "ステータス": "取得成功"
        }

    except Exception as e:
        return {
            "URL": url,
            "従業員数": "-",
            "代表者": "-",
            "資本金": "-",
            "ステータス": f"エラー: {str(e)}"
        }

def main():
    print("--- 全国対応：企業情報 自動抽出ツール ---")
    print("本来は検索エンジンAPIと連動しますが、今回はデモとして")
    print("『調査対象のURLリスト』を読み込み、結果をCSV出力します。")
    print("-" * 40)

    # 本来はここに検索ロジックが入るが、Demo用にリストを受け取る形とする
    # ユーザーが「このURL調べて」と入力することを想定
    
    target_urls = [
        # 例：群馬の実在企業のURL（※存在確認用ダミーURLではありませんが、負荷をかけないよう注意）
        # 実際にはここに、Google検索結果から抽出したURL配列が入ります。
        "https://www.kojima-iron.co.jp/company/", # 小島鉄工所
        "https://www.sakamoto-ind.co.jp/company/", # 坂本工業
    ]
    
    results = []
    print(f"調査対象: {len(target_urls)}件のWebサイトを解析中...")
    
    for url in target_urls:
        print(f"Accessing: {url} ...")
        data = fetch_and_analyze(url)
        results.append(data)
        time.sleep(2) # サーバー負荷軽減のためのWait
        
    # CSV出力
    filename = "Nationwide_Company_List_Auto.csv"
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["URL", "従業員数", "代表者", "資本金", "ステータス"])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\n完了: {filename} に調査結果を保存しました。")
    print("※このスクリプトを拡張し、Google Custom Search API等を組み込むことで")
    print("  『全国』『全業種』のリスト作成を完全自動化可能です。")

if __name__ == "__main__":
    main()
