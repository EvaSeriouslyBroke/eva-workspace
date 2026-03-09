"""CLI command handlers for options-toolkit.

All cmd_* functions extracted from toolkit.py and trading.py.
Each function receives an argparse Namespace and handles one subcommand.
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime
from statistics import mean

from eva import DISCORD_CHANNEL, ET, MAJOR_DIV, SCRIPT_DIR
from eva.analysis import compute_directional_score, score_sentiment
from eva.evaluate import build_evaluate
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
from eva.news import fetch_news, research
from eva.storage import (
    data_dir,
    load_history,
    load_iv_history,
    load_known_positions,
    load_previous,
    load_reasons,
    log_event,
    save_known_positions,
    save_reasons,
    save_snapshot,
)
from eva.symbols import build_occ_symbol, parse_occ_symbol
from eva.news import fetch_headlines
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

    # Evaluate each ticker (only quote/history/chain are per-ticker)
    results = []
    for ticker in tickers:
        try:
            result = build_evaluate(cfg, ticker, args.mode,
                                    account=account, positions=positions, orders=orders)
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

    # Duplicate check
    positions = fetch_positions(cfg)
    for p in positions:
        if p.get("symbol") == occ:
            print(f"Error: duplicate position exists for {occ}", file=sys.stderr)
            sys.exit(1)

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
                    greeks = opt.get("greeks", {})
                    entry_iv = round((greeks.get("mid_iv") or greeks.get("smv_vol", 0) or 0) * 100, 1)
                    option_greeks = {
                        "delta": round(greeks.get("delta", 0) or 0, 3),
                        "gamma": round(greeks.get("gamma", 0) or 0, 4),
                        "theta": round(greeks.get("theta", 0) or 0, 4),
                        "vega": round(greeks.get("vega", 0) or 0, 4),
                        "rho": round(greeks.get("rho", 0) or 0, 4),
                    }
                    ask_price = opt.get("ask", 0) or 0
                    break
        except Exception:
            pass

        # Get IV context
        iv_context = {}
        try:
            from eva.analysis import compute_iv_rank
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

        # Get price trends
        trends_snapshot = {}
        try:
            from eva.analysis import compute_trends
            history_data = fetch_history(cfg, ticker, days=365)
            trends = compute_trends(history_data, entry_price)
            trends_snapshot = {
                "sma_signal": trends.get("sma_signal"),
                "sma_50": trends.get("sma_50"),
                "sma_200": trends.get("sma_200"),
                "price_vs_52w_pct": trends.get("price_vs_52w_pct"),
                "price_52w_high": trends.get("price_52w_high"),
                "price_52w_low": trends.get("price_52w_low"),
                "returns": trends.get("returns", {}),
                "trend_summary": trends.get("trend_summary"),
            }
        except Exception:
            pass

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

        # Save known position with rich context
        known = load_known_positions(args.mode)
        known[occ] = {
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
        }
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
        import shutil
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
    for fname in ("reasons.json", "known_positions.json"):
        path = os.path.join(data_dir(mode), fname)
        if os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f)

    log_event(mode, {"event": "reset"})
    print("Reset complete.")
