"""CLI command handlers for options-toolkit.

All cmd_* functions extracted from toolkit.py and trading.py.
Each function receives an argparse Namespace and handles one subcommand.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from statistics import mean

from eva import DISCORD_CHANNEL, ET, MAJOR_DIV, SCRIPT_DIR
from eva.analysis import (
    compute_directional_score, compute_iv_rank, compute_rsi, compute_atr,
    compute_bollinger_bands, compute_trends, score_sentiment, _num,
)
from eva.evaluate import build_evaluate, fetch_spy_context
from eva.formatters import (
    format_chain,
    format_history_iv,
    format_iv_summary,
    format_news,
    format_price,
    format_report,
    format_status,
    format_summary,
    format_trade_history,
    is_scheduled_time,
    is_summary_time,
)
from eva.news import fetch_headlines, fetch_news, research
from eva.storage import (
    clear_pending_experience_updates,
    data_dir,
    load_closed_watches,
    load_history,
    load_iv_history,
    last_evaluate_age_seconds,
    load_known_positions,
    load_pending_experience_updates,
    load_position_snapshots,
    load_market_history,
    load_news_history,
    load_post_sale_snapshots,
    load_previous,
    load_reasons,
    log_event,
    save_closed_watches,
    save_known_positions,
    save_pending_experience_updates,
    save_reasons,
    save_snapshot,
)
from eva.symbols import build_occ_symbol, extract_greeks, parse_occ_symbol
from eva.tradier import (
    fetch_balances,
    fetch_chain_raw,
    fetch_history,
    fetch_options_chain,
    fetch_orders,
    fetch_positions,
    fetch_price,
    fetch_quote,
    is_market_open,
    load_config,
    normalize_list,
    tradier_delete,
    tradier_post,
)


# ── Private helpers ──────────────────────────────────────────────────────────

def _notify_discord(message):
    """Send a message to the paper-trading Discord channel."""
    try:
        subprocess.run(
            ["openclaw", "message", "send",
             "--channel", "discord",
             "--target", DISCORD_CHANNEL,
             "--message", message],
            timeout=15,
            capture_output=True,
        )
    except Exception as e:
        print(f"Warning: Discord notification failed: {e}", file=sys.stderr)


# ── Toolkit commands (from toolkit.py) ───────────────────────────────────────

def cmd_price(args):
    cfg = load_config(args.mode)
    sym = args.ticker.upper()
    try:
        data = fetch_price(cfg, sym)
    except Exception as e:
        print(f"Error fetching price for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        out = {
            "ticker": data["ticker"],
            "price": data["price"],
            "previous_close": data["previous_close"],
            "change": round(data["change"], 2),
            "change_pct": round(data["change_pct"], 2),
            "timestamp": data["timestamp_iso"],
        }
        print(json.dumps(out, indent=2))
    else:
        print(format_price(data))


def cmd_chain(args):
    cfg = load_config(args.mode)
    sym = args.ticker.upper()
    try:
        data = fetch_options_chain(cfg, sym, target_dte=args.dte)
    except Exception as e:
        print(f"Error fetching chain for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        out = {
            "ticker": data["ticker"],
            "expiry": data["expiry"],
            "dte": data["dte"],
            "atm_strike": data["atm_strike"],
            "current_price": data["current_price"],
            "calls": data["calls"],
            "puts": data["puts"],
        }
        print(json.dumps(out, indent=2))
    else:
        print(format_chain(data))


def cmd_news(args):
    cfg = load_config(args.mode)
    sym = args.ticker.upper()
    try:
        data = fetch_news(cfg, sym)
    except Exception as e:
        print(f"Error fetching news for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_news(data))


def cmd_news_research(args):
    """Run deep news research for a ticker."""
    ticker = args.ticker.upper()
    try:
        result = research(
            ticker,
            max_articles=args.max_articles,
            max_search=args.max_search,
            queries=args.query,
        )
    except Exception as e:
        print(f"Error running news research for {ticker}: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2))


def cmd_history(args):
    sym = args.ticker.upper()
    try:
        snapshots = load_history(sym, days=args.days, mode=args.mode)
    except Exception as e:
        print(f"Error loading history for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        out = {
            "ticker": sym,
            "days_requested": args.days,
            "days_found": len(snapshots),
            "snapshots": snapshots,
        }
        if len(snapshots) >= 2:
            newest = snapshots[0].get("overall_avg_iv", 0)
            oldest = snapshots[-1].get("overall_avg_iv", 0)
            change = newest - oldest
            if change > 2:
                direction = "EXPANDING"
            elif change < -2:
                direction = "CONTRACTING"
            else:
                direction = "STABLE"
            out["trend"] = {"direction": direction, "change": round(change, 2), "period_days": len(snapshots)}
        print(json.dumps(out, indent=2))
    else:
        print(format_history_iv(snapshots, sym))


def cmd_summary(args):
    sym = args.ticker.upper()
    try:
        output = format_summary(sym, mode=args.mode, force=args.force)
    except Exception as e:
        print(f"Error generating summary for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if output:
        print(output)


def cmd_report(args):
    cfg = load_config(args.mode)
    sym = args.ticker.upper()
    try:
        output = format_report(cfg, sym, mode=args.mode, force=args.force)
    except Exception as e:
        print(f"Error generating report for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if output:
        if args.json:
            # For JSON mode, build structured data
            chain_data = fetch_options_chain(cfg, sym)
            prev = load_previous(sym, mode=args.mode)
            calls = chain_data["calls"]
            puts = chain_data["puts"]
            avg_call_iv = mean([c["iv"] for c in calls]) if calls else 0
            avg_put_iv = mean([p["iv"] for p in puts]) if puts else 0
            overall = (avg_call_iv + avg_put_iv) / 2
            total_call_vol = sum(c["volume"] for c in calls)
            total_put_vol = sum(p["volume"] for p in puts)
            total_call_oi = sum(c["open_interest"] for c in calls)
            total_put_oi = sum(p["open_interest"] for p in puts)
            pc_vol = total_put_vol / total_call_vol if total_call_vol else None
            pc_oi = total_put_oi / total_call_oi if total_call_oi else None
            skew = avg_put_iv - avg_call_iv

            score_data = {
                "overall_avg_iv": overall,
                "skew": skew,
                "pc_vol_ratio": pc_vol,
                "pc_oi_ratio": pc_oi,
                "dte": chain_data["dte"],
                "overall_iv_change": (overall - prev.get("overall_avg_iv", overall)) if prev else None,
            }
            b, be = compute_directional_score(score_data)
            if b > be + 1:
                rec = "BUY CALLS"
            elif be > b + 1:
                rec = "BUY PUTS"
            else:
                rec = "WAIT OR STRADDLE"

            out = {
                "ticker": sym,
                "timestamp": chain_data["timestamp_iso"],
                "price": {
                    "current": chain_data["current_price"],
                    "prev_close": chain_data["previous_close"],
                    "change": round(chain_data["change"], 2),
                    "change_pct": round(chain_data["change_pct"], 2),
                },
                "expiry": {"date": chain_data["expiry"], "dte": chain_data["dte"]},
                "atm_strike": chain_data["atm_strike"],
                "calls": calls,
                "puts": puts,
                "iv_summary": {
                    "avg_call_iv": round(avg_call_iv, 2),
                    "avg_put_iv": round(avg_put_iv, 2),
                    "overall_avg_iv": round(overall, 2),
                    "skew": round(skew, 2),
                },
                "volumes": {
                    "total_call": total_call_vol,
                    "total_put": total_put_vol,
                    "pc_ratio": round(pc_vol, 2) if pc_vol else None,
                },
                "oi": {
                    "total_call": total_call_oi,
                    "total_put": total_put_oi,
                    "pc_ratio": round(pc_oi, 2) if pc_oi else None,
                },
                "directional_score": {"bullish": b, "bearish": be},
                "recommendation": rec,
                "previous_run": {
                    "timestamp": prev.get("timestamp") if prev else None,
                    "overall_avg_iv": prev.get("overall_avg_iv") if prev else None,
                },
            }
            print(json.dumps(out, indent=2))
        else:
            print(output)


# ── Trading commands (from trading.py) ───────────────────────────────────────

def cmd_evaluate(args):
    """Build evaluation JSON for one or all tickers."""
    cfg = load_config(args.mode)

    if not args.force and not is_market_open(cfg):
        sys.exit(0)

    # Guard: skip if evaluated less than 60 seconds ago (prevents duplicate calls)
    if not args.force:
        age = last_evaluate_age_seconds(args.mode)
        if age is not None and age < 60:
            print("Skipping evaluate: last run was {:.0f}s ago".format(age),
                  file=sys.stderr)
            sys.exit(0)

    # Determine ticker list
    if args.all:
        tickers_path = os.path.join(SCRIPT_DIR, "trading_tickers.json")
        with open(tickers_path) as f:
            tickers = [t.upper() for t in json.load(f)["tickers"]]
    else:
        if not args.ticker:
            print("Error: --ticker or --all required", file=sys.stderr)
            sys.exit(1)
        tickers = [args.ticker.upper()]

    # Pre-fetch account-level data once for all tickers
    try:
        account = fetch_balances(cfg)
    except Exception as e:
        account = {"error": str(e)}
    try:
        positions = fetch_positions(cfg)
    except Exception as e:
        positions = []
    try:
        orders = fetch_orders(cfg)
    except Exception as e:
        orders = []

    # Pre-fetch SPY context once for all tickers
    spy_context = fetch_spy_context(cfg, include_trends=True)

    # Evaluate each ticker (only quote/history/chain are per-ticker)
    results = []
    for ticker in tickers:
        try:
            result = build_evaluate(cfg, ticker, args.mode,
                                    account=account, positions=positions, orders=orders,
                                    spy_context=spy_context)
            results.append(result)
            log_event(args.mode, {"event": "evaluate", "ticker": ticker})
        except Exception as e:
            results.append({"ticker": ticker, "error": str(e)})
            print(f"Error evaluating {ticker}: {e}", file=sys.stderr)

    # Output: single object for one ticker, array for multiple
    if len(results) == 1:
        print(json.dumps(results[0], indent=2))
    else:
        print(json.dumps(results, indent=2))


def cmd_status(args):
    """Show formatted portfolio status."""
    cfg = load_config(args.mode)
    try:
        balances = fetch_balances(cfg)
        positions = fetch_positions(cfg)
        orders = fetch_orders(cfg)
        print(format_status(balances, positions, orders))
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_buy(args):
    """Place a buy_to_open order."""
    cfg = load_config(args.mode)
    ticker = args.ticker.upper()
    occ = build_occ_symbol(ticker, args.expiry, args.type, args.strike)

    try:
        # Get quote for entry context
        quote = fetch_quote(cfg, ticker)
        entry_price = quote.get("last", 0) or 0
        change_pct = quote.get("change_percentage", 0) or 0
        if isinstance(change_pct, str):
            change_pct = float(change_pct.replace("%", ""))

        # Get chain data — Greeks + ask price in one fetch
        entry_iv = 0
        option_greeks = {}
        ask_price = 0
        try:
            chain = fetch_chain_raw(cfg, ticker, args.expiry)
            for opt in chain:
                if opt.get("symbol") == occ:
                    entry_iv, option_greeks = extract_greeks(opt)
                    ask_price = opt.get("ask", 0) or 0
                    break
        except Exception:
            pass

        # Get IV context
        iv_context = {}
        try:
            iv_history = load_iv_history(ticker, mode=args.mode)
            if entry_iv and iv_history:
                avg_ivs = [(d, (c + p) / 2) for d, c, p in iv_history]
                iv_rank, iv_pct = compute_iv_rank(entry_iv, avg_ivs)
                all_ivs = [(c + p) / 2 for _, c, p in iv_history]
                iv_context = {
                    "iv_rank": iv_rank,
                    "iv_percentile": iv_pct,
                    "iv_52w_high": round(max(all_ivs), 1),
                    "iv_52w_low": round(min(all_ivs), 1),
                }
        except Exception:
            pass

        # Get price trends (full dict — includes RSI, ATR, Bollinger, volume, etc.)
        trends_snapshot = {}
        try:
            history_data = fetch_history(cfg, ticker, days=365)
            trends_snapshot = compute_trends(history_data, entry_price)
        except Exception:
            pass

        # Get broader market context (SPY)
        spy_context = fetch_spy_context(cfg) if ticker.upper() != "SPY" else {}

        # Save news headlines with trade context (lightweight — deep research
        # should have been done before deciding to buy)
        news_at_entry = []
        try:
            headlines = fetch_headlines(ticker, max_results=5)
            news_at_entry = [{"title": h["title"], "publisher": h["publisher"], "date": h["date"]}
                             for h in headlines]
        except Exception:
            pass

        # Place order
        resp = tradier_post(cfg, f"/accounts/{cfg['account_id']}/orders", {
            "class": "option",
            "symbol": ticker,
            "option_symbol": occ,
            "side": "buy_to_open",
            "quantity": args.quantity,
            "type": "market",
            "duration": "day",
        })

        order_id = str(resp.get("order", {}).get("id", ""))
        status = resp.get("order", {}).get("status", "unknown")
        print(f"Order placed: {occ} x{args.quantity} \u2014 {status} (ID: {order_id})")

        # Build rich market context
        market_context = {
            "price": entry_price,
            "change_pct": round(change_pct, 2),
            "iv": entry_iv,
            "option_greeks": option_greeks,
            "iv_context": iv_context,
            "trends": trends_snapshot,
            "news": news_at_entry,
            "broader_market": spy_context,
        }

        # Save reason with rich context
        reasons = load_reasons(args.mode)
        reasons[order_id] = {
            "reason": args.reason,
            "timestamp": datetime.now(ET).isoformat(),
            "side": "buy_to_open",
            "symbol": occ,
            "market_context": market_context,
        }
        save_reasons(args.mode, reasons)

        # Save known position with rich context (append to list for averaging)
        known = load_known_positions(args.mode)
        known.setdefault(occ, []).append({
            "order_id": order_id,
            "reason": args.reason,
            "entry_price": entry_price,
            "entry_iv": entry_iv,
            "entry_date": date.today().isoformat(),
            "ticker": ticker,
            "type": args.type,
            "strike": float(args.strike),
            "expiry": args.expiry,
            "quantity": args.quantity,
            "cost_basis": round(ask_price * 100 * args.quantity, 2),
            "reflected": False,
            "market_context": market_context,
        })
        save_known_positions(args.mode, known)

        log_event(args.mode, {
            "event": "order_placed",
            "order_id": order_id,
            "side": "buy_to_open",
            "symbol": occ,
            "quantity": args.quantity,
            "reason": args.reason,
        })

        # Notify Discord
        parsed = parse_occ_symbol(occ)
        try:
            exp_short = datetime.strptime(parsed["expiry"], "%Y-%m-%d").strftime("%b %d")
        except Exception:
            exp_short = parsed["expiry"]
        dte = (datetime.strptime(parsed["expiry"], "%Y-%m-%d").date() - date.today()).days
        msg = (
            f"\U0001f4b0 **BUY** {ticker} ${parsed['strike']} {parsed['type'].title()} \u2014 {exp_short} ({dte} DTE)\n"
            f"Qty: {args.quantity} | Cost: ${round(ask_price * 100 * args.quantity, 2):,.2f}\n"
            f"Reason: {args.reason}"
        )
        _notify_discord(msg)

    except Exception as e:
        print(f"Error placing buy order: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_sell(args):
    """Place a sell_to_close order."""
    cfg = load_config(args.mode)
    ticker = args.ticker.upper()
    occ = build_occ_symbol(ticker, args.expiry, args.type, args.strike)

    try:
        # Capture sell-time market context before placing order
        sell_price = 0
        sell_iv = 0
        sell_greeks = {}
        sell_underlying_price = 0
        try:
            quote = fetch_quote(cfg, ticker)
            sell_underlying_price = quote.get("last", 0) or 0
            chain = fetch_chain_raw(cfg, ticker, args.expiry)
            for opt in chain:
                if opt.get("symbol") == occ:
                    sell_price = opt.get("bid", 0) or 0
                    sell_iv, sell_greeks = extract_greeks(opt)
                    break
        except Exception as e:
            print(f"Warning: failed to capture sell-time market context: {e}", file=sys.stderr)

        resp = tradier_post(cfg, f"/accounts/{cfg['account_id']}/orders", {
            "class": "option",
            "symbol": ticker,
            "option_symbol": occ,
            "side": "sell_to_close",
            "quantity": args.quantity,
            "type": "market",
            "duration": "day",
        })

        order_id = str(resp.get("order", {}).get("id", ""))
        status = resp.get("order", {}).get("status", "unknown")
        print(f"Order placed: SELL {occ} x{args.quantity} \u2014 {status} (ID: {order_id})")

        # Save reason
        reasons = load_reasons(args.mode)
        reasons[order_id] = {
            "reason": args.reason,
            "timestamp": datetime.now(ET).isoformat(),
            "side": "sell_to_close",
            "symbol": occ,
        }
        save_reasons(args.mode, reasons)

        log_event(args.mode, {
            "event": "order_placed",
            "order_id": order_id,
            "side": "sell_to_close",
            "symbol": occ,
            "quantity": args.quantity,
            "reason": args.reason,
        })

        # Write pending experience update immediately so the next reflect
        # cycle can process it without waiting for detect_recently_closed.
        known = load_known_positions(args.mode)
        if occ in known:
            entries = known[occ]
            first = entries[0]
            open_reasons = [e.get("reason", "") for e in entries]
            open_reason = open_reasons[0] if len(open_reasons) == 1 else " | ".join(f"Buy {i+1}: {r}" for i, r in enumerate(open_reasons))
            total_cost = sum(e.get("cost_basis", 0) for e in entries)
            total_qty = sum(e.get("quantity", 1) for e in entries)
            pre_sale_snaps = load_position_snapshots(args.mode, occ)
            save_pending_experience_updates(args.mode, [{
                "symbol": occ,
                "type": first.get("type", ""),
                "strike": first.get("strike", 0),
                "expiry": first.get("expiry", ""),
                "quantity": total_qty,
                "cost_basis": total_cost,
                "open_reason": open_reason,
                "close_reason": args.reason,
                "closed_how": "sell_to_close",
                "needs_experience_update": True,
                "entry_market_context": first.get("market_context", {}),
                "buy_entries": entries,
                "position_snapshots": pre_sale_snaps,
                "pre_sale_analysis": _build_pre_sale_analysis(
                    pre_sale_snaps, total_cost, total_qty, sell_price),
            }])

            # Build rich sell market context (mirrors buy-time context)
            sell_trends = {}
            sell_spy_context = {}
            sell_iv_context = {}
            try:
                sell_history = fetch_history(cfg, ticker, days=365)
                sell_trends = compute_trends(sell_history, sell_underlying_price)
            except Exception:
                pass

            try:
                sell_iv_history = load_iv_history(ticker, mode=args.mode)
                if sell_iv_history and sell_iv:
                    iv_tuples = [(d, (c + p) / 2) for d, c, p in sell_iv_history]
                    s_rank, s_pct = compute_iv_rank(sell_iv, iv_tuples)
                    all_ivs = [(c + p) / 2 for _, c, p in sell_iv_history]
                    sell_iv_context = {
                        "iv_rank": s_rank,
                        "iv_percentile": s_pct,
                        "iv_52w_high": round(max(all_ivs), 1),
                        "iv_52w_low": round(min(all_ivs), 1),
                    }
            except Exception:
                pass

            try:
                if ticker.upper() != "SPY":
                    sell_spy_context = fetch_spy_context(cfg)
            except Exception:
                pass

            sell_market_context = {
                "underlying_price": sell_underlying_price,
                "option_price": sell_price,
                "iv": sell_iv,
                "greeks": sell_greeks,
                "iv_context": sell_iv_context,
                "trends": sell_trends,
                "broader_market": sell_spy_context,
            }
            watches = load_closed_watches(args.mode)
            watches[occ] = {
                "ticker": ticker,
                "type": args.type,
                "strike": float(args.strike),
                "expiry": args.expiry,
                "quantity": total_qty,
                "cost_basis": total_cost,
                "sell_date": date.today().isoformat(),
                "sell_proceeds": round(sell_price * 100 * total_qty, 2),
                "sell_price": sell_price,
                "sell_iv": sell_iv,
                "open_reason": open_reason,
                "close_reason": args.reason,
                "entry_market_context": first.get("market_context", {}),
                "sell_market_context": sell_market_context,
            }
            save_closed_watches(args.mode, watches)

            known.pop(occ)
            save_known_positions(args.mode, known)

        # Notify Discord
        parsed = parse_occ_symbol(occ)
        try:
            exp_short = datetime.strptime(parsed["expiry"], "%Y-%m-%d").strftime("%b %d")
        except Exception:
            exp_short = parsed["expiry"]
        msg = (
            f"\U0001f4e4 **SELL** {ticker} ${parsed['strike']} {parsed['type'].title()} \u2014 {exp_short}\n"
            f"Qty: {args.quantity}\n"
            f"Reason: {args.reason}"
        )
        _notify_discord(msg)

    except Exception as e:
        print(f"Error placing sell order: {e}", file=sys.stderr)
        sys.exit(1)


def _build_daily_trajectory(snapshots):
    """Condense 15-min snapshots into daily OHLC-style summaries."""
    by_date = {}
    for snap in snapshots:
        ts = snap.get("ts", "")
        day = ts[:10] if ts else ""
        if not day:
            continue
        by_date.setdefault(day, []).append(snap)

    trajectory = []
    for day in sorted(by_date):
        snaps = by_date[day]
        bids = [s.get("bid", 0) for s in snaps]
        ivs = [s.get("iv", 0) for s in snaps]
        underlyings = [s.get("underlying_price", 0) for s in snaps]
        close_greeks = snaps[-1].get("greeks", {})

        # Stock OHLC — use enriched fields if available, else synthesize
        # from underlying_price values (backward compat with old snapshots)
        stock_highs = [s["stock_high"] for s in snaps if s.get("stock_high")]
        stock_lows = [s["stock_low"] for s in snaps if s.get("stock_low")]

        entry = {
            "date": day,
            "bid_open": bids[0],
            "bid_high": max(bids),
            "bid_low": min(bids),
            "bid_close": bids[-1],
            "iv_open": ivs[0],
            "iv_close": ivs[-1],
            "underlying_open": snaps[0].get("stock_open") or underlyings[0],
            "underlying_high": max(stock_highs) if stock_highs else max(underlyings),
            "underlying_low": min(stock_lows) if stock_lows else min(underlyings),
            "underlying_close": underlyings[-1],
            "delta": close_greeks.get("delta", 0),
            "theta": close_greeks.get("theta", 0),
            "dte": snaps[-1].get("dte", 0),
            "snapshots": len(snaps),
        }
        # Stock volume — last snapshot has cumulative intraday volume
        stock_vol = snaps[-1].get("stock_volume")
        if stock_vol:
            entry["underlying_volume"] = stock_vol
        trajectory.append(entry)
    return trajectory


def _find_peak_trough(snapshots):
    """Find peak and trough bid prices from a list of snapshots.

    Skips zero bids for trough to avoid stale/bad quotes.
    Returns (peak_bid, peak_ts, peak_underlying,
             trough_bid, trough_ts, trough_underlying).
    """
    peak_bid = 0
    peak_ts = ""
    peak_underlying = 0
    trough_bid = float("inf")
    trough_ts = ""
    trough_underlying = 0
    for snap in snapshots:
        bid = snap.get("bid", 0)
        if bid > peak_bid:
            peak_bid = bid
            peak_ts = snap.get("ts", "")
            peak_underlying = snap.get("underlying_price", 0)
        if 0 < bid < trough_bid:
            trough_bid = bid
            trough_ts = snap.get("ts", "")
            trough_underlying = snap.get("underlying_price", 0)
    if trough_bid == float("inf"):
        trough_bid = 0
    return peak_bid, peak_ts, peak_underlying, trough_bid, trough_ts, trough_underlying


def _build_pre_sale_analysis(snapshots, cost_basis, qty, sell_price):
    """Analyze the position lifecycle between buy and sell.

    Builds a daily trajectory and identifies peak/trough during the hold
    so Eva can see if there was a better exit point before the actual sell.
    """
    if not snapshots:
        return {}

    daily_trajectory = _build_daily_trajectory(snapshots)

    (peak_bid, peak_ts, peak_underlying,
     trough_bid, trough_ts, trough_underlying) = _find_peak_trough(snapshots)

    peak_value = round(peak_bid * 100 * qty, 2)
    trough_value = round(trough_bid * 100 * qty, 2)

    return {
        "daily_trajectory": daily_trajectory,
        "peak_bid": peak_bid,
        "peak_date": peak_ts[:10] if peak_ts else "",
        "peak_value": peak_value,
        "peak_pnl": round(peak_value - cost_basis, 2) if cost_basis else 0,
        "peak_pnl_pct": round((peak_value - cost_basis) / cost_basis * 100, 1) if cost_basis else 0,
        "underlying_at_peak": peak_underlying,
        "trough_bid": trough_bid,
        "trough_date": trough_ts[:10] if trough_ts else "",
        "trough_value": trough_value,
        "underlying_at_trough": trough_underlying,
        "sold_near_peak": sell_price >= peak_bid * 0.95 if peak_bid else False,
        "snapshot_count": len(snapshots),
    }


def _find_key_moments(post_sale):
    """Extract full snapshots at peak, trough, and boundaries."""
    if not post_sale:
        return {}
    moments = {
        "first_after_sell": post_sale[0],
        "at_peak": max(post_sale, key=lambda s: s.get("bid", 0)),
        "at_trough": min(post_sale, key=lambda s: s.get("bid", 0)),
        "latest": post_sale[-1],
    }
    return moments


def _build_stock_context(cfg, ticker, sell_date, key_dates, history=None):
    """Build stock-level context for hindsight: trajectory + indicators at key dates.

    Accepts optional pre-fetched history to avoid redundant API calls.
    Slices and computes indicators at each key date so Eva can see what the
    stock was doing (not just the option).
    """

    if history is None:
        try:
            history = fetch_history(cfg, ticker, days=365)
        except Exception:
            return {}

    if not history:
        return {}

    # Stock trajectory: daily OHLCV from sell_date onward
    trajectory = []
    sell_idx = None
    for i, d in enumerate(history):
        if d["date"] >= sell_date:
            if sell_idx is None:
                sell_idx = i
            trajectory.append({
                "date": d["date"],
                "open": _num(d.get("open")),
                "high": _num(d.get("high")),
                "low": _num(d.get("low")),
                "close": _num(d.get("close")),
                "volume": int(_num(d.get("volume"))),
            })

    # Compute 50-day avg volume as of sell date for comparison
    if sell_idx is not None and sell_idx >= 50:
        pre_sell_vols = [int(_num(history[j].get("volume")))
                         for j in range(sell_idx - 50, sell_idx)]
        avg_vol = round(sum(pre_sell_vols) / len(pre_sell_vols))
    else:
        avg_vol = None

    # Compute indicators at each key date
    indicators_at_dates = {}
    for label, target_date in key_dates.items():
        if not target_date:
            continue
        # Find the index of this date (or nearest prior)
        idx = None
        for i, d in enumerate(history):
            if d["date"] <= target_date:
                idx = i
            else:
                break
        if idx is None:
            continue

        # Slice history up to this date and compute indicators
        slice_data = history[:idx + 1]
        closes = [_num(d.get("close")) for d in slice_data if _num(d.get("close")) > 0]

        entry = {"date": target_date}
        if closes:
            entry["price"] = closes[-1]
            rsi = compute_rsi(closes)
            if rsi is not None:
                entry["rsi_14"] = rsi
            atr = compute_atr(slice_data)
            if atr is not None:
                entry["atr_14"] = atr
            bb = compute_bollinger_bands(closes)
            if bb:
                entry["bollinger_pct_b"] = bb["pct_b"]
            if len(closes) >= 50:
                entry["sma_50"] = round(sum(closes[-50:]) / 50, 2)
            if len(closes) >= 200:
                entry["sma_200"] = round(sum(closes[-200:]) / 200, 2)

        indicators_at_dates[label] = entry

    result = {
        "stock_trajectory": trajectory,
        "avg_volume_50d": avg_vol,
        "indicators_at_key_dates": indicators_at_dates,
    }
    return result


def _load_context_around_dates(mode, ticker, target_dates, window=1):
    """Load news and market data around specific dates for investigation."""
    valid_dates = [d for d in target_dates if d]
    if not valid_dates:
        return {"news": {}, "market": {}}

    earliest = min(valid_dates)
    days_back = (date.today() - date.fromisoformat(earliest)).days + window + 1

    # Build set of dates we care about (+/- window days)
    relevant_dates = set()
    for d in valid_dates:
        base = date.fromisoformat(d)
        for offset in range(-window, window + 1):
            relevant_dates.add((base + timedelta(days=offset)).isoformat())

    news = {}
    try:
        all_news = load_news_history(mode, ticker, days=days_back)
        for entry in all_news:
            if entry["date"] in relevant_dates:
                news[entry["date"]] = [
                    h["title"] if isinstance(h, dict) else h
                    for h in entry.get("headlines", [])
                ]
    except Exception:
        pass

    market = {}
    try:
        all_market = load_market_history(ticker, days=days_back, mode=mode)
        for entry in all_market:
            if entry["date"] in relevant_dates:
                market[entry["date"]] = entry
    except Exception:
        pass

    return {"news": news, "market": market}


def cmd_hindsight(args):
    """Generate hindsight analysis for closed (sold) positions."""
    mode = args.mode
    watches = load_closed_watches(mode)

    if not watches:
        print(json.dumps([], indent=2))
        return

    # Filter by symbol if specified
    if args.symbol:
        sym = args.symbol.upper()
        if sym not in watches:
            print(f"Error: {sym} not in closed watches", file=sys.stderr)
            sys.exit(1)
        watches = {sym: watches[sym]}

    # Filter expired-only if requested
    if args.expired_only:
        watches = {s: w for s, w in watches.items()
                   if w.get("expiry", "9999") <= date.today().isoformat()}

    # Clear expired watches — skip analysis, just clean up.
    # Re-load the full set so prior --symbol/--expired-only filtering
    # doesn't cause non-matching watches to be silently deleted.
    if args.clear_expired:
        all_watches = load_closed_watches(mode)
        expired_symbols = [sym for sym, w in all_watches.items()
                           if w.get("expiry", "9999") <= date.today().isoformat()]
        if expired_symbols:
            for sym in expired_symbols:
                all_watches.pop(sym, None)
                snap_path = os.path.join(data_dir(mode), "post-sale-snapshots", f"{sym}.jsonl")
                if os.path.exists(snap_path):
                    os.remove(snap_path)
            save_closed_watches(mode, all_watches)
        print(f"Cleared {len(expired_symbols)} expired watches.")
        return

    cfg = load_config(mode)

    # Pre-fetch history per ticker (avoid redundant API calls for same ticker)
    history_cache = {}

    results = []
    for symbol, watch in watches.items():
        cost_basis = watch.get("cost_basis", 0)
        sell_proceeds = watch.get("sell_proceeds", 0)
        realized_pnl = sell_proceeds - cost_basis
        realized_pnl_pct = round(realized_pnl / cost_basis * 100, 1) if cost_basis else 0

        expired = watch.get("expiry", "9999") <= date.today().isoformat()

        # Load pre-sale and post-sale snapshots
        pre_sale = load_position_snapshots(mode, symbol)
        post_sale = load_post_sale_snapshots(mode, symbol)

        # Pre-sale analysis — what happened during the hold (was there a better exit?)
        pre_sale_analysis = _build_pre_sale_analysis(
            pre_sale, cost_basis, watch.get("quantity", 1), watch.get("sell_price", 0))

        # Compute counterfactual from post-sale snapshots
        counterfactual = {}
        if post_sale:
            qty = watch.get("quantity", 1)
            # Current/final value
            latest = post_sale[-1]
            latest_bid = latest.get("bid", 0)
            hold_to_now_value = round(latest_bid * 100 * qty, 2)
            hold_to_now_pnl = round(hold_to_now_value - cost_basis, 2)
            hold_to_now_pnl_pct = round(hold_to_now_pnl / cost_basis * 100, 1) if cost_basis else 0

            # Peak and trough after sale
            (peak_bid, peak_ts, peak_underlying,
             trough_bid, trough_ts, trough_underlying) = _find_peak_trough(post_sale)

            peak_value = round(peak_bid * 100 * qty, 2)
            trough_value = round(trough_bid * 100 * qty, 2)

            counterfactual = {
                "hold_to_now_value": hold_to_now_value,
                "hold_to_now_pnl": hold_to_now_pnl,
                "hold_to_now_pnl_pct": hold_to_now_pnl_pct,
                "missed_upside": round(peak_value - sell_proceeds, 2),
                "avoided_downside": round(sell_proceeds - trough_value, 2),
                "peak_value_after_sale": peak_value,
                "peak_date": peak_ts[:10] if peak_ts else "",
                "underlying_at_peak": peak_underlying,
                "trough_value_after_sale": trough_value,
                "trough_date": trough_ts[:10] if trough_ts else "",
                "underlying_at_trough": trough_underlying,
                "sell_was_optimal": sell_proceeds >= hold_to_now_value,
                "post_sale_snapshots_count": len(post_sale),
            }

        # Current or final state
        current_or_final = {}
        if post_sale:
            latest = post_sale[-1]
            current_or_final = {
                "price": latest.get("bid", 0),
                "iv": latest.get("iv", 0),
                "underlying_price": latest.get("underlying_price", 0),
                "dte": latest.get("dte", 0),
                "greeks": latest.get("greeks", {}),
            }

        # Daily trajectory — condense 15-min snapshots into daily summaries
        daily_trajectory = _build_daily_trajectory(post_sale)

        # Key moment snapshots — full data at peak, trough, boundaries
        key_moments = _find_key_moments(post_sale)

        # News and market context around key dates (sell, peak, trough)
        key_dates_list = [
            watch.get("sell_date", ""),
            counterfactual.get("peak_date", "") if counterfactual else "",
            counterfactual.get("trough_date", "") if counterfactual else "",
        ]
        context = _load_context_around_dates(
            mode, watch.get("ticker", ""), key_dates_list)

        # Stock context — what the STOCK did during the hold and after the sell
        ticker_name = watch.get("ticker", "")
        if ticker_name and ticker_name not in history_cache:
            try:
                history_cache[ticker_name] = fetch_history(cfg, ticker_name, days=365)
            except Exception:
                history_cache[ticker_name] = []

        # Derive entry date from first pre-sale snapshot or buy entries
        entry_date = ""
        if pre_sale:
            entry_date = pre_sale[0].get("ts", "")[:10]

        # Post-sale stock context (sell → now)
        stock_context = {}
        try:
            stock_context = _build_stock_context(
                cfg, ticker_name,
                watch.get("sell_date", ""),
                {
                    "at_sell": watch.get("sell_date", ""),
                    "at_peak": counterfactual.get("peak_date", "") if counterfactual else "",
                    "at_trough": counterfactual.get("trough_date", "") if counterfactual else "",
                    "latest": date.today().isoformat(),
                },
                history=history_cache.get(ticker_name),
            )
        except Exception:
            pass

        # Hold-period stock context (entry → sell)
        hold_stock_context = {}
        if entry_date:
            try:
                hold_stock_context = _build_stock_context(
                    cfg, ticker_name,
                    entry_date,
                    {
                        "at_entry": entry_date,
                        "at_option_peak": pre_sale_analysis.get("peak_date", ""),
                        "at_option_trough": pre_sale_analysis.get("trough_date", ""),
                        "at_sell": watch.get("sell_date", ""),
                    },
                    history=history_cache.get(ticker_name),
                )
            except Exception:
                pass

        result = {
            "symbol": symbol,
            "ticker": ticker_name,
            "type": watch.get("type", ""),
            "strike": watch.get("strike", 0),
            "expiry": watch.get("expiry", ""),
            "sell_date": watch.get("sell_date", ""),
            "sell_price": watch.get("sell_price", 0),
            "sell_iv": watch.get("sell_iv", 0),
            "cost_basis": cost_basis,
            "sell_proceeds": sell_proceeds,
            "realized_pnl": round(realized_pnl, 2),
            "realized_pnl_pct": realized_pnl_pct,
            "expired": expired,
            "current_or_final": current_or_final,
            "counterfactual": counterfactual,
            "open_reason": watch.get("open_reason", ""),
            "close_reason": watch.get("close_reason", ""),
            "entry_market_context": watch.get("entry_market_context", {}),
            "sell_market_context": watch.get("sell_market_context", {}),
            "pre_sale_analysis": pre_sale_analysis,
            "hold_stock_context": hold_stock_context,
            "stock_context": stock_context,
            "daily_trajectory": daily_trajectory,
            "key_moments": key_moments,
            "news_around_key_dates": context["news"],
            "market_around_key_dates": context["market"],
            "post_sale_snapshot_count": len(post_sale),
        }
        results.append(result)

    print(json.dumps(results if len(results) != 1 else results[0], indent=2))


def cmd_pending_experience(args):
    """Show or clear pending experience updates."""
    if args.clear:
        clear_pending_experience_updates(args.mode)
        print("Pending experience updates cleared.")
    else:
        updates = load_pending_experience_updates(args.mode)
        print(json.dumps(updates, indent=2))


def cmd_trade_history(args):
    """Show order history with reasoning."""
    cfg = load_config(args.mode)
    try:
        orders = fetch_orders(cfg, limit=args.limit)
        reasons = load_reasons(args.mode)
        print(format_trade_history(orders, reasons, limit=args.limit))
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_reset(args):
    """Reset: cancel orders, close positions, archive local data."""
    if not args.confirm:
        print("Error: --confirm flag required for reset", file=sys.stderr)
        sys.exit(1)

    cfg = load_config(args.mode)
    mode = args.mode

    # Archive reasons.json
    reasons_path = os.path.join(data_dir(mode), "reasons.json")
    if os.path.exists(reasons_path):
        archive = os.path.join(data_dir(mode), f"reasons.{date.today().isoformat()}.json")
        shutil.copy2(reasons_path, archive)
        print(f"Archived reasons to {archive}")

    # Cancel open orders
    try:
        orders = fetch_orders(cfg)
        for o in orders:
            if o.get("status") in ("pending", "open", "partially_filled"):
                oid = o.get("id")
                try:
                    tradier_delete(cfg, f"/accounts/{cfg['account_id']}/orders/{oid}")
                    print(f"Canceled order {oid}")
                except Exception as e:
                    print(f"Failed to cancel order {oid}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error fetching orders for cancel: {e}", file=sys.stderr)

    # Close all positions
    try:
        positions = fetch_positions(cfg)
        for p in positions:
            sym = p.get("symbol", "")
            qty = abs(p.get("quantity", 0))
            if not sym or not qty:
                continue
            parsed = parse_occ_symbol(sym)
            try:
                tradier_post(cfg, f"/accounts/{cfg['account_id']}/orders", {
                    "class": "option",
                    "symbol": parsed["ticker"],
                    "option_symbol": sym,
                    "side": "sell_to_close",
                    "quantity": qty,
                    "type": "market",
                    "duration": "day",
                })
                print(f"Closed position {sym} x{qty}")
            except Exception as e:
                print(f"Failed to close {sym}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error fetching positions for close: {e}", file=sys.stderr)

    # Clear local data
    for fname in ("reasons.json", "known_positions.json", "closed_watches.json"):
        path = os.path.join(data_dir(mode), fname)
        if os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f)
    clear_pending_experience_updates(mode)
    for snap_dir in ("position-snapshots", "post-sale-snapshots"):
        path = os.path.join(data_dir(mode), snap_dir)
        if os.path.isdir(path):
            shutil.rmtree(path)

    log_event(mode, {"event": "reset"})
    print("Reset complete.")
