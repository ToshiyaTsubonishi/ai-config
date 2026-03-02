import csv
import sys
import argparse
import os
from datetime import datetime

def load_data(filepath):
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    return data

def assess_risk(row):
    """
    Evaluates risk. 
    Note: Heuristics here are general.
    """
    domain = row['generated_domain']
    status = row['status']
    technique = row['technique']
    
    if status != "Active":
        return "None", "Inactive"

    # Rule 1: TLD Risk
    if technique == "TLD Variation":
        if domain.endswith(".com"):
            return "High", "Critical TLD (.com) Active"
        if domain.endswith(".xyz") or domain.endswith(".info"):
            return "Medium", "Spam-heavy TLD Active"
        if domain.endswith(".jp") or domain.endswith(".net"):
            return "Medium", "Major TLD Active (Check content)"
        return "Low", "Minor TLD Active"

    # Rule 2: Typosquatting
    if technique == "Typosquatting":
        if domain.endswith(".com"):
             return "High", "Typosquat on .com"
        return "Medium", "Active Typosquat Domain"

    # Rule 3: Keywords
    if technique == "Keyword Insertion":
        keywords = ["login", "secure", "account", "update", "support", "admin"]
        if any(k in domain for k in keywords):
            return "High", "Phishing Keyword Detected"
        return "Medium", "Keyword Variation Active"

    # Rule 4: Homoglyphs
    if technique == "Homoglyphs":
        return "Medium", "Visual Spoofing Domain Active"

    return "Low", "Active Unknown Variation"

def generate_report(data, output_file, base_url):
    total = len(data)
    active = [d for d in data if d['status'] == "Active"]
    active_count = len(active)
    
    high_risks = []
    medium_risks = []
    
    for row in active:
        level, reason = assess_risk(row)
        row['risk_reason'] = reason
        if level == "High":
            high_risks.append(row)
        elif level == "Medium":
            medium_risks.append(row)

    # Write Markdown
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Domain Threat Assessment Report\n")
        f.write(f"**Target:** `{base_url}`\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 1. Executive Summary\n")
        f.write(f"- **Total Scanned:** {total}\n")
        f.write(f"- **Active Domains:** {active_count} ({active_count/total*100:.1f}%)\n")
        f.write(f"- **High Risk Threats:** {len(high_risks)}\n")
        f.write(f"- **Medium Risk Threats:** {len(medium_risks)}\n\n")

        f.write("## 2. High Priority Threats (Action Required)\n")
        if high_risks:
            f.write("| Domain | IP Address | Technique | Risk Reason |\n")
            f.write("|---|---|---|---|\n")
            for r in high_risks:
                f.write(f"| `{r['generated_domain']}` | {r['ip_address']} | {r['technique']} | **{r['risk_reason']}** |\n")
        else:
            f.write("No High Risk threats detected.\n")
        f.write("\n")

        f.write("## 3. Medium Priority Threats (Monitor)\n")
        if medium_risks:
            f.write("| Domain | IP Address | Technique | Reason |\n")
            f.write("|---|---|---|---|\n")
            for r in medium_risks[:15]: 
                f.write(f"| `{r['generated_domain']}` | {r['ip_address']} | {r['technique']} | {r['risk_reason']} |\n")
            if len(medium_risks) > 15:
                f.write(f"| ... and {len(medium_risks) - 15} more | ... | ... | ... |\n")
        else:
            f.write("No Medium Risk threats detected.\n")
        f.write("\n")

        f.write("## 4. Observations & Recommendations\n")
        f.write(f"- **Observation**: {len(high_risks)} high-risk domains identified. ")
        if any(d['generated_domain'].endswith('.com') for d in high_risks):
            f.write("Presence of active `.com` domains suggests potential for traffic interception. ")
        f.write("\n- **Action 1**: Add High Risk domains to firewall/email blacklists.\n")
        f.write("- **Action 2**: Verify content of Medium Risk domains (especially TLD variations) to distinguish legitimate third-parties from attackers.\n")

    print(f"[+] Report generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Analyze Domain Risks from CSV")
    parser.add_argument("input_csv", help="Path to scan results CSV")
    args = parser.parse_args()

    data = load_data(args.input_csv)
    
    # Extract base url from the first row if available
    base_url = "Unknown"
    if data:
        base_url = data[0].get('base_url', 'Unknown')

    # Generate output filename based on input
    base_name = os.path.splitext(os.path.basename(args.input_csv))[0]
    output_file = f"REPORT_{base_name}.md"

    generate_report(data, output_file, base_url)

if __name__ == "__main__":
    main()
