"""
alert_system.py - Multi-Channel Alert & Notification System
Delivers instant alerts to Phone (Telegram/Discord) and Windows Desktop Toast
when contractors reply, submit drawings/plans, or when daily pipeline milestones are met.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List

DATA_DIR = Path(__file__).parent
ENV_FILE = DATA_DIR / ".env"

def load_alert_config() -> Dict[str, str]:
    """Load alert credentials and settings from .env."""
    config = {
        "telegram_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
        "discord_webhook": os.environ.get("DISCORD_WEBHOOK_URL", ""),
        "desktop_toast": os.environ.get("ENABLE_DESKTOP_TOAST", "true").lower() in ("true", "1", "yes")
    }
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "TELEGRAM_BOT_TOKEN":
                        config["telegram_token"] = v
                    elif k == "TELEGRAM_CHAT_ID":
                        config["telegram_chat_id"] = v
                    elif k == "DISCORD_WEBHOOK_URL":
                        config["discord_webhook"] = v
                    elif k == "ENABLE_DESKTOP_TOAST":
                        config["desktop_toast"] = v.lower() in ("true", "1", "yes")
                    elif k == "TELEGRAM_PROXY":
                        config["telegram_proxy"] = v
                    elif k == "TELEGRAM_API_BASE_URL":
                        config["telegram_api_base"] = v
    return config

class AlertSystem:
    def __init__(self):
        self.config = load_alert_config()
        self.log_file = DATA_DIR / "alerts.log"

    def _log(self, text: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {text}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def send_telegram(self, message: str) -> bool:
        """Send message via Telegram Bot API (standard library urllib with optional proxy)."""
        token = self.config.get("telegram_token")
        chat_id = self.config.get("telegram_chat_id")
        if not token or not chat_id:
            return False

        base_url = (self.config.get("telegram_api_base") or "https://api.telegram.org").strip().rstrip("/")
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = "https://" + base_url
        url = f"{base_url}/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            proxy = self.config.get("telegram_proxy") or os.environ.get("HTTPS_PROXY")
            opener = None
            if proxy:
                handler = urllib.request.ProxyHandler({'https': proxy, 'http': proxy})
                opener = urllib.request.build_opener(handler)
            else:
                opener = urllib.request.build_opener()

            with opener.open(req, timeout=12) as resp:
                if resp.status == 200:
                    self._log("Telegram alert sent successfully.")
                    return True
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8", errors="ignore")
                self._log(f"Telegram API HTTP {e.code}: {err_body}")
                print(f"[!] Telegram API HTTP {e.code}: {err_body}")
            except Exception:
                self._log(f"Telegram send failed: {e}")
            return False
        except Exception as e:
            self._log(f"Telegram send failed: {e}")
            return False

    def send_discord(self, title: str, description: str, fields: Optional[List[Dict[str, Any]]] = None, color: int = 0x00FF88) -> bool:
        """Send rich embed message to Discord Webhook."""
        webhook_url = self.config.get("discord_webhook")
        if not webhook_url:
            return False

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "footer": {"text": "Autonomous Takeoff Lead Agent"}
        }
        if fields:
            embed["fields"] = fields

        payload = {"embeds": [embed]}
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "AutonomousAgent/1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 204):
                    self._log("Discord alert sent successfully.")
                    return True
        except Exception as e:
            self._log(f"Discord send failed: {e}")
        return False

    def send_windows_toast(self, title: str, message: str) -> bool:
        """Display native Windows notification via PowerShell System.Windows.Forms balloon tip."""
        if not self.config.get("desktop_toast", True):
            return False

        clean_title = title.replace('"', '`"').replace("'", "`'")
        clean_msg = message.replace('"', '`"').replace("'", "`'").replace("\n", " ")

        ps_script = (
            f"[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null; "
            f"$notify = New-Object System.Windows.Forms.NotifyIcon; "
            f"$notify.Icon = [System.Drawing.SystemIcons]::Information; "
            f"$notify.BalloonTipTitle = \"{clean_title}\"; "
            f"$notify.BalloonTipText = \"{clean_msg}\"; "
            f"$notify.Visible = $true; "
            f"$notify.ShowBalloonTip(7000); "
            f"Start-Sleep -Seconds 2; "
            f"$notify.Dispose()"
        )
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._log(f"Windows desktop toast triggered: {title}")
            return True
        except Exception as e:
            self._log(f"Windows desktop toast failed: {e}")
            return False

    def notify_hot_lead(self, company: str, sender_email: str, subject: str, snippet: str, attachments: List[str], intent: str = "HOT_LEAD"):
        """Trigger multi-channel alert when a contractor replies or submits drawings."""
        badge = "🚨 [HOT LEAD WITH PLANS]" if attachments else "🎯 [CLIENT INQUIRY RECEIVED]"
        ascii_badge = "[HOT LEAD WITH PLANS]" if attachments else "[CLIENT INQUIRY RECEIVED]"
        
        # 1. Windows Toast
        toast_title = f"{ascii_badge} {company}"
        toast_msg = f"{subject}\nFrom: {sender_email}\nAttachments: {', '.join(attachments) if attachments else 'None'}"
        self.send_windows_toast(toast_title, toast_msg)

        # 2. Telegram HTML
        tg_text = (
            f"<b>{badge}</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"✉️ <b>From:</b> <code>{sender_email}</code>\n"
            f"📋 <b>Subject:</b> {subject}\n"
            f"💬 <b>Snippet:</b> <i>\"{snippet[:250]}\"</i>\n"
        )
        if attachments:
            tg_text += f"📎 <b>Attached Plans:</b> <code>{', '.join(attachments)}</code>\n\n"
            tg_text += "🔥 <b>ACTION REQUIRED:</b> Contractor sent drawings! Open Gmail and prepare takeoff pricing ($500 - $2,500 value)!"
        else:
            tg_text += "\n💡 <b>ACTION:</b> Reply promptly to secure the takeoff bid deadline."
        
        self.send_telegram(tg_text)

        # 3. Discord Embed
        fields = [
            {"name": "Company", "value": company, "inline": True},
            {"name": "Sender", "value": sender_email, "inline": True},
            {"name": "Subject", "value": subject, "inline": False},
            {"name": "Message Preview", "value": snippet[:300] or "N/A", "inline": False}
        ]
        if attachments:
            fields.append({"name": "📎 Attached Plan Sets", "value": ", ".join(attachments), "inline": False})
        
        color = 0xFF3300 if attachments else 0x00AAFF
        self.send_discord(title=badge, description=f"Incoming opportunity from **{company}**", fields=fields, color=color)

        self._log(f"HOT LEAD NOTIFIED: {company} <{sender_email}> | Subject: {subject} | Attachments: {len(attachments)}")

    def notify_daily_summary(self, sent_today: int, total_sent: int, replies_today: int, active_pipeline_value: float):
        """Send daily evening executive revenue & outreach briefing."""
        title = "📊 Daily Preconstruction Pipeline Briefing"
        desc = (
            f"Today's AI Automation Summary:\n"
            f"• <b>Dispatched Today:</b> {sent_today} personalized pitches\n"
            f"• <b>Total Pipeline Sent:</b> {total_sent:,} contractors\n"
            f"• <b>New Inbound Inquiries:</b> {replies_today}\n"
            f"• <b>Est. Active Pipeline Value:</b> ${active_pipeline_value:,.2f}"
        )
        self.send_telegram(f"<b>{title}</b>\n\n{desc}")
        self.send_discord(
            title=title,
            description="Autonomous Outreach & Lead Acquisition Daily Report",
            fields=[
                {"name": "Outreach Sent Today", "value": str(sent_today), "inline": True},
                {"name": "Total Contractors Pitch", "value": f"{total_sent:,}", "inline": True},
                {"name": "New Inbound Inquiries", "value": str(replies_today), "inline": True},
                {"name": "Est. Pipeline Value", "value": f"${active_pipeline_value:,.2f}", "inline": False}
            ],
            color=0x00FF88
        )
        self.send_windows_toast(title, f"Sent: {sent_today} | Inquiries: {replies_today} | Pipeline: ${active_pipeline_value:,.0f}")
        self._log(f"DAILY SUMMARY: Sent={sent_today}, Replies={replies_today}, Value=${active_pipeline_value}")

    def test_all_channels(self) -> Dict[str, bool]:
        """Test active notification channels."""
        print("[*] Testing notification channels...")
        results = {}

        # 1. Desktop Toast
        print("  -> Testing Windows Desktop Toast...")
        results["desktop_toast"] = self.send_windows_toast(
            "🚀 AI Agent Alert System Online",
            "Background Takeoff Lead Agent is active and monitoring in the background."
        )

        # 2. Telegram
        if self.config.get("telegram_token") and self.config.get("telegram_chat_id"):
            print("  -> Testing Telegram Bot notification...")
            results["telegram"] = self.send_telegram(
                "🚀 <b>AI Agent Alert System Online</b>\nYour background PC agent is running and ready to alert you on client responses!"
            )
        else:
            print("  [i] Telegram not configured in .env (TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID). Skipping.")
            results["telegram"] = False

        # 3. Discord
        if self.config.get("discord_webhook"):
            print("  -> Testing Discord Webhook notification...")
            results["discord"] = self.send_discord(
                title="🚀 AI Agent Alert System Online",
                description="Background Takeoff Lead Agent is active and connected."
            )
        else:
            print("  [i] Discord webhook not configured in .env (DISCORD_WEBHOOK_URL). Skipping.")
            results["discord"] = False

        print("[+] Test completed.")
        return results

if __name__ == "__main__":
    alert = AlertSystem()
    alert.test_all_channels()
