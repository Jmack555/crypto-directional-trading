# Market-data and execution benchmark plan

## What to optimize

Measure separately: exchange event timestamp to local receive time, WebSocket reconnect/gap rate, event processing time, signal-to-order-intent time, order acknowledgement, fill latency, realized spread, fees, slippage, and missed/partial fills. Report p50/p95/p99 by venue, symbol, message type, and hour. Never compare a vendor's median snapshot age with our end-to-end order latency as if they were equivalent.

## Initial live-data stack

1. Start with Coinbase's public Exchange WebSocket `ticker` and `heartbeat` channels for a small USD-quoted universe. Public feed needs no API key. Use the official `wss://ws-feed.exchange.coinbase.com` endpoint; Coinbase also documents an authenticated direct-market-data endpoint, which is a separate tier to benchmark rather than assume is faster for our account.
2. Add Kraken WebSocket v2 public `trade`, `ticker`, and `book` feeds as a second independent source after the first adapter is stable. Kraken documents `wss://ws.kraken.com/v2`; book updates must be applied in sequence and checksum-validated.
3. Compare actual feeds from the intended hosting regions. Keep an independent receive timestamp using a monotonic clock and preserve the exchange timestamp. Do not infer feed freshness from REST ping times.
4. Evaluate Tardis.dev for replay-quality historical trades/order-book data and feed cross-checks. Purchase only after an instrument/retention/throughput trial demonstrates value; it is not selected as the primary live feed yet.

## Hosting hypothesis

A public benchmark measured Coinbase REST API latency at 17.8 ms from Newark and Kraken at 19.9 ms from London in its tested deployment set. Another US-East test on 2026-11-10 reported Coinbase HTTP p95 16.51 ms and Kraken 20.28 ms, but it also reported inconsistent/blocked access for some global venues. These are directional reference points, not guarantees or WebSocket measurements. Benchmark a small VPS in US-East against at least one alternate region using our own persistent connections before committing to hosting.

## Required feed quality gates

- Reject signals if event age exceeds configured threshold or the feed is disconnected.
- Detect sequence gaps where the exchange protocol exposes sequence numbers; rebuild snapshots before resuming.
- Track heartbeat and per-symbol coverage. A connected socket with no useful updates is not healthy by itself.
- Persist raw event, exchange timestamp, receive timestamp, adapter version, and normalized event.
- Reconnect with jittered exponential backoff; never trade on stale cached prices.
- Preserve out-of-order and duplicate events for diagnosis; do not silently fabricate missing bars.

## Strategy/execution implications

The intended 1–120 minute holding period does not require sub-millisecond HFT infrastructure. Correct data, stable tails, liquidity, and realistic execution-cost modelling are more valuable than paying for co-location before a repeatable edge exists. A 5–20 ms HTTP benchmark does not prove a profitable signal or a fill at the displayed quote.

## Research gates

No paid feed or production hosting decision until measured symbol coverage, event rate, p95/p99 age, outage behavior, retention, historical depth, and total cost are recorded. No live order path until point-in-time backtests, out-of-sample tests, paper trading, reconciliation, and operator approval pass.