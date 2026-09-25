"""
send_gmail.py - Autonomous Gmail Dispatcher & Pipeline Bridge
Provides direct command-line access to find & auto-email US construction clients,
filter by trade (e.g. Commercial General Contractors), integrate with Gmail SMTP SSL,
upload drafts directly to Gmail 'Drafts' folder, and launch 1-click browser compose drafts.
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure UTF-8 console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from agent_mailer import GmailAutomator
from lead_hunter import LeadHunter
from pitch_generator import SENDER_PROFILE, prepare_campaign_touch
from command_center import generate_dashboard
from gmail_draft_uploader import GmailDraftUploader

def is_commercial_gc(lead: dict) -> bool:
    """Check if lead is a Commercial General Contractor."""
    t = (lead.get("trade_niche") or lead.get("trade") or lead.get("Category / Specialty") or "").lower()
    if "commercial" in t and ("general" in t or "contractor" in t or "gc" in t or "builder" in t or "construction" in t):
        return True
    if "general contractor" in t or "general contracting" in t:
        return True
    return False

def run_terminal_console(hunter, automator, uploader):
    """Interactive full-featured outreach terminal control panel."""
    while True:
        state = automator.state
        sent_ids = set(state.get("sent_ids", []))
        unsent_all = [l for l in hunter.master_leads if l.get("id") not in sent_ids and l.get("email")]
        unsent_gcs = [l for l in unsent_all if is_commercial_gc(l)]

        print("\n" + "=" * 80)
        print("  ⚡ AUTONOMOUS AI OUTREACH TERMINAL - 1-COMMAND DIRECT CLIENT DISPATCH")
        print(f"  Sender Identity: {SENDER_PROFILE['name']} <{automator.creds.get('user')}>")
        print("=" * 80)
        print(f"  Total Master Leads : {len(hunter.master_leads):,}  |  Commercial GCs : {len([l for l in hunter.master_leads if is_commercial_gc(l)]):,}")
        print(f"  Sent Dispatched    : {len(sent_ids):,}  |  Unsent Commercial GCs Ready: {len(unsent_gcs):,}")
        print("-" * 80)
        print("  [1] 🚀 Send Next Batch to Commercial GCs (1 command)")
        print("  [2] ✉️  Send Directly to a Specific Client Email (1 command)")
        print("  [3] 📋 List Next Queued Commercial GCs")
        print("  [4] 👁️  Preview Commercial GC Personalized Pitch")
        print("  [5] 📥 Upload Drafts to Gmail 'Drafts' Folder")
        print("  [6] 📊 View Real-Time Pipeline Stats & Latest Sent Logs")
        print("  [7] 🌐 Launch Web Dashboard (Command Center)")
        print("  [8] 🧪 Run Safe Dry-Run Simulation")
        print("  [0] ❌ Exit Terminal")
        print("=" * 80)

        choice = input("\nEnter Choice [0-8]: ").strip()

        if choice == "1":
            cnt = input("How many Commercial GCs to send to? (default 10, or 'all'): ").strip()
            count = len(unsent_gcs) if cnt.lower() == "all" else (int(cnt) if cnt.isdigit() else 10)
            dry = input("Dry run simulation? (y/n, default n): ").strip().lower() == "y"
            automator.dispatch_batch_smtp(unsent_gcs, touch_number=1, max_sends=count, dry_run=dry)
            generate_dashboard()

        elif choice == "2":
            email = input("Client Email Address: ").strip()
            if not email or "@" not in email:
                print("[!] Invalid email address.")
                continue
            company = input("Client Company Name (optional): ").strip()
            name = input("Client Contact Name (optional): ").strip()
            custom_subject = input("Custom Subject (press enter for auto-generated AI pitch): ").strip() or None
            custom_body = input("Custom Body (press enter for auto-generated AI pitch): ").strip() or None
            automator.send_direct_to_client(
                to_email=email,
                company=company,
                name=name,
                subject=custom_subject,
                body=custom_body
            )

        elif choice == "3":
            cnt = input("How many to display? (default 20): ").strip()
            limit = int(cnt) if cnt.isdigit() else 20
            print("-" * 110)
            print(f"{'ID':<6} | {'COMPANY':<35} | {'LOCATION':<22} | {'EMAIL':<30} | {'PHONE'}")
            print("-" * 110)
            for l in unsent_gcs[:limit]:
                loc = f"{l.get('city', '')}, {l.get('state', '')}"
                comp = (l.get('company') or 'Unknown')[:34]
                em = (l.get('email') or '')[:29]
                ph = l.get('phone') or 'N/A'
                print(f"{l.get('id', 0):<6} | {comp:<35} | {loc:<22} | {em:<30} | {ph}")
            print("-" * 110)

        elif choice == "4":
            if unsent_gcs:
                sample = unsent_gcs[0]
                pitch = prepare_campaign_touch(sample, touch_number=1)
                print("=" * 78)
                print(f"Recipient : {pitch['recipient']}")
                print(f"Company   : {sample.get('company')}")
                print(f"Subject   : {pitch['subject']}")
                print("-" * 78)
                print(pitch["body"])
                print("=" * 78)
            else:
                print("[!] No unsent Commercial GCs remaining.")

        elif choice == "5":
            cnt = input("Number of drafts to upload to Gmail (default 10): ").strip()
            limit = int(cnt) if cnt.isdigit() else 10
            uploader.upload_drafts(unsent_gcs, touch_number=1, limit=limit)

        elif choice == "6":
            stats = hunter.get_stats()
            print("\nPipeline Status Breakdown:")
            for k, v in stats["status_breakdown"].items():
                print(f"  - {k:<20}: {v:,}")
            logs = state.get("send_logs", [])
            print(f"\nRecent Deliveries ({len(logs)} total):")
            for log in logs[-5:]:
                print(f"  - {log.get('sent_at')}: {log.get('company')} ({log.get('email')}) -> {log.get('status')}")

        elif choice == "7":
            dash = generate_dashboard()
            import webbrowser
            webbrowser.open(str(dash))
            print(f"[+] Launched dashboard: {dash}")

        elif choice == "8":
            cnt = input("Number of Commercial GCs to simulate (default 5): ").strip()
            limit = int(cnt) if cnt.isdigit() else 5
            automator.dispatch_batch_smtp(unsent_gcs, touch_number=1, max_sends=limit, dry_run=True)

        elif choice in ["0", "q", "exit"]:
            print("\nExiting outreach terminal. Good luck closing clients!\n")
            break

def build_parser():
    parser = argparse.ArgumentParser(
        description="Autonomous Gmail Outreach Engine for US Construction Contractors",
        add_help=True
    )
    # Action modes
    parser.add_argument("--smtp", "--send", dest="send_smtp", action="store_true", help="Dispatch outreach directly to client inboxes via Gmail SMTP")
    parser.add_argument("--upload", "--upload-drafts", dest="upload_drafts", action="store_true", help="Upload drafts directly into your real Gmail 'Drafts' folder")
    parser.add_argument("--upload-imap", dest="upload_imap", action="store_true", help="Upload drafts specifically via IMAP using Google App Password")
    parser.add_argument("--upload-api", dest="upload_api", action="store_true", help="Upload drafts specifically via official Gmail REST API")
    parser.add_argument("--browser", dest="browser", action="store_true", help="Launch pre-filled Gmail compose tabs in default browser")
    parser.add_argument("--list", dest="list_leads", action="store_true", help="List matched contractors and contact information")
    parser.add_argument("--pitch-preview", dest="pitch_preview", action="store_true", help="Preview the personalized email copy for a matched contractor")
    parser.add_argument("--stats", dest="stats", action="store_true", help="Display pipeline status breakdown and metrics")
    parser.add_argument("--dashboard", dest="dashboard", action="store_true", help="Generate and launch interactive HTML dashboard")

    # Filters
    parser.add_argument("--gc", "--commercial-gc", dest="commercial_gc", action="store_true", help="Target Commercial General Contractors specifically")
    parser.add_argument("--trade", "-t", type=str, default=None, help="Filter by specific trade niche (e.g. 'Commercial General Contractors', 'HVAC')")
    parser.add_argument("--city", type=str, default=None, help="Filter by city")
    parser.add_argument("--state", "-s", type=str, default=None, help="Filter by US state (e.g. TX, CA, AR, FL)")

    # 1-Command Direct Client Dispatch
    parser.add_argument("--to", type=str, default=None, help="Direct client email address to send to on 1 command")
    parser.add_argument("--company", "-c", type=str, default=None, help="Client company name for direct sending")
    parser.add_argument("--name", "-n", type=str, default=None, help="Client contact name for direct sending")
    parser.add_argument("--subject", type=str, default=None, help="Custom subject line for direct send")
    parser.add_argument("--body", type=str, default=None, help="Custom email body for direct send")
    parser.add_argument("--terminal", "--interactive", dest="interactive", action="store_true", help="Launch interactive outreach terminal control panel")

    # Controls
    parser.add_argument("count", nargs="?", default=None, help="Number of leads to process (legacy positional syntax)")
    parser.add_argument("--batch", "-b", type=int, default=None, help="Batch size of leads to process")
    parser.add_argument("--all", dest="process_all", action="store_true", help="Target all available unsent leads matching criteria")
    parser.add_argument("--touch", type=int, default=1, choices=[1, 2, 3, 4], help="Touch sequence number (1-4)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulate email sending without real dispatch")
    parser.add_argument("--daily-limit", type=int, default=45, help="Daily sending limit cap for safety")

    return parser

def main():
    print("\n" + "=" * 78)
    print(" [*] SEND_GMAIL: AUTONOMOUS GMAIL OUTREACH ENGINE")
    print(f" [*] Sender Identity: {SENDER_PROFILE['name']} <{SENDER_PROFILE['email']}>")
    print("=" * 78 + "\n")

    parser = build_parser()
    args = parser.parse_args()

    # Backwards compatibility for mode as first positional argument
    if args.count and not args.count.isdigit():
        cmd = args.count.lower()
        if cmd in ["--smtp", "--send", "-smtp"]:
            args.send_smtp = True
            args.count = None
        elif cmd in ["--upload", "--upload-drafts"]:
            args.upload_drafts = True
            args.count = None
        elif cmd in ["--browser"]:
            args.browser = True
            args.count = None
        elif cmd in ["--stats"]:
            args.stats = True
            args.count = None
        elif cmd in ["--dashboard"]:
            args.dashboard = True
            args.count = None

    hunter = LeadHunter()
    automator = GmailAutomator(daily_send_limit=args.daily_limit)
    uploader = GmailDraftUploader()
    state = automator.state
    sent_ids = set(state.get("sent_ids", []))

    # Determine trade filter
    trade_filter = args.trade
    if args.commercial_gc:
        trade_filter = "Commercial General Contractors"

    # Filter unsent leads
    unsent_leads = [
        l for l in hunter.master_leads
        if l.get("id") not in sent_ids and l.get("email")
    ]

    if args.commercial_gc:
        unsent_leads = [l for l in unsent_leads if is_commercial_gc(l)]
    elif trade_filter:
        unsent_leads = [
            l for l in unsent_leads
            if trade_filter.lower() in (l.get("trade_niche") or "").lower()
        ]

    if args.state:
        unsent_leads = [
            l for l in unsent_leads
            if (l.get("state") or "").strip().upper() == args.state.strip().upper()
        ]

    if args.city:
        unsent_leads = [
            l for l in unsent_leads
            if args.city.lower() in (l.get("city") or "").lower()
        ]

    # Calculate statistics
    total_in_db = len(hunter.master_leads)
    comm_gcs_in_db = len([l for l in hunter.master_leads if is_commercial_gc(l)])
    sent_total = len(sent_ids)

    print(f"Total Staged Leads in Database      : {total_in_db:,}")
    print(f"Total Commercial GCs in Database    : {comm_gcs_in_db:,}")
    print(f"Emails Dispatched So Far (Sent)     : {sent_total:,}")
    if trade_filter or args.commercial_gc or args.state or args.city:
        target_name = "Commercial General Contractors" if args.commercial_gc else (trade_filter or "Filtered")
        print(f"Target Queue [{target_name}] : {len(unsent_leads):,} unsent ready\n")
    else:
        print(f"Unsent Qualified Leads Ready        : {len(unsent_leads):,}\n")

    # Determine batch size
    batch_size = 10
    if args.process_all:
        batch_size = len(unsent_leads)
    elif args.batch is not None:
        batch_size = args.batch
    elif args.count and args.count.isdigit():
        batch_size = int(args.count)

    # 0. Action: Direct 1-Command Specific Client Email Dispatch
    if args.to:
        automator.send_direct_to_client(
            to_email=args.to,
            company=args.company or "",
            name=args.name or "",
            trade=trade_filter or "Commercial General Contractors",
            subject=args.subject,
            body=args.body,
            touch_number=args.touch,
            dry_run=args.dry_run
        )
        return

    # Action: Interactive Terminal Console
    if args.interactive:
        run_terminal_console(hunter, automator, uploader)
        return

    # 1. Action: Pitch Preview
    if args.pitch_preview:
        if not unsent_leads:
            print("[!] No leads match the filter to preview.")
            return
        sample = unsent_leads[0]
        pitch = prepare_campaign_touch(sample, touch_number=args.touch)
        print("=" * 78)
        print(f" [*] PREVIEWING TOUCH {args.touch} PITCH FOR: {sample.get('company')}")
        print(f" [*] Recipient : {pitch['recipient']}")
        print(f" [*] Location  : {sample.get('city')}, {sample.get('state')}")
        print(f" [*] Trade     : {sample.get('trade_niche')}")
        print(f" [*] Subject   : {pitch['subject']}")
        print("-" * 78)
        print(pitch["body"])
        print("=" * 78)
        return

    # 2. Action: List Leads
    if args.list_leads:
        show_count = min(batch_size if (args.batch or args.count) else 30, len(unsent_leads))
        print(f"[*] Displaying {show_count} of {len(unsent_leads)} matched leads:")
        print("-" * 110)
        print(f"{'ID':<6} | {'COMPANY':<35} | {'LOCATION':<22} | {'EMAIL':<30} | {'PHONE'}")
        print("-" * 110)
        for l in unsent_leads[:show_count]:
            loc = f"{l.get('city', '')}, {l.get('state', '')}"
            comp = (l.get('company') or 'Unknown')[:34]
            em = (l.get('email') or '')[:29]
            ph = l.get('phone') or 'N/A'
            print(f"{l.get('id', 0):<6} | {comp:<35} | {loc:<22} | {em:<30} | {ph}")
        print("-" * 110)
        if len(unsent_leads) > show_count:
            print(f"... and {len(unsent_leads) - show_count} more leads in queue. (Use --batch {len(unsent_leads)} or --all to view/process all).")
        return

    # 3. Action: Send via SMTP
    if (args.process_all or args.batch is not None or (args.count and args.count.isdigit())) and not (args.upload_drafts or args.upload_imap or args.upload_api or args.browser or args.list_leads or args.pitch_preview or args.stats or args.dashboard):
        args.send_smtp = True

    if args.send_smtp or (args.count and args.count.isdigit()):
        if not unsent_leads:
            print("[!] No matching unsent leads found.")
            return

        if args.process_all:
            automator.daily_send_limit = max(automator.daily_send_limit, batch_size)

        if batch_size > automator.daily_send_limit and not args.dry_run:
            print(f"[!] SAFETY WARNING: You requested {batch_size} sends, but daily limit is set to {automator.daily_send_limit}.")
            print(f"[*] Capping this batch to {automator.daily_send_limit} to protect Gmail account reputation.")
            actual_sends = automator.daily_send_limit
        else:
            actual_sends = batch_size

        print(f"[*] Dispatching Touch {args.touch} outreach to {actual_sends} client inboxes via Gmail SMTP...")
        automator.dispatch_batch_smtp(unsent_leads, touch_number=args.touch, max_sends=actual_sends, dry_run=args.dry_run)
        generate_dashboard()
        return

    # 4. Action: Upload Drafts to Gmail
    if args.upload_drafts or args.upload_imap or args.upload_api:
        if not unsent_leads:
            print("[!] No matching unsent leads found.")
            return

        print(f"[*] Uploading {min(batch_size, len(unsent_leads))} drafts directly into your Gmail 'Drafts' folder...")
        if args.upload_imap:
            uploader.upload_via_imap(unsent_leads, touch_number=args.touch, limit=batch_size)
        elif args.upload_api:
            uploader.upload_via_api(unsent_leads, touch_number=args.touch, limit=batch_size)
        else:
            uploader.upload_drafts(unsent_leads, touch_number=args.touch, limit=batch_size)
        return

    # 5. Action: Browser Compose Launcher
    if args.browser:
        if not unsent_leads:
            print("[!] No matching unsent leads found.")
            return

        limit = min(batch_size if (args.batch or args.count) else 5, 10)
        print(f"[*] Launching {limit} pre-filled Gmail compose drafts in default browser...")
        automator.launch_browser_drafts(unsent_leads, touch_number=args.touch, limit=limit)
        generate_dashboard()
        return

    # 6. Action: Stats
    if args.stats:
        stats = hunter.get_stats()
        print("Pipeline Status Breakdown:")
        for k, v in stats["status_breakdown"].items():
            print(f"  - {k:<20}: {v:,}")
        print("\nTop Trade Specializations:")
        for t, c in sorted(stats["trade_breakdown"].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {t:<35}: {c:,}")
        return

    # 7. Action: Dashboard
    if args.dashboard:
        dash_path = generate_dashboard()
        print(f"[+] Launching Dashboard in browser: {dash_path}")
        import webbrowser
        webbrowser.open(str(dash_path))
        return

    # Default: Menu / Help
    dash_path = generate_dashboard()
    print("[AVAILABLE ACTIONS & SHORTCUTS]")
    print("  Targeting Commercial General Contractors:")
    print("    1. List Commercial GCs          : python send_gmail.py --gc --list")
    print("    2. Preview GC Pitch Copy        : python send_gmail.py --gc --pitch-preview")
    print("    3. Upload Drafts to Gmail       : python send_gmail.py --gc --upload [count]")
    print("    4. Auto-Send via Gmail SMTP     : python send_gmail.py --gc --smtp [count] [--dry-run]")
    print("    5. 1-Click Browser Drafts       : python send_gmail.py --gc --browser [count]")
    print("\n  General Commands:")
    print("    - Direct Auto-Send via SMTP     : python send_gmail.py --smtp [count] [--dry-run]")
    print("    - Direct Upload to Gmail Drafts : python send_gmail.py --upload [count]")
    print("    - Interactive Web Dashboard     : python send_gmail.py --dashboard")
    print("    - View Pipeline Stats           : python send_gmail.py --stats")
    print(f"\n[+] Interactive Dashboard refreshed at: {dash_path}\n")

if __name__ == "__main__":
    main()

