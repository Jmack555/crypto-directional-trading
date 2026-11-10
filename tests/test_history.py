from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from crypto_directional.market_data.history import (
    download_coinbase_history,
    write_candles_csv,
)


def test_downloads_and_sorts_coinbase_candles():
    start = datetime(2025, 1, 1, tzinfo=UTC)
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return [
            [start.timestamp() + 60, 99, 102, 100, 101, 12],
            [start.timestamp(), 98, 101, 99, 100, 10],
        ]

    candles = download_coinbase_history(
        "BTC-USD", start, start + timedelta(minutes=2),
        fetch_page=fake_fetch, pause_seconds=0,
    )

    assert len(candles) == 2
    assert candles[0].timestamp == start
    assert candles[1].close == 101
    params = parse_qs(urlparse(calls[0]).query)
    assert params["granularity"] == ["60"]


def test_download_rejects_invalid_ranges_and_intervals():
    now = datetime(2025, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="earlier"):
        download_coinbase_history("BTC-USD", now, now, fetch_page=lambda _: [])
    with pytest.raises(ValueError, match="granularity"):
        download_coinbase_history(
            "BTC-USD", now, now + timedelta(hours=1), 120,
            fetch_page=lambda _: [],
        )


def test_csv_output_matches_backtester_schema(tmp_path):
    from crypto_directional.backtest.engine import Candle

    start = datetime(2025, 1, 1, tzinfo=UTC)
    candles = [Candle(start, 100, 101, 99, 100, 5)]
    path = tmp_path / "nested" / "candles.csv"
    write_candles_csv(candles, path)
    lines = path.read_text().splitlines()
    assert lines[0] == "timestamp,open,high,low,close,volume"
    assert lines[1].startswith("2025-01-01T00:00:00Z,")
