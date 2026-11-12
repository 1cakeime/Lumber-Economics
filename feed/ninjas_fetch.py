#!/usr/bin/env python3
"""Fetch lumber futures prices from API Ninjas and write the document the
Lumber Economics page reads from its `market/daily` record.

The API key is read from the macOS Keychain (service "api-ninjas"), never from
this file or the command line.

Free keys get the last daily settlement only, so each run adds one day to the
history kept in the output file. Premium keys also backfill daily history.

Usage: python3 ninjas_fetch.py [output.json]   (default: market_daily.json)
"""
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.api-ninjas.com/v1"
NAME = "lumber"
START = dt.datetime(2018, 1, 1, tzinfo=dt.timezone.utc)
SOURCE = "API Ninjas (CME lumber futures, $/MBF)"
DAY_MS = 86_400_000


def api_key():
    try:
        key = subprocess.run(
            ["security", "find-generic-password", "-s", "api-ninjas", "-w"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        key = ""
    if not key:
        sys.exit("No key found in Keychain under service 'api-ninjas'.")
    return key


def get(key, path, **params):
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"X-Api-Key": key, "User-Agent": "lumber-feed/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode("utf-8", "replace")
        if "premium" in body.lower():
            return None
        sys.exit(f"API error {e.code} on {path}: {body}")


def day(ts_seconds):
    """Midnight UTC (ms) of the day a timestamp falls on."""
    return int(ts_seconds) * 1000 // DAY_MS * DAY_MS


def backfill(key):
    """Daily closes since START (premium only). Returns None on a free key."""
    out, start = {}, START
    now = dt.datetime.now(dt.timezone.utc)
    while start < now:
        end = min(start + dt.timedelta(days=900), now)
        rows = get(key, "commoditypricehistorical", name=NAME, period="1d",
                   start=int(start.timestamp()), end=int(end.timestamp()))
        if rows is None:
            return None
        for r in rows or []:
            try:
                close = float(r["close"])
                if close > 50:
                    out[day(r["time"])] = round(close, 2)
            except (KeyError, ValueError, TypeError):
                continue
        start = end
    return out


def load(path):
    try:
        with open(path) as f:
            return {int(t): float(p) for t, p in json.load(f).get("daily", [])}
    except (FileNotFoundError, ValueError, TypeError):
        return {}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "market_daily.json"
    key = api_key()

    daily = load(out)
    hist = backfill(key)
    if hist:
        daily.update(hist)

    cur = get(key, "commodityprice", name=NAME)
    if not cur or "price" not in cur:
        sys.exit(f"Unexpected response: {cur!r}")
    price, asof = round(float(cur["price"]), 2), day(cur["updated"])
    daily[asof] = price

    doc = {
        "price": price, "asOf": asof, "source": SOURCE, "symbol": cur.get("futures_contract"),
        "contractMonth": cur.get("futures_contract_month"), "previousClose": cur.get("previous_close"),
        "high52w": cur.get("high_52w"), "low52w": cur.get("low_52w"),
        "daily": sorted([t, p] for t, p in daily.items()),
        "fetchedAt": int(dt.datetime.now().timestamp() * 1000),
    }
    tmp = out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f)
    os.replace(tmp, out)
    print(f"${price}/MBF ({doc['symbol']}) on {dt.datetime.fromtimestamp(asof / 1000, dt.timezone.utc):%Y-%m-%d}; "
          f"{len(doc['daily'])} days stored; history backfill: {'yes' if hist else 'premium only'} -> {out}")
