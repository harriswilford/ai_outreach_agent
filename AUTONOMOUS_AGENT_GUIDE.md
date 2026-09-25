# 🏗️ Autonomous AI Lead Acquisition & Outreach Agent
**Dedicated to:** Quantity Takeoff & Cost Estimation Client Acquisition in the United States  
**Sender Profile:** Harris Wilford, Lead Preconstruction Consultant (`harriswilford1618@gmail.com`)  
**Verified Proofs:** Strictly mapped to real deliverables in `E:\Esimation Sample Project`

---

## 🚀 Overview & Capabilities

The **Autonomous AI Lead Agent** is an end-to-end client acquisition system built specifically for quantity takeoff and estimation businesses. It automates every step of finding, qualifying, pitching, and following up with USA construction decision-makers (Commercial General Contractors, MEP Subcontractors, Drywall, Concrete, Roofing, Painting, Flooring, and Custom Home Builders).

### Core Engine Modules:
1. **Live Contractor Prospector (`lead_hunter.py`)**:
   - Searches top US metropolitan markets (Dallas, Houston, Austin, Atlanta, Tampa, Phoenix, Denver, Charlotte, etc.) across 10 specialized construction trades.
   - Crawls contractor websites and `/contact` pages to extract verified emails (`bids@`, `estimating@`, `info@`, `contact@`, and executive emails) and direct phone numbers.
   - Pre-loaded with **2,176+ verified US contractor leads**.

2. **Trade Intelligence & CSI Division Matrix (`trade_intelligence.py`)**:
   - Addresses specific contractor bottlenecks:
     - **MEP HVAC (Div 23):** Ductwork poundage, diffuser counts, CFM schedules (`mechanical.pdf`).
     - **MEP Electrical (Div 26):** Lighting fixture counts, conduit feeder lengths, gear schedules (`mechanical.pdf`).
     - **MEP Plumbing (Div 22):** Sanitary, storm, water pipe LF & fixture counts (`mechanical.pdf`).
     - **Commercial GCs (Div 01-33):** Overflow multi-division takeoffs in 3-5 days (`NAVY FEDERAL COVINGTON.TAKEOFF.pdf`).
     - **Concrete & Masonry (Div 03/04):** Exact concrete CY, rebar tonnage with lap splices (`WEEPING WILLOW ESTATES.pdf`).
     - **Drywall & Framing (Div 05/09):** Metal stud LF, board counts, mud/tape (`SPAULDING DUPLEX.TAKEOFF.pdf`).
     - **Painting & Wallcovering (Div 09):** Net wall/ceiling SF minus deductions, trim LF (`Eve Estabaya Remodel Takeoff.pdf`).
     - **Residential Builders:** Lumber packages, foundation volumes, window/door schedules.

3. **High-Converting Copywriting Engine (`pitch_generator.py`)**:
   - Generates tailored **on-demand takeoff proposals**: contractor sends plans, we deliver the complete takeoff and material count within 24-48 hours.
   - 4-Touch Sequences:
     - *Touch 1 (Day 1):* Introduction & Value Proposition.
     - *Touch 2 (Day +2):* Turnaround Guarantee (24-48 hrs) & Deliverable Breakdown (color-coded PDF + CSI Excel).
     - *Touch 3 (Day +4):* Software Compatibility (PlanSwift, Bluebeam Revu, custom bidding sheets).
     - *Touch 4 (Day +7):* Polite Breakup & Contact Retention.

4. **Automated Gmail Sender (`agent_mailer.py` & `send_gmail.py`)**:
   - **Full SMTP Automation:** Direct programmatic delivery via `smtp.gmail.com:465` (SSL) with anti-spam jitter delay (random 2-5s intervals) and daily volume protection.
   - **1-Click Browser Launcher:** Generates pre-filled Gmail Compose tabs directly in your browser.
   - **State Tracking:** Automatically records sent IDs in `campaign_state.json` to prevent duplicates.

5. **Interactive HTML5 Command Center (`dashboard.html` & `command_center.py`)**:
   - Real-time KPI dashboard, instant lead search, trade filters, 1-click "Send in Gmail" buttons, and copy preview.

---

## ⚡ Quick Start Commands

Run all commands from either the root folder `F:\Antigravity CLI` or `F:\Antigravity CLI\outreach_engine`:

### 1. Launch 1-Command Interactive Outreach Terminal
Provides an all-in-one console interface for hands-on control:
```powershell
python terminal.py
```
*(Or run `.\send_gmail.bat` directly on Windows)*

### 2. Send Direct Email to Any Specific Client (1 Command)
Directly delivers an AI-personalized preconstruction takeoff pitch to any client inbox:
```powershell
# Auto-generates high-converting subject & body
python send_gmail.py --to "client@company.com" --company "Acme Commercial Builders" --name "David"

# With custom subject & message
python send_gmail.py --to "client@company.com" --subject "Takeoff inquiry" --body "Hi David, ..."
```

### 3. Send Directly to Commercial General Contractors (1 Command)
```powershell
# Send to next 10 Commercial GCs directly via Gmail SMTP
python send_gmail.py --gc 10

# Send to all unsent Commercial GCs
python send_gmail.py --gc --all

# Test safely in dry-run simulation mode
python send_gmail.py --gc 10 --dry-run
```

### 4. Upload Directly to Gmail 'Drafts' Folder
Uploads drafts directly to your Gmail account so you can inspect and hit send:
```powershell
python send_gmail.py --gc --upload 15
```

### 5. View Real-Time Pipeline Stats & Live Logs
```powershell
python send_gmail.py --gc --stats
```

### 6. Hunt Fresh Live Leads Across US Markets
Discover real contractors from the web dynamically:
```powershell
python run_lead_agent.py --hunt --trade "Commercial General Contractors" --city "Dallas" --state "TX" --batch 5
```

### 7. Open the Web Dashboard
```powershell
python send_gmail.py --dashboard
```
Or open `F:\Antigravity CLI\outreach_engine\dashboard.html` in your browser.

---

## 🔑 Configuring 100% Hands-Free Background Gmail Sending

To allow the AI agent to send emails autonomously in the background without needing your browser:

1. Go to your Google Account Security settings: **[https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**
2. Turn on **2-Step Verification** (if not already enabled).
3. Under **App Passwords**, generate a new 16-character password named `"Antigravity Outreach"`.
4. Open `F:\Antigravity CLI\outreach_engine\.env` and add:
```env
GMAIL_USER=harriswilford1618@gmail.com
GMAIL_APP_PASS=xxxx xxxx xxxx xxxx
```
*(Replace `xxxx xxxx xxxx xxxx` with your generated 16-character password)*

Once configured, running `python run_lead_agent.py --cycle` or `python send_gmail.py --smtp` will send emails autonomously with anti-spam jitter delay!

---

## 📂 File Structure

- [run_lead_agent.py](file:///F:/Antigravity%20CLI/run_lead_agent.py) - Root CLI entrypoint.
- [autonomous_agent.py](file:///F:/Antigravity%20CLI/outreach_engine/autonomous_agent.py) - Autonomous agent orchestrator & scheduler.
- [lead_hunter.py](file:///F:/Antigravity%20CLI/outreach_engine/lead_hunter.py) - Live web contractor discovery & scraping engine.
- [trade_intelligence.py](file:///F:/Antigravity%20CLI/outreach_engine/trade_intelligence.py) - CSI division pain points, hooks & portfolio proof mappings.
- [pitch_generator.py](file:///F:/Antigravity%20CLI/outreach_engine/pitch_generator.py) - Multi-touch AI cold email copywriting engine.
- [agent_mailer.py](file:///F:/Antigravity%20CLI/outreach_engine/agent_mailer.py) - Gmail SMTP auto-sender & state tracker.
- [send_gmail.py](file:///F:/Antigravity%20CLI/outreach_engine/send_gmail.py) - Direct Gmail outreach bridge.
- [command_center.py](file:///F:/Antigravity%20CLI/outreach_engine/command_center.py) - Web dashboard generator.
- [dashboard.html](file:///F:/Antigravity%20CLI/outreach_engine/dashboard.html) - Interactive visual Command Center.
- [campaign_state.json](file:///F:/Antigravity%20CLI/outreach_engine/campaign_state.json) - Persistent lead delivery tracking.
