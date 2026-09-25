"""
autonomous_planner.py - Autonomous AI Outreach & Passive Income Strategy Planner
Calculates revenue targets, orchestrates multi-touch follow-up cycles,
enforces US business hours, and schedules daily email batches for maximum conversion.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DATA_DIR = Path(__file__).parent
ENV_FILE = DATA_DIR / ".env"
STATE_FILE = DATA_DIR / "campaign_state.json"
MASTER_DB_FILE = DATA_DIR / "leads_master_db.json"

from trade_intelligence import TRADE_INTELLIGENCE, US_CONSTRUCTION_METROS

# US Central Time is primary for major construction markets (Texas, Midwest, South)
# Default US Business Hours: 8:30 AM - 4:30 PM
DEFAULT_START_HOUR = 8
DEFAULT_START_MINUTE = 30
DEFAULT_END_HOUR = 16
DEFAULT_END_MINUTE = 30

class AutonomousPlanner:
    def __init__(self, target_monthly_income: float = 12000.0, avg_order_value: float = 650.0):
        self.target_monthly_income = target_monthly_income
        self.avg_order_value = avg_order_value
        self.config = self._load_planner_config()

    def _load_planner_config(self) -> Dict[str, Any]:
        cfg = {
            "daily_limit": 300,
            "business_hours_only": True,
            "min_jitter_seconds": 5,
            "max_jitter_seconds": 5,
            "target_monthly_income": self.target_monthly_income,
            "avg_takeoff_price": self.avg_order_value
        }
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "DAILY_SEND_LIMIT" and v.isdigit():
                            cfg["daily_limit"] = int(v)
                        elif k == "BUSINESS_HOURS_ONLY":
                            cfg["business_hours_only"] = v.lower() in ("true", "1", "yes")
                        elif k == "MIN_JITTER_SECONDS" and v.isdigit():
                            cfg["min_jitter_seconds"] = int(v)
                        elif k == "MAX_JITTER_SECONDS" and v.isdigit():
                            cfg["max_jitter_seconds"] = int(v)
        return cfg

    def calculate_revenue_metrics(self) -> Dict[str, Any]:
        """
        Passive Income Calculus:
        Target Monthly Income -> Required Closed Takeoff Projects -> Required Plans -> Required Outreach Volume
        """
        daily_limit = self.config["daily_limit"]
        weekly_sends_target = daily_limit * 5
        monthly_sends = weekly_sends_target * 4

        # Funnel conversion benchmark: ~4% reply rate, ~40% plan submit, ~50% close
        est_monthly_replies = round(monthly_sends * 0.04)
        est_monthly_plans = round(est_monthly_replies * 0.40)
        closed_deals_month = max(1, round(est_monthly_plans * 0.50))
        closed_deals_week = max(1, round(closed_deals_month / 4))

        avg_deal = self.config["avg_takeoff_price"]
        est_monthly_revenue = closed_deals_month * avg_deal
        est_weekly_revenue = closed_deals_week * avg_deal

        return {
            "target_monthly_income": f"${est_monthly_revenue:,.2f}",
            "avg_takeoff_price": f"${avg_deal:,.2f}",
            "closed_deals_needed_month": closed_deals_month,
            "closed_deals_needed_week": closed_deals_week,
            "est_weekly_revenue": f"${est_weekly_revenue:,.2f}",
            "daily_outreach_quota": daily_limit,
            "weekly_outreach_quota": weekly_sends_target,
            "expected_weekly_replies": f"{round(weekly_sends_target * 0.04)} - {round(weekly_sends_target * 0.06)} warm inquiries",
            "expected_weekly_plans": f"{round(weekly_sends_target * 0.04 * 0.4)} - {round(weekly_sends_target * 0.06 * 0.5)} project bid sets"
        }

    def is_business_hours(self) -> Tuple[bool, str, int]:
        """
        Check if current time is inside optimal US contractor decision-maker hours.
        Target Market: US Central Time (CDT / UTC-5: Dallas, Houston, Austin, Chicago).
        Window: Monday - Friday, 8:30 AM to 4:30 PM US Central Time.
        """
        if not self.config.get("business_hours_only", True):
            return True, "Business hours restriction disabled. Ready to send.", 0

        # Convert to US Central Time (UTC-5)
        now_utc = datetime.now(timezone.utc)
        us_central_tz = timezone(timedelta(hours=-5))
        now_us = now_utc.astimezone(us_central_tz)

        weekday = now_us.weekday()  # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
        us_time_str = now_us.strftime("%I:%M %p CDT (%A)")

        # Check weekend in the US
        if weekday >= 5:  # Saturday or Sunday
            days_ahead = 7 - weekday  # Days until Monday
            next_window = now_us.replace(hour=DEFAULT_START_HOUR, minute=DEFAULT_START_MINUTE, second=0, microsecond=0) + timedelta(days=days_ahead)
            wait_sec = int((next_window - now_us).total_seconds())
            return False, f"US Weekend pause. Next US window opens Monday at {DEFAULT_START_HOUR:02d}:{DEFAULT_START_MINUTE:02d} CDT.", wait_sec

        current_minutes = now_us.hour * 60 + now_us.minute
        start_minutes = DEFAULT_START_HOUR * 60 + DEFAULT_START_MINUTE
        end_minutes = DEFAULT_END_HOUR * 60 + DEFAULT_END_MINUTE

        if current_minutes < start_minutes:
            wait_sec = (start_minutes - current_minutes) * 60
            return False, f"Early morning in US ({us_time_str}). Window opens at {DEFAULT_START_HOUR:02d}:{DEFAULT_START_MINUTE:02d} CDT.", wait_sec
        elif current_minutes > end_minutes:
            tomorrow_start = (now_us + timedelta(days=1)).replace(hour=DEFAULT_START_HOUR, minute=DEFAULT_START_MINUTE, second=0, microsecond=0)
            wait_sec = int((tomorrow_start - now_us).total_seconds())
            return False, f"Evening in US ({us_time_str}). Window opens tomorrow at {DEFAULT_START_HOUR:02d}:{DEFAULT_START_MINUTE:02d} CDT.", wait_sec

        return True, f"Currently within peak US Business Hours ({us_time_str}). Window is open.", 0

    def get_today_sent_count(self) -> int:
        """Count how many emails have been sent today."""
        if not STATE_FILE.exists():
            return 0
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            today_str = datetime.now().strftime("%Y-%m-%d")
            send_logs = state.get("send_logs", [])
            count = sum(1 for log in send_logs if (log.get("sent_at") or "").startswith(today_str))
            return count
        except Exception:
            return 0

    def plan_next_batch(self, max_batch_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Assemble the optimal queue for today:
        1. Identifies follow-ups due (Touch 2, Touch 3, Touch 4)
        2. Fills remainder of daily quota with fresh Touch 1 prospects
        3. Strictly filters out replied, closed, or blacklisted leads
        """
        today_sent = self.get_today_sent_count()
        remaining_daily_quota = max(0, self.config["daily_limit"] - today_sent)

        if remaining_daily_quota == 0:
            return []

        limit = min(max_batch_size, remaining_daily_quota) if max_batch_size else remaining_daily_quota

        # Load state
        sent_ids = set()
        replied_ids = set()
        blacklisted_emails = set()
        send_logs = []

        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    sent_ids = set(state.get("sent_ids", []))
                    replied_ids = set(state.get("replied_ids", []))
                    blacklisted_emails = set(e.lower() for e in state.get("blacklisted_emails", []))
                    send_logs = state.get("send_logs", [])
            except Exception:
                pass

        # Load master leads
        master_leads = []
        if MASTER_DB_FILE.exists():
            try:
                with open(MASTER_DB_FILE, "r", encoding="utf-8") as f:
                    master_leads = json.load(f)
            except Exception:
                pass

        leads_by_id = {l.get("id"): l for l in master_leads if l.get("id")}
        now = datetime.now()

        # Phase 1: Determine Follow-ups (Touch 2, 3, 4)
        # Check logs for leads sent earlier touches
        last_sent_by_lead: Dict[int, Dict[str, Any]] = {}
        for log in send_logs:
            lid = log.get("lead_id")
            if lid and lid not in replied_ids:
                last_sent_by_lead[lid] = log

        follow_up_queue: List[Dict[str, Any]] = []

        for lid, last_log in last_sent_by_lead.items():
            lead = leads_by_id.get(lid)
            if not lead:
                continue
            email_addr = (lead.get("email") or "").lower().strip()
            if email_addr in blacklisted_emails:
                continue

            sent_at_str = last_log.get("sent_at", "")
            try:
                sent_at = datetime.strptime(sent_at_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            days_elapsed = (now - sent_at).total_seconds() / 86400.0
            last_touch = last_log.get("touch", 1)

            # Touch 2: 2 days after Touch 1
            if last_touch == 1 and days_elapsed >= 2.0:
                follow_up_queue.append({"lead": lead, "touch": 2, "reason": f"Follow-up: {days_elapsed:.1f} days since Touch 1"})
            # Touch 3: 2 days after Touch 2
            elif last_touch == 2 and days_elapsed >= 2.0:
                follow_up_queue.append({"lead": lead, "touch": 3, "reason": f"Follow-up: {days_elapsed:.1f} days since Touch 2"})
            # Touch 4: 3 days after Touch 3
            elif last_touch == 3 and days_elapsed >= 3.0:
                follow_up_queue.append({"lead": lead, "touch": 4, "reason": f"Breakup note: {days_elapsed:.1f} days since Touch 3"})

        # Take up to half of limit for follow-ups (since follow-ups have 2.5x higher conversion)
        staged_batch: List[Dict[str, Any]] = []
        max_followups = min(len(follow_up_queue), max(1, limit // 2))
        staged_batch.extend(follow_up_queue[:max_followups])

        # Phase 2: Fill remaining quota with fresh Touch 1 prospects
        slots_for_touch_1 = limit - len(staged_batch)
        if slots_for_touch_1 > 0:
            unsent_leads = [
                l for l in master_leads
                if l.get("id") not in sent_ids
                and l.get("email")
                and (l.get("email") or "").lower().strip() not in blacklisted_emails
            ]

            # Prioritize high-value commercial GCs and MEP trades
            def lead_priority(lead: Dict[str, Any]) -> int:
                t = (lead.get("trade_niche") or "").lower()
                if "commercial general contractor" in t:
                    return 1
                if "hvac" in t or "electrical" in t or "plumbing" in t:
                    return 2
                if "drywall" in t or "concrete" in t:
                    return 3
                return 4

            unsent_sorted = sorted(unsent_leads, key=lead_priority)
            for fresh_lead in unsent_sorted[:slots_for_touch_1]:
                staged_batch.append({
                    "lead": fresh_lead,
                    "touch": 1,
                    "reason": "Fresh High-Ticket Prospect (Touch 1)"
                })

        return staged_batch

if __name__ == "__main__":
    planner = AutonomousPlanner()
    print("=" * 70)
    print("  AUTONOMOUS AI PASSIVE INCOME & REVENUE STRATEGY PLANNER")
    print("=" * 70)
    rev = planner.calculate_revenue_metrics()
    for k, v in rev.items():
        print(f"  {k:<30}: {v}")
    print("-" * 70)
    is_active, msg, wait_sec = planner.is_business_hours()
    print(f"  Business Hours Active         : {is_active}")
    print(f"  Schedule Status               : {msg}")
    print(f"  Today's Emails Sent So Far    : {planner.get_today_sent_count()} / {planner.config['daily_limit']}")
    print("-" * 70)
    batch = planner.plan_next_batch(max_batch_size=5)
    print(f"  Next Staged Action Queue      : {len(batch)} targeted leads")
    for idx, item in enumerate(batch, 1):
        lead = item["lead"]
        print(f"    {idx}. [Touch {item['touch']}] {lead['company']} ({lead.get('trade_niche')}) -> {lead['email']}")
    print("=" * 70)
