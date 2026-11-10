from __future__ import annotations

import argparse
from datetime import datetime

from .history import download_coinbase_history, write_candles_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Coinbase Exchange OHLCV history")
    parser.add_argument("product", help="Coinbase product id, e.g. BTC-USD")
    parser.add_argument("--start", required=True, help="ISO-8601 start timestamp with timezone")
    parser.add_argument("--end", required=True, help="ISO-8601 end timestamp with timezone")
    parser.add_argument(
        "--granularity", type=int, default=60,
        choices=[60, 300, 900, 3600, 21600, 86400],
    )
    parser.add_argument("--output", required=True, help="Destination CSV path")
    args = parser.parse_args()

    candles = download_coinbase_history(
        args.product,
        datetime.fromisoformat(args.start),
        datetime.fromisoformat(args.end),
        granularity=args.granularity,
    )
    write_candles_csv(candles, args.output)
    print(f"Wrote {len(candles)} candles to {args.output}")


if __name__ == "__main__":
    main()
