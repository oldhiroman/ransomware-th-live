# Ransomware.live Thailand Daily Monitor

สคริปต์ตรวจสอบข้อมูลเหยื่อ Ransomware ในประเทศไทย (Thailand) จาก [ransomware.live/map/th](https://www.ransomware.live/country/THA) และแจ้งเตือนอัตโนมัติเมื่อพบเหยื่อรายใหม่

---

## 📁 ไฟล์ภายในโฟลเดอร์

- `check_th_victims.py` : สคริปต์หลักที่ดึงข้อมูล ตรวจจับเหยื่อใหม่ และส่งแจ้งเตือน
- `config.json` : ไฟล์กำหนดค่า Webhook / Token สำหรับการแจ้งเตือน
- `seen_victims.json` : ฐานข้อมูลบันทึก ID เหยื่อที่เคยตรวจพบแล้ว (เพื่อไม่ให้แจ้งเตือนซ้ำ)

---

## ⚙️ การตั้งค่าการแจ้งเตือน (`config.json`)

เปิดไฟล์ `config.json` เพื่อใส่ Token หรือ Webhook ของช่องทางที่ต้องการ:

```json
{
    "telegram_bot_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID",
    "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
    "slack_webhook_url": "YOUR_SLACK_WEBHOOK_URL",
    "enable_macos_notification": true
}
```

- **Telegram**: แจ้งเตือนผ่าน Bot (ใส่ `telegram_bot_token` และ `telegram_chat_id`)
- **Discord**: แจ้งเตือนเข้า Channel ผ่าน Webhook (ใส่ `discord_webhook_url`)
- **Slack**: แจ้งเตือนเข้า Channel ผ่าน Incoming Webhook (ใส่ `slack_webhook_url`)
- **macOS Notification**: แจ้งเตือนเป็นป๊อปอัป Banner บนหน้าจอ Mac ทันที (เปิดใช้งานโดยตั้งเป็น `true`)

---

## ⏰ วิธีตั้งค่าให้รันอัตโนมัติทุกวันตอน 9:00 น.

### วิธีที่ 1: ตั้งค่าผ่าน macOS `crontab` (แนะนำ ง่ายและเร็ว)

1. เปิด Terminal แล้วพิมพ์คำสั่ง:
   ```bash
   crontab -e
   ```
2. ใส่บรรทัดต่อไปนี้ลงไป (รันทุกวันเวลา 09:00 น.):
   ```cron
   0 9 * * * /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 /Users/pranodhm/Downloads/ransamware.live/check_th_victims.py >> /Users/pranodhm/Downloads/ransamware.live/cron.log 2>&1
   ```
3. กดบันทึก (หากใช้ vim กด `Esc` แล้วพิมพ์ `:wq` แล้วกด Enter)

---

### วิธีที่ 2: ตั้งค่าผ่าน macOS `launchd` (สำหรับให้ทำงานแม้เครื่อง sleep/wake)

1. สร้างไฟล์ `~/Library/LaunchAgents/com.user.ransomware.th.plist` ด้วยเนื้อหา:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.user.ransomware.th</string>
       <key>ProgramArguments</key>
       <array>
           <string>/Library/Frameworks/Python.framework/Versions/3.11/bin/python3</string>
           <string>/Users/pranodhm/Downloads/ransamware.live/check_th_victims.py</string>
       </array>
       <key>StartCalendarInterval</key>
       <dict>
           <key>Hour</key>
           <integer>9</integer>
           <key>Minute</key>
           <integer>0</integer>
       </dict>
       <key>StandardOutPath</key>
       <string>/Users/pranodhm/Downloads/ransamware.live/launchd.log</string>
       <key>StandardErrorPath</key>
       <string>/Users/pranodhm/Downloads/ransamware.live/launchd_err.log</string>
   </dict>
   </plist>
   ```
2. โหลด service:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.user.ransomware.th.plist
   ```
