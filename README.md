# Lumber Economics

Lumber pricing for contractors and home builders: prices by area, local yard
comparisons, contractor discounts, price history with an outlook, a shared
area quote index, and lumber takeoffs from uploaded house plans.

- `index.html` – the page, published as a claude.ai artifact. It uses the
  artifact runtime (`claude.use("sample" | "db" | "user")`), so it only runs
  fully inside claude.ai.
- `feed/ninjas_fetch.py` – the active feed. Pulls the CME lumber futures
  settlement from API Ninjas and writes the `market/daily` document the page
  reads. A free key adds one day per run; a premium key also backfills history.
- `feed/te_fetch.py` – alternative feed from the Trading Economics API.

## API keys

Keys are **never stored in this repo**. The feed scripts read them from the
macOS Keychain. Add a key in Terminal (it prompts, so the key never appears in
shell history):

```sh
security add-generic-password -U -a "$USER" -s api-ninjas -w
python3 feed/ninjas_fetch.py feed/market_daily.json
```

(`te_fetch.py` uses the Keychain service `tradingeconomics-api`.)

`market_daily.json` is git-ignored; it also holds the accumulated daily
history, so keep it between runs.
