# 🚀 Deploying AI Passive Outreach & Inbox Sentinel to 24/7 Dokploy VPS

This guide explains how to deploy your **Autonomous AI Lead Agent & Inbox Sentinel** to Dokploy on your remote VPS so it runs 24/7 without needing your laptop powered on.

---

## 🏗️ Architecture Summary

```
                      24/7 Cloud VPS (Ubuntu + Dokploy)
                       ┌──────────────────────────────┐
                       │       Dokploy Engine         │
                       │   (Auto-restart, SSL, Logs)  │
                       └──────────────┬───────────────┘
                                      │
                       ┌──────────────▼───────────────┐
                       │   Container: ai-outreach     │
                       │                              │
                       │  1. Background Daemon (24/7) │──▶ US Business Hours Outreach
                       │  2. Inbox Sentinel (IMAP)    │──▶ Real-time Blueprint Alerts
                       │  3. FastAPI Web Dashboard    │──▶ Port 8000 Web UI
                       └──────────────────────────────┘
```

---

## 📋 Step 1: Push your Code to GitHub (Recommended)

1. Initialize git in your repository (if not already done):
   ```bash
   git add .
   git commit -m "Add Dockerfile and Compose for 24/7 Dokploy deployment"
   git push origin main
   ```

*(Keep `.env` in `.gitignore` — your secrets will be configured directly in Dokploy).*

---

## 🚀 Step 2: Deploy in Dokploy Dashboard

1. Open your Dokploy dashboard: `http://<your-vps-ip>:3000`.
2. Click **Create Project** (or select your existing project).
3. Click **Create Service** &rarr; Select **Application** (or **Compose**):
   * **Source Type:** Choose **GitHub** (or **Git**).
   * **Repository:** Select your repository URL.
   * **Branch:** `main`.
   * **Build Type:** Choose **Dockerfile** (or **Docker Compose**).
   * **Dockerfile Path:** `./outreach_engine/Dockerfile` (or `./Dockerfile` if repository root is outreach_engine).

---

## 🔑 Step 3: Configure Environment Variables in Dokploy

In Dokploy under your application's **Environment** tab, add your secrets:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `GMAIL_USER` | Your Google Workspace / Gmail address | `harriswilford1618@gmail.com` |
| `GMAIL_APP_PASS` | 16-character Google App Password | `xxxx xxxx xxxx xxxx` |
| `TELEGRAM_BOT_TOKEN` | (Optional) Telegram bot token for phone alerts | `123456789:ABC...` |
| `TELEGRAM_CHAT_ID` | (Optional) Your Telegram chat ID | `987654321` |
| `DISCORD_WEBHOOK_URL`| (Optional) Discord channel webhook | `https://discord.com/api/webhooks/...` |
| `TZ` | Operational Timezone | `America/New_York` |
| `PORT` | Web Dashboard Port | `8000` |

---

## 🌐 Step 4: Configure Domain & Traefik (Optional)

If you want a public custom domain with automatic SSL (HTTPS) for your web dashboard:

1. In Dokploy, go to the **Domains** tab of your application.
2. Click **Add Domain**.
3. Enter your domain (e.g. `outreach.yourdomain.com`).
4. Set container port to **`8000`**.
5. Enable **HTTPS** (Dokploy + Traefik will automatically issue a free Let's Encrypt SSL certificate!).

---

## 📊 Step 5: Deploy & Monitor

1. Click **Deploy**.
2. Dokploy will build the image, initialize the 24/7 background daemon, and start the web dashboard.
3. Check the **Logs** tab in Dokploy to see live progress:
   * `[+] Background Daemon active (PID: ...)`
   * `[+] Monitoring inbox for contractor plan submissions...`
   * `[+] Starting Web Dashboard on http://0.0.0.0:8000`
4. Access your live dashboard anytime at `http://<your-vps-ip>:8000` or your custom domain.

---

## 🔄 Persistence & Data Safety

The following files are mounted persistently so no campaign state or lead data is lost during container updates:
* `leads_master_db.json` — Master contractor lead database.
* `campaign_state.json` — Tracks sent touches and prevents duplicate emails.
* `daemon_state.json` — Tracks daily sending quotas and operational timers.
* `sentinel_state.json` — Tracks processed reply threads and blueprint submissions.
