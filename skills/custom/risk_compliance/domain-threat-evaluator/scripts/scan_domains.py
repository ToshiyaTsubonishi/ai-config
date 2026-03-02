import socket
import csv
import time
import argparse
import sys
import os

# --- Configuration ---
TIMEOUT = 2.0
COMMON_TLDS = ["com", "net", "org", "jp", "co.jp", "info", "xyz", "biz", "site", "io", "ai"]

def check_domain(domain):
    try:
        socket.setdefaulttimeout(TIMEOUT)
        ip = socket.gethostbyname(domain)
        return "Active", ip
    except socket.gaierror:
        return "Inactive", None
    except Exception as e:
        return "Error", str(e)

def generate_typos(base):
    typos = set()
    neighbors = {
        'f': ['g', 'd', 'r', 'v', 'c', 't'],
        'd': ['s', 'f', 'e', 'x', 'c'],
        'u': ['y', 'i', 'j', 'h', 'k'],
        'a': ['q', 'w', 's', 'z'],
        's': ['a', 'w', 'e', 'd', 'x', 'z'],
        'b': ['v', 'g', 'h', 'n'],
        'i': ['u', 'j', 'k', 'o'],
    }
    for i, char in enumerate(base):
        if char in neighbors:
            for n in neighbors[char]:
                typos.add(base[:i] + n + base[i+1:])
    for i in range(len(base)):
        typos.add(base[:i] + base[i+1:])
    for i in range(len(base) - 1):
        chars = list(base)
        chars[i], chars[i+1] = chars[i+1], chars[i]
        typos.add("".join(chars))
    for i in range(len(base)):
        typos.add(base[:i] + base[i] + base[i:])
        
    return list(typos)

def generate_homoglyphs(base):
    replacements = {
        'l': ['1', 'i'], 'o': ['0'], 'd': ['b', 'cl'], 'm': ['rn'], 'w': ['vv'],
        'a': ['4', '@'], 'e': ['3'], 's': ['5', '$'], 't': ['7']
    }
    variations = set()
    for i, char in enumerate(base):
        if char in replacements:
            for r in replacements[char]:
                variations.add(base[:i] + r + base[i+1:])
    return list(variations)

def generate_keywords(base):
    keywords = ["login", "support", "secure", "account", "member", "update", "admin", "portal", "web", "mail"]
    variations = set()
    for k in keywords:
        variations.add(f"{base}-{k}")
        variations.add(f"{k}-{base}")
        variations.add(f"{base}{k}")
    return list(variations)

def generate_subdomains(base, tld):
    subs = ["login", "secure", "admin", "www-update", "mail", "remote"]
    variations = set()
    for s in subs:
        variations.add(f"{s}-{base}")
    return list(variations)

def main():
    parser = argparse.ArgumentParser(description="Domain Threat Intelligence Scanner")
    parser.add_argument("domain", help="Base domain name (e.g., 'fdua', 'sbi')")
    parser.add_argument("tld", help="Base TLD (e.g., 'org', 'co.jp')")
    parser.add_argument("-o", "--output", help="Output CSV filename", default=None)
    args = parser.parse_args()

    base_domain = args.domain
    base_tld = args.tld
    base_url = f"https://www.{base_domain}.{base_tld}/"
    
    if args.output:
        output_file = args.output
    else:
        output_file = f"scan_{base_domain}_{base_tld}.csv"

    print(f"[*] Starting Intelligence Scan for: {base_domain}.{base_tld}")
    print(f"[*] Results will be saved to: {output_file}")

    results = []
    checked_domains = set()

    original = f"{base_domain}.{base_tld}"
    results.append({"base_url": base_url, "generated_domain": original, "technique": "Original", "status": "Pending", "ip_address": None})
    checked_domains.add(original)

    check_tlds = list(set(COMMON_TLDS + [base_tld]))

    generators = [
        (check_tlds, "TLD Variation", lambda x: [f"{base_domain}.{t}" for t in x]),
        (generate_typos(base_domain), "Typosquatting", lambda x: [f"{n}.{t}" for n in x for t in [base_tld, "com"]]),
        (generate_homoglyphs(base_domain), "Homoglyphs", lambda x: [f"{n}.{base_tld}" for n in x]),
        (generate_keywords(base_domain), "Keyword Insertion", lambda x: [f"{n}.{t}" for n in x for t in [base_tld, "com"]]),
        (generate_subdomains(base_domain, base_tld), "Subdomain (Simulated)", lambda x: [f"{n}.{base_tld}" for n in x])
    ]

    for raw_list, tech, formatter in generators:
        formatted_list = formatter(raw_list)
        for domain in formatted_list:
            if domain not in checked_domains:
                results.append({
                    "base_url": base_url,
                    "generated_domain": domain,
                    "technique": tech,
                    "status": "Pending",
                    "ip_address": None
                })
                checked_domains.add(domain)

    print(f"[*] Generated {len(results)} potential threat vectors.")
    print("[*] Starting resolution checks...")

    active_count = 0
    start_time = time.time()

    for i, entry in enumerate(results):
        if i % 20 == 0:
            # Fixed f-string format
            msg = f"\rProgress: {i}/{len(results)}..."
            sys.stdout.write(msg)
            sys.stdout.flush()

        time.sleep(0.01)
        status, ip = check_domain(entry["generated_domain"])
        entry["status"] = status
        entry["ip_address"] = ip if ip else "-"
        
        if status == "Active":
            active_count += 1

    sys.stdout.write(f"\rProgress: {len(results)}/{len(results)} Done.\n")

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["base_url", "generated_domain", "status", "ip_address", "technique"])
            writer.writeheader()
            writer.writerows(results)
        print(f"\n[+] Scan complete.")
        print(f"    Total Active: {active_count}")
        print(f"    Active Rate: {active_count/len(results)*100:.1f}%")
        print(f"    Saved to: {output_file}")
    except IOError as e:
        print(f"[Error] Could not write to file: {e}")

if __name__ == "__main__":
    main()