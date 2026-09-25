"""
background_daemon.py - Autonomous AI Background Daemon for PC Passive Income Automation
Runs continuously in the background of your PC:
1. Orchestrates strategic multi-touch client outreach during US business hours.
2. Continuously monitors Gmail inbox for incoming contractor replies and project drawings.
3. Fires instant Telegram, Discord, and Windows Desktop Toast alerts when hot opportunities land.
4. Auto-recovers from network pauses and tracks all metrics in real-time.
"""

import os
import sys
import time
import signal
import json
import random
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any

DATA_DIR = Path(__file__).parent
DAEMON_LOG_FILE = DATA_DIR / "daemon.log"

# Support pythonw.exe (windowless GUI runner where stdout is None)
if sys.stdout is None:
    try:
        sys.stdout = open(DAEMON_LOG_FILE, "a", encoding="utf-8")
        sys.stderr = sys.stdout
    except Exception:
        pass
elif getattr(sys.stdout, "encoding", None) != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
PID_FILE = DATA_DIR / "daemon.pid"
DAEMON_STATE_FILE = DATA_DIR / "daemon_state.json"
DAEMON_LOG_FILE = DATA_DIR / "daemon.log"
STATE_FILE = DATA_DIR / "campaign_state.json"

from autonomous_planner import AutonomousPlanner
from inbox_sentinel import InboxSentinel
from alert_system import AlertSystem
from agent_mailer import GmailAutomator
from pitch_generator import prepare_campaign_touch, SENDER_PROFILE
from trade_intelligence import get_trade_intelligence

def log_event(message: str, level: str = "INFO"):
    """Write timestamped message to daemon.log and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}"
    try:
        print(entry)
    except Exception:
        pass
    try:
        with open(DAEMON_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass

class AutonomousBackgroundDaemon:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.running = False
        self.planner = AutonomousPlanner()
        self.sentinel = InboxSentinel()
        self.alert_system = AlertSystem()
        self.automator = GmailAutomator(daily_send_limit=self.planner.config["daily_limit"])
        self.last_inbox_check = 0.0
        self.last_daily_summary_date = ""
        self.inbox_check_interval = 600.0  # Check inbox every 10 minutes

    def _save_daemon_state(self, status: str = "RUNNING", extra: Optional[Dict[str, Any]] = None):
        state = {
            "status": status,
            "pid": os.getpid(),
            "dry_run": self.dry_run,
            "last_heartbeat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "today_sent": self.planner.get_today_sent_count(),
            "daily_limit": self.planner.config["daily_limit"],
            "business_hours_active": self.planner.is_business_hours()[0]
        }
        if extra:
            state.update(extra)
        try:
            with open(DAEMON_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            if status == "RUNNING":
                with open(PID_FILE, "w", encoding="utf-8") as f:
                    f.write(str(os.getpid()))
        except Exception:
            pass

    def stop_signal_handler(self, signum, frame):
        log_event("Shutdown signal received. Stopping background daemon gracefully...", "SHUTDOWN")
        self.running = False
        self._save_daemon_state("STOPPED")
        if PID_FILE.exists():
            try:
                if PID_FILE.read_text().strip() == str(os.getpid()):
                    PID_FILE.unlink()
            except Exception:
                pass
        sys.exit(0)

    def run_single_step(self) -> Dict[str, Any]:
        """Execute one complete cycle of inbox check + scheduled outreach."""
        now_ts = time.time()
        result = {"inbox_checked": False, "outreach_action": "NONE", "leads_sent": 0}

        # 1. Periodic Inbox Monitoring
        if now_ts - self.last_inbox_check >= self.inbox_check_interval:
            log_event("Scanning Gmail inbox for incoming contractor replies & drawings...", "INBOX")
            inquiries = self.sentinel.scan_inbox()
            self.last_inbox_check = now_ts
            result["inbox_checked"] = True
            if inquiries:
                log_event(f"Discovered {len(inquiries)} new inquiries! Alerts dispatched.", "ALERT")

        # 2. Daily Evening Briefing check (5:00 PM US Central Time)
        now_us = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5)))
        today_str = now_us.strftime("%Y-%m-%d")
        if now_us.hour >= 17 and self.last_daily_summary_date != today_str:
            sent_today = self.planner.get_today_sent_count()
            total_sent = len(self.automator.state.get("sent_ids", []))
            replies_count = len(self.automator.state.get("replied_ids", []))
            pipeline_value = replies_count * self.planner.config.get("avg_takeoff_price", 650.0)
            self.alert_system.notify_daily_summary(sent_today, total_sent, replies_count, pipeline_value)
            self.last_daily_summary_date = today_str

        # 3. Schedule & Business Hours Evaluation
        is_active, status_msg, wait_sec = self.planner.is_business_hours()
        if not is_active:
            result["outreach_action"] = f"PAUSED: {status_msg}"
            return result

        # 4. Daily Outreach Quota Check
        today_sent = self.planner.get_today_sent_count()
        if today_sent >= self.planner.config["daily_limit"]:
            result["outreach_action"] = f"QUOTA_REACHED: {today_sent}/{self.planner.config['daily_limit']} sent today"
            return result

        # 5. Retrieve Next Lead from Queue
        batch = self.planner.plan_next_batch(max_batch_size=1)
        if not batch:
            result["outreach_action"] = "QUEUE_EMPTY: No eligible leads available right now"
            return result

        item = batch[0]
        lead = item["lead"]
        touch = item["touch"]
        reason = item.get("reason", "Scheduled Outreach")

        # Prepare customized pitch
        pitch = prepare_campaign_touch(lead, touch_number=touch)
        recipient = pitch["recipient"]
        subject = pitch["subject"]
        body = pitch["body"]
        company = lead.get("company", "Contractor")
        lead_id = lead.get("id")

        log_event(f"Dispatching Touch {touch} -> {company} ({lead.get('trade_niche')}) <{recipient}> [{reason}]", "OUTREACH")

        if self.dry_run:
            log_event(f"[SIMULATED] Touch {touch} prepared for {recipient} (Dry Run mode)", "DRY_RUN")
            result["outreach_action"] = "SIMULATED_SEND"
            result["leads_sent"] = 1
            return result

        # Live SMTP Send
        if not self.automator.server:
            if not self.automator.connect_smtp():
                log_event("Failed to connect to Gmail SMTP. Will retry next cycle.", "ERROR")
                result["outreach_action"] = "SMTP_CONNECT_FAILED"
                return result

        try:
            self.automator.send_single_email(recipient, subject, body, lead_id=lead_id, lead_company=company)
            # Update log touch info
            logs = self.automator.state.get("send_logs", [])
            if logs:
                logs[-1]["touch"] = touch
            from agent_mailer import save_campaign_state
            save_campaign_state(self.automator.state)

            log_event(f"SUCCESS: Touch {touch} email delivered directly to {recipient}!", "SENT")
            result["outreach_action"] = "DELIVERED"
            result["leads_sent"] = 1
        except Exception as e:
            log_event(f"Failed to send email to {recipient}: {e}", "ERROR")
            result["outreach_action"] = f"ERROR: {e}"

        return result

    def start_loop(self):
        """Continuous background loop."""
        self.running = True
        signal.signal(signal.SIGINT, self.stop_signal_handler)
        signal.signal(signal.SIGTERM, self.stop_signal_handler)

        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))

        log_event("=" * 75)
        log_event(f"AUTONOMOUS AI BACKGROUND DAEMON ONLINE (PID: {os.getpid()})", "START")
        log_event(f"Mode: {'DRY RUN SIMULATION' if self.dry_run else 'LIVE DISPATCH'}")
        log_event(f"Sender: {SENDER_PROFILE['name']} <{self.automator.creds.get('user')}>")
        log_event(f"Daily Target: {self.planner.config['daily_limit']} pitches/day | Window: US Business Hours (8:30AM - 4:30PM)")
        log_event("=" * 75)

        # Notify phone/desktop that daemon started
        self.alert_system.send_windows_toast(
            "AI Background Agent Online",
            f"Autonomous lead pipeline is active. Target: {self.planner.config['daily_limit']} pitches/day."
        )

        try:
            while self.running:
                self._save_daemon_state("RUNNING")
                res = self.run_single_step()
                if res.get("leads_sent", 0) > 0:
                    # Apply interval delay between individual emails
                    min_sec = self.planner.config.get("min_jitter_seconds", 5)
                    max_sec = self.planner.config.get("max_jitter_seconds", 5)
                    jitter = random.randint(min(min_sec, max_sec), max(min_sec, max_sec))
                    log_event(f"Interval delay: Sleeping {jitter}s before next pitch...", "DELAY")
                    time.sleep(jitter)
                else:
                    # Idle loop sleep (60 seconds)
                    time.sleep(60)

        except Exception as e:
            import traceback
            log_event(f"Daemon encountered unexpected crash: {e}\n{traceback.format_exc()}", "FATAL")
        finally:
            self._save_daemon_state("STOPPED")
            if PID_FILE.exists():
                try:
                    if PID_FILE.read_text().strip() == str(os.getpid()):
                        PID_FILE.unlink()
                except Exception:
                    pass

def get_running_pid() -> Optional[int]:
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process is alive on Windows
        output = subprocess.check_output(f'tasklist /FI "PID eq {pid}" /NH', shell=True).decode()
        if str(pid) in output:
            return pid
        else:
            PID_FILE.unlink(missing_ok=True)
            return None
    except Exception:
        return None

def cmd_start(dry_run: bool = False):
    existing_pid = get_running_pid()
    if existing_pid:
        print(f"[!] Background Daemon is already running (PID: {existing_pid}).")
        return

    print("[*] Launching Autonomous AI Agent in the background...")
    vbs_path = DATA_DIR / "start_background_agent.vbs"
    if vbs_path.exists() and not dry_run:
        subprocess.run(["wscript.exe", str(vbs_path)], check=True)
    else:
        script_path = str(Path(__file__).resolve())
        python_exe = sys.executable
        pythonw_exe = Path(python_exe).parent / "pythonw.exe"
        runner = str(pythonw_exe) if pythonw_exe.exists() else python_exe
        args = [runner, script_path, "run"]
        if dry_run:
            args.append("--dry-run")
        creation_flags = 0x08000000 | 0x00000200 if os.name == 'nt' else 0
        subprocess.Popen(args, creationflags=creation_flags)

    time.sleep(2.5)
    pid = get_running_pid()
    if pid:
        print(f"[SUCCESS] Autonomous AI Background Agent started successfully (PID: {pid})!")
        print(f"[*] View live logs with: python background_daemon.py logs")
        print(f"[*] Check status with:   python background_daemon.py status")
    else:
        print("[!] Note: Agent launched. Initializing background tasks...")

def cmd_stop():
    pid = get_running_pid()
    if not pid:
        print("[i] Background Daemon is not currently running.")
        return
    print(f"[*] Halting Background Daemon (PID: {pid})...")
    try:
        subprocess.run(f"taskkill /PID {pid} /F", shell=True, check=True, stdout=subprocess.DEVNULL)
        if PID_FILE.exists():
            PID_FILE.unlink()
        print("[SUCCESS] Background Daemon stopped cleanly.")
    except Exception as e:
        print(f"[!] Error stopping daemon: {e}")

def cmd_status():
    pid = get_running_pid()
    planner = AutonomousPlanner()
    rev = planner.calculate_revenue_metrics()
    is_active, status_msg, wait_sec = planner.is_business_hours()

    print("\n" + "=" * 70)
    print("  AUTONOMOUS AI BACKGROUND AGENT - SYSTEM STATUS")
    print("=" * 70)
    print(f"  Daemon Lifecycle State       : {'🟢 RUNNING (PID: ' + str(pid) + ')' if pid else '⚪ STOPPED'}")
    print(f"  Target Monthly Revenue       : {rev['target_monthly_income']} ({rev['closed_deals_needed_month']} closed takeoffs)")
    print(f"  Expected Weekly Revenue      : {rev['est_weekly_revenue']}")
    print(f"  Daily Outreach Limit         : {planner.config['daily_limit']} emails/day")
    print(f"  Emails Dispatched Today      : {planner.get_today_sent_count()} / {planner.config['daily_limit']}")
    print(f"  Business Hours Active        : {is_active} ({status_msg})")
    print("-" * 70)

    if DAEMON_STATE_FILE.exists():
        try:
            with open(DAEMON_STATE_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
            print(f"  Last Daemon Heartbeat        : {st.get('last_heartbeat', 'N/A')}")
        except Exception:
            pass

    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                cs = json.load(f)
            print(f"  Total Contacts Pitched       : {len(cs.get('sent_ids', [])):,}")
            print(f"  Inbound Replies Captured     : {len(cs.get('replied_ids', [])):,}")
            print(f"  Active Plan Sets / RFPs      : {len(cs.get('sample_requested_ids', [])):,}")
        except Exception:
            pass
    print("=" * 70 + "\n")

def cmd_logs(lines: int = 25):
    if not DAEMON_LOG_FILE.exists():
        print("[i] No log file found yet.")
        return
    try:
        content = DAEMON_LOG_FILE.read_text(encoding="utf-8").splitlines()
        print("\n" + "=" * 70)
        print(f"  RECENT DAEMON LOGS (Last {lines} lines)")
        print("=" * 70)
        for line in content[-lines:]:
            print("  " + line)
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"[!] Error reading logs: {e}")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    dry_run = "--dry-run" in sys.argv

    if action == "start":
        cmd_start(dry_run=dry_run)
    elif action == "stop":
        cmd_stop()
    elif action == "status":
        cmd_status()
    elif action == "logs":
        lines = 25
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            lines = int(sys.argv[2])
        cmd_logs(lines)
    elif action == "run":
        # Run directly in foreground (useful for debug and spawned subprocess)
        daemon = AutonomousBackgroundDaemon(dry_run=dry_run)
        daemon.start_loop()
    elif action == "run-once":
        print("[*] Executing single step test...")
        daemon = AutonomousBackgroundDaemon(dry_run=dry_run)
        res = daemon.run_single_step()
        print(f"[+] Result: {res}")
    elif action == "test-alerts":
        alert = AlertSystem()
        alert.test_all_channels()
    elif action == "test-inbox":
        sentinel = InboxSentinel()
        found = sentinel.scan_inbox()
        print(f"[+] Inbox scan complete. {len(found)} opportunities discovered.")
    else:
        print("Usage: python background_daemon.py [start|stop|status|logs|run|run-once|test-alerts|test-inbox] [--dry-run]")
