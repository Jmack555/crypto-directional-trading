# Historical market data

The collector uses Coinbase Exchange's unauthenticated public candle endpoint (`/products/{product_id}/candles`). It requests bounded windows of at most 300 bars, supports 1m/5m/15m/1h/6h/1d bars, retries transient transport errors, normalizes timestamps to UTC, sorts and deduplicates candles, and writes the exact CSV format accepted by the backtester.

Download from the repository root after installing the package:

```bash
python -m crypto_directional.market_data BTC-USD \
  --start 2025-01-01T00:00:00Z --end 2025-02-01T00:00:00Z \
  --granularity 60 --output data/raw/BTC-USD-1m.csv
```

The same operation is available as a Python function:

```python
from datetime import UTC, datetime
from crypto_directional.market_data.history import (
    download_coinbase_history,
    write_candles_csv,
)

bars = download_coinbase_history(
    "BTC-USD",
    datetime(2025, 1, 1, tzinfo=UTC),
    datetime(2025, 2, 1, tzinfo=UTC),
    granularity=60,
)
write_candles_csv(bars, "data/raw/BTC-USD-1m.csv")
```

The collector does not silently fill missing bars. Check gaps, duplicates, timestamp alignment, symbol changes, and exchange outages before using a file for research. Public endpoints can rate-limit requests; the collector pauses between windows. Historical candles are venue-specific and do not represent executable order-book fills.

See the [Coinbase Exchange candles API](https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles) for current endpoint constraints.
