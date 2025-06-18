import asyncio
import os
import re
import requests
import quopri
from dotenv import load_dotenv
from aiosmtpd.controller import Controller
import email
from email.header import decode_header
from email.utils import parseaddr

# 載入 .env 設定
load_dotenv(dotenv_path="SMTP2TG.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))  # ✅ 預設改為 25

def extract_sender_email(raw_from):
    name, addr = parseaddr(raw_from)
    return f"<{addr}>" if addr else "(未知)"

class MailHandler:
    async def handle_DATA(self, server, session, envelope):
        try:
            raw_bytes = envelope.content
            msg = email.message_from_bytes(raw_bytes)

            # ✅ 根據 Content-Transfer-Encoding 決定是否解 quoted-printable
            encoding = msg.get('Content-Transfer-Encoding', '').lower()
            if encoding == 'quoted-printable':
                decoded_content = quopri.decodestring(raw_bytes).decode('utf8', errors='replace')
            else:
                decoded_content = raw_bytes.decode('utf8', errors='replace')

            # ✅ 擷取寄件人（只保留 email）
            raw_from = msg.get('From', '(未知)')
            sender_email = extract_sender_email(raw_from)

            # ✅ 讀取規則 match_rules.txt
            try:
                with open("match_rules.txt", "r") as f:
                    match_lines = [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"⚠️ 無法讀取 match_rules.txt：{e}")
                match_lines = []

            # ✅ 套用 regex
            matches = []
            for line in match_lines:
                if '___' in line:
                    label, pattern = line.split('___', 1)
                else:
                    label, pattern = '未命名', line
                m = re.search(pattern, decoded_content)
                if m:
                    matches.append(f"📌 來源：{label}\n擷取：{m.group(1)}")

            # ✅ 組合訊息並限制長度為 400 字
            if matches:
                message = f"📩 來自：{sender_email}\n" + "\n\n".join(matches)
            else:
                message = f"📩 來自：{sender_email}\n⚠️ 沒有擷取到符合的資訊。"

            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            resp = requests.post(telegram_url, data={
                'chat_id': CHAT_ID,
                'text': message[:400]  # ✅ 長度限制為 400
            })

            print("== decoded content ==")
            print(decoded_content)
            print("== Telegram response ==")
            print(resp.status_code, resp.text)

            return '250 OK'
        except Exception as e:
            print(f"❌ 發生錯誤：{e}")
            return '451 Temporary failure'

def check_required_env():
    required = ['BOT_TOKEN', 'CHAT_ID']
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(f"❌ 缺少必要設定：{', '.join(missing)}，請確認 Mail2Telegram.env 是否正確。")
        exit(1)

async def main():
    controller = Controller(MailHandler(), hostname="", port=SMTP_PORT)
    controller.start()
    print(f"📬 Mail2Telegram SMTP Server 正在監聽 port {SMTP_PORT} ...")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("🛑 收到中斷，關閉中...")
    finally:
        controller.stop()

if __name__ == "__main__":
    check_required_env()
    asyncio.run(main())