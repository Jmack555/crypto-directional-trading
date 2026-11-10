"""Historical OHLCV ingestion from Coinbase Exchange's public REST API.

The API returns at most 300 candles per request. The downloader uses bounded
windows, retries transient HTTP failures, deduplicates timestamps, and writes
the same CSV schema consumed by the backtester.
"""
from __future__ import annotations

import csv
import json
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from crypto_directional.backtest.engine import Candle

BASE_URL = "https://api.exchange.coinbase.com"
ALLOWED_GRANULARITIES = {60, 300, 900, 3600, 21600, 86400}


def _request_json(url: str) -> list[list[float]]:
    request = Request(url, headers={"User-Agent": "crypto-directional-research/0.1"})
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read())
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected Coinbase response: {payload!r}")
    return payload


def download_coinbase_history(
    product_id: str,
    start: datetime,
    end: datetime,
    granularity: int = 60,
    fetch_page: Callable[[str], list[list[float]]] = _request_json,
    pause_seconds: float = 0.25,
    max_retries: int = 3,
) -> list[Candle]:
    """Download candles for [start, end); all datetimes must be timezone-aware."""
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start and end must be timezone-aware")
    if start >= end:
        raise ValueError("start must be earlier than end")
    if granularity not in ALLOWED_GRANULARITIES:
        raise ValueError(f"unsupported granularity: {granularity}")
    if not product_id or "/" in product_id:
        raise ValueError("invalid Coinbase product id")
    if pause_seconds < 0 or max_retries < 0:
        raise ValueError("pause_seconds and max_retries cannot be negative")

    cursor = start.astimezone(UTC)
    finish = end.astimezone(UTC)
    step = timedelta(seconds=granularity)
    candles_by_time: dict[datetime, Candle] = {}

    while cursor < finish:
        window_end = min(cursor + step * 299, finish)
        query = urlencode({
            "start": cursor.isoformat().replace("+00:00", "Z"),
            "end": window_end.isoformat().replace("+00:00", "Z"),
            "granularity": granularity,
        })
        url = f"{BASE_URL}/products/{product_id}/candles?{query}"
        for attempt in range(max_retries + 1):
            try:
                rows = fetch_page(url)
                break
            except (HTTPError, URLError, TimeoutError):
                if attempt == max_retries:
                    raise
                time.sleep(min(2**attempt, 8))
        if len(rows) > 300:
            raise ValueError("Coinbase returned more than 300 candles for one request")
        for row in rows:
            if len(row) != 6:
                raise ValueError(f"Malformed Coinbase candle: {row!r}")
            stamp, low, high, open_, close, volume = row
            candle = Candle(
                timestamp=datetime.fromtimestamp(int(stamp), tz=UTC),
                open=float(open_),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=float(volume),
            )
            if cursor <= candle.timestamp < finish:
                candles_by_time[candle.timestamp] = candle
        cursor = window_end + step
        if cursor < finish and pause_seconds:
            time.sleep(pause_seconds)

    return [candles_by_time[key] for key in sorted(candles_by_time)]


def write_candles_csv(candles: list[Candle], path: str | Path) -> None:
    """Write chronological candles using the backtester's standard CSV schema."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for candle in candles:
            writer.writerow([
                candle.timestamp.isoformat().replace("+00:00", "Z"),
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            ])
