"""
Interactive Command Center & Dashboard Generator
Generates a modern, responsive HTML5 dashboard for visual pipeline inspection,
lead filtering, 1-click Gmail sending, and real-time status management.
"""

import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import List, Dict, Any

from lead_hunter import LeadHunter
from pitch_generator import prepare_campaign_touch, SENDER_PROFILE
from agent_mailer import load_campaign_state

DATA_DIR = Path(__file__).parent
DASHBOARD_HTML = DATA_DIR / "dashboard.html"

def generate_dashboard():
    hunter = LeadHunter()
    state = load_campaign_state()
    sent_ids = set(state.get("sent_ids", []))
    leads = hunter.master_leads

    # Sort leads: put unsent high-priority leads first
    display_leads = sorted(leads, key=lambda l: (l.get("id") in sent_ids, l.get("id", 0)))[:500]

    stats = hunter.get_stats()
    total = len(leads)
    sent_count = len(sent_ids)
    sample_count = len(state.get("sample_requested_ids", []))
    closed_count = len(state.get("closed_ids", []))

    rows_html = []
    for l in display_leads:
        lid = l.get("id")
        comp = l.get("company", "Company")
        trade = l.get("trade_niche", "General Contracting")
        city = l.get("city", "USA")
        state_code = l.get("state", "US")
        email = l.get("email", "")
        phone = l.get("phone", "")
        is_sent = lid in sent_ids

        # Generate Touch 1 Pitch & Gmail Compose URL
        pitch = prepare_campaign_touch(l, touch_number=1)
        compose_url = pitch["gmail_compose_url"]
        preview_body = pitch["body"].replace("\n", " ").replace('"', '&quot;')[:180] + "..."
        subject_esc = pitch["subject"].replace('"', '&quot;')

        badge_class = "bg-emerald-100 text-emerald-800 border-emerald-300" if is_sent else "bg-blue-50 text-blue-700 border-blue-200"
        status_text = "DISPATCHED (SENT)" if is_sent else "READY TO PITCH"

        # Trade styling
        trade_color = "bg-amber-100 text-amber-800"
        if "MEP" in trade:
            trade_color = "bg-sky-100 text-sky-800"
        elif "Concrete" in trade:
            trade_color = "bg-stone-200 text-stone-800"
        elif "Drywall" in trade:
            trade_color = "bg-purple-100 text-purple-800"
        elif "Commercial" in trade:
            trade_color = "bg-indigo-100 text-indigo-800"
        elif "Residential" in trade:
            trade_color = "bg-emerald-100 text-emerald-800"

        sample_file = l.get("sample_file", "Sample Takeoff PDF")

        row = f"""
        <tr class="hover:bg-slate-50 transition border-b border-slate-200 text-sm" data-trade="{trade}" data-state="{state_code}" data-status="{status_text}">
            <td class="p-3 font-semibold text-slate-800">
                <div class="font-bold text-slate-900">{comp}</div>
                <div class="text-xs text-slate-500">{city}, {state_code} &bull; <a href="{l.get('website', '#')}" target="_blank" class="text-blue-600 hover:underline">{l.get('website', '').replace('https://', '').replace('http://', '').strip('/')[:25]}</a></div>
            </td>
            <td class="p-3">
                <span class="px-2.5 py-1 rounded-full text-xs font-semibold {trade_color}">{trade}</span>
                <div class="text-[11px] text-slate-400 mt-1">Proof: {sample_file[:22]}</div>
            </td>
            <td class="p-3">
                <div class="font-medium text-slate-800">{l.get('contact_name', 'Estimator')}</div>
                <div class="text-xs text-slate-500 font-mono"><a href="mailto:{email}" class="hover:text-blue-600">{email}</a></div>
                <div class="text-[11px] text-slate-400">{phone}</div>
            </td>
            <td class="p-3">
                <span class="px-2 py-0.5 rounded text-xs font-medium border {badge_class}">{status_text}</span>
            </td>
            <td class="p-3">
                <button onclick="previewPitch({lid})" class="text-xs text-indigo-600 hover:text-indigo-800 font-medium underline">Preview Pitch</button>
                <div id="pitch-data-{lid}" class="hidden" data-subject="{subject_esc}" data-body="{pitch['body'].replace(chr(10), '<br>').replace('"', '&quot;')}"></div>
            </td>
            <td class="p-3 text-right">
                <a href="{compose_url}" target="_blank" class="inline-flex items-center px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg shadow-sm transition space-x-1">
                    <span>Send in Gmail</span>
                    <span>✉️</span>
                </a>
            </td>
        </tr>
        """
        rows_html.append(row)

    table_rows = "\n".join(rows_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Lead Acquisition Command Center | Takeoff & Estimation</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}
        code, pre {{ font-family: 'JetBrains+Mono', monospace; }}
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen">
    <!-- Header -->
    <header class="bg-slate-950 border-b border-slate-800 sticky top-0 z-30 shadow-lg">
        <div class="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
            <div>
                <div class="flex items-center space-x-3">
                    <span class="text-2xl">🏗️</span>
                    <div>
                        <h1 class="text-xl font-black tracking-tight text-white">AUTONOMOUS TAKE-OFF LEAD AGENT</h1>
                        <p class="text-xs text-slate-400">USA Construction Client Acquisition Engine &bull; Sender: <span class="text-emerald-400 font-semibold">{SENDER_PROFILE['name']}</span> ({SENDER_PROFILE['email']})</p>
                    </div>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <button onclick="launchFirstFiveDrafts()" class="px-4 py-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white text-xs font-bold rounded-lg shadow-md transition flex items-center space-x-1.5">
                    <span>Launch Top 5 Drafts in Gmail</span>
                    <span>🚀</span>
                </button>
                <button onclick="location.reload()" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition">
                    Refresh Feed 🔄
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <!-- KPI Cards -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-sm">
                <div class="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Leads Staged</div>
                <div class="text-3xl font-extrabold text-white mt-1">{total:,}</div>
                <div class="text-xs text-slate-500 mt-1">Verified US Construction Accounts</div>
            </div>
            <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-sm">
                <div class="text-xs font-semibold uppercase tracking-wider text-blue-400">Dispatched (Sent)</div>
                <div class="text-3xl font-extrabold text-blue-400 mt-1">{sent_count:,}</div>
                <div class="text-xs text-slate-500 mt-1">{(sent_count/max(1,total))*100:.1f}% Outreach Coverage</div>
            </div>
            <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-sm">
                <div class="text-xs font-semibold uppercase tracking-wider text-amber-400">Takeoff Plan Requests</div>
                <div class="text-3xl font-extrabold text-amber-400 mt-1">{sample_count}</div>
                <div class="text-xs text-slate-500 mt-1">Plans Submitted for Takeoff</div>
            </div>
            <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-sm">
                <div class="text-xs font-semibold uppercase tracking-wider text-emerald-400">Closed Retainers</div>
                <div class="text-3xl font-extrabold text-emerald-400 mt-1">{closed_count}</div>
                <div class="text-xs text-slate-500 mt-1">$1,500 - $2,500/mo Contracts</div>
            </div>
        </div>

        <!-- Strategy & Offer Banner -->
        <div class="bg-gradient-to-r from-blue-950/60 to-slate-900 border border-blue-800/40 rounded-xl p-5 text-sm text-slate-300 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div class="space-y-1">
                <div class="font-bold text-white flex items-center space-x-2">
                    <span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-xs font-mono">VALUE OFFER</span>
                    <span>The On-Demand Takeoff Pipeline</span>
                </div>
                <p class="text-xs text-slate-400">Every outreach email offers fast on-demand quantity takeoffs on upcoming plans (24-48 hr turnaround, PlanSwift/Bluebeam markups + Excel BOQ) with verified portfolio proofs.</p>
            </div>
            <div class="flex items-center space-x-2 text-xs">
                <span class="text-slate-400">Verified Portfolio Proofs:</span>
                <span class="px-2 py-1 rounded bg-slate-800 text-slate-300 font-mono text-[11px] border border-slate-700">mechanical.pdf</span>
                <span class="px-2 py-1 rounded bg-slate-800 text-slate-300 font-mono text-[11px] border border-slate-700">SPAULDING DUPLEX.pdf</span>
                <span class="px-2 py-1 rounded bg-slate-800 text-slate-300 font-mono text-[11px] border border-slate-700">NAVY FEDERAL.pdf</span>
            </div>
        </div>

        <!-- Controls & Filters -->
        <div class="bg-slate-800/90 border border-slate-700 rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between">
            <div class="flex flex-wrap gap-3 items-center">
                <!-- Search -->
                <div class="relative">
                    <input type="text" id="searchInput" onkeyup="filterLeads()" placeholder="Search company, contact, city..." class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-64">
                </div>
                <!-- Trade Filter -->
                <select id="tradeFilter" onchange="filterLeads()" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500">
                    <option value="">All Trades / Niches</option>
                    <option value="Commercial General Contractors">Commercial General Contractors</option>
                    <option value="MEP - Mechanical & HVAC">MEP - Mechanical & HVAC</option>
                    <option value="MEP - Electrical">MEP - Electrical</option>
                    <option value="MEP - Plumbing & Piping">MEP - Plumbing & Piping</option>
                    <option value="Concrete & Masonry">Concrete & Masonry</option>
                    <option value="Drywall & Framing">Drywall & Framing</option>
                    <option value="Painting & Wallcovering">Painting & Wallcovering</option>
                    <option value="Flooring & Tile">Flooring & Tile</option>
                    <option value="Roofing & Siding">Roofing & Siding</option>
                    <option value="Residential Custom Builders">Residential Custom Builders</option>
                    <option value="Architecture">Architecture & Design-Build</option>
                </select>
                <!-- Status Filter -->
                <select id="statusFilter" onchange="filterLeads()" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500">
                    <option value="">All Statuses</option>
                    <option value="READY TO PITCH">Ready to Pitch (Unsent)</option>
                    <option value="DISPATCHED (SENT)">Dispatched (Sent)</option>
                </select>
            </div>
            <div class="text-xs text-slate-400">
                Showing <span id="visibleCount" class="font-bold text-white">{len(display_leads)}</span> leads
            </div>
        </div>

        <!-- Leads Table -->
        <div class="bg-white rounded-xl shadow-xl overflow-hidden border border-slate-200">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse" id="leadsTable">
                    <thead>
                        <tr class="bg-slate-100 text-xs font-bold uppercase tracking-wider text-slate-600 border-b border-slate-200">
                            <th class="p-3">Company & Market</th>
                            <th class="p-3">Trade & Proof</th>
                            <th class="p-3">Decision Maker & Contact</th>
                            <th class="p-3">Pipeline Status</th>
                            <th class="p-3">Pitch Copy</th>
                            <th class="p-3 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Modal for Previewing Pitch -->
    <div id="previewModal" class="hidden fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl max-w-2xl w-full p-6 text-slate-900 shadow-2xl border border-slate-200 space-y-4">
            <div class="flex justify-between items-center pb-3 border-b border-slate-200">
                <h3 class="text-lg font-bold text-slate-900" id="modalSubject">Email Subject</h3>
                <button onclick="closeModal()" class="text-slate-400 hover:text-slate-600 text-2xl font-bold">&times;</button>
            </div>
            <div class="bg-slate-50 p-4 rounded-xl text-xs text-slate-700 leading-relaxed font-mono whitespace-pre-wrap max-h-96 overflow-y-auto" id="modalBody">
                Email Content
            </div>
            <div class="flex justify-end space-x-3 pt-2">
                <button onclick="closeModal()" class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-bold rounded-lg transition">Close</button>
            </div>
        </div>
    </div>

    <script>
        function filterLeads() {{
            const search = document.getElementById("searchInput").value.toLowerCase();
            const trade = document.getElementById("tradeFilter").value.toLowerCase();
            const status = document.getElementById("statusFilter").value;
            const rows = document.querySelectorAll("#leadsTable tbody tr");
            let visible = 0;

            rows.forEach(r => {{
                const rTrade = (r.getAttribute("data-trade") || "").toLowerCase();
                const rStatus = r.getAttribute("data-status") || "";
                const rText = r.innerText.toLowerCase();

                const matchesSearch = !search || rText.includes(search);
                const matchesTrade = !trade || rTrade.includes(trade);
                const matchesStatus = !status || rStatus === status;

                if (matchesSearch && matchesTrade && matchesStatus) {{
                    r.style.display = "";
                    visible++;
                }} else {{
                    r.style.display = "none";
                }}
            }});
            document.getElementById("visibleCount").innerText = visible;
        }}

        function previewPitch(lid) {{
            const container = document.getElementById(`pitch-data-${{lid}}`);
            if (!container) return;
            const subject = container.getAttribute("data-subject");
            const body = container.getAttribute("data-body").replaceAll("<br>", "\\n");
            document.getElementById("modalSubject").innerText = subject;
            document.getElementById("modalBody").innerText = body;
            document.getElementById("previewModal").classList.remove("hidden");
        }}

        function closeModal() {{
            document.getElementById("previewModal").classList.add("hidden");
        }}

        function launchFirstFiveDrafts() {{
            const visibleLinks = Array.from(document.querySelectorAll("#leadsTable tbody tr"))
                .filter(r => r.style.display !== "none")
                .slice(0, 5)
                .map(r => r.querySelector("a[href*='mail.google.com']"));

            if (visibleLinks.length === 0) {{
                alert("No leads currently visible to open.");
                return;
            }}

            if (confirm(`Open ${{visibleLinks.length}} Gmail draft tabs in your browser?`)) {{
                visibleLinks.forEach((a, i) => {{
                    setTimeout(() => {{
                        window.open(a.href, '_blank');
                    }}, i * 800);
                }});
            }}
        }}
    </script>
</body>
</html>"""

    with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[SUCCESS] Interactive Dashboard generated at: {DASHBOARD_HTML}")
    return DASHBOARD_HTML

if __name__ == "__main__":
    path = generate_dashboard()
    if len(sys.argv) > 1 and sys.argv[1] == "--open":
        print("[+] Opening dashboard in default browser...")
        webbrowser.open(str(path))
