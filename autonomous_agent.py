"""
Autonomous AI Lead Agent for USA Construction Quantity Takeoff & Estimation
Orchestrates end-to-end client acquisition:
1. Autonomous Prospecting: Finds US construction companies across top metros & trades
2. Deep Enrichment: CSI MasterFormat division mapping, pain points & portfolio proof linking
3. AI Personalization: Tailored multi-touch outreach sequences with on-demand takeoff offer
4. Automated Dispatch: Auto-sends emails via Gmail (SMTP or 1-click browser compose)
5. State Tracking: Tracks every lead from Discovery to Closed Retainer
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 console output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from trade_intelligence import TRADE_INTELLIGENCE, US_CONSTRUCTION_METROS, get_trade_intelligence
from lead_hunter import LeadHunter
from pitch_generator import prepare_campaign_touch, SENDER_PROFILE
from agent_mailer import GmailAutomator

DATA_DIR = Path(__file__).parent

class AutonomousLeadAgent:
    def __init__(self, daily_limit: int = 40):
        self.hunter = LeadHunter()
        self.mailer = GmailAutomator(daily_send_limit=daily_limit)
        self.daily_limit = daily_limit

    def print_banner(self):
        print("\n" + "=" * 80)
        print("  [+] AUTONOMOUS AI LEAD AGENT - USA TAKEOFF & ESTIMATION CLIENT ACQUISITION")
        print("  Dedicated Preconstruction & Estimating Client Pipeline for Harris Wilford")
        print(f"  Sender: {SENDER_PROFILE['name']} <{self.mailer.creds.get('user')}>")
        print("=" * 80 + "\n")

    def display_pipeline_stats(self):
        """Display real-time pipeline status and conversion funnel."""
        stats = self.hunter.get_stats()
        sent_count = len(self.mailer.state.get("sent_ids", []))
        total = stats["total_leads"]

        print("=" * 80)
        print(" [*] REAL-TIME CLIENT ACQUISITION PIPELINE")
        print("=" * 80)
        print(f" Total Master Leads Staged   : {total:,}")
        print(f" Outreach Dispatched (Sent)  : {sent_count:,} ({(sent_count/max(1, total))*100:.1f}%)")
        print(f" Unsent Leads Ready for Pitch : {max(0, total - sent_count):,}")
        print(f" Plans Submitted for Review  : {len(self.mailer.state.get('sample_requested_ids', [])):,}")
        print(f" Closed Paying Retainers     : {len(self.mailer.state.get('closed_ids', [])):,}")
        print("-" * 80)

        print(f"{'TRADE / SPECIALTY':<40} | {'AVAILABLE LEADS':<15} | {'PORTFOLIO PROOF'}")
        print("-" * 80)
        for trade, count in sorted(stats["trade_breakdown"].items(), key=lambda x: x[1], reverse=True)[:10]:
            intel = get_trade_intelligence(trade)
            print(f"{trade:<40} | {count:<15} | {intel['sample_file']}")
        print("=" * 80 + "\n")

    def hunt_fresh_leads(self, trade: Optional[str] = None, city: Optional[str] = None, state: Optional[str] = None, target_count: int = 5) -> List[Dict[str, Any]]:
        """Autonomously discover fresh leads from live search."""
        target_trade = trade or "Commercial General Contractors"
        target_city = city or "Dallas"
        target_state = state or "TX"

        print(f"[*] Autonomous Agent: Initiating live search for [{target_trade}] in {target_city}, {target_state}...")
        discovered = self.hunter.search_contractors_live(target_trade, target_city, target_state, max_results=target_count)
        print(f"[+] Autonomous Agent: Discovered {len(discovered)} fresh qualified contractor accounts.")
        return discovered

    def run_outreach_cycle(self, batch_size: int = 10, touch_number: int = 1, trade_filter: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute full automated outreach sequence:
        1. Select best qualified unsent leads
        2. Generate tailored copy & value hooks
        3. Dispatch via Gmail
        4. Log results and update CRM status
        """
        sent_ids = set(self.mailer.state.get("sent_ids", []))
        unsent_leads = [
            l for l in self.hunter.master_leads
            if l.get("id") not in sent_ids and l.get("email")
        ]

        if trade_filter:
            unsent_leads = [l for l in unsent_leads if trade_filter.lower() in l.get("trade_niche", "").lower()]

        if not unsent_leads:
            print("[!] No unsent leads in queue. Automatically hunting fresh live leads...")
            metro = US_CONSTRUCTION_METROS[0]
            fresh = self.hunt_fresh_leads(trade=trade_filter or "Commercial General Contractors", city=metro["city"], state=metro["state"], target_count=batch_size)
            unsent_leads = fresh

        if not unsent_leads:
            print("[!] Unable to source unsent leads at this time.")
            return {"sent": 0, "status": "NO_LEADS"}

        batch = unsent_leads[:batch_size]
        print(f"[*] Staged {len(batch)} targeted leads for Touch {touch_number} Outreach:")
        for idx, l in enumerate(batch, 1):
            print(f"    {idx}. {l['company']} ({l['trade_niche']}) -> {l['email']}")

        # Dispatch via Gmail
        results = self.mailer.dispatch_batch_smtp(
            batch,
            touch_number=touch_number,
            max_sends=batch_size,
            delay_range=(2.5, 5.0),
            dry_run=dry_run
        )

        # Update status in master database
        for detail in results.get("details", []):
            if detail.get("status") in ["SENT", "SIMULATED"]:
                self.hunter.update_lead_status(detail["id"], "SENT", f"Touch {touch_number} dispatched directly to inbox")

        return results

    def hunt_and_send_direct(self, trade: str, city: str, state: str, count: int = 5, touch_number: int = 1, dry_run: bool = False) -> Dict[str, Any]:
        """
        Hunt fresh leads live and immediately dispatch emails directly to client inboxes via Gmail SMTP.
        """
        print(f"\n[*] Autonomous Hunter: Sourcing {count} fresh leads for [{trade}] in {city}, {state}...")
        fresh_leads = self.hunt_fresh_leads(trade=trade, city=city, state=state, target_count=count)
        if not fresh_leads:
            print("[!] No new leads found to email.")
            return {"sent": 0, "failed": 0}

        print(f"\n[+] Delivering outreach emails directly to client inboxes via Gmail SMTP...")
        results = self.mailer.dispatch_batch_smtp(fresh_leads, touch_number=touch_number, max_sends=count, dry_run=dry_run)
        
        for detail in results.get("details", []):
            if detail.get("status") in ["SENT", "SIMULATED"]:
                self.hunter.update_lead_status(detail["id"], "SENT", f"Touch {touch_number} sent directly to inbox")

        return results

    def run_autonomous_loop(self, total_days: int = 7, daily_batch: int = 25, dry_run: bool = False):
        """
        Autonomous Agent continuous loop:
        Cycles through top trades, hunts leads, personalizes pitches, dispatches emails daily.
        """
        self.print_banner()
        print(f"[*] Starting Autonomous 7-Day Campaign Loop (Target: {daily_batch} emails/day)...")

        trades = list(TRADE_INTELLIGENCE.keys())
        for day in range(1, total_days + 1):
            print(f"\n{'#'*80}")
            print(f" [AUTONOMOUS CAMPAIGN DAY {day} OF {total_days}]")
            print(f"{'#'*80}\n")

            trade_for_today = trades[(day - 1) % len(trades)]
            metro_for_today = US_CONSTRUCTION_METROS[(day - 1) % len(US_CONSTRUCTION_METROS)]

            print(f"[*] Today's Target Niche  : {trade_for_today}")
            print(f"[*] Today's Target Market : {metro_for_today['city']}, {metro_for_today['state']}")

            # Check if we have enough leads staged for today's niche
            matching = [
                l for l in self.hunter.master_leads
                if l.get("id") not in self.mailer.state.get("sent_ids", [])
                and trade_for_today.lower() in l.get("trade_niche", "").lower()
            ]

            if len(matching) < daily_batch:
                needed = daily_batch - len(matching)
                print(f"[*] Sourcing {needed} additional live contractor leads for {trade_for_today}...")
                self.hunt_fresh_leads(trade=trade_for_today, city=metro_for_today["city"], state=metro_for_today["state"], target_count=needed)

            # Dispatch today's batch
            self.run_outreach_cycle(batch_size=daily_batch, touch_number=1, trade_filter=trade_for_today, dry_run=dry_run)
            self.display_pipeline_stats()

            if day < total_days:
                print(f"[+] Autonomous Day {day} complete. Waiting for next schedule window...")
                break

    def export_leads_csv(self, filename: str = "outreach_leads_master.csv"):
        """Export master leads database to formatted CSV."""
        import csv
        out_path = DATA_DIR / filename
        leads = self.hunter.master_leads
        if not leads:
            print("[!] No leads to export.")
            return

        keys = [
            "id", "company", "contact_name", "role", "trade_niche", "division",
            "city", "state", "email", "phone", "website", "status", "sample_file", "sample_proof"
        ]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(leads)
        print(f"[SUCCESS] Exported {len(leads)} leads to {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Lead Agent for Construction Quantity Takeoff & Estimation")
    parser.add_argument("--cycle", action="store_true", help="Run 1 complete automated outreach cycle (Hunt -> Pitch -> Send)")
    parser.add_argument("--hunt", action="store_true", help="Hunt fresh live contractor leads across the US")
    parser.add_argument("--send", action="store_true", help="Send emails directly to staged leads' inboxes via Gmail SMTP")
    parser.add_argument("--hunt-and-send", action="store_true", help="Hunt live contractors and immediately send directly to their inboxes")
    parser.add_argument("--upload-drafts", action="store_true", help="Upload drafts directly into your Gmail 'Drafts' folder")
    parser.add_argument("--browser", action="store_true", help="Launch pre-filled Gmail compose tabs in default browser")
    parser.add_argument("--stats", action="store_true", help="Display real-time pipeline status and analytics")
    parser.add_argument("--export", action="store_true", help="Export master leads database to CSV")
    parser.add_argument("--trade", type=str, default=None, help="Filter by specific trade (e.g., 'MEP - HVAC', 'Drywall', 'Commercial')")
    parser.add_argument("--city", type=str, default="Dallas", help="Target city for live search")
    parser.add_argument("--state", type=str, default="TX", help="Target state for live search")
    parser.add_argument("--batch", type=int, default=10, help="Number of leads to process in batch")
    parser.add_argument("--touch", type=int, default=1, help="Touch sequence number (1-4)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate email sending without real dispatch")
    parser.add_argument("--daemon", action="store_true", help="Run continuous autonomous 7-day loop")

    args = parser.parse_args()
    agent = AutonomousLeadAgent()
    agent.print_banner()

    if args.stats:
        agent.display_pipeline_stats()
    elif args.hunt_and_send:
        trade = args.trade or "Commercial General Contractors"
        agent.hunt_and_send_direct(trade=trade, city=args.city, state=args.state, count=args.batch, touch_number=args.touch, dry_run=args.dry_run)
    elif args.hunt:
        agent.hunt_fresh_leads(trade=args.trade, city=args.city, state=args.state, target_count=args.batch)
    elif args.upload_drafts:
        from gmail_draft_uploader import GmailDraftUploader
        uploader = GmailDraftUploader()
        leads = [l for l in agent.hunter.master_leads if l.get("id") not in agent.mailer.state.get("sent_ids", [])]
        if args.trade:
            leads = [l for l in leads if args.trade.lower() in l.get("trade_niche", "").lower()]
        uploader.upload_drafts(leads, touch_number=args.touch, limit=args.batch)
    elif args.send:
        agent.run_outreach_cycle(batch_size=args.batch, touch_number=args.touch, trade_filter=args.trade, dry_run=args.dry_run)
    elif args.browser:
        leads = agent.hunter.get_prospects(status="QUALIFIED", trade=args.trade, limit=args.batch)
        if not leads:
            leads = [l for l in agent.hunter.master_leads if l.get("id") not in agent.mailer.state.get("sent_ids", [])][:args.batch]
        agent.mailer.launch_browser_drafts(leads, touch_number=args.touch, limit=args.batch)
    elif args.cycle:
        print("[*] Executing 1-Click Autonomous Outreach Cycle...")
        agent.run_outreach_cycle(batch_size=args.batch, touch_number=args.touch, trade_filter=args.trade, dry_run=args.dry_run)
        agent.display_pipeline_stats()
    elif args.daemon:
        agent.run_autonomous_loop(total_days=7, daily_batch=args.batch, dry_run=args.dry_run)
    elif args.export:
        agent.export_leads_csv()
    else:
        agent.display_pipeline_stats()
        print("[QUICK START COMMANDS (DIRECT INBOX DELIVERY)]")
        print("  python autonomous_agent.py --send --batch 10                                 : Send 10 emails directly to client inboxes")
        print("  python autonomous_agent.py --hunt-and-send --trade 'Drywall' --city 'Dallas'  : Hunt live contractors and send directly to inboxes")
        print("  python autonomous_agent.py --cycle --batch 15                                : Run 1 full autonomous cycle (hunt & send to inboxes)")
        print("  python autonomous_agent.py --hunt --trade 'HVAC'                             : Hunt live US HVAC contractor leads")
        print("  python autonomous_agent.py --stats                                           : View real-time lead pipeline metrics")
        print("  python app.py --web                                                          : Start interactive web dashboard (http://localhost:8000)")

if __name__ == "__main__":
    main()
