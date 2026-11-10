from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .engine import BacktestConfig, load_csv, run_backtest


def main() -> None:
    parser = argparse.ArgumentParser(description="Causal EMA/ATR spot backtest")
    parser.add_argument("csv", help="OHLCV CSV: timestamp,open,high,low,close,volume")
    parser.add_argument("--equity", type=float, default=500.0)
    parser.add_argument("--fee-bps", type=float, default=40.0, help="maker/taker fee per side")
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--spread-bps", type=float, default=4.0, help="full spread")
    args = parser.parse_args()
    cfg = BacktestConfig(initial_equity=args.equity, fee_bps_per_side=args.fee_bps,
                         slippage_bps_per_side=args.slippage_bps, spread_bps=args.spread_bps)
    result = run_backtest(load_csv(args.csv), cfg)
    summary = asdict(result)
    summary.pop("trades")
    summary["profit_factor"] = result.profit_factor if result.profit_factor != float("inf") else "infinity"
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
