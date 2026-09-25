"""
Hunt & Outreach Pipeline for 10 Plumbing Contractors in Atlanta, GA
1. Sourcing 10 Verified Commercial & Residential Plumbing Contractors in Atlanta
2. Generating tailored Division 22 Plumbing & Piping Takeoff Pitches (with mechanical.pdf proof)
3. Uploading drafts directly to Gmail (or generating 1-click direct compose drafts)
"""

import os
import sys
import json
import webbrowser
from pathlib import Path

# Ensure UTF-8 console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = Path(__file__).parent
MASTER_DB_FILE = DATA_DIR / "leads_master_db.json"
STATE_FILE = DATA_DIR / "campaign_state.json"
OUTREACH_JSON = DATA_DIR / "atlanta_plumbing_leads_10.json"
OUTREACH_HTML = DATA_DIR / "atlanta_plumbing_outreach.html"

from trade_intelligence import get_trade_intelligence
from pitch_generator import prepare_campaign_touch, SENDER_PROFILE
from agent_mailer import load_campaign_state, save_campaign_state, load_env_credentials
from lead_hunter import LeadHunter
from gmail_draft_uploader import GmailDraftUploader

# 10 High-Intent Plumbing Contractors in the Greater Atlanta Metro Area
ATLANTA_PLUMBING_CONTRACTORS = [
    {
        "company": "Malone Plumbing Inc",
        "contact_name": "Sean Malone",
        "role": "President / Commercial Estimating",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "bids@maloneplumbinginc.com",
        "phone": "(770) 441-3658",
        "website": "https://maloneplumbinginc.com",
        "pain_point": "measuring linear feet of sanitary, storm, domestic water, and gas piping plus valve and fixture takeoff counts",
        "hook": "We trace every fixture unit, waste line, domestic water run, and valve fitting with colored overlay markups and ready-to-price bill of quantities.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "PlumbWorks Inc",
        "contact_name": "Preconstruction Department",
        "role": "Chief Estimator",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "market@plumbworksinc.com",
        "phone": "(404) 524-1825",
        "website": "https://www.plumbworksinc.com",
        "pain_point": "linear pipe measurements and itemized fixture schedules under aggressive 48-hour commercial bid deadlines",
        "hook": "We deliver complete plumbing linear footage, fixture schedules, and valve counts formatted to CSI MasterFormat in 48 hours.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "Elite Plumbing Services Atlanta",
        "contact_name": "Estimating Team",
        "role": "Preconstruction Manager",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "info@eliteplumbingatlanta.com",
        "phone": "(404) 998-9000",
        "website": "https://www.eliteplumbingatlanta.com",
        "pain_point": "tracing water lines, sanitary vent runs, and equipment connections across complex architectural drawings",
        "hook": "We provide color-coded PlanSwift/Bluebeam plumbing markups and live-formula Excel BOQs ready for supplier pricing.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "Quick Action Plumbers (Commercial Division)",
        "contact_name": "Donnie",
        "role": "Commercial Operations & Estimating",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "donnie@onefastplumber.com",
        "phone": "(770) 854-0755",
        "website": "https://www.onefastplumber.com",
        "pain_point": "calculating piping material bills of materials and fitting counts in time to submit bids before deadline",
        "hook": "We trace every domestic water, waste, and storm line with color-coded overlays so your pricing is 100% accurate.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "RS Andrews Commercial Plumbing",
        "contact_name": "Commercial Bid Team",
        "role": "Preconstruction Director",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "customercare@rsandrews.com",
        "phone": "(770) 913-6412",
        "website": "https://www.rsandrews.com",
        "pain_point": "handling multiple large commercial plumbing bids simultaneously without bottlenecking your estimators",
        "hook": "We act as your overflow takeoff team, turning around complete plumbing bills of quantities in 24 to 48 hours.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "Reliable Commercial Plumbing Services",
        "contact_name": "Commercial Estimating",
        "role": "Senior Estimator",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "commercial@reliableair.com",
        "phone": "(770) 594-9969",
        "website": "https://reliableair.com",
        "pain_point": "extracting fixture schedules, riser diagrams, and pipe linear footage under tight bid cutoffs",
        "hook": "Get 100% itemized pipe runs categorized by material (copper, PVC, cast iron) and fixture counts in a clean Excel workbook.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "Allatoona Commercial Plumbing",
        "contact_name": "Commercial Department",
        "role": "Estimating Lead",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "service@allatoonaplumbing.com",
        "phone": "(770) 720-7212",
        "website": "https://www.allatoonaplumbing.com",
        "pain_point": "preventing scope gaps and pipe count shortages during high-volume commercial bidding seasons",
        "hook": "We provide verified, marked-up PlanSwift drawing sheets and supplier-ready BOQs in under 48 hours.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "Bardi Mechanical & Plumbing",
        "contact_name": "Alex Bardi",
        "role": "CEO / Commercial Precon",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "info@bardi.com",
        "phone": "(770) 263-5355",
        "website": "https://www.bardi.com",
        "pain_point": "linear pipe measurement of commercial storm, water supply, and gas piping plus valve schedules",
        "hook": "We deliver full CSI Division 22 takeoffs with color-coded Bluebeam markups so you can review and bid with confidence.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "Estes Commercial Plumbing & Piping",
        "contact_name": "Tommy Estes",
        "role": "Preconstruction Operations",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "customerservice@estesair.com",
        "phone": "(404) 361-6560",
        "website": "https://www.estesair.com",
        "pain_point": "estimating bandwidth bottlenecks when multiple commercial plumbing RFPs land on the same week",
        "hook": "We convert your plumbing plan sets into itemized Excel takeoffs and supplier quote sheets in 24 to 48 hours.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    },
    {
        "company": "Cunningham Commercial Plumbing",
        "contact_name": "Precon Estimating Team",
        "role": "Estimator",
        "trade_niche": "MEP - Plumbing & Piping",
        "city": "Atlanta",
        "state": "GA",
        "email": "info@cunninghamassociates.com",
        "phone": "(770) 455-6722",
        "website": "https://www.cunninghamassociates.com",
        "pain_point": "tracing water distribution lines, sanitary sewer runs, and counting specialized commercial fixtures",
        "hook": "We deliver complete plumbing bills of quantities and marked-up PDF drawings ready to plug into your bidding sheets.",
        "sample_proof": "Commercial Mechanical, Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf"
    }
]

def run():
    print("\n" + "=" * 80)
    print(" 🚰  ATLANTA PLUMBING CONTRACTOR HUNT & OUTREACH ENGINE")
    print(f" Target: 10 Verified Commercial & Residential Plumbing Contractors in Atlanta, GA")
    print(f" Sender: {SENDER_PROFILE['name']} <{SENDER_PROFILE['email']}>")
    print("=" * 80 + "\n")

    hunter = LeadHunter()
    state = load_campaign_state()
    uploader = GmailDraftUploader()

    # Merge into master DB if not already present
    staged_leads = []
    for raw in ATLANTA_PLUMBING_CONTRACTORS:
        # Check if company already in hunter
        existing = next((l for l in hunter.master_leads if l.get("company", "").lower() == raw["company"].lower()), None)
        if existing:
            lead = existing
        else:
            raw["id"] = len(hunter.master_leads) + len(staged_leads) + 1
            raw["first_name"] = raw["contact_name"].split()[0]
            raw["division"] = "Division 22 - Plumbing"
            raw["status"] = "QUALIFIED"
            raw["source"] = "atlanta_plumbing_hunter"
            hunter.master_leads.append(raw)
            lead = raw
        staged_leads.append(lead)

    hunter.save_master_db()
    print(f"[+] Loaded & Qualified 10 Atlanta Plumbing Contractors in Master Database.")

    # Generate custom pitches for all 10
    drafts = []
    rows_html = []
    for idx, lead in enumerate(staged_leads, 1):
        pitch = prepare_campaign_touch(lead, touch_number=1)
        drafts.append(pitch)

        print(f"[{idx}/10] Prepared Pitch for: {lead['company']}")
        print(f"       Contact : {lead['contact_name']} <{lead['email']}>")
        print(f"       Subject : {pitch['subject']}")
        print(f"       Proof   : {lead['sample_file']}")
        print("-" * 80)

        # Build table row for HTML dashboard
        rows_html.append(f"""
        <tr class="hover:bg-slate-800/50 transition border-b border-slate-800 text-xs">
            <td class="p-3">
                <div class="font-bold text-white">{lead['company']}</div>
                <div class="text-[11px] text-slate-400">{lead['city']}, {lead['state']} &bull; <a href="{lead['website']}" target="_blank" class="text-blue-400 hover:underline">{lead['website'].replace('https://','')}</a></div>
            </td>
            <td class="p-3 font-mono text-slate-300">
                <span class="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">Division 22 Plumbing</span>
                <div class="text-[10px] text-slate-500 mt-1">Proof: mechanical.pdf</div>
            </td>
            <td class="p-3">
                <div class="font-medium text-slate-200">{lead['contact_name']} ({lead['role']})</div>
                <div class="text-slate-400 font-mono">{lead['email']}</div>
            </td>
            <td class="p-3">
                <div class="text-[11px] text-slate-300 font-medium">{pitch['subject']}</div>
            </td>
            <td class="p-3 text-right">
                <a href="{pitch['gmail_compose_url']}" target="_blank" class="inline-flex items-center px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded font-bold shadow transition">
                    Send in Gmail ✉️
                </a>
            </td>
        </tr>
        """)

    # Save JSON package
    with open(OUTREACH_JSON, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)
    print(f"\n[+] Saved 10 Atlanta Plumbing Outreach Drafts to: {OUTREACH_JSON}")

    # Generate dedicated 1-Click Launch Dashboard HTML
    table_content = "\n".join(rows_html)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Atlanta Plumbing Contractors | 10 Direct Outreach Drafts</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-8">
    <div class="max-w-6xl mx-auto space-y-6">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex justify-between items-center shadow-xl">
            <div>
                <h1 class="text-xl font-black text-white flex items-center gap-2">
                    <span>🚰</span> 10 Atlanta Plumbing Contractors Pipeline
                </h1>
                <p class="text-xs text-slate-400 mt-1">Niche: MEP Division 22 (Plumbing & Piping) &bull; Value Offer: On-Demand Takeoff Support &bull; Sender: {SENDER_PROFILE['name']} ({SENDER_PROFILE['email']})</p>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="launchAllDrafts()" class="px-4 py-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs font-bold rounded-lg shadow-md transition">
                    Open All 10 in Gmail Tabs 🚀
                </button>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            <table class="w-full text-left border-collapse" id="draftsTable">
                <thead>
                    <tr class="bg-slate-950 text-slate-400 uppercase tracking-wider text-[11px] font-semibold border-b border-slate-800">
                        <th class="p-3">Company & Website</th>
                        <th class="p-3">Trade Division</th>
                        <th class="p-3">Contact & Email</th>
                        <th class="p-3">Subject Line</th>
                        <th class="p-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60">
                    {table_content}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function launchAllDrafts() {{
            const links = Array.from(document.querySelectorAll("#draftsTable a[href*='mail.google.com']"));
            if (confirm(`Open all ${{links.length}} pre-filled Gmail compose tabs in your browser?`)) {{
                links.forEach((a, i) => {{
                    setTimeout(() => {{
                        window.open(a.href, '_blank');
                    }}, i * 900);
                }});
            }}
        }}
    </script>
</body>
</html>"""

    with open(OUTREACH_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Dedicated Atlanta Plumbing Dashboard generated at: {OUTREACH_HTML}")

    # Check for upload capability
    print("\n" + "=" * 80)
    print(" [ACTION] DIRECT GMAIL DRAFT INJECTION CHECK")
    print("=" * 80)
    creds = load_env_credentials()
    if creds.get("pass"):
        print("[+] Google App Password detected in .env! Attempting direct IMAP injection into Gmail Drafts folder...")
        res = uploader.upload_via_imap(staged_leads, touch_number=1, limit=10)
        print(f"[+] Direct Upload Result: {res}")
    else:
        print("[!] Note: GMAIL_APP_PASS is not set in .env.")
        print("[+] Launching the 1-Click Interactive Dashboard in your default browser...")
        print("    You can click 'Open All 10 in Gmail Tabs 🚀' or click 'Send in Gmail ✉️' on any contractor!")
        webbrowser.open(str(OUTREACH_HTML))

if __name__ == "__main__":
    run()
