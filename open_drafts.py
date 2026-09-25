"""
Guaranteed Direct Browser Tab Opener for Gmail Outreach Drafts
Directly invokes Google Chrome / Default Browser executable to bypass popup blockers.
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def get_browser_exe():
    if os.path.exists(CHROME_PATH):
        return CHROME_PATH
    elif os.path.exists(EDGE_PATH):
        return EDGE_PATH
    return None

def open_leads_in_browser(json_file, start_idx=0, count=10):
    if not os.path.exists(json_file):
        print(f"[!] Error: {json_file} not found.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        leads = json.load(f)

    batch = leads[start_idx : start_idx + count]
    if not batch:
        print(f"[!] No leads found in range {start_idx} to {start_idx + count}.")
        return

    browser_exe = get_browser_exe()
    print(f"\n[+] Launching {len(batch)} Gmail drafts in Chrome (Leads #{start_idx + 1} to #{start_idx + len(batch)})...")
    
    for idx, lead in enumerate(batch, 1):
        url = lead.get("gmail_compose_url")
        comp = lead.get("company")
        em = lead.get("email")
        print(f"  [{idx}/{len(batch)}] Opening draft for {comp} ({em})...")
        
        if browser_exe:
            subprocess.Popen([browser_exe, url])
        else:
            os.system(f'start "" "{url}"')
            
        time.sleep(1.2)  # Generous interval so Chrome opens each tab cleanly without throttling

    print("\n[SUCCESS] All draft tabs have been launched in your browser!")

if __name__ == "__main__":
    file_to_open = "architecture_construction_leads.json"
    start = 0
    count = 10
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--day1":
            file_to_open = "day_1_drafts_341.json"
        elif sys.argv[1] == "--arch":
            file_to_open = "architecture_construction_leads.json"
        else:
            file_to_open = sys.argv[1]
            
    if len(sys.argv) > 2:
        start = int(sys.argv[2])
    if len(sys.argv) > 3:
        count = int(sys.argv[3])
        
    open_leads_in_browser(file_to_open, start, count)
