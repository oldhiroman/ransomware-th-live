# 🚨 Ransomware.live Thailand Daily Monitor

Automated threat intelligence monitoring for new ransomware victims in Thailand reported on [Ransomware.live](https://www.ransomware.live/country/THA).

Supports scheduled daily checks with automated notifications across **LINE**, **Telegram**, **iMessage**, **macOS Dialog**, **Discord**, and **Slack**.

---

## ✨ Features

- 🇹🇭 **Targeted Monitoring:** Scrapes and tracks ransomware leak site posts specifically affecting organizations in Thailand.
- 🔄 **Multi-Environment Execution:**
  - **GitHub Actions (Cloud):** Runs 24/7 in the cloud without requiring a running computer.
  - **macOS Cron (Local):** Runs locally on Mac with native desktop alerts.
- 📱 **Multi-Channel Alerting:**
  - 💚 **LINE Official Account (Messaging API):** Push alerts directly to your LINE app.
  - ✈️ **Telegram Bot:** Real-time markdown alerts via your Telegram Bot.
  - 💬 **Apple iMessage:** Native iMessage alerts sent to your Apple ID on iPhone/Mac.
  - 🖥️ **macOS Dialog Box:** Persistent on-screen popup alert with quick "Open Details" button.
  - 🎮 **Discord / Slack:** Webhook integrations supported.
- 🛡️ **Zero Duplicate Alerts:** State is maintained in `seen_victims.json` so only newly detected victims trigger alerts.

---

## 📁 Repository Structure

```text
├── .github/workflows/
│   └── daily_check.yml       # GitHub Actions workflow (Scheduled at 09:05 AM Bangkok time)
├── check_th_victims.py       # Main monitoring & notification Python script
├── config.json               # Local credentials configuration file
├── seen_victims.json         # Database of previously observed victims
├── README.md                 # Project documentation
└── .gitignore                # Git ignore patterns
```

---

## ☁️ Running on GitHub Actions (Recommended)

The workflow runs daily at **09:05 AM Bangkok Time (02:05 UTC)** via `.github/workflows/daily_check.yml`. When new victims are detected, the runner sends notifications and automatically commits the updated `seen_victims.json` back to the repository.

### Required GitHub Secrets

To enable alerts in the cloud, add the following secrets in **Settings > Secrets and variables > Actions**:

| Secret Name | Description |
| :--- | :--- |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API Channel Access Token |
| `LINE_USER_ID` | Your LINE User ID (`U...`) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token from `@BotFather` |
| `TELEGRAM_CHAT_ID` | Your personal Telegram Chat ID |
| `DISCORD_WEBHOOK_URL` | *(Optional)* Discord Webhook URL |
| `SLACK_WEBHOOK_URL` | *(Optional)* Slack Incoming Webhook URL |

---

## 💻 Running Locally on macOS

### 1. Requirements
- Python 3.10+
- Dependencies:
  ```bash
  pip install requests beautifulsoup4
  ```

### 2. Configure `config.json`
Edit `config.json` with your credentials:
```json
{
    "apple_id_or_phone": "your_apple_id@example.com",
    "line_channel_access_token": "YOUR_LINE_ACCESS_TOKEN",
    "line_user_id": "YOUR_LINE_USER_ID",
    "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID",
    "enable_macos_notification": true,
    "enable_macos_dialog": true
}
```

### 3. Test Notifications
Send a mock alert through all configured channels:
```bash
python3 check_th_victims.py --test
```

### 4. Schedule via macOS `crontab`
To run every day at 09:00 AM:
```bash
(crontab -l 2>/dev/null; echo "0 9 * * * $(which python3) $(pwd)/check_th_victims.py >> $(pwd)/cron.log 2>&1") | crontab -
```

Check current crontab:
```bash
crontab -l
```

---

## 🔔 Alert Preview

When a new victim is detected, alerts look like this:

```text
🚨 [Ransomware.live] New Victims Detected in Thailand (1 total)

🎯 Victim: Target Company Thailand Co., Ltd.
🏴‍☠️ Ransomware Group: LockBit 3.0
📅 Discovered: 2026-10-08
🏢 Industry/Sector: Technology
🔗 Link: https://www.ransomware.live/map/th
```

---

## 📄 License
MIT License. Open threat intelligence powered by [Ransomware.live](https://www.ransomware.live/).
