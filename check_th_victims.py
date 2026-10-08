import os
import json
import logging
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "seen_victims.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Default Config
DEFAULT_CONFIG = {
    "apple_id_or_phone": "",
    "line_channel_access_token": "",
    "line_user_id": "",
    "ms_teams_webhook_url": "",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "discord_webhook_url": "",
    "slack_webhook_url": "",
    "enable_macos_notification": True,
    "enable_macos_dialog": True
}

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            logger.error(f"Error loading config.json: {e}")
    
    # Override from Environment Variables (for GitHub Actions / CI)
    if os.getenv("LINE_CHANNEL_ACCESS_TOKEN"):
        cfg["line_channel_access_token"] = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if os.getenv("LINE_USER_ID"):
        cfg["line_user_id"] = os.getenv("LINE_USER_ID")
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        cfg["telegram_bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    if os.getenv("TELEGRAM_CHAT_ID"):
        cfg["telegram_chat_id"] = os.getenv("TELEGRAM_CHAT_ID")
    if os.getenv("DISCORD_WEBHOOK_URL"):
        cfg["discord_webhook_url"] = os.getenv("DISCORD_WEBHOOK_URL")
    if os.getenv("SLACK_WEBHOOK_URL"):
        cfg["slack_webhook_url"] = os.getenv("SLACK_WEBHOOK_URL")

    # If running in CI (GitHub Actions), disable macOS GUI dialogs
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        cfg["enable_macos_notification"] = False
        cfg["enable_macos_dialog"] = False

    return cfg

def load_seen_ids():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Failed to read state file: {e}")
    return set()

def save_seen_ids(seen_ids):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen_ids), f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")

def fetch_victims_api():
    """Fetch recent Thailand victims via api.ransomware.live/v2/recentvictims"""
    url = "https://api.ransomware.live/v2/recentvictims"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            th_victims = []
            for item in data:
                if item.get("country") == "TH":
                    victim_name = item.get("victim", "Unknown")
                    group_name = item.get("group", "Unknown")
                    disc_date = item.get("discovered", "")[:10]
                    link = item.get("url") or f"https://www.ransomware.live/id/{item.get('id', '')}"
                    th_victims.append({
                        "id": f"{victim_name}@{group_name}".lower(),
                        "name": victim_name,
                        "group": group_name,
                        "discovered": disc_date,
                        "sector": item.get("activity", ""),
                        "url": link,
                        "description": item.get("description", "")
                    })
            logger.info(f"Fetched {len(th_victims)} Thailand victims from API recentvictims")
            return th_victims
    except Exception as e:
        logger.warning(f"API fetch failed or timed out: {e}")
    return []

def fetch_victims_web():
    """Scrape Thailand victims list directly from country page"""
    url = "https://www.ransomware.live/country/THA"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200:
            logger.error(f"Web scraper returned HTTP {res.status_code}")
            return []
        
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".victim-item")
        victims = []
        for card in cards:
            title_el = card.select_one(".victim-title")
            if not title_el:
                continue
            name = title_el.text.strip()
            url_path = title_el.get("href", "")
            full_url = f"https://www.ransomware.live{url_path}" if url_path else ""

            group_el = card.select_one(".rl-group-badge")
            group = group_el.text.strip() if group_el else "Unknown"

            meta = card.select_one(".victim-meta")
            meta_text = meta.text if meta else ""
            disc_m = re.search(r"Discovered:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", meta_text)
            discovered = disc_m.group(1) if disc_m else ""

            desc_el = card.select_one(".victim-desc")
            desc = desc_el.text.strip() if desc_el else ""

            sector_link = card.select_one("a[href*=\"/activity/\"]")
            sector = sector_link.get("title", "").replace("View more victims in ", "").strip() if sector_link else ""

            victims.append({
                "id": f"{name}@{group}".lower(),
                "name": name,
                "group": group,
                "discovered": discovered,
                "sector": sector,
                "url": full_url,
                "description": desc
            })
        logger.info(f"Scraped {len(victims)} Thailand victims from country page")
        return victims
    except Exception as e:
        logger.error(f"Web scraping failed: {e}")
        return []

def get_thailand_victims():
    # Attempt scraper first since it has all 200+ historical victims and fresh updates
    victims = fetch_victims_web()
    if not victims:
        # Fallback to API
        victims = fetch_victims_api()
    return victims

def send_macos_notification(title, message, sound="Hero"):
    try:
        # Standard banner notification
        script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
        os.system(f"osascript -e '{script}'")
    except Exception as e:
        logger.warning(f"macOS notification failed: {e}")

def show_macos_dialog(new_victims):
    """Show a persistent popup dialog on macOS that stays on screen until dismissed or clicked."""
    try:
        count = len(new_victims)
        summary_lines = []
        for v in new_victims[:4]:
            summary_lines.append(f"• {v['name']} ({v['group']})")
        if count > 4:
            summary_lines.append(f"...and {count - 4} more")
        
        body = f"Detected {count} new ransomware victim(s) in Thailand:\\n" + "\\n".join(summary_lines)
        
        first_url = new_victims[0].get("url") or "https://www.ransomware.live/map/th"
        
        # AppleScript with dialog box
        applescript = f'''
        tell application "System Events"
            activate
            set dialogResult to display dialog "{body}" with title "🚨 Ransomware.live Alert (TH)" buttons {{"Close", "Open Details"}} default button "Open Details" with icon caution
            if button returned of dialogResult is "Open Details" then
                open location "{first_url}"
            end if
        end tell
        '''
        # Run asynchronously in background so it doesn't block other tasks if user is away
        import subprocess
        subprocess.Popen(["osascript", "-e", applescript])
    except Exception as e:
        logger.warning(f"macOS dialog popup failed: {e}")

def send_imessage(recipient, message):
    """Send an iMessage to the user's Apple ID (email or phone number)."""
    if not recipient or not recipient.strip():
        return
    
    recipient = recipient.strip()
    # Clean markdown asterisks for plain text SMS/iMessage
    clean_message = message.replace("*", "")
    
    applescript = '''
    on run argv
        set targetRecipient to item 1 of argv
        set targetMessage to item 2 of argv
        tell application "Messages"
            try
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to participant targetRecipient of targetService
                send targetMessage to targetBuddy
            on error errMsg
                -- Fallback directly sending to buddy
                send targetMessage to buddy targetRecipient
            end try
        end tell
    end run
    '''
    try:
        import subprocess
        res = subprocess.run(
            ["osascript", "-e", applescript, recipient, clean_message],
            capture_output=True,
            text=True,
            timeout=15
        )
        if res.returncode == 0:
            logger.info(f"iMessage alert sent successfully to {recipient}")
        else:
            logger.warning(f"iMessage send failed: {res.stderr.strip()}")
    except Exception as e:
        logger.error(f"Error executing iMessage AppleScript: {e}")

def send_line_message(access_token, user_id, message):
    """Send alert to LINE Official Account user via Messaging API."""
    if not access_token or not user_id:
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # Clean markdown formatting for clean LINE display
    clean_message = message.replace("*", "")
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": clean_message
            }
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            logger.info("LINE notification sent successfully")
        else:
            logger.warning(f"LINE notification failed: {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"LINE notification error: {e}")

def send_telegram(bot_token, chat_id, message):
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            logger.info("Telegram notification sent successfully")
        else:
            logger.warning(f"Telegram failed: {r.text}")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def send_discord(webhook_url, message):
    if not webhook_url:
        return
    payload = {"content": message}
    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        if r.status_code in [200, 204]:
            logger.info("Discord notification sent successfully")
        else:
            logger.warning(f"Discord failed: {r.text}")
    except Exception as e:
        logger.error(f"Discord error: {e}")

def send_slack(webhook_url, message):
    if not webhook_url:
        return
    payload = {"text": message}
    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        if r.status_code == 200:
            logger.info("Slack notification sent successfully")
        else:
            logger.warning(f"Slack failed: {r.text}")
    except Exception as e:
        logger.error(f"Slack error: {e}")

def send_ms_teams(webhook_url, new_victims):
    if not webhook_url:
        return
    
    count = len(new_victims)
    facts = []
    for v in new_victims:
        val = f"**Group:** {v['group']} | **Discovered:** {v['discovered'] or 'N/A'}"
        if v.get('sector'):
            val += f" | **Sector:** {v['sector']}"
        facts.append({"name": f"🎯 {v['name']}", "value": val})

    first_url = new_victims[0].get("url") or "https://www.ransomware.live/map/th"

    # MS Teams Adaptive Card (Power Automate / Workflow Webhook standard)
    adaptive_card_payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"🚨 Ransomware.live Alert: {count} New Victim(s) in Thailand",
                            "weight": "Bolder",
                            "size": "Medium",
                            "color": "Attention"
                        },
                        {
                            "type": "FactSet",
                            "facts": facts
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "Open Ransomware.live",
                            "url": first_url
                        }
                    ]
                }
            }
        ]
    }

    try:
        r = requests.post(webhook_url, json=adaptive_card_payload, timeout=10)
        # If workflow/webhook rejected adaptive card (e.g. legacy O365 connector), fallback to legacy MessageCard
        if r.status_code not in [200, 202]:
            legacy_payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "d9534f",
                "summary": f"Ransomware.live Alert (TH): {count} new victims",
                "title": f"🚨 Ransomware.live: {count} New Victim(s) in Thailand",
                "sections": [
                    {
                        "facts": facts
                    }
                ],
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "Open Details",
                        "targets": [{"os": "default", "uri": first_url}]
                    }
                ]
            }
            r = requests.post(webhook_url, json=legacy_payload, timeout=10)

        if r.status_code in [200, 202]:
            logger.info("Microsoft Teams notification sent successfully")
        else:
            logger.warning(f"Microsoft Teams webhook returned: {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"Microsoft Teams webhook error: {e}")

def notify_all(config, new_victims):
    count = len(new_victims)
    header = f"🚨 *[Ransomware.live]* New Victims Detected in Thailand ({count} total)\n\n"
    
    details = []
    for v in new_victims:
        line = (
            f"🎯 *Victim:* {v['name']}\n"
            f"🏴‍☠️ *Ransomware Group:* {v['group']}\n"
            f"📅 *Discovered:* {v['discovered'] or 'N/A'}\n"
        )
        if v['sector']:
            line += f"🏢 *Industry/Sector:* {v['sector']}\n"
        if v['url']:
            line += f"🔗 *Link:* {v['url']}\n"
        details.append(line)
        
    full_message = header + "\n-------------------\n".join(details)

    # 1. macOS Desktop Notification & Dialog Popup
    if config.get("enable_macos_notification", True):
        names = ", ".join([v['name'] for v in new_victims[:3]])
        if count > 3:
            names += f" and {count - 3} more"
        send_macos_notification("Ransomware.live Alert (TH)", f"New victim(s) in Thailand: {names}")
        
        # Persistent Dialog Popup
        if config.get("enable_macos_dialog", True):
            show_macos_dialog(new_victims)

    # 2. Apple iMessage (iPhone / Mac Sync)
    if config.get("apple_id_or_phone"):
        send_imessage(config.get("apple_id_or_phone"), full_message)

    # 3. LINE Official Account (Messaging API)
    if config.get("line_channel_access_token") and config.get("line_user_id"):
        send_line_message(
            config.get("line_channel_access_token"),
            config.get("line_user_id"),
            full_message
        )

    # 4. Telegram
    send_telegram(
        config.get("telegram_bot_token"),
        config.get("telegram_chat_id"),
        full_message
    )

    # 4. Discord
    send_discord(
        config.get("discord_webhook_url"),
        full_message
    )

    # 5. Slack
    send_slack(
        config.get("slack_webhook_url"),
        full_message
    )

def main():
    import sys
    config = load_config()

    if "--test" in sys.argv or "-t" in sys.argv:
        print("🔔 Running notification TEST...")
        mock_victims = [
            {
                "id": "mock_company@lockbit",
                "name": "Test Company Thailand Ltd.",
                "group": "LockBit 3.0",
                "discovered": datetime.now().strftime("%Y-%m-%d"),
                "sector": "Technology",
                "url": "https://www.ransomware.live/map/th",
                "description": "Mock alert for testing notifications."
            }
        ]
        notify_all(config, mock_victims)
        print("✅ Sent test notifications via configured channels!")
        return

    logger.info("Starting Ransomware.live Thailand monitor check...")
    seen_ids = load_seen_ids()
    is_initial_run = (len(seen_ids) == 0)

    victims = get_thailand_victims()
    if not victims:
        logger.warning("No victims retrieved. Aborting check.")
        return

    new_victims = []
    for v in victims:
        vid = v["id"]
        if vid not in seen_ids:
            new_victims.append(v)
            seen_ids.add(vid)

    if is_initial_run:
        logger.info(f"Initial run completed. Indexed {len(seen_ids)} existing Thailand victims.")
        save_seen_ids(seen_ids)
        print(f"✅ Initialized database with {len(seen_ids)} historical victims.")
        print("Subsequent runs will only alert on newly published victims.")
        return

    if new_victims:
        logger.info(f"Found {len(new_victims)} NEW Thailand victims! Sending notifications...")
        notify_all(config, new_victims)
    else:
        logger.info("No new Thailand victims found.")

    save_seen_ids(seen_ids)

if __name__ == "__main__":
    main()

