#!/usr/bin/env python3
"""Fetch daily lumber futures closes from the Trading Economics API and write
the document the Lumber Economics page reads from its `market/daily` record.

The API key is read from the macOS Keychain (service "tradingeconomics-api"),
never from this file or the command line.

Usage: python3 te_fetch.py [output.json]
"""
import datetime as dt
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

SYMBOL = "LB1:COM"          # Trading Economics symbol for front-month lumber futures
START = "2018-01-01"
SOURCE = "Trading Economics (lumber futures, $/MBF)"


def api_key():
    try:
        return subprocess.run(
            ["security", "find-generic-password", "-s", "tradingeconomics-api", "-w"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit("No key found in Keychain under service 'tradingeconomics-api'.")


def fetch(key):
    q = urllib.parse.urlencode({"c": key, "d1": START, "f": "json"})
    url = f"https://api.tradingeconomics.com/markets/historical/{urllib.parse.quote(SYMBOL)}?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "lumber-feed/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read()[:300]!r}")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        sys.exit("API did not return JSON: " + body[:300])


def build(rows):
    daily = []
    for r in rows:
        try:
            d = dt.datetime.strptime(r["Date"], "%d/%m/%Y").replace(tzinfo=dt.timezone.utc)
            close = float(r["Close"])
        except (KeyError, ValueError, TypeError):
            continue
        if close > 50:
            daily.append([int(d.timestamp() * 1000), round(close, 2)])
    if not daily:
        sys.exit("No usable rows returned.")
    daily.sort()
    return {"price": daily[-1][1], "asOf": daily[-1][0], "source": SOURCE,
            "symbol": SYMBOL, "daily": daily, "fetchedAt": int(dt.datetime.now().timestamp() * 1000)}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "market_daily.json"
    doc = build(fetch(api_key()))
    with open(out, "w") as f:
        json.dump(doc, f)
    print(f"{len(doc['daily'])} days, latest ${doc['price']}/MBF on "
          f"{dt.datetime.fromtimestamp(doc['asOf'] / 1000, dt.timezone.utc):%Y-%m-%d} -> {out}")
