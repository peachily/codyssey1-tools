#!/bin/bash

LOG_FILE="/var/log/agent-app/monitor-leak.log"
APP_NAME="agent-leak-app-arm64"
PORT="15034"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

rotate_log() {
  if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE")" -ge 10485760 ]; then
    rm -f "${LOG_FILE}.9"

    for i in 8 7 6 5 4 3 2 1; do
      [ -f "${LOG_FILE}.${i}" ] && mv "${LOG_FILE}.${i}" "${LOG_FILE}.$((i+1))"
    done

    mv "$LOG_FILE" "${LOG_FILE}.1"
  fi
}

PIDS=$(pgrep -f "$APP_NAME")

if [ -z "$PIDS" ]; then
  echo "[ERROR] Agent process is not running"
  exit 1
fi

PID_LIST=$(echo "$PIDS" | paste -sd, -)

if ! ss -ltn | grep -q ":$PORT "; then
  echo "[ERROR] TCP port $PORT is not listening"
  exit 1
fi

if ! systemctl is-active --quiet ufw; then
  echo "[WARNING] UFW firewall is inactive"
fi

CPU=$(ps -p "$PID_LIST" -o %cpu= | awk '{sum += $1} END {printf "%.1f", sum}')
MEM_PCT=$(ps -p "$PID_LIST" -o %mem= | awk '{sum += $1} END {printf "%.1f", sum}')
RSS_KB=$(ps -p "$PID_LIST" -o rss= | awk '{sum += $1} END {print sum}')
MEM_MB=$(awk "BEGIN {printf \"%.1f\", $RSS_KB/1024}")

DISK_USED=$(df / | awk 'NR==2 {gsub("%","",$5); print $5}')

if awk "BEGIN {exit !($CPU > 20)}"; then
  echo "[WARNING] CPU usage is over 20%: $CPU%"
fi

if awk "BEGIN {exit !($MEM_PCT > 10)}"; then
  echo "[WARNING] Memory usage is over 10%: $MEM_PCT%"
fi

if [ "$DISK_USED" -gt 80 ]; then
  echo "[WARNING] Disk usage is over 80%: $DISK_USED%"
fi

rotate_log

echo "[$TIMESTAMP] PIDS:$PID_LIST CPU:$CPU% MEM:${MEM_MB}MB MEM_PCT:$MEM_PCT% DISK_USED:$DISK_USED%" >> "$LOG_FILE"
