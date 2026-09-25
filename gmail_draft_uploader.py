"""
Direct Gmail Draft Uploader
Uploads email drafts directly into your real Gmail "Drafts" folder (mail.google.com/#drafts)
via either:
1. IMAP SSL Append (imap.gmail.com:993 to "[Gmail]/Drafts")
2. Official Gmail API OAuth2 (users.drafts.create)
"""

import os
import sys
import time
import base64
import json
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from pitch_generator import prepare_campaign_touch, SENDER_PROFILE
from agent_mailer import load_env_credentials, load_campaign_state, save_campaign_state

DATA_DIR = Path(__file__).parent
CREDENTIALS_FILE = DATA_DIR / "credentials.json"
TOKEN_FILE = DATA_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify"
]

class GmailDraftUploader:
    def __init__(self):
        self.creds = load_env_credentials()
        self.state = load_campaign_state()

    def upload_via_imap(self, leads: List[Dict[str, Any]], touch_number: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        Upload drafts directly to Gmail using IMAP SSL append to '[Gmail]/Drafts'.
        Requires GMAIL_USER and GMAIL_APP_PASS in .env.
        """
        user = self.creds.get("user")
        app_pass = self.creds.get("pass")

        if not user or not app_pass:
            print("[!] IMAP draft upload requires GMAIL_USER and GMAIL_APP_PASS in .env")
            return {"uploaded": 0, "error": "MISSING_CREDENTIALS"}

        batch = leads[:limit]
        print(f"\n[+] Connecting to imap.gmail.com:993 as {user}...")
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            imap.login(user, app_pass)
            print("[+] Logged into Gmail IMAP successfully.")
        except Exception as e:
            print(f"[!] IMAP Authentication Failed: {e}")
            return {"uploaded": 0, "error": str(e)}

        # Gmail standard drafts mailbox is typically '[Gmail]/Drafts'
        drafts_folder = '"[Gmail]/Drafts"'
        uploaded_count = 0

        try:
            for idx, lead in enumerate(batch, 1):
                pitch = prepare_campaign_touch(lead, touch_number=touch_number)
                recipient = pitch["recipient"]
                subject = pitch["subject"]
                body = pitch["body"]
                comp = lead.get("company", "Contractor")
                lead_id = lead.get("id")

                msg = MIMEMultipart()
                msg["From"] = f"{SENDER_PROFILE['name']} <{user}>"
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))

                print(f"[{idx}/{len(batch)}] Uploading draft for {comp} ({recipient})...", end=" ")
                # Append to Gmail Drafts folder with \Draft flag
                res, data = imap.append(drafts_folder, "\\Draft", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
                if res == "OK":
                    print("UPLOADED TO DRAFTS.")
                    uploaded_count += 1
                    if lead_id and lead_id not in self.state.get("sent_ids", []):
                        self.state.setdefault("drafted_ids", []).append(lead_id)
                else:
                    print(f"FAILED ({res})")

        except Exception as e:
            print(f"\n[!] Error during draft upload: {e}")
        finally:
            try:
                imap.logout()
            except Exception:
                pass
            save_campaign_state(self.state)

        print(f"\n[SUCCESS] Uploaded {uploaded_count} drafts directly into your Gmail 'Drafts' folder!")
        print("Open https://mail.google.com/mail/#drafts to review and send them.")
        return {"uploaded": uploaded_count, "mode": "IMAP"}

    def upload_via_api(self, leads: List[Dict[str, Any]], touch_number: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        Upload drafts directly to Gmail using the official Google Gmail REST API.
        Does NOT require an App Password. Uses standard OAuth2 browser authorization.
        """
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            print("[!] Google API client packages missing. Run: pip install google-auth-oauthlib google-api-python-client")
            return {"uploaded": 0, "error": "MISSING_PACKAGES"}

        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    print("\n" + "=" * 75)
                    print(" [!] GMAIL API SETUP NEEDED (ONE-TIME SETUP - 2 MINUTES)")
                    print("=" * 75)
                    print(" To upload drafts directly via official Gmail API without an App Password:")
                    print(" 1. Go to Google Cloud Console: https://console.cloud.google.com/")
                    print(" 2. Create a project and enable the 'Gmail API'")
                    print(" 3. Go to 'APIs & Services' -> 'Credentials' -> 'Create Credentials' -> 'OAuth client ID'")
                    print(" 4. Select Application type: 'Desktop App' and click Create")
                    print(f" 5. Download the JSON file and save it as:")
                    print(f"    {CREDENTIALS_FILE}")
                    print("=" * 75 + "\n")
                    return {"uploaded": 0, "error": "CREDENTIALS_FILE_NOT_FOUND"}

                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)
        batch = leads[:limit]
        uploaded_count = 0

        print(f"\n[+] Uploading {len(batch)} drafts directly into Gmail via official API...")
        for idx, lead in enumerate(batch, 1):
            pitch = prepare_campaign_touch(lead, touch_number=touch_number)
            recipient = pitch["recipient"]
            subject = pitch["subject"]
            body = pitch["body"]
            comp = lead.get("company", "Contractor")
            lead_id = lead.get("id")

            msg = MIMEMultipart()
            msg["From"] = f"{SENDER_PROFILE['name']} <{self.creds.get('user')}>"
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
            draft_body = {"message": {"raw": raw_msg}}

            print(f"[{idx}/{len(batch)}] Creating Gmail draft for {comp} ({recipient})...", end=" ")
            try:
                draft_res = service.users().drafts().create(userId="me", body=draft_body).execute()
                print(f"OK (Draft ID: {draft_res.get('id')[:10]}...)")
                uploaded_count += 1
                if lead_id:
                    self.state.setdefault("drafted_ids", []).append(lead_id)
            except Exception as e:
                print(f"FAILED: {e}")

        save_campaign_state(self.state)
        print(f"\n[SUCCESS] Uploaded {uploaded_count} drafts directly into your Gmail account!")
        print("Check them right now at: https://mail.google.com/mail/#drafts")
        return {"uploaded": uploaded_count, "mode": "GMAIL_API"}

    def upload_drafts(self, leads: List[Dict[str, Any]], touch_number: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        Auto-selects the best available method:
        - If TOKEN_FILE or CREDENTIALS_FILE exists -> Uses official Gmail API.
        - If GMAIL_APP_PASS is set in .env -> Uses direct IMAP append.
        - Otherwise, provides clear instructions on both options.
        """
        if TOKEN_FILE.exists() or CREDENTIALS_FILE.exists():
            return self.upload_via_api(leads, touch_number=touch_number, limit=limit)
        
        if self.creds.get("pass"):
            return self.upload_via_imap(leads, touch_number=touch_number, limit=limit)

        print("\n" + "=" * 75)
        print(" [!] DIRECT GMAIL DRAFT UPLOAD: AUTHENTICATION SELECTION")
        print("=" * 75)
        print(" You can upload drafts directly into your Gmail 'Drafts' folder using either:")
        print("\n 1. IMAP DIRECT UPLOAD (Fastest if you have a Google App Password):")
        print("    - Add GMAIL_APP_PASS=your_16_char_password into .env")
        print("    - Command: python send_gmail.py --upload-imap 10")
        print("\n 2. OFFICIAL GMAIL API (Best if App Passwords are not shown in your account):")
        print("    - Zero password needed.")
        print(f"    - Put Google Cloud 'credentials.json' in {DATA_DIR}")
        print("    - Command: python send_gmail.py --upload-api 10")
        print("=" * 75 + "\n")
        return {"uploaded": 0, "error": "NO_AUTH_METHOD_CONFIGURED"}

if __name__ == "__main__":
    from lead_hunter import LeadHunter
    hunter = LeadHunter()
    uploader = GmailDraftUploader()

    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    unsent = [l for l in hunter.master_leads if l.get("id") not in uploader.state.get("sent_ids", [])]

    if "--imap" in sys.argv:
        uploader.upload_via_imap(unsent, touch_number=1, limit=count)
    elif "--api" in sys.argv or "--oauth" in sys.argv:
        uploader.upload_via_api(unsent, touch_number=1, limit=count)
    else:
        uploader.upload_drafts(unsent, touch_number=1, limit=count)
