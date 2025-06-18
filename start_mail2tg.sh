#!/bin/bash

# 切換到程式目錄
cd /data/mail2tg

# 啟動 venv
source venv/bin/activate

# 執行程式並丟到背景
nohup python3 SMTP2TG.py > mail2tg.log 2>&1 &
echo $! > mail2tg.pid

echo "SMTP2Telegram 已在背景啟動，PID: $(cat mail2tg.pid)"