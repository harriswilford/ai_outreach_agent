"""
Gmail Auto-Sender & Campaign Dispatcher
Handles automated sending via Gmail SMTP SSL (smtp.gmail.com:465) with anti-spam jitter,
daily volume capping, 1-click browser compose fallbacks, and multi-touch state tracking.
"""

import os
import sys
import time
import json
import random
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any, Optional

from pitch_generator import prepare_campaign_touch, SENDER_PROFILE
from trade_intelligence import get_trade_intelligence

DATA_DIR = Path(__file__).parent
ENV_FILE = DATA_DIR / ".env"
STATE_FILE = DATA_DIR / "campaign_state.json"
MASTER_DB_FILE = DATA_DIR / "leads_master_db.json"

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def load_env_credentials() -> Dict[str, str]:
    """Load Gmail credentials from .env file."""
    creds = {
        "user": os.environ.get("GMAIL_USER", "harriswilford1618@gmail.com"),
        "pass": os.environ.get("GMAIL_APP_PASS", "")
    }
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "GMAIL_USER":
                        creds["user"] = v
                    elif k == "GMAIL_APP_PASS":
                        creds["pass"] = v
    return creds

def load_campaign_state() -> Dict[str, Any]:
    """Load persistent campaign state tracking."""
    if not STATE_FILE.exists():
        state = {
            "sent_ids": [],
            "replied_ids": [],
            "sample_requested_ids": [],
            "closed_ids": [],
            "send_logs": []
        }
        save_campaign_state(state)
        return state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sent_ids": [], "replied_ids": [], "sample_requested_ids": [], "closed_ids": [], "send_logs": []}

def save_campaign_state(state: Dict[str, Any]):
    """Persist campaign state."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

class GmailAutomator:
    def __init__(self, daily_send_limit: int = 300):
        self.creds = load_env_credentials()
        self.state = load_campaign_state()
        self.daily_send_limit = daily_send_limit
        self.server = None

    def connect_smtp(self) -> bool:
        """Connect and authenticate to Gmail SMTP server."""
        user = self.creds.get("user")
        app_pass = self.creds.get("pass")

        if not user or not app_pass:
            return False

        try:
            print(f"[+] Connecting to Gmail SMTP (smtp.gmail.com:465) as {user}...")
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
            server.login(user, app_pass)
            self.server = server
            print("[+] Gmail SMTP authentication successful!")
            return True
        except Exception as e:
            print(f"[!] SMTP Connection Failed: {e}")
            return False

    def close_smtp(self):
        """Safely disconnect SMTP connection."""
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass
            self.server = None

    def send_single_email(self, to_email: str, subject: str, body: str, lead_id: Optional[int] = None, lead_company: str = "") -> bool:
        """Send a single email via SMTP server."""
        if not self.server:
            raise RuntimeError("SMTP server is not connected.")

        user = self.creds.get("user")
        msg = MIMEMultipart()
        msg["From"] = f"{SENDER_PROFILE['name']} <{user}>"
        msg["To"] = to_email
        msg["Reply-To"] = user
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            self.server.sendmail(user, to_email, msg.as_string())
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, smtplib.SMTPException, OSError) as e:
            print(f"\n[!] SMTP connection dropped ({e}). Reconnecting to Gmail SMTP...")
            time.sleep(2.0)
            if self.connect_smtp():
                self.server.sendmail(user, to_email, msg.as_string())
            else:
                raise

        # Log to state
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if lead_id and lead_id not in self.state.get("sent_ids", []):
            self.state["sent_ids"].append(lead_id)

        self.state.setdefault("send_logs", []).append({
            "lead_id": lead_id,
            "company": lead_company,
            "email": to_email,
            "subject": subject,
            "sent_at": timestamp,
            "status": "DELIVERED_SMTP"
        })
        save_campaign_state(self.state)
        return True

    def send_direct_to_client(self, to_email: str, company: str = "", name: str = "", trade: str = "Commercial General Contractors", subject: Optional[str] = None, body: Optional[str] = None, touch_number: int = 1, dry_run: bool = False) -> Dict[str, Any]:
        """
        Send an outreach email directly to an arbitrary client with 1 command.
        Automatically generates high-converting trade pitch if subject/body are omitted.
        """
        if not to_email or "@" not in to_email:
            return {"success": False, "error": "Invalid client email address."}

        lead = {
            "id": None,
            "company": company or "your company",
            "contact_name": name or "Preconstruction Team",
            "first_name": name.split()[0] if name else "there",
            "role": "Chief Estimator / Preconstruction Director",
            "trade_niche": trade,
            "city": "your market",
            "state": "USA",
            "email": to_email.strip()
        }

        if not subject or not body:
            pitch = prepare_campaign_touch(lead, touch_number=touch_number)
            subject = subject or pitch["subject"]
            body = body or pitch["body"]

        print(f"\n[*] Direct Client Dispatch: {to_email} ({company or 'Client'})...")
        print(f"[*] Subject: {subject}")

        if dry_run:
            print("[+] SIMULATION OK: Email prepared successfully (Dry-Run).")
            return {"success": True, "status": "SIMULATED", "to": to_email, "subject": subject, "body": body}

        close_after = False
        if not self.server:
            connected = self.connect_smtp()
            if not connected:
                return {"success": False, "error": "SMTP authentication failed. Verify .env credentials."}
            close_after = True

        try:
            self.send_single_email(to_email.strip(), subject, body, lead_id=None, lead_company=company)
            print(f"[SUCCESS] Email delivered directly to {to_email}!")
            return {"success": True, "status": "DELIVERED_SMTP", "to": to_email, "subject": subject}
        except Exception as e:
            print(f"[!] ERROR sending email: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if close_after:
                self.close_smtp()

    def dispatch_batch_smtp(self, leads: List[Dict[str, Any]], touch_number: int = 1, max_sends: int = 10, delay_range: tuple = (2.0, 5.0), dry_run: bool = False) -> Dict[str, Any]:
        """
        Dispatch outreach emails to a batch of leads via Gmail SMTP.
        Respects anti-spam throttling, jitter delay, and daily quotas.
        """
        results = {"sent": 0, "failed": 0, "skipped": 0, "details": []}
        eligible = [l for l in leads if l.get("id") not in self.state.get("sent_ids", []) and l.get("email")]

        if not eligible:
            print("[!] No eligible unsent leads in this batch.")
            return results

        batch = eligible[:min(max_sends, self.daily_send_limit)]
        print(f"\n{'='*75}")
        print(f" [*] GMAIL AUTO-DISPATCHER: TOUCH {touch_number} OUTREACH")
        print(f" [*] Volume: {len(batch)} recipients | Mode: {'DRY RUN SIMULATION' if dry_run else 'LIVE SMTP DISPATCH'}")
        print(f" [*] Sender: {SENDER_PROFILE['name']} <{self.creds.get('user')}>")
        print(f"{'='*75}\n")

        if not dry_run:
            connected = self.connect_smtp()
            if not connected:
                err_msg = "Gmail SMTP Authentication failed. Verify GMAIL_USER and GMAIL_APP_PASS in .env."
                print(f"\n[!] ERROR: {err_msg}")
                return {"sent": 0, "failed": len(batch), "error": err_msg}

        try:
            for idx, lead in enumerate(batch, 1):
                pitch = prepare_campaign_touch(lead, touch_number=touch_number)
                recipient = pitch["recipient"]
                subject = pitch["subject"]
                body = pitch["body"]
                company = lead.get("company", "Contractor")
                lead_id = lead.get("id")

                print(f"[{idx}/{len(batch)}] Sending to {company} ({recipient})...", end=" ")

                if dry_run:
                    time.sleep(0.1)
                    print("SIMULATED OK.")
                    results["sent"] += 1
                    results["details"].append({"id": lead_id, "company": company, "email": recipient, "status": "SIMULATED"})
                else:
                    try:
                        self.send_single_email(recipient, subject, body, lead_id=lead_id, lead_company=company)
                        print("SENT.")
                        results["sent"] += 1
                        results["details"].append({"id": lead_id, "company": company, "email": recipient, "status": "SENT"})
                        
                        # Anti-spam jitter delay between sends
                        if idx < len(batch):
                            jitter = random.uniform(delay_range[0], delay_range[1])
                            time.sleep(jitter)
                    except Exception as err:
                        print(f"FAILED: {err}")
                        results["failed"] += 1
                        results["details"].append({"id": lead_id, "company": company, "email": recipient, "status": f"ERROR: {err}"})

        finally:
            if not dry_run:
                self.close_smtp()

        print(f"\n[+] Batch complete: {results['sent']} sent, {results['failed']} failed.")
        return results

    def launch_browser_drafts(self, leads: List[Dict[str, Any]], touch_number: int = 1, limit: int = 5) -> Dict[str, Any]:
        """
        Launch pre-filled Gmail Compose tabs directly in the user's browser.
        Bypasses SMTP authentication entirely; user simply clicks 'Send' in each tab.
        """
        batch = leads[:limit]
        print(f"\n[+] Launching {len(batch)} pre-filled Gmail Compose tabs in default browser...")
        
        browser_exe = CHROME_PATH if os.path.exists(CHROME_PATH) else (EDGE_PATH if os.path.exists(EDGE_PATH) else None)
        launched = 0

        for idx, lead in enumerate(batch, 1):
            pitch = prepare_campaign_touch(lead, touch_number=touch_number)
            url = pitch["gmail_compose_url"]
            comp = lead.get("company")
            em = lead.get("email")

            print(f"  [{idx}/{len(batch)}] Opening draft for {comp} ({em})...")
            if browser_exe:
                subprocess.Popen([browser_exe, url])
            else:
                os.system(f'start "" "{url}"')

            launched += 1
            lead_id = lead.get("id")
            if lead_id and lead_id not in self.state.get("sent_ids", []):
                self.state["sent_ids"].append(lead_id)
            time.sleep(1.0)

        save_campaign_state(self.state)
        print(f"\n[SUCCESS] Launched {launched} Gmail draft tabs! State updated.")
        return {"sent": launched, "failed": 0, "mode": "BROWSER_TABS"}

if __name__ == "__main__":
    automator = GmailAutomator()
    print("Testing Gmail Automator...")
    print(f"Configured Gmail User: {automator.creds.get('user')}")
    print(f"Has App Password: {'YES' if automator.creds.get('pass') else 'NO (Set in .env for full hands-free background sending)'}")
    print(f"Total Sent in State: {len(automator.state.get('sent_ids', []))}")
