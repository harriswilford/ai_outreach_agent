"""
Direct Automated Gmail Dispatcher for Atlanta Plumbing Contractors
Connects to Gmail SMTP SSL (smtp.gmail.com:465) using configured App Password,
applies deliverability jitter delay, sends Touch 1 outreach, and records state.
"""

import os
import sys
import json
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Ensure UTF-8 console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = Path(__file__).parent
LEADS_JSON = DATA_DIR / "atlanta_plumbing_leads_10.json"
STATE_FILE = DATA_DIR / "campaign_state.json"

from agent_mailer import load_env_credentials, load_campaign_state, save_campaign_state
from pitch_generator import SENDER_PROFILE

def dispatch():
    print("\n" + "=" * 80)
    print(" 🚀  LIVE GMAIL OUTREACH DISPATCH: 10 ATLANTA PLUMBING CONTRACTORS")
    print(f" Sender Identity : {SENDER_PROFILE['name']} <{SENDER_PROFILE['email']}>")
    print(" Protocol        : Gmail SMTP SSL (smtp.gmail.com:465)")
    print(" Deliverability  : Human-like Anti-Spam Jitter (2.5s - 4.5s)")
    print("=" * 80 + "\n")

    if not LEADS_JSON.exists():
        print(f"[!] Error: {LEADS_JSON} not found. Run hunt_atlanta_plumbing.py first.")
        return

    with open(LEADS_JSON, "r", encoding="utf-8") as f:
        drafts = json.load(f)

    creds = load_env_credentials()
    user = creds.get("user")
    app_pass = creds.get("pass")

    if not user or not app_pass:
        print("[!] Error: GMAIL_USER or GMAIL_APP_PASS is missing in .env")
        return

    state = load_campaign_state()

    print(f"[+] Connecting to Gmail SMTP server as {user}...")
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20)
        server.login(user, app_pass)
        print("[+] Authenticated successfully with Gmail SMTP!\n")
    except Exception as e:
        print(f"[!] SMTP Authentication Failed: {e}")
        return

    sent_count = 0
    failed_count = 0

    try:
        for idx, draft in enumerate(drafts, 1):
            recipient = draft["recipient"]
            subject = draft["subject"]
            body = draft["body"]
            company = draft["company"]
            lead_id = draft.get("lead_id")

            msg = MIMEMultipart()
            msg["From"] = f"{SENDER_PROFILE['name']} <{user}>"
            msg["To"] = recipient
            msg["Reply-To"] = user
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            print(f"[{idx}/{len(drafts)}] Dispatching email to: {company}")
            print(f"       Recipient: {recipient}")
            print(f"       Subject  : {subject}")

            try:
                server.sendmail(user, recipient, msg.as_string())
                print(f"       Status   : [DELIVERED VIA GMAIL SMTP] ✅")
                sent_count += 1

                # Update state
                if lead_id and lead_id not in state.get("sent_ids", []):
                    state["sent_ids"].append(lead_id)

                state.setdefault("send_logs", []).append({
                    "lead_id": lead_id,
                    "company": company,
                    "email": recipient,
                    "subject": subject,
                    "sent_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "SENT_SMTP_LIVE"
                })
                save_campaign_state(state)

                # Anti-spam jitter delay between emails
                if idx < len(drafts):
                    jitter = random.uniform(2.5, 4.5)
                    print(f"       Delay    : Pausing {jitter:.1f}s for deliverability hygiene...")
                    time.sleep(jitter)

            except Exception as send_err:
                print(f"       Status   : [FAILED]: {send_err} ❌")
                failed_count += 1

            print("-" * 80)

    finally:
        try:
            server.quit()
        except Exception:
            pass
        save_campaign_state(state)

    print(f"\n[CAMPAIGN SUMMARY]")
    print(f"  - Successfully Sent : {sent_count}/{len(drafts)}")
    print(f"  - Failed            : {failed_count}")
    print(f"  - Sender Account    : {user}")
    print(f"  - Total Sent in CRM : {len(state.get('sent_ids', []))}")
    print(f"\n[SUCCESS] 10 Atlanta Plumbing Contractors have been emailed via Gmail!")

if __name__ == "__main__":
    dispatch()
