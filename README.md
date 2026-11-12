# Lumber Economics

Lumber pricing for contractors and home builders: prices by area, local yard
comparisons, contractor discounts, price history with an outlook, a shared
area quote index, and lumber takeoffs from uploaded house plans.

- `index.html` – the page, published as a claude.ai artifact. It uses the
  artifact runtime (`claude.use("sample" | "db" | "user")`), so it only runs
  fully inside claude.ai.
- `feed/te_fetch.py` – pulls daily lumber futures closes from the Trading
  Economics API and writes the `market/daily` document the page reads.

## API key

The Trading Economics key is **never stored in this repo**. The feed script
reads it from the macOS Keychain:

```sh
security add-generic-password -a "$USER" -s tradingeconomics-api -w
python3 feed/te_fetch.py market_daily.json
```

`market_daily.json` is git-ignored.
