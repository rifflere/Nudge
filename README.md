# 🔔 Nudge

A lightweight web monitoring tool that checks for updates on any webpage and sends email notifications. Built with Python, Playwright, and GitHub Actions.

**Current use case:** Monitor IKEA Renton events page for new workshops and activities.

*Built with assistance from Claude (Anthropic).*

---

## 📑 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

---

## Features

✅ Automated monitoring via GitHub Actions  
✅ Smart change detection - only notifies on new content  
✅ Email notifications via Gmail  
✅ Privacy-focused - encrypted artifacts for public repos  
✅ Easy to customize for any website  

---

## Quick Start

### Local Setup

1. **Clone and install**
```bash
   git clone https://github.com/yourusername/nudge.git
   cd nudge
   python3 -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   # OR .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   playwright install chromium
```

2. **Configure .env file**
```bash
   cp .env.example .env
```
   
   Edit `.env` and add your Gmail App Password from [here](https://myaccount.google.com/apppasswords) (requires 2FA):
```dotenv
   EMAIL_PASSWORD=your-16-char-app-password
```

3. **Test run**
```bash
   python src/check_events.py
```

### GitHub Actions Setup

1. **Generate encryption key**
```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. **Add secrets** to Repository → Settings → Secrets and variables → Actions:
   - `TARGET_URL`: 
   - `EVENTS_CONTAINER_SELECTOR`: 
   - `EVENT_ITEM_SELECTOR`: 
   - `NOTIFY_EMAIL`: your.email@gmail.com
   - `FROM_EMAIL`: your.email@gmail.com
   - `EMAIL_PASSWORD`: (Gmail App Password)
   - `SMTP_HOST`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`
   - `ARTIFACT_ENCRYPTION_KEY`: (output from step 1)

3. **Test** via Actions → "Weekly IKEA Renton Events Check" → Run workflow

---

## Configuration

### Monitor a Different Website

Update these in `.env` (local) or GitHub Secrets (Actions):
```dotenv
TARGET_URL=https://example.com/page-to-monitor
EVENTS_CONTAINER_SELECTOR=div.content-wrapper
EVENT_ITEM_SELECTOR=article.item
```

**Finding selectors:** Right-click element → Inspect → Copy → Copy selector

### Change Schedule

Edit `.github/workflows/weekly_check.yml`:
```yaml
schedule:
  - cron: "0 17 * * 1"  # Mondays at 5pm UTC
```

Use [crontab.guru](https://crontab.guru/) for custom schedules.

---

## How It Works

1. **Scrapes** target page with Playwright (headless browser)
2. **Extracts** text from specified CSS selectors
3. **Normalizes** text to avoid false positives from formatting changes
4. **Compares** to previous run using set difference
5. **Emails** you if new content detected
6. **Saves** encrypted state as GitHub artifact (for public repos)

**Security:** 
- Credentials stored in GitHub Secrets (encrypted at rest)
- State artifacts encrypted with Fernet (AES-128)
- Gmail App Passwords used (not account password)

---

## Troubleshooting

**"ModuleNotFoundError"**  
→ `pip install -r requirements.txt`

**"Authentication failed"**  
→ Use [Gmail App Password](https://myaccount.google.com/apppasswords), not account password (requires 2FA)

**"Timed out waiting for events container"**  
→ Verify selectors by inspecting the page. Increase timeout in `check_events.py` if needed.

**No email received**  
→ Check spam folder. Verify `NOTIFY_EMAIL` is correct. Second run won't email if no changes.

---

**License:** MIT