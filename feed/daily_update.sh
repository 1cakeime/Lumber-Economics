#!/bin/zsh
# Daily lumber price collection: fetches the latest CME lumber settlement from
# API Ninjas and adds it to market_daily.json (the accumulated daily history).
# Scheduled by ~/Library/LaunchAgents/com.lumbereconomics.daily.plist.
#
# Loading the file into the page's `market/daily` record needs Claude's
# Artifact tool (not available to headless runs): in a Claude session, say
# "update lumber price".
set -euo pipefail
export PATH="/usr/bin:/bin:/usr/sbin:/sbin"
cd "$(dirname "$0")"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
python3 ninjas_fetch.py "$PWD/market_daily.json"
