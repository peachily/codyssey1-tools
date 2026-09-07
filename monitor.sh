#!/bin/bash

LOG_FILE="/var/log/agent-app/monitor.log"
APP_NAME="agent-app-linux-arm64"
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

PID=$(pgrep -f "$APP_NAME" | head -n 1)

if [ -z "$PID" ]; then
  echo "[ERROR] Agent process is not running"
  exit 1
fi

if ! ss -ltn | grep -q ":$PORT "; then
  echo "[ERROR] TCP port $PORT is not listening"
  exit 1
fi

if ! systemctl is-active --quiet ufw; then
  echo "[WARNING] UFW firewall is inactive"
fi

CPU=$(ps -p "$PID" -o %cpu= | xargs)
MEM=$(ps -p "$PID" -o %mem= | xargs)
DISK_USED=$(df / | awk 'NR==2 {gsub("%","",$5); print $5}')

if awk "BEGIN {exit !($CPU > 20)}"; then
  echo "[WARNING] CPU usage is over 20%: $CPU%"
fi

if awk "BEGIN {exit !($MEM > 10)}"; then
  echo "[WARNING] Memory usage is over 10%: $MEM%"
fi

if [ "$DISK_USED" -gt 80 ]; then
  echo "[WARNING] Disk usage is over 80%: $DISK_USED%"
fi

rotate_log

echo "[$TIMESTAMP] PID:$PID CPU:$CPU% MEM:$MEM% DISK_USED:$DISK_USED%" >> "$LOG_FILE"
