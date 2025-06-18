#!/bin/bash

if [ -f mail2tg.pid ]; then
    kill $(cat mail2tg.pid) && echo "Mail2Telegram 已停止" && rm mail2tg.pid
else
    echo "找不到 PID，可能未啟動"
fi