"""Evaluation builder and closed position detection for paper trading."""

import sys
from datetime import date, datetime

from eva import ET
from eva.analysis import _num, build_chain_summary, compute_iv_rank, compute_trends, score_sentiment
from eva.news import fetch_headlines
from eva.storage import (
    count_position_snapshots, load_iv_history, load_known_positions,
    load_market_history, load_news_history, load_position_snapshots,
    load_reasons, save_known_positions, save_market_snapshot,
    save_news_snapshot, save_position_snapshot,
)
from eva.symbols import parse_occ_symbol
from eva.tradier import (
    fetch_balances, fetch_chain_raw, fetch_expirations,
    fetch_history, fetch_orders, fetch_positions, fetch_quote,
)


def order_option_info(order):
    """Extract option_symbol and side from an order (top-level or leg)."""
    opt_sym = order.get("option_symbol", "")
    side = order.get("side", "")
    if not opt_sym:
        leg = order.get("leg", [])
        if isinstance(leg, dict):
            leg = [leg]
        for lg in leg:
            opt_sym = lg.get("option_symbol", "")
            side = side or lg.get("side", "")
            if opt_sym:
                break
    return opt_sym, side


def detect_recently_closed(mode, current_positions, orders):
    """Detect positions that disappeared from Tradier (closed/expired).

    Uses pre-fetched positions and orders to avoid redundant API calls.
    """
    known = load_known_positions(mode)
    current_symbols = {p.get("symbol") for p in current_positions}
    reasons = load_reasons(mode)

    recently_closed = []
    for sym, info in list(known.items()):
        if not info.get("reflected"):
            continue
        if sym not in current_symbols:
            open_reason = info.get("reason", "")
            close_reason = ""
            closed_how = "unknown"

            for order in orders:
                opt_sym, opt_side = order_option_info(order)
                if opt_sym == sym and opt_side == "sell_to_close":
                    closed_how = "sell_to_close"
                    oid = str(order.get("id", ""))
                    if oid in reasons:
                        close_reason = reasons[oid].get("reason", "")
                    break

            if closed_how == "unknown":
                parsed = parse_occ_symbol(sym)
                if parsed["expiry"] <= date.today().isoformat():
                    closed_how = "expired"

            recently_closed.append({
                "symbol": sym,
                "type": info.get("type", ""),
                "strike": info.get("strike", 0),
                "expiry": info.get("expiry", ""),
                "quantity": info.get("quantity", 1),
                "cost_basis": info.get("cost_basis", 0),
                "open_reason": open_reason,
                "close_reason": close_reason,
                "closed_how": closed_how,
                "needs_experience_update": True,
                "entry_market_context": info.get("market_context", {}),
                "position_snapshots": load_position_snapshots(mode, sym),
            })

    if recently_closed:
        for item in recently_closed:
            known.pop(item["symbol"], None)
        save_known_positions(mode, known)

    return recently_closed


def build_evaluate(cfg, ticker, mode, account=None, positions=None, orders=None):
    """Build the full evaluation JSON for a ticker.

    Accepts pre-fetched account/positions/orders to avoid redundant API calls
    when evaluating multiple tickers in a single cycle.
    """
    ticker = ticker.upper()
    result = {
        "timestamp": datetime.now(ET).isoformat(),
        "mode": mode,
        "ticker": ticker,
    }

    # Account — use pre-fetched or fetch once
    if account is not None:
        result["account"] = account
    else:
        try:
            account = fetch_balances(cfg)
            result["account"] = account
        except Exception as e:
            result["account"] = {"error": str(e)}

    # Positions/orders — use pre-fetched or fetch once
    if positions is None:
        try:
            positions = fetch_positions(cfg)
        except Exception as e:
            result["positions"] = {"error": str(e)}
            positions = []
    if orders is None:
        try:
            orders = fetch_orders(cfg)
        except Exception as e:
            orders = []

    # Fetch quote once for this ticker
    quote = {}
    current_price = 0
    try:
        quote = fetch_quote(cfg, ticker)
        current_price = quote.get("last", 0) or quote.get("close", 0) or 0
    except Exception:
        pass

    # Shared state used by position building and later snapshot recording
    known = {}
    chain_data = []
    target_exp = None

    # Build positions with entry context
    try:
        known = load_known_positions(mode)
        pos_list = []
        for p in positions:
            sym = p.get("symbol", "")
            parsed = parse_occ_symbol(sym) if sym else {}
            cost = p.get("cost_basis", 0) or 0
            mkt_val = (p.get("quantity", 0) or 0) * ((p.get("close", 0) or 0) * 100) if p.get("close") else 0
            if not mkt_val:
                mkt_val = cost
            unrealized = mkt_val - cost
            pnl_pct = round(unrealized / cost * 100, 1) if cost else 0

            entry_ctx = {}
            if sym in known:
                ki = known[sym]
                entry_ctx = {
                    "reason": ki.get("reason", ""),
                    "entry_price": ki.get("entry_price", 0),
                    "entry_iv": ki.get("entry_iv", 0),
                    "entry_date": ki.get("entry_date", ""),
                }
                # Include rich market context if available
                if ki.get("market_context"):
                    entry_ctx["market_context"] = ki["market_context"]
                pos_ticker = parsed.get("ticker", "")
                ctx_price = current_price if pos_ticker == ticker else 0
                if not ctx_price and pos_ticker:
                    try:
                        ctx_price = (fetch_quote(cfg, pos_ticker).get("last", 0) or 0)
                    except Exception:
                        pass
                if entry_ctx["entry_price"] and ctx_price:
                    entry_ctx["price_change_since_entry_pct"] = round(
                        (ctx_price - entry_ctx["entry_price"]) / entry_ctx["entry_price"] * 100, 1
                    )

            dte = 0
            if parsed.get("expiry"):
                try:
                    exp_date = datetime.strptime(parsed["expiry"], "%Y-%m-%d").date()
                    dte = (exp_date - date.today()).days
                except Exception:
                    pass

            pos_list.append({
                "symbol": sym,
                "type": parsed.get("type", ""),
                "strike": parsed.get("strike", 0),
                "expiry": parsed.get("expiry", ""),
                "dte": dte,
                "quantity": p.get("quantity", 0),
                "cost_basis": cost,
                "current_bid": p.get("close", 0),
                "market_value": mkt_val,
                "unrealized_pnl": round(unrealized, 2),
                "pnl_pct": pnl_pct,
                "entry_context": entry_ctx,
            })
        result["positions"] = pos_list

        # Update reflected status for positions now confirmed in Tradier
        updated = False
        for p in positions:
            sym = p.get("symbol", "")
            if sym in known and not known[sym].get("reflected"):
                known[sym]["reflected"] = True
                updated = True
        if updated:
            save_known_positions(mode, known)
    except Exception as e:
        result["positions"] = {"error": str(e)}

    # Recently closed
    try:
        result["recently_closed"] = detect_recently_closed(mode, positions, orders)
    except Exception as e:
        result["recently_closed"] = {"error": str(e)}

    # Market data
    try:
        change_pct = quote.get("change_percentage", 0) or 0
        if isinstance(change_pct, str):
            change_pct = float(change_pct.replace("%", ""))

        history_data = fetch_history(cfg, ticker, days=365)
        trends = compute_trends(history_data, current_price)

        # Get available expirations with DTE
        expirations = fetch_expirations(cfg, ticker)
        available_exps = []
        target_exp = None
        for exp in sorted(expirations):
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                dte = (exp_date - date.today()).days
                if dte >= 0:
                    available_exps.append({"date": exp, "dte": dte})
                if dte >= 120 and target_exp is None:
                    target_exp = exp
            except Exception:
                continue

        # Fetch chain for nearest 120+ DTE (used for IV analytics)
        chain_summary = {}
        chain_data = []
        if target_exp:
            chain_data = fetch_chain_raw(cfg, ticker, target_exp)
            chain_summary = build_chain_summary(chain_data, current_price)

        # Compute average Greeks for near-money options
        def _avg_greeks(options):
            keys = ("delta", "gamma", "theta", "vega", "rho")
            sums = {k: 0 for k in keys}
            count = 0
            for o in options:
                greeks = o.get("greeks") or {}
                if greeks.get("delta") is not None:
                    for k in keys:
                        sums[k] += greeks.get(k, 0) or 0
                    count += 1
            if not count:
                return None
            return {k: round(sums[k] / count, 4) for k in keys}

        margin = current_price * 0.05
        near_calls = [o for o in chain_data
                      if o.get("option_type") == "call"
                      and abs(o.get("strike", 0) - current_price) <= margin]
        near_puts = [o for o in chain_data
                     if o.get("option_type") == "put"
                     and abs(o.get("strike", 0) - current_price) <= margin]
        avg_call_greeks = _avg_greeks(near_calls)
        avg_put_greeks = _avg_greeks(near_puts)

        # Save market snapshot and compute IV rank
        avg_call_iv = chain_summary.get("avg_call_iv")
        avg_put_iv = chain_summary.get("avg_put_iv")
        if avg_call_iv and avg_call_iv > 0 and avg_put_iv and avg_put_iv > 0:
            save_market_snapshot(ticker, current_price, avg_call_iv, avg_put_iv,
                                avg_call_greeks=avg_call_greeks,
                                avg_put_greeks=avg_put_greeks, mode=mode)

        current_avg_iv = round(((avg_call_iv or 0) + (avg_put_iv or 0)) / 2, 1) if (avg_call_iv or avg_put_iv) else None
        iv_history = load_iv_history(ticker, mode=mode)
        # IV rank uses average of call+put IV for percentile positioning
        iv_rank, iv_percentile = compute_iv_rank(
            current_avg_iv,
            [(d, (c + p) / 2) for d, c, p in iv_history],
        )

        iv_context = {
            "current_avg_iv": current_avg_iv,
            "avg_call_iv": avg_call_iv,
            "avg_put_iv": avg_put_iv,
            "iv_rank": iv_rank,
            "iv_percentile": iv_percentile,
            "data_points": len(iv_history),
        }
        if iv_history:
            call_ivs = [c for _, c, _ in iv_history]
            put_ivs = [p for _, _, p in iv_history]
            avg_ivs = [(c + p) / 2 for _, c, p in iv_history]
            iv_context["iv_52w_high"] = round(max(avg_ivs), 1)
            iv_context["iv_52w_low"] = round(min(avg_ivs), 1)
            iv_context["call_iv_52w_high"] = round(max(call_ivs), 1)
            iv_context["call_iv_52w_low"] = round(min(call_ivs), 1)
            iv_context["put_iv_52w_high"] = round(max(put_ivs), 1)
            iv_context["put_iv_52w_low"] = round(min(put_ivs), 1)

        # Intraday context
        intraday_high = _num(quote.get("high")) or current_price
        intraday_low = _num(quote.get("low")) or current_price
        intraday_range = intraday_high - intraday_low
        intraday = {
            "open": _num(quote.get("open")) or current_price,
            "high": intraday_high,
            "low": intraday_low,
            "last": current_price,
            "change_pct": round(change_pct, 2),
            "range_position": round((current_price - intraday_low) / intraday_range * 100) if intraday_range > 0 else 50,
        }

        # Recent daily candles
        recent_days = []
        for d in history_data[-5:]:
            d_open = _num(d.get("open"))
            d_close = _num(d.get("close"))
            day_change = round((d_close - d_open) / d_open * 100, 2) if d_open and d_close and d_open > 0 else None
            recent_days.append({
                "date": d.get("date"),
                "open": d_open,
                "high": _num(d.get("high")),
                "low": _num(d.get("low")),
                "close": d_close,
                "change_pct": day_change,
            })
        recent_days.reverse()

        result["market"] = {
            "price": current_price,
            "change_pct": round(change_pct, 2),
            "intraday": intraday,
            "recent_days": recent_days,
            "trends": trends,
            "chain_summary": chain_summary,
            "chain_expiration": target_exp,
            "available_expirations": available_exps,
            "iv_context": iv_context,
        }

        # Affordable options
        settled = 0
        if isinstance(result.get("account"), dict) and "settled_cash" in result["account"]:
            settled = result["account"]["settled_cash"]

        affordable = []
        for opt in chain_data:
            ask = opt.get("ask", 0) or 0
            cost = ask * 100
            if cost > 0 and cost <= settled:
                greeks = opt.get("greeks", {})
                iv_val = greeks.get("mid_iv") or greeks.get("smv_vol", 0) or 0
                parsed = parse_occ_symbol(opt.get("symbol", "")) if opt.get("symbol") else {}
                dte = 0
                if target_exp:
                    try:
                        dte = (datetime.strptime(target_exp, "%Y-%m-%d").date() - date.today()).days
                    except Exception:
                        pass
                affordable.append({
                    "symbol": opt.get("symbol", ""),
                    "type": opt.get("option_type", ""),
                    "strike": opt.get("strike", 0),
                    "expiry": target_exp,
                    "dte": dte,
                    "bid": opt.get("bid", 0),
                    "ask": ask,
                    "iv": round(iv_val * 100, 1) if iv_val else 0,
                    "delta": round((greeks.get("delta", 0) or 0), 3),
                    "gamma": round((greeks.get("gamma", 0) or 0), 4),
                    "theta": round((greeks.get("theta", 0) or 0), 4),
                    "vega": round((greeks.get("vega", 0) or 0), 4),
                    "rho": round((greeks.get("rho", 0) or 0), 4),
                    "open_interest": opt.get("open_interest", 0) or 0,
                    "volume": opt.get("volume", 0) or 0,
                    "cost": round(cost, 2),
                })
        result["affordable_options"] = affordable

    except Exception as e:
        result["market"] = {"error": str(e)}
        result["affordable_options"] = []

    # Market history — recent days of price + IV + Greeks for pattern spotting
    try:
        result["market_history"] = load_market_history(ticker, days=14, mode=mode)
    except Exception:
        result["market_history"] = []

    # News — fetch fresh headlines every evaluate cycle via yfinance.
    # Deep news research is done separately (news-research command) only for
    # tickers Eva wants to buy or double down on.
    try:
        headlines = fetch_headlines(ticker)
        compact = [{"title": h["title"], "publisher": h["publisher"], "date": h["date"]}
                    for h in headlines]
        save_news_snapshot(mode, ticker, compact)

        score, label, themes, warnings = score_sentiment(
            [{"title": h.get("title", "")} for h in compact])
        result["news"] = {
            "headlines": compact,
            "sentiment": {"label": label, "score": score},
            "themes": themes,
            "warnings": warnings,
        }
    except Exception:
        result["news"] = {"headlines": [], "sentiment": None, "themes": [], "warnings": {}}

    try:
        result["news_history"] = load_news_history(mode, ticker, days=14)
    except Exception:
        result["news_history"] = []

    # Position snapshots — record option price/IV/greeks for open positions.
    # Enables hindsight analysis: Eva can see how a position evolved over time
    # and use that during experience building to refine entry/exit timing.
    try:
        ticker_positions = {sym: info for sym, info in known.items()
                           if info.get("ticker", "").upper() == ticker}
        current_symbols = {p.get("symbol") for p in positions}
        active_positions = {sym: info for sym, info in ticker_positions.items()
                          if sym in current_symbols}

        if active_positions:
            # Fetch chain data per unique expiry (reuse target_exp chain if available)
            chains_by_symbol = {}
            by_expiry = {}
            for sym, info in active_positions.items():
                exp = info.get("expiry", "")
                by_expiry.setdefault(exp, []).append(sym)

            for exp, syms in by_expiry.items():
                try:
                    if exp == target_exp and chain_data:
                        exp_chain = chain_data
                    else:
                        exp_chain = fetch_chain_raw(cfg, ticker, exp)
                    for opt in exp_chain:
                        if opt.get("symbol") in syms:
                            chains_by_symbol[opt["symbol"]] = opt
                except Exception:
                    pass

            for sym in active_positions:
                opt = chains_by_symbol.get(sym)
                if not opt:
                    continue

                pos_data = next((p for p in result.get("positions", [])
                                if isinstance(p, dict) and p.get("symbol") == sym), {})
                greeks = opt.get("greeks", {})
                iv_val = greeks.get("mid_iv") or greeks.get("smv_vol", 0) or 0
                snapshot = {
                    "underlying_price": current_price,
                    "dte": pos_data.get("dte", 0),
                    "cost_basis": active_positions[sym].get("cost_basis", 0),
                    "unrealized_pnl": pos_data.get("unrealized_pnl", 0),
                    "pnl_pct": pos_data.get("pnl_pct", 0),
                    "bid": opt.get("bid", 0) or 0,
                    "ask": opt.get("ask", 0) or 0,
                    "last": opt.get("last", 0) or 0,
                    "iv": round(iv_val * 100, 1) if iv_val else 0,
                    "greeks": {
                        "delta": round(greeks.get("delta", 0) or 0, 3),
                        "gamma": round(greeks.get("gamma", 0) or 0, 4),
                        "theta": round(greeks.get("theta", 0) or 0, 4),
                        "vega": round(greeks.get("vega", 0) or 0, 4),
                        "rho": round(greeks.get("rho", 0) or 0, 4),
                    },
                }

                save_position_snapshot(mode, sym, snapshot)
    except Exception as e:
        print(f"Warning: position snapshot recording failed: {e}", file=sys.stderr)

    # Add snapshot counts to position entries so Eva knows history depth
    if isinstance(result.get("positions"), list):
        for pos in result["positions"]:
            sym = pos.get("symbol", "")
            if sym:
                pos["snapshot_count"] = count_position_snapshots(mode, sym)

    return result
