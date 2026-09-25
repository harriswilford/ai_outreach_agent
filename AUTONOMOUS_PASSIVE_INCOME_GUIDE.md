# 🤖 Autonomous AI Agent: Background PC Passive Income Machine
**Dedicated to:** US Preconstruction Quantity Takeoff & Cost Estimation Client Acquisition  
**Sender Profile:** Harris Wilford, Lead Preconstruction Consultant (`harriswilford1618@gmail.com`)  
**Operating Mode:** Silent Windows Background Daemon + Real-time Phone & Desktop Alerts  

---

## 💰 The Passive Income Architecture & Math

In the United States construction industry, general contractors and subcontractors bid on hundreds of millions of dollars in projects every month. Their #1 bottleneck is **estimating bandwidth**: they do not have the time or staff to measure every linear foot of pipe, cubic yard of concrete, or square foot of drywall before the bid deadline.

### The Financial Calculus:
| Metric | Conservative | Scale Target (300/day) | High Retainer Scale |
| :--- | :--- | :--- | :--- |
| **Average Project Fee** | $650 / job | $650 / job | $750 / job |
| **Weekly Closed Deals** | 2 projects / week | 8–12 projects / week | 15+ projects / week |
| **Daily Automated Sends** | 50 emails / day | **300 emails / day** | 300 emails / day |
| **Weekly Outreach** | 250 emails / week | **1,500 emails / week** | 1,500 emails / week |
| **Contractor Reply Rate** | 4% - 6% | ~60 - 90 warm replies / mo | ~90+ replies / mo |
| **Est. Monthly Pipeline** | $5,000 / mo | **$25,000 - $31,000 / mo** | $35,000+ / mo |

Once you complete 1 accurate takeoff for a contractor, they treat you as their default estimating partner and send plans for **every new bid package** on repeat without any additional outreach required.

---

## ⚙️ The 4 Core Autonomous Engines

```
 +-----------------------------------------------------------------------------------+
 |                             AUTONOMOUS AI AGENT ENGINE                            |
 +-----------------------------------------------------------------------------------+
                                          |
          +-------------------------------+-------------------------------+
          |                               |                               |
          v                               v                               v
 +-------------------+           +-------------------+           +-------------------+
 | AUTONOMOUS        |           | BACKGROUND DAEMON |           | INBOX SENTINEL    |
 | PLANNER           |           | RUNNER            |           | (24/7 IMAP)       |
 | (Strategy & Math) |           | (Silent Windows)  |           | (Reply Classifier)|
 +-------------------+           +-------------------+           +-------------------+
          |                               |                               |
          | Plans Multi-Touch Funnel      | Dispatches via SMTP           | Scans unread emails
          | US Business Hours (8:30-4:30) | Anti-Spam Jitter (60-180s)    | Detects PDF/Drawings
          | Balances Follow-ups vs New    | Auto-recovers on drops        | Identifies Hot Leads
          +-------------------------------+-------------------------------+
                                          |
                                          v
                                 +-------------------+
                                 | ALERT SYSTEM      |
                                 | (Multi-Channel)   |
                                 +-------------------+
                                          |
                 +------------------------+------------------------+
                 |                        |                        |
                 v                        v                        v
        [Windows Toast]           [Telegram Bot]          [Discord Webhook]
        Native popup on PC        Instant push to phone    Rich server embed
```

### 1. The Strategy Planner (`autonomous_planner.py`)
- Calculates exact daily/weekly volume quotas to hit your revenue targets.
- Restricts sending to **US Business Hours** (8:30 AM – 4:30 PM CST/EST) when decision-makers (Chief Estimators, Owners) actually open emails.
- Automatically organizes multi-touch follow-up sequences:
  - **Touch 1 (Day 1):** Niche Hook & Takeoff Bandwidth Offer
  - **Touch 2 (Day +2):** Turnaround Guarantee (24-48 hrs) & Deliverable Sample
  - **Touch 3 (Day +4):** Software Compatibility (PlanSwift, Bluebeam Revu, CSI Excel)
  - **Touch 4 (Day +7):** Polite Breakup & Contact Retention

### 2. The Silent Background Daemon (`background_daemon.py`)
- Runs as an invisible background process on Windows using detached execution or silent VBScript.
- Automatically handles Gmail SMTP authentication with anti-spam jitter intervals (random 60 to 180 seconds between emails) so Gmail deliverability stays 100% clean.
- Automatically pauses in the evening and wakes up each morning.

### 3. The 24/7 Inbox Sentinel (`inbox_sentinel.py`)
- Connects securely to `imap.gmail.com:993` using SSL.
- Periodically scans inbox for incoming messages from contacted contractors.
- **Intelligent Intent Classifier**:
  - `HOT_LEAD_PLANS`: Identifies emails with attached PDF blueprints, CAD drawings, Dropbox/Drive links, or RFP bid requests.
  - `INTERESTED`: Identifies contractors asking for rates, samples, or availability.
  - `UNSUBSCRIBE`: Instantly blacklists the lead so they are never emailed again.

### 4. The Multi-Channel Alert System (`alert_system.py`)
- Whenever a contractor sends drawings or asks for pricing:
  - Pops a native **Windows Desktop Toast Notification** on your PC screen.
  - Pushes an instant **Telegram alert** to your phone with company name, email, snippet, and attached files.
  - Posts an alert embed to **Discord**.

---

## 🚀 Quick-Start Control Panel

All scripts are available in `F:\Antigravity CLI` and `F:\Antigravity CLI\outreach_engine`:

### 1-Click Desktop Launchers:
| Action | File to Double-Click | Description |
| :--- | :--- | :--- |
| **Start Agent** | `start_background_agent.bat` | Launches the AI agent completely silently in the background of your PC. |
| **Check Status** | `check_agent_status.bat` | Displays live status, today's sent count, total replies, and active pipeline metrics. |
| **Stop Agent** | `stop_background_agent.bat` | Safely terminates the background daemon. |
| **View Live Logs** | `view_live_logs.bat` | Displays the last 35 timestamped log entries from the agent. |

### Command Line Interface:
```powershell
# From F:\Antigravity CLI\outreach_engine:

# Check system status
python background_daemon.py status

# Start daemon in background
python background_daemon.py start

# Stop daemon
python background_daemon.py stop

# Test notifications (Desktop Toast, Telegram, Discord)
python background_daemon.py test-alerts

# Test live inbox scan for incoming replies
python background_daemon.py test-inbox

# Run 1 single step immediately (Simulation / Dry Run)
python background_daemon.py run-once --dry-run
```

---

## 📱 Setting Up Free Telegram & Discord Alerts (Optional)

To receive push notifications directly on your smartphone whenever a contractor replies with project plans:

### Telegram Setup (2 Minutes):
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts to get your **Bot Token** (e.g. `123456789:ABCdef...`).
3. Search for `@userinfobot` in Telegram and send `/start` to get your personal **Chat ID** (e.g. `987654321`).
4. Add these two lines to your `F:\Antigravity CLI\outreach_engine\.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
5. Run `python background_daemon.py test-alerts` to verify your phone rings!

### Discord Setup (1 Minute):
1. In your Discord server, go to **Channel Settings > Integrations > Webhooks > New Webhook**.
2. Copy the Webhook URL and add it to `.env`:
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

---

## 🖥️ Auto-Start on Windows Boot (Set and Forget)

To make your PC run this AI agent completely automatically whenever you turn on or log in to your computer:

1. Right-click on PowerShell and select **Run as Administrator**.
2. Run:
   ```powershell
   cd "F:\Antigravity CLI\outreach_engine"
   .\register_windows_startup_task.ps1
   ```
3. To disable auto-start at any time:
   ```powershell
   .\unregister_windows_startup_task.ps1
   ```

---

## 📈 Next Steps to Scale Passive Income
1. **Double-click `start_background_agent.bat`**: The agent will run quietly in the background during US business hours.
2. **When an alert pops up**: A contractor has sent over a plan set or asked for a quote. Simply review the drawing page count, reply with a turnaround quote ($400 - $1,500 depending on division complexity), and deliver the takeoff to collect payment!
