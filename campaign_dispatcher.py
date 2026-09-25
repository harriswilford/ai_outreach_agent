"""
Takeoff & Estimation Outreach Campaign Dispatcher
Handles Multi-Inbox Gmail Automation, 1-Click Browser Draft Launching, 
SMTP Rotation, Rate-Limiting, .env Credentials, and 7-Day Campaign Management.
"""

import json
import os
import sys
import time
import random
import smtplib
import urllib.parse
import webbrowser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"
LEADS_FILE = Path(__file__).parent / "takeoff_leads_3000.json"
STATE_FILE = Path(__file__).parent / "campaign_state.json"

SELECTED_NICHES = [
    "MEP - Mechanical & HVAC",
    "MEP - Electrical",
    "MEP - Plumbing & Piping",
    "Concrete & Masonry",
    "Commercial General Contractors",
    "Flooring & Tile",
    "Painting & Wallcovering",
    "Residential Custom Builders & Remodelers"
]

def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

def load_leads():
    if not LEADS_FILE.exists():
        print(f"[!] Error: {LEADS_FILE} not found. Run takeoff_lead_scraper.py first.")
        sys.exit(1)
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_state():
    if not STATE_FILE.exists():
        state = {"sent_ids": [], "replied_ids": [], "sample_requested_ids": [], "closed_ids": []}
        save_state(state)
        return state
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def generate_gmail_compose_url(to, subject, body):
    base_url = "https://mail.google.com/mail/?view=cm&fs=1"
    params = {
        "to": to,
        "su": subject,
        "body": body
    }
    return base_url + "&" + urllib.parse.urlencode(params)

def display_stats(leads, state):
    print("=" * 80)
    print(" [*] 7-DAY 3,000 CONTRACTOR OUTREACH PIPELINE - REAL-TIME STATUS")
    print("=" * 80)
    
    total = len(leads)
    sent_count = len(state.get("sent_ids", []))
    replied_count = len(state.get("replied_ids", []))
    sample_count = len(state.get("sample_requested_ids", []))
    closed_count = len(state.get("closed_ids", []))
    
    print(f"Total Staged Prospects     : {total:,}")
    print(f"Outreach Dispatched (Sent) : {sent_count:,} ({(sent_count/total)*100:.1f}%)")
    print(f"Responses Received         : {replied_count:,}")
    print(f"Plan Sets Received         : {sample_count:,}")
    print(f"Closed Paying Clients      : {closed_count:,}")
    print("-" * 80)
    
    niche_counts = {}
    for l in leads:
        n = l["trade_niche"]
        niche_counts[n] = niche_counts.get(n, 0) + 1
        
    print(f"{'TRADE / NICHE':<42} | {'PROSPECTS':<10} | {'TYPICAL TICKET'}")
    print("-" * 80)
    for n, count in sorted(niche_counts.items(), key=lambda x: x[1], reverse=True):
        sample_val = next(l["typical_value"] for l in leads if l["trade_niche"] == n)
        print(f"{n:<42} | {count:<10} | {sample_val}")
    print("=" * 80)
    
    print(f"{'SCHEDULE':<15} | {'LEADS':<10} | {'STATUS':<20} | {'RECOMMENDED INBOXES'}")
    print("-" * 80)
    for d in range(1, 8):
        day_leads = [l for l in leads if l.get("target_outreach_day") == d]
        day_sent = [l for l in day_leads if l["id"] in state["sent_ids"]]
        status = f"{len(day_sent)}/{len(day_leads)} Sent"
        print(f"Day {d:<11} | {len(day_leads):<10} | {status:<20} | 7-8 Inboxes (48 sends/inbox)")
    print("=" * 80)

def open_browser_batch(leads, state, day=1, limit=10):
    target_leads = [l for l in leads if l.get("target_outreach_day") == day and l["id"] not in state["sent_ids"]]
    if not target_leads:
        print(f"[!] No unsent leads found for Day {day}.")
        return
        
    batch = target_leads[:limit]
    print(f"\n[+] Opening {len(batch)} Gmail compose drafts in your browser for Day {day}...")
    for idx, lead in enumerate(batch, 1):
        url = generate_gmail_compose_url(lead["email"], lead["subject"], lead["body"])
        print(f"  [{idx}/{len(batch)}] {lead['company']} ({lead['trade_niche']}) -> {lead['email']}")
        webbrowser.open(url)
        time.sleep(0.5)
        state["sent_ids"].append(lead["id"])
    
    save_state(state)
    print(f"\n[SUCCESS] Launched {len(batch)} draft tabs in Gmail. State updated.")

def send_via_smtp_pipeline(leads, state, gmail_user, app_password, day=1, max_sends=341, dry_run=False):
    target_leads = [l for l in leads if l.get("target_outreach_day") == day and l["id"] not in state["sent_ids"]]
    if not target_leads:
        print(f"[!] No unsent leads available for Day {day}.")
        return
        
    batch = target_leads[:max_sends]
    print(f"\n" + "="*80)
    print(f" [*] AUTOMATED SMTP OUTREACH DISPATCH - DAY {day} BATCH ({len(batch)} LEADS)")
    print(f" [*] Sender: Harris Wilford <{gmail_user}>")
    print(f" [*] Mode  : {'DRY RUN SIMULATION' if dry_run else 'LIVE PRODUCTION SEND'}")
    print("="*80)
    
    if not dry_run:
        try:
            print(f"[+] Connecting to smtp.gmail.com:465 (SSL)...")
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(gmail_user, app_password)
            print("[+] Logged into Gmail SMTP successfully.\n")
        except Exception as e:
            print(f"\n[ERROR] Authentication failed: {e}")
            print("\n[TROUBLESHOOTING GMAIL SMTP]")
            print("1. Ensure 2-Step Verification is turned ON for your Google Account.")
            print("2. Generate a 16-character App Password at: https://myaccount.google.com/apppasswords")
            print("3. Set GMAIL_USER and GMAIL_APP_PASS in F:\\Antigravity CLI\\outreach_engine\\.env")
            return
    else:
        server = None

    sent_this_session = 0
    try:
        for idx, lead in enumerate(batch, 1):
            msg = MIMEMultipart()
            msg["From"] = f"Harris Wilford <{gmail_user}>"
            msg["To"] = lead["email"]
            msg["Subject"] = lead["subject"]
            msg.attach(MIMEText(lead["body"], "plain"))
            
            print(f"[{idx}/{len(batch)}] Sending to {lead['company']} ({lead['email']}) [{lead['trade_niche']}]...", end=" ")
            
            if not dry_run:
                server.sendmail(gmail_user, lead["email"], msg.as_string())
                state["sent_ids"].append(lead["id"])
                
                # Anti-spam deliverability jitter delay (1.5 - 3.5 seconds)
                delay = random.uniform(1.5, 3.5)
                time.sleep(delay)
            else:
                state["sent_ids"].append(lead["id"])
                time.sleep(0.05)
                
            print("SENT.")
            sent_this_session += 1
            
            # Periodically save state
            if idx % 10 == 0:
                save_state(state)
                
    except KeyboardInterrupt:
        print("\n[!] Dispatch paused by user. Saving current progress...")
    finally:
        if server:
            server.quit()
        save_state(state)
        print(f"\n[SUCCESS] Processed {sent_this_session}/{len(batch)} emails for Day {day}!")
        print(f"[+] Current Total Dispatched in Pipeline: {len(state['sent_ids'])} leads")

def export_batch_csv(leads, day):
    batch = [l for l in leads if l.get("target_outreach_day") == day]
    out_file = Path(__file__).parent / f"day_{day}_batch_{len(batch)}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2)
    print(f"[+] Exported Day {day} batch ({len(batch)} leads) to {out_file}")

if __name__ == "__main__":
    load_env()
    use_selected = "--selected" in sys.argv or True  # default to selected niches
    dry_run = "--dry-run" in sys.argv
    
    leads = load_leads()
    if use_selected:
        leads = [l for l in leads if l["trade_niche"] in SELECTED_NICHES]
        sys.argv = [a for a in sys.argv if a not in ["--selected", "--dry-run"]]
        
    state = load_state()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--stats":
            display_stats(leads, state)
        elif cmd == "--browser":
            day = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            open_browser_batch(leads, state, day, limit)
        elif cmd == "--smtp":
            day = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            max_sends = int(sys.argv[3]) if len(sys.argv) > 3 else 341
            user = os.environ.get("GMAIL_USER")
            pw = os.environ.get("GMAIL_APP_PASS")
            
            if not user or not pw:
                if dry_run:
                    user = "harris.wilford@takeoffs.com"
                    pw = "dummy_pass"
                else:
                    print("\n[!] Gmail Credentials Required for Automated SMTP Dispatch:")
                    user = input("Enter Gmail / Google Workspace address: ").strip()
                    pw = input("Enter 16-Character Google App Password: ").strip()
                    
            send_via_smtp_pipeline(leads, state, user, pw, day, max_sends, dry_run=dry_run)
        elif cmd == "--export":
            day = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            export_batch_csv(leads, day)
        else:
            print("Unknown command. Use --stats, --browser [day] [limit], --smtp [day] [max], or --export [day].")
    else:
        display_stats(leads, state)
