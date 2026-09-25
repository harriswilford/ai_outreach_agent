"""
Autonomous Takeoff & Estimation AI Lead Agent - Main Application
Provides both:
1. Interactive CLI Terminal Menu (python app.py)
2. Interactive Web Application Server (python app.py --web) with live Gmail Draft Uploading,
   Live Lead Hunting, SMTP Auto-Dispatching, and Real-time Pipeline Analytics.
"""

import os
import sys
import json
import time
import base64
import webbrowser
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = Path(__file__).parent
ENV_FILE = DATA_DIR / ".env"
MASTER_DB_FILE = DATA_DIR / "leads_master_db.json"
STATE_FILE = DATA_DIR / "campaign_state.json"
CREDENTIALS_FILE = DATA_DIR / "credentials.json"
TOKEN_FILE = DATA_DIR / "token.json"

from trade_intelligence import TRADE_INTELLIGENCE, US_CONSTRUCTION_METROS, get_trade_intelligence
from lead_hunter import LeadHunter
from pitch_generator import prepare_campaign_touch, SENDER_PROFILE
from agent_mailer import GmailAutomator, load_campaign_state, save_campaign_state, load_env_credentials
from gmail_draft_uploader import GmailDraftUploader

# ---------------------------------------------------------
# FastAPI Web Application Setup
# ---------------------------------------------------------
try:
    from fastapi import FastAPI, HTTPException, Query, Body
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

if FASTAPI_AVAILABLE:
    api_app = FastAPI(title="Autonomous Takeoff Lead Agent API", version="2.0.0")
    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    hunter_instance = LeadHunter()
    uploader_instance = GmailDraftUploader()
    automator_instance = GmailAutomator()

    @api_app.get("/api/stats")
    def get_stats():
        stats = hunter_instance.get_stats()
        state = load_campaign_state()
        sent_count = len(state.get("sent_ids", []))
        drafted_count = len(state.get("drafted_ids", []))
        return {
            "total_leads": stats["total_leads"],
            "sent_count": sent_count,
            "drafted_count": drafted_count,
            "sample_requests": len(state.get("sample_requested_ids", [])),
            "closed_count": len(state.get("closed_ids", [])),
            "trade_breakdown": stats["trade_breakdown"],
            "status_breakdown": stats["status_breakdown"],
            "sender": SENDER_PROFILE
        }

    @api_app.get("/api/leads")
    def get_leads(
        search: Optional[str] = None,
        trade: Optional[str] = None,
        state_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 150
    ):
        state = load_campaign_state()
        sent_ids = set(state.get("sent_ids", []))
        drafted_ids = set(state.get("drafted_ids", []))

        leads = hunter_instance.master_leads
        results = []

        for l in leads:
            lid = l.get("id")
            comp = l.get("company", "")
            tr = l.get("trade_niche", "")
            st = l.get("state", "")
            em = l.get("email", "")

            if search:
                s_lower = search.lower()
                if s_lower not in comp.lower() and s_lower not in tr.lower() and s_lower not in em.lower() and s_lower not in l.get("city", "").lower():
                    continue

            if trade and trade.lower() not in tr.lower():
                continue

            if state_filter and state_filter.upper() != st.upper():
                continue

            is_sent = lid in sent_ids
            is_drafted = lid in drafted_ids

            curr_status = "SENT" if is_sent else ("DRAFTED" if is_drafted else "READY")
            if status_filter and status_filter != curr_status:
                continue

            lead_copy = dict(l)
            lead_copy["is_sent"] = is_sent
            lead_copy["is_drafted"] = is_drafted
            lead_copy["display_status"] = curr_status
            
            # Generate pitch data
            pitch = prepare_campaign_touch(l, touch_number=1)
            lead_copy["subject"] = pitch["subject"]
            lead_copy["body"] = pitch["body"]
            lead_copy["gmail_compose_url"] = pitch["gmail_compose_url"]

            results.append(lead_copy)
            if len(results) >= limit:
                break

        return {"total_matching": len(results), "leads": results}

    @api_app.post("/api/hunt")
    def hunt_leads(payload: Dict[str, Any] = Body(...)):
        trade = payload.get("trade", "Commercial General Contractors")
        city = payload.get("city", "Dallas")
        state = payload.get("state", "TX")
        count = int(payload.get("count", 3))

        discovered = hunter_instance.search_contractors_live(trade, city, state, max_results=count)
        return {
            "success": True,
            "discovered_count": len(discovered),
            "discovered": discovered
        }

    @api_app.post("/api/upload-drafts")
    def upload_drafts_endpoint(payload: Dict[str, Any] = Body(...)):
        count = int(payload.get("count", 5))
        touch = int(payload.get("touch", 1))
        trade_filter = payload.get("trade")
        method = payload.get("method", "auto")

        state = load_campaign_state()
        sent_ids = set(state.get("sent_ids", []))
        unsent = [l for l in hunter_instance.master_leads if l.get("id") not in sent_ids and l.get("email")]

        if trade_filter:
            unsent = [l for l in unsent if trade_filter.lower() in l.get("trade_niche", "").lower()]

        if not unsent:
            return {"success": False, "message": "No unsent leads available."}

        target_batch = unsent[:count]

        if method == "imap":
            res = uploader_instance.upload_via_imap(target_batch, touch_number=touch, limit=count)
        elif method == "api":
            res = uploader_instance.upload_via_api(target_batch, touch_number=touch, limit=count)
        else:
            res = uploader_instance.upload_drafts(target_batch, touch_number=touch, limit=count)

        return {
            "success": res.get("uploaded", 0) > 0,
            "uploaded": res.get("uploaded", 0),
            "mode": res.get("mode", "NONE"),
            "error": res.get("error")
        }

    @api_app.post("/api/send-batch")
    def send_batch_endpoint(payload: Dict[str, Any] = Body(...)):
        count = int(payload.get("count", 5))
        touch = int(payload.get("touch", 1))
        trade_filter = payload.get("trade")
        dry_run = bool(payload.get("dry_run", False))

        state = load_campaign_state()
        sent_ids = set(state.get("sent_ids", []))
        unsent = [l for l in hunter_instance.master_leads if l.get("id") not in sent_ids and l.get("email")]

        if trade_filter:
            unsent = [l for l in unsent if trade_filter.lower() in l.get("trade_niche", "").lower()]

        if not unsent:
            return {"success": False, "message": "No unsent leads available."}

        target_batch = unsent[:count]
        res = automator_instance.dispatch_batch_smtp(target_batch, touch_number=touch, max_sends=count, dry_run=dry_run)

        # Update status in db
        for d in res.get("details", []):
            if d.get("status") in ["SENT", "SIMULATED"]:
                hunter_instance.update_lead_status(d["id"], "SENT", f"Touch {touch} via Web App")

        return {
            "success": res.get("sent", 0) > 0,
            "sent": res.get("sent", 0),
            "failed": res.get("failed", 0),
            "details": res.get("details", [])
        }

    @api_app.post("/api/send-single")
    def send_single_endpoint(payload: Dict[str, Any] = Body(...)):
        lead_id = payload.get("lead_id")
        touch = int(payload.get("touch", 1))
        lead = next((l for l in hunter_instance.master_leads if l.get("id") == lead_id), None)
        if not lead:
            return {"success": False, "error": "Lead not found in master database."}

        pitch = prepare_campaign_touch(lead, touch_number=touch)
        if not automator_instance.connect_smtp():
            return {"success": False, "error": "Gmail SMTP connection failed. Check GMAIL_USER and GMAIL_APP_PASS in Settings."}

        try:
            automator_instance.send_single_email(
                pitch["recipient"],
                pitch["subject"],
                pitch["body"],
                lead_id=lead["id"],
                lead_company=lead["company"]
            )
            hunter_instance.update_lead_status(lead["id"], "SENT", f"Touch {touch} sent directly to inbox via Web App")
            return {
                "success": True,
                "message": f"Email delivered directly to {lead['company']} ({pitch['recipient']}) inbox!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            automator_instance.close_smtp()

    @api_app.get("/api/config")
    def get_config():
        creds = load_env_credentials()
        return {
            "gmail_user": creds.get("user", ""),
            "has_app_pass": bool(creds.get("pass")),
            "has_oauth_credentials": CREDENTIALS_FILE.exists(),
            "has_oauth_token": TOKEN_FILE.exists()
        }

    @api_app.post("/api/config")
    def update_config(payload: Dict[str, Any] = Body(...)):
        gmail_user = payload.get("gmail_user", "").strip()
        app_pass = payload.get("app_pass", "").strip()

        lines = []
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = [l for l in f if not l.startswith("GMAIL_USER") and not l.startswith("GMAIL_APP_PASS")]

        if gmail_user:
            lines.append(f"GMAIL_USER={gmail_user}\n")
        if app_pass:
            lines.append(f"GMAIL_APP_PASS={app_pass}\n")

        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # Reload creds
        automator_instance.creds = load_env_credentials()
        uploader_instance.creds = load_env_credentials()

        return {"success": True, "message": "Settings updated successfully."}

    @api_app.get("/", response_class=HTMLResponse)
    def render_app_ui():
        """Serve full interactive Single-Page Application UI."""
        return get_app_ui_html()


def get_app_ui_html() -> str:
    """Return modern HTML5/Tailwind/Vue-style client application."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Takeoff Lead Agent | Control Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
        body { font-family: 'Inter', sans-serif; }
        code, pre { font-family: 'JetBrains+Mono', monospace; }
        .tab-active { border-bottom: 2px solid #3b82f6; color: #60a5fa; font-weight: 600; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">
    <!-- Navbar -->
    <header class="bg-slate-900 border-b border-slate-800 sticky top-0 z-40 shadow-xl">
        <div class="max-w-7xl mx-auto px-6 py-3.5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">🏗️</span>
                <div>
                    <h1 class="text-lg font-black tracking-tight text-white flex items-center gap-2">
                        AUTONOMOUS TAKEOFF LEAD AGENT
                        <span class="text-[10px] uppercase tracking-wider bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">v2.0 Active</span>
                    </h1>
                    <p class="text-xs text-slate-400">USA Construction Client Acquisition Engine &bull; Harris Wilford (<span id="navEmail">harriswilford1618@gmail.com</span>)</p>
                </div>
            </div>
            
            <div class="flex items-center gap-2.5">
                <button onclick="openSendBatchModal()" class="px-3.5 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-lg shadow-md transition flex items-center gap-1.5">
                    <span>🚀 Send Directly to Inboxes</span>
                </button>
                <button onclick="openHuntModal()" class="px-3.5 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-lg shadow-md transition flex items-center gap-1.5">
                    <span>🔍 Hunt Live Leads</span>
                </button>
                <button onclick="openConfigModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition">
                    ⚙️ Settings
                </button>
            </div>
        </div>
    </header>

    <!-- Main Body -->
    <main class="max-w-7xl mx-auto px-6 py-6 flex-1 space-y-6 w-full">
        <!-- Toast Notification Container -->
        <div id="toast" class="hidden fixed bottom-6 right-6 z-50 bg-slate-900 border border-slate-700 shadow-2xl rounded-xl p-4 max-w-sm text-xs transition-all duration-300">
            <div class="flex items-center gap-3">
                <span id="toastIcon" class="text-lg">✅</span>
                <div id="toastMessage" class="text-slate-200 font-medium">Operation completed!</div>
            </div>
        </div>

        <!-- Metric Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Master Staged Leads</div>
                <div class="text-2xl font-black text-white mt-1" id="kpiTotal">...</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Verified US Contractors</div>
            </div>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-blue-400">Drafted to Gmail</div>
                <div class="text-2xl font-black text-blue-400 mt-1" id="kpiDrafted">...</div>
                <div class="text-[11px] text-slate-500 mt-0.5">In Gmail Drafts Folder</div>
            </div>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">Outreach Dispatched</div>
                <div class="text-2xl font-black text-emerald-400 mt-1" id="kpiSent">...</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Sent to Inboxes</div>
            </div>
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-amber-400">Takeoff Plan Requests</div>
                <div class="text-2xl font-black text-amber-400 mt-1" id="kpiSamples">0</div>
                <div class="text-[11px] text-slate-500 mt-0.5">Contractor Plan Sets Received</div>
            </div>
        </div>

        <!-- Action Quick-Bar -->
        <div class="bg-gradient-to-r from-blue-950/40 via-slate-900 to-slate-900 border border-blue-900/40 rounded-xl p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div class="space-y-1">
                <div class="text-sm font-bold text-white flex items-center gap-2">
                    <span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-xs">OFFER</span>
                    <span>On-Demand Takeoff Sequence</span>
                </div>
                <p class="text-xs text-slate-400">All emails pitch on-demand takeoff & estimating support (24-48 hr turnaround, PlanSwift/Bluebeam markups + Excel BOQs) mapped to portfolio proofs (mechanical.pdf, SPAULDING DUPLEX.pdf, NAVY FEDERAL.pdf).</p>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="triggerQuickSend(5)" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow transition flex items-center gap-1">
                    <span>Send Next 5 to Inboxes 🚀</span>
                </button>
                <button onclick="triggerQuickSend(10)" class="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg shadow transition flex items-center gap-1">
                    <span>Send Next 10 to Inboxes 🚀</span>
                </button>
            </div>
        </div>

        <!-- Filter & Search Bar -->
        <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 flex flex-wrap gap-3 justify-between items-center">
            <div class="flex flex-wrap gap-2.5 items-center flex-1">
                <input type="text" id="searchInput" oninput="debounceFetch()" placeholder="Search company, city, email..." class="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-56">
                
                <select id="tradeSelect" onchange="fetchLeads()" class="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500">
                    <option value="">All Trades</option>
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
                </select>

                <select id="statusSelect" onchange="fetchLeads()" class="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500">
                    <option value="">All Statuses</option>
                    <option value="READY">Ready to Pitch (Unsent)</option>
                    <option value="DRAFTED">Drafted in Gmail</option>
                    <option value="SENT">Dispatched (Sent)</option>
                </select>
            </div>

            <div class="text-xs text-slate-400">
                Displaying <span id="leadsCount" class="font-bold text-white">0</span> prospects
            </div>
        </div>

        <!-- Leads Table -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                            <th class="p-3">Company & Market</th>
                            <th class="p-3">Trade / Niche</th>
                            <th class="p-3">Contact & Email</th>
                            <th class="p-3">Status</th>
                            <th class="p-3">Pitch Preview</th>
                            <th class="p-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="leadsBody" class="divide-y divide-slate-800/60">
                        <tr><td colspan="6" class="p-8 text-center text-slate-500">Loading prospects...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Modal: Upload Drafts to Gmail -->
    <div id="uploadModal" class="hidden fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 text-slate-100 shadow-2xl space-y-4">
            <div class="flex justify-between items-center pb-3 border-b border-slate-800">
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                    <span>📥</span> Upload Drafts Directly to Gmail
                </h3>
                <button onclick="closeModals()" class="text-slate-400 hover:text-white font-bold text-xl">&times;</button>
            </div>
            
            <p class="text-xs text-slate-400">This injects pre-written outreach emails directly into your real Gmail account's <strong>Drafts</strong> folder (mail.google.com/#drafts).</p>

            <div class="space-y-3">
                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Batch Size</label>
                    <input type="number" id="draftCount" value="10" min="1" max="50" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                </div>

                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Upload Protocol</label>
                    <select id="draftMethod" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                        <option value="auto">Auto-Select (Best Available)</option>
                        <option value="imap">Direct IMAP Append (Requires App Password)</option>
                        <option value="api">Official Gmail API (Requires OAuth credentials.json)</option>
                    </select>
                </div>
            </div>

            <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button onclick="closeModals()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition">Cancel</button>
                <button onclick="executeUploadDrafts()" id="uploadBtn" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg shadow-md transition">Start Uploading</button>
            </div>
        </div>
    </div>

    <!-- Modal: Send Directly to Client Inboxes -->
    <div id="sendBatchModal" class="hidden fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 text-slate-100 shadow-2xl space-y-4">
            <div class="flex justify-between items-center pb-3 border-b border-slate-800">
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                    <span>🚀</span> Send Directly to Client Inboxes
                </h3>
                <button onclick="closeModals()" class="text-slate-400 hover:text-white font-bold text-xl">&times;</button>
            </div>
            
            <p class="text-xs text-slate-400">Dispatches customized cold outreach emails directly to client inboxes using Gmail SMTP SSL with human-like anti-spam jitter delay.</p>

            <div class="space-y-3">
                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Batch Size</label>
                    <input type="number" id="sendBatchCount" value="10" min="1" max="45" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500">
                </div>

                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Target Trade Niche (Optional)</label>
                    <select id="sendBatchTrade" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500">
                        <option value="">All Qualified Unsent Leads</option>
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
                    </select>
                </div>
            </div>

            <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button onclick="closeModals()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition">Cancel</button>
                <button onclick="executeSendBatch()" id="sendBatchBtn" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-md transition">Dispatch Directly to Inboxes 🚀</button>
            </div>
        </div>
    </div>

    <!-- Modal: Hunt Live Leads -->
    <div id="huntModal" class="hidden fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 text-slate-100 shadow-2xl space-y-4">
            <div class="flex justify-between items-center pb-3 border-b border-slate-800">
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                    <span>🔍</span> Hunt Fresh Contractor Leads Live
                </h3>
                <button onclick="closeModals()" class="text-slate-400 hover:text-white font-bold text-xl">&times;</button>
            </div>
            
            <p class="text-xs text-slate-400">Scrapes search engines and contractor directories live to extract verified emails, phones, and decision makers.</p>

            <div class="space-y-3">
                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Trade Specialization</label>
                    <select id="huntTrade" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
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
                    </select>
                </div>

                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs text-slate-300 font-semibold mb-1">Target City</label>
                        <input type="text" id="huntCity" value="Dallas" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs text-slate-300 font-semibold mb-1">State</label>
                        <input type="text" id="huntState" value="TX" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                    </div>
                </div>

                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Target Quantity</label>
                    <input type="number" id="huntCount" value="3" min="1" max="10" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                </div>
            </div>

            <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button onclick="closeModals()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition">Cancel</button>
                <button onclick="executeHunt()" id="huntBtn" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-md transition">Start Hunting</button>
            </div>
        </div>
    </div>

    <!-- Modal: Settings & Config -->
    <div id="configModal" class="hidden fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 text-slate-100 shadow-2xl space-y-4">
            <div class="flex justify-between items-center pb-3 border-b border-slate-800">
                <h3 class="text-base font-bold text-white flex items-center gap-2">
                    <span>⚙️</span> Outreach & Gmail Settings
                </h3>
                <button onclick="closeModals()" class="text-slate-400 hover:text-white font-bold text-xl">&times;</button>
            </div>

            <div class="space-y-3">
                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Gmail / Sender Email</label>
                    <input type="email" id="cfgEmail" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                </div>

                <div>
                    <label class="block text-xs text-slate-300 font-semibold mb-1">Google App Password (16-characters)</label>
                    <input type="password" id="cfgPass" placeholder="Enter 16-char password if available" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
                    <p class="text-[11px] text-slate-500 mt-1">Generate at: <a href="https://myaccount.google.com/apppasswords" target="_blank" class="text-blue-400 hover:underline">myaccount.google.com/apppasswords</a></p>
                </div>
            </div>

            <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button onclick="closeModals()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition">Cancel</button>
                <button onclick="saveConfig()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg shadow-md transition">Save Changes</button>
            </div>
        </div>
    </div>

    <!-- Modal: Preview Pitch -->
    <div id="previewModal" class="hidden fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 text-slate-100 shadow-2xl space-y-4">
            <div class="flex justify-between items-center pb-3 border-b border-slate-800">
                <h3 class="text-base font-bold text-white" id="modalSubject">Subject</h3>
                <button onclick="closeModals()" class="text-slate-400 hover:text-white font-bold text-xl">&times;</button>
            </div>

            <div class="bg-slate-950 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto" id="modalBody">
            </div>

            <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button onclick="closeModals()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition">Close</button>
            </div>
        </div>
    </div>

    <!-- Client Logic -->
    <script>
        let currentLeads = [];
        let debounceTimer;

        async function init() {
            await fetchStats();
            await fetchConfig();
            await fetchLeads();
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('kpiTotal').innerText = data.total_leads.toLocaleString();
                document.getElementById('kpiDrafted').innerText = (data.drafted_count || 0).toLocaleString();
                document.getElementById('kpiSent').innerText = data.sent_count.toLocaleString();
                document.getElementById('kpiSamples').innerText = data.sample_requests || 0;
            } catch (e) {
                console.error(e);
            }
        }

        async function fetchConfig() {
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                if (data.gmail_user) {
                    document.getElementById('navEmail').innerText = data.gmail_user;
                    document.getElementById('cfgEmail').value = data.gmail_user;
                }
            } catch (e) {
                console.error(e);
            }
        }

        function debounceFetch() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(fetchLeads, 300);
        }

        async function fetchLeads() {
            const search = document.getElementById('searchInput').value;
            const trade = document.getElementById('tradeSelect').value;
            const status = document.getElementById('statusSelect').value;

            const url = new URL('/api/leads', window.location.origin);
            if (search) url.searchParams.append('search', search);
            if (trade) url.searchParams.append('trade', trade);
            if (status) url.searchParams.append('status_filter', status);

            try {
                const res = await fetch(url);
                const data = await res.json();
                currentLeads = data.leads;
                document.getElementById('leadsCount').innerText = data.total_matching;
                renderLeadsTable(data.leads);
            } catch (e) {
                console.error(e);
            }
        }

        function renderLeadsTable(leads) {
            const tbody = document.getElementById('leadsBody');
            if (!leads || leads.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-slate-500">No matching contractor accounts found.</td></tr>';
                return;
            }

            let html = '';
            leads.forEach(l => {
                let badge = '<span class="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">Ready</span>';
                if (l.is_sent) {
                    badge = '<span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Sent</span>';
                } else if (l.is_drafted) {
                    badge = '<span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Drafted</span>';
                }

                html += `
                <tr class="hover:bg-slate-900/50 transition">
                    <td class="p-3">
                        <div class="font-bold text-white">${l.company}</div>
                        <div class="text-[11px] text-slate-400">${l.city}, ${l.state} &bull; <a href="${l.website || '#'}" target="_blank" class="text-blue-400 hover:underline">${(l.website || '').replace('https://','').replace('http://','').slice(0,25)}</a></div>
                    </td>
                    <td class="p-3">
                        <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">${l.trade_niche}</span>
                        <div class="text-[10px] text-slate-500 mt-1">Proof: ${(l.sample_file || '').slice(0, 20)}</div>
                    </td>
                    <td class="p-3">
                        <div class="font-medium text-slate-300">${l.contact_name}</div>
                        <div class="font-mono text-slate-400 text-[11px]">${l.email}</div>
                    </td>
                    <td class="p-3">${badge}</td>
                    <td class="p-3">
                        <button onclick="previewLeadPitch(${l.id})" class="text-indigo-400 hover:text-indigo-300 font-semibold underline">Preview</button>
                    </td>
                    <td class="p-3 text-right">
                        <button onclick="sendSingleToInbox(${l.id})" class="inline-flex items-center px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-bold shadow-sm transition">
                            Send to Inbox 🚀
                        </button>
                    </td>
                </tr>
                `;
            });
            tbody.innerHTML = html;
        }

        function previewLeadPitch(lid) {
            const lead = currentLeads.find(l => l.id === lid);
            if (!lead) return;
            document.getElementById('modalSubject').innerText = lead.subject;
            document.getElementById('modalBody').innerText = lead.body;
            document.getElementById('previewModal').classList.remove('hidden');
        }

        function closeModals() {
            document.getElementById('sendBatchModal').classList.add('hidden');
            document.getElementById('uploadModal').classList.add('hidden');
            document.getElementById('huntModal').classList.add('hidden');
            document.getElementById('configModal').classList.add('hidden');
            document.getElementById('previewModal').classList.add('hidden');
        }

        function openSendBatchModal() { document.getElementById('sendBatchModal').classList.remove('hidden'); }
        function openUploadModal() { document.getElementById('uploadModal').classList.remove('hidden'); }
        function openHuntModal() { document.getElementById('huntModal').classList.remove('hidden'); }
        function openConfigModal() { document.getElementById('configModal').classList.remove('hidden'); }

        async function executeSendBatch() {
            const count = document.getElementById('sendBatchCount').value;
            const trade = document.getElementById('sendBatchTrade').value;
            const btn = document.getElementById('sendBatchBtn');
            btn.disabled = true;
            btn.innerText = "Dispatching directly to inboxes...";

            try {
                const res = await fetch('/api/send-batch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ count, trade, dry_run: false })
                });
                const data = await res.json();
                closeModals();
                if (data.success) {
                    showToast(`🚀 Dispatched ${data.sent} emails directly to client inboxes!`);
                } else {
                    showToast(`⚠️ ${data.error || data.message || 'Check SMTP credentials in Settings'}`);
                }
                await fetchStats();
                await fetchLeads();
            } catch (e) {
                showToast(`❌ Error: ${e.message}`);
            } finally {
                btn.disabled = false;
                btn.innerText = "Dispatch Directly to Inboxes 🚀";
            }
        }

        async function sendSingleToInbox(lid) {
            const lead = currentLeads.find(l => l.id === lid);
            const comp = lead ? lead.company : "client";
            showToast(`⏳ Delivering email directly to ${comp}...`);
            try {
                const res = await fetch('/api/send-single', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ lead_id: lid, touch: 1 })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`🚀 Delivered directly to ${comp} inbox!`);
                } else {
                    showToast(`⚠️ ${data.error || 'Failed to send'}`);
                }
                await fetchStats();
                await fetchLeads();
            } catch (e) {
                showToast(`❌ Error: ${e.message}`);
            }
        }

        async function executeUploadDrafts() {
            const count = document.getElementById('draftCount').value;
            const method = document.getElementById('draftMethod').value;
            const btn = document.getElementById('uploadBtn');
            btn.disabled = true;
            btn.innerText = "Uploading to Gmail...";

            try {
                const res = await fetch('/api/upload-drafts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ count, method })
                });
                const data = await res.json();
                closeModals();
                if (data.success) {
                    showToast(`✅ Successfully uploaded ${data.uploaded} drafts to your Gmail Drafts folder!`);
                } else {
                    showToast(`⚠️ ${data.error || data.message || 'Check authentication in Settings'}`);
                }
                await fetchStats();
                await fetchLeads();
            } catch (e) {
                showToast(`❌ Error: ${e.message}`);
            } finally {
                btn.disabled = false;
                btn.innerText = "Start Uploading";
            }
        }

        async function executeHunt() {
            const trade = document.getElementById('huntTrade').value;
            const city = document.getElementById('huntCity').value;
            const state = document.getElementById('huntState').value;
            const count = document.getElementById('huntCount').value;
            const btn = document.getElementById('huntBtn');
            btn.disabled = true;
            btn.innerText = "Hunting live...";

            try {
                const res = await fetch('/api/hunt', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ trade, city, state, count })
                });
                const data = await res.json();
                closeModals();
                showToast(`🎯 Discovered ${data.discovered_count} fresh verified contractor leads!`);
                await fetchStats();
                await fetchLeads();
            } catch (e) {
                showToast(`❌ Error: ${e.message}`);
            } finally {
                btn.disabled = false;
                btn.innerText = "Start Hunting";
            }
        }

        async function triggerQuickDraft(count) {
            showToast(`⏳ Uploading ${count} drafts to Gmail...`);
            try {
                const res = await fetch('/api/upload-drafts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ count })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`✅ Uploaded ${data.uploaded} drafts directly to Gmail Drafts!`);
                } else {
                    showToast(`⚠️ ${data.error || 'Authentication required'}`);
                }
                await fetchStats();
                await fetchLeads();
            } catch (e) {
                showToast(`❌ Error: ${e.message}`);
            }
        }

        async function triggerQuickSend(count) {
            showToast(`⏳ Sending ${count} emails via SMTP...`);
            try {
                const res = await fetch('/api/send-batch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ count })
                });
                const data = await res.json();
                showToast(`🚀 Dispatched ${data.sent} emails!`);
                await fetchStats();
                await fetchLeads();
            } catch (e) {
                showToast(`❌ Error: ${e.message}`);
            }
        }

        async function saveConfig() {
            const gmail_user = document.getElementById('cfgEmail').value;
            const app_pass = document.getElementById('cfgPass').value;

            try {
                await fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ gmail_user, app_pass })
                });
                closeModals();
                showToast("✅ Settings updated successfully!");
                await fetchConfig();
            } catch (e) {
                showToast(`❌ Error: ${e.message}`);
            }
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            document.getElementById('toastMessage').innerText = msg;
            toast.classList.remove('hidden');
            setTimeout(() => { toast.classList.add('hidden'); }, 5000);
        }

        window.onload = init;
    </script>
</body>
</html>"""


# ---------------------------------------------------------
# Interactive CLI Menu & Runner
# ---------------------------------------------------------
def run_cli_menu():
    """Interactive console menu for hands-on control."""
    hunter = LeadHunter()
    uploader = GmailDraftUploader()
    automator = GmailAutomator()

    while True:
        stats = hunter.get_stats()
        state = load_campaign_state()
        sent_count = len(state.get("sent_ids", []))
        drafted_count = len(state.get("drafted_ids", []))
        total = stats["total_leads"]

        print("\n" + "=" * 78)
        print("  [+] AUTONOMOUS TAKEOFF LEAD AGENT - CONSOLE CONTROL PANEL")
        print(f"  Sender: {SENDER_PROFILE['name']} <{automator.creds.get('user')}>")
        print("=" * 78)
        print(f"  Total Staged Leads : {total:,}  |  Drafted in Gmail : {drafted_count:,}  |  Sent : {sent_count:,}")
        print("-" * 78)
        print("  [1] 🚀 Send Outreach Emails Directly to Client Inboxes (SMTP)")
        print("  [2] 🎯 Hunt & Send Directly to Client Inboxes (Autonomous 1-Click)")
        print("  [3] 🔍 Hunt Fresh USA Leads (Live Web Scraping by Trade & City)")
        print("  [4] 🖥️ Launch Web App / Dashboard Server (http://localhost:8000)")
        print("  [5] 📊 Display Real-Time Pipeline Analytics")
        print("  [6] 📁 Export Master Leads to CSV")
        print("  [7] 📥 Upload Drafts to Gmail (Drafts Mode)")
        print("  [0] Exit")
        print("=" * 78)

        choice = input("\nEnter choice [0-7]: ").strip()

        if choice == "1":
            count = input("Number of emails to send directly to inboxes (default 5): ").strip()
            count = int(count) if count.isdigit() else 5
            dry = input("Dry run simulation? (y/n, default n): ").strip().lower() == "y"
            unsent = [l for l in hunter.master_leads if l.get("id") not in state.get("sent_ids", []) and l.get("email")]
            automator.dispatch_batch_smtp(unsent, touch_number=1, max_sends=count, dry_run=dry)

        elif choice == "2":
            print("\nAvailable Trades:")
            trades = list(TRADE_INTELLIGENCE.keys())
            for idx, t in enumerate(trades, 1):
                print(f"  {idx}. {t}")
            t_idx = input(f"Select trade [1-{len(trades)}] (default 1): ").strip()
            selected_trade = trades[int(t_idx) - 1] if t_idx.isdigit() and 1 <= int(t_idx) <= len(trades) else trades[0]
            city = input("Target city (default Dallas): ").strip() or "Dallas"
            st = input("Target state code (default TX): ").strip() or "TX"
            cnt = input("Quantity to hunt and send (default 5): ").strip()
            cnt = int(cnt) if cnt.isdigit() else 5
            dry = input("Dry run simulation? (y/n, default n): ").strip().lower() == "y"
            
            print(f"\n[*] Sourcing fresh leads for [{selected_trade}] in {city}, {st}...")
            fresh = hunter.search_contractors_live(selected_trade, city, st, max_results=cnt)
            if fresh:
                print(f"[+] Delivering emails directly to {len(fresh)} contractor inboxes...")
                automator.dispatch_batch_smtp(fresh, touch_number=1, max_sends=cnt, dry_run=dry)

        elif choice == "3":
            print("\nAvailable Trades:")
            trades = list(TRADE_INTELLIGENCE.keys())
            for idx, t in enumerate(trades, 1):
                print(f"  {idx}. {t}")
            t_idx = input(f"Select trade [1-{len(trades)}] (default 1): ").strip()
            selected_trade = trades[int(t_idx) - 1] if t_idx.isdigit() and 1 <= int(t_idx) <= len(trades) else trades[0]
            city = input("Target city (default Dallas): ").strip() or "Dallas"
            st = input("Target state code (default TX): ").strip() or "TX"
            cnt = input("Quantity to find (default 3): ").strip()
            cnt = int(cnt) if cnt.isdigit() else 3
            hunter.search_contractors_live(selected_trade, city, st, max_results=cnt)

        elif choice == "4":
            start_web_server()
            break

        elif choice == "5":
            print("\nPipeline Status Breakdown:")
            for k, v in stats["status_breakdown"].items():
                print(f"  - {k:<25}: {v:,}")
            print("\nTrade Specialization Coverage:")
            for t, c in sorted(stats["trade_breakdown"].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {t:<35}: {c:,}")

        elif choice == "6":
            import csv
            out_file = DATA_DIR / "leads_export.csv"
            keys = ["id", "company", "trade_niche", "city", "state", "email", "phone", "website", "status"]
            with open(out_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(hunter.master_leads)
            print(f"[+] Exported {len(hunter.master_leads)} leads to {out_file}")

        elif choice == "7":
            count = input("How many drafts to upload to Gmail? (default 5): ").strip()
            count = int(count) if count.isdigit() else 5
            unsent = [l for l in hunter.master_leads if l.get("id") not in state.get("sent_ids", []) and l.get("email")]
            uploader.upload_drafts(unsent, touch_number=1, limit=count)

        elif choice in ["0", "exit", "q"]:
            print("\nGoodbye!")
            break
        else:
            print("[!] Invalid option. Please select 0 to 8.")


def start_web_server(port: int = 8000):
    """Launch FastAPI web server and open browser."""
    if not FASTAPI_AVAILABLE:
        print("[!] FastAPI or Uvicorn not available. Please run in CLI mode.")
        return

    url = f"http://127.0.0.1:{port}"
    print(f"\n[+] Starting Autonomous Lead Agent Web Server on {url}...")
    print(f"[+] Launching your web browser...")
    webbrowser.open(url)
    uvicorn.run(api_app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    if "--web" in sys.argv or "--serve" in sys.argv or "--server" in sys.argv:
        port = 8000
        for i, a in enumerate(sys.argv):
            if a == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        start_web_server(port=port)
    elif "--upload-drafts" in sys.argv or "--upload" in sys.argv:
        uploader = GmailDraftUploader()
        hunter = LeadHunter()
        cnt = 10
        for i, a in enumerate(sys.argv):
            if a in ["--upload-drafts", "--upload"] and i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
                cnt = int(sys.argv[i + 1])
        unsent = [l for l in hunter.master_leads if l.get("id") not in uploader.state.get("sent_ids", [])]
        uploader.upload_drafts(unsent, limit=cnt)
    else:
        run_cli_menu()
