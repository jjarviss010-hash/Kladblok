#!/usr/bin/env bash
# Start de Hyped-bot en herstart hem automatisch als hij stopt (macOS / Linux).
cd "$(dirname "$0")"
while true; do
  python3 hyped_bot.py
  echo "Bot gestopt, herstart over 10 seconden..."
  sleep 10
done
