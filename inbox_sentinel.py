"""
inbox_sentinel.py - Autonomous Inbound Reply Monitor & Lead Classifier
Monitors Gmail inbox via IMAP SSL, classifies incoming contractor responses,
identifies uploaded plan sets/drawings, updates CRM pipeline state,
and dispatches instant phone/desktop notifications.
"""

import os
import re
import sys
import json
import time
import email
import imaplib
from email.header import decode_header
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure UTF-8 console output on Windows
if sys.stdout and getattr(sys.stdout, "encoding", None) != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_DIR = Path(__file__).parent
ENV_FILE = DATA_DIR / ".env"
STATE_FILE = DATA_DIR / "campaign_state.json"
MASTER_DB_FILE = DATA_DIR / "leads_master_db.json"
SENTINEL_STATE_FILE = DATA_DIR / "sentinel_state.json"

from alert_system import AlertSystem

HOT_KEYWORDS = [
    "plan", "plans", "drawing", "drawings", "blueprint", "blueprints",
    "takeoff", "take-off", "take off", "bid", "bidding", "quote",
    "pricing", "spec", "specs", "specification", "estimator", "rfp",
    "dropbox", "google drive", "onedrive", "box.com", "wetransfer",
    "sharefile", "planswift", "bluebeam"
]

INTERESTED_KEYWORDS = [
    "rate", "rates", "cost", "fee", "how much", "samples", "portfolio",
    "call me", "phone", "interested", "availability", "turnaround", "schedule a call"
]

UNSUBSCRIBE_KEYWORDS = [
    "unsubscribe", "remove", "take me off", "stop emailing", "do not contact", "opt out"
]

PLAN_EXTENSIONS = (
    ".pdf", ".dwg", ".dxf", ".pln", ".zip", ".rar", ".7z", ".xlsx", ".xls"
)

def decode_mime_words(raw_header: Optional[str]) -> str:
    """Decode MIME encoded header words safely."""
    if not raw_header:
        return ""
    decoded_parts = []
    for part, enc in decode_header(raw_header):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(enc or "utf-8", errors="replace"))
            except Exception:
                decoded_parts.append(part.decode("latin-1", errors="replace"))
        else:
            decoded_parts.append(str(part))
    return " ".join(decoded_parts)

def extract_email_address(from_header: str) -> str:
    """Extract clean email address from From: header."""
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1).lower().strip()
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
    if match:
        return match.group(0).lower().strip()
    return from_header.lower().strip()

class InboxSentinel:
    def __init__(self):
        self.alert_system = AlertSystem()
        self.creds = self._load_creds()
        self.leads_lookup = self._build_leads_lookup()
        self.sentinel_state = self._load_sentinel_state()

    def _load_creds(self) -> Dict[str, str]:
        user = os.environ.get("GMAIL_USER", "harriswilford1618@gmail.com")
        pwd = os.environ.get("GMAIL_APP_PASS", "")
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "GMAIL_USER":
                            user = v.strip().strip('"').strip("'")
                        elif k.strip() == "GMAIL_APP_PASS":
                            pwd = v.strip().strip('"').strip("'")
        return {"user": user, "pass": pwd}

    def _build_leads_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Index master leads by email and company domain for fast matching."""
        lookup = {}
        if MASTER_DB_FILE.exists():
            try:
                with open(MASTER_DB_FILE, "r", encoding="utf-8") as f:
                    leads = json.load(f)
                    for l in leads:
                        email_addr = (l.get("email") or "").lower().strip()
                        if email_addr:
                            lookup[email_addr] = l
            except Exception:
                pass
        return lookup

    def _load_sentinel_state(self) -> Dict[str, Any]:
        if SENTINEL_STATE_FILE.exists():
            try:
                with open(SENTINEL_STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"processed_uids": [], "last_check_timestamp": None, "total_replies_captured": 0}

    def _save_sentinel_state(self):
        with open(SENTINEL_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.sentinel_state, f, indent=2)

    def _update_campaign_state(self, lead_id: Optional[int], email_addr: str, status: str, reply_info: Dict[str, Any]):
        """Persist reply or unsubscribe into campaign_state.json."""
        if not STATE_FILE.exists():
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {"sent_ids": [], "replied_ids": [], "sample_requested_ids": [], "closed_ids": []}

        state.setdefault("replied_ids", [])
        state.setdefault("sample_requested_ids", [])
        state.setdefault("blacklisted_emails", [])
        state.setdefault("inbound_opportunities", [])

        if status == "UNSUBSCRIBE":
            if email_addr not in state["blacklisted_emails"]:
                state["blacklisted_emails"].append(email_addr)
        else:
            if lead_id and lead_id not in state["replied_ids"]:
                state["replied_ids"].append(lead_id)
            if status == "HOT_LEAD_PLANS" and lead_id and lead_id not in state["sample_requested_ids"]:
                state["sample_requested_ids"].append(lead_id)
            state["inbound_opportunities"].append(reply_info)

        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def classify_email(self, subject: str, body: str, attachments: List[str]) -> str:
        """Classify message intent into HOT_LEAD_PLANS, INTERESTED, UNSUBSCRIBE, or GENERAL."""
        content = (subject + " " + body).lower()

        # Check unsubscribe first
        if any(unsub in content for unsub in UNSUBSCRIBE_KEYWORDS):
            return "UNSUBSCRIBE"

        # Check for drawing attachments or plan links
        has_plan_attachment = any(att.lower().endswith(PLAN_EXTENSIONS) for att in attachments)
        has_hot_keyword = any(kw in content for kw in HOT_KEYWORDS)

        if has_plan_attachment or has_hot_keyword:
            return "HOT_LEAD_PLANS"

        if any(kw in content for kw in INTERESTED_KEYWORDS):
            return "INTERESTED"

        return "GENERAL_INQUIRY"

    def parse_message_body_and_attachments(self, msg: email.message.Message) -> Tuple[str, List[str]]:
        """Extract plain text snippet and attachment filenames."""
        body = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition") or "")
                filename = part.get_filename()
                if filename:
                    decoded_fn = decode_mime_words(filename)
                    attachments.append(decoded_fn)
                elif "attachment" in content_disposition:
                    fn = part.get_param("name")
                    if fn:
                        attachments.append(decode_mime_words(fn))

                content_type = part.get_content_type()
                if content_type == "text/plain" and not filename:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode("utf-8", errors="replace") + "\n"
                    except Exception:
                        pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="replace")
            except Exception:
                pass

        snippet = " ".join(body.split())[:400]
        return snippet, attachments

    def scan_inbox(self) -> List[Dict[str, Any]]:
        """
        Connect to IMAP and scan for incoming replies.
        Returns list of newly discovered contractor inquiries.
        """
        user = self.creds["user"]
        pwd = self.creds["pass"]

        if not user or not pwd:
            print("[!] InboxSentinel: Missing GMAIL_USER or GMAIL_APP_PASS credentials.")
            return []

        print(f"[*] InboxSentinel: Connecting to IMAP (imap.gmail.com:993) as {user}...")
        new_inquiries = []

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=20)
            mail.login(user, pwd)
            mail.select("INBOX", readonly=True)

            # Search unseen messages
            status, response = mail.search(None, "UNSEEN")
            message_ids = response[0].split() if status == "OK" and response[0] else []

            # If no unread, check recent messages
            if not message_ids:
                status, response = mail.search(None, "ALL")
                if status == "OK" and response[0]:
                    message_ids = response[0].split()

            # Always limit inspection to the most recent 10 messages to ensure sub-second speed
            if len(message_ids) > 10:
                message_ids = message_ids[-10:]

            print(f"[*] InboxSentinel: Scanning {len(message_ids)} message headers...")

            for msg_id_bytes in reversed(message_ids):
                uid_str = msg_id_bytes.decode()
                if uid_str in self.sentinel_state.get("processed_uids", []):
                    continue

                # Fast lightweight header fetch first
                status, data = mail.fetch(msg_id_bytes, "(RFC822.HEADER)")
                if status != "OK" or not data or not data[0]:
                    continue

                raw_header = None
                for part in data:
                    if isinstance(part, tuple) and len(part) >= 2:
                        raw_header = part[1]
                        break

                if not raw_header:
                    continue

                msg = email.message_from_bytes(raw_header)
                from_raw = decode_mime_words(msg.get("From"))
                sender_email = extract_email_address(from_raw)
                subject = decode_mime_words(msg.get("Subject"))
                date_str = msg.get("Date")

                # Ignore automated google/security emails and own emails
                if sender_email == user.lower() or "google.com" in sender_email or "security" in sender_email or "accounts.google" in sender_email:
                    self.sentinel_state.setdefault("processed_uids", []).append(uid_str)
                    continue

                # Quick relevance check: either sender is in our leads database, or subject mentions takeoff/plans
                matched_lead = self.leads_lookup.get(sender_email)
                subj_lower = subject.lower()
                is_relevant = (matched_lead is not None) or any(k in subj_lower for k in ("takeoff", "plan", "bid", "quote", "estimating"))

                if not is_relevant:
                    self.sentinel_state.setdefault("processed_uids", []).append(uid_str)
                    continue

                # Fetch full message only for relevant candidate
                status, full_data = mail.fetch(msg_id_bytes, "(RFC822)")
                if status != "OK" or not full_data or not full_data[0]:
                    continue
                full_msg = email.message_from_bytes(full_data[0][1])

                # Match sender against master leads database or sent campaign
                matched_lead = self.leads_lookup.get(sender_email)
                company = matched_lead.get("company", "Contractor Client") if matched_lead else "Prospective Client"
                lead_id = matched_lead.get("id") if matched_lead else None

                snippet, attachments = self.parse_message_body_and_attachments(full_msg)
                intent = self.classify_email(subject, snippet, attachments)

                inquiry_record = {
                    "uid": uid_str,
                    "company": company,
                    "lead_id": lead_id,
                    "sender_email": sender_email,
                    "subject": subject,
                    "date": date_str,
                    "intent": intent,
                    "snippet": snippet,
                    "attachments": attachments,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }

                if intent in ("HOT_LEAD_PLANS", "INTERESTED"):
                    print(f"\n[HOT ALARM] Incoming contractor inquiry from {company} <{sender_email}>!")
                    print(f"    Subject: {subject}")
                    print(f"    Attachments: {attachments}")
                    self.alert_system.notify_hot_lead(
                        company=company,
                        sender_email=sender_email,
                        subject=subject,
                        snippet=snippet,
                        attachments=attachments,
                        intent=intent
                    )
                    self._update_campaign_state(lead_id, sender_email, intent, inquiry_record)
                    new_inquiries.append(inquiry_record)
                elif intent == "UNSUBSCRIBE":
                    print(f"[!] Unsubscribe request from {sender_email}. Blacklisting.")
                    self._update_campaign_state(lead_id, sender_email, "UNSUBSCRIBE", inquiry_record)

                self.sentinel_state.setdefault("processed_uids", []).append(uid_str)

            mail.close()
            mail.logout()

            self.sentinel_state["last_check_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.sentinel_state["total_replies_captured"] += len(new_inquiries)
            self._save_sentinel_state()

        except Exception as e:
            print(f"[!] InboxSentinel Error: {e}")

        return new_inquiries

if __name__ == "__main__":
    sentinel = InboxSentinel()
    print("[*] Running manual Inbox scan...")
    found = sentinel.scan_inbox()
    print(f"[+] Scan finished. Inbound opportunities discovered: {len(found)}")
