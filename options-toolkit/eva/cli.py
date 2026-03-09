"""Unified CLI — argparse setup and dispatch for all Eva commands."""

import argparse
import sys

from eva.commands import (
    cmd_buy,
    cmd_chain,
    cmd_evaluate,
    cmd_history,
    cmd_news,
    cmd_news_research,
    cmd_price,
    cmd_report,
    cmd_reset,
    cmd_sell,
    cmd_status,
    cmd_summary,
    cmd_trade_history,
)


def main():
    parser = argparse.ArgumentParser(description="Eva — options analysis and paper trading toolkit")
    parser.add_argument("--mode", choices=["paper", "real"], default="paper",
                        help="Trading mode (default: paper)")
    subparsers = parser.add_subparsers(dest="command")

    # ── Market data commands ─────────────────────────────────────────────────

    p_price = subparsers.add_parser("price", help="Current stock price")
    p_price.add_argument("--ticker", required=True)
    p_price.add_argument("--json", action="store_true")

    p_chain = subparsers.add_parser("chain", help="Options chain with IV")
    p_chain.add_argument("--ticker", required=True)
    p_chain.add_argument("--dte", type=int, default=120, help="Target DTE (default: 120)")
    p_chain.add_argument("--json", action="store_true")

    p_news = subparsers.add_parser("news", help="News headlines with sentiment")
    p_news.add_argument("--ticker", required=True)
    p_news.add_argument("--json", action="store_true")

    p_news_research = subparsers.add_parser("news-research", help="Deep news research with article extraction")
    p_news_research.add_argument("--ticker", required=True)
    p_news_research.add_argument("--max-articles", type=int, default=3)
    p_news_research.add_argument("--max-search", type=int, default=5)

    p_history = subparsers.add_parser("history", help="IV snapshot history")
    p_history.add_argument("--ticker", required=True)
    p_history.add_argument("--days", type=int, default=5)
    p_history.add_argument("--json", action="store_true")

    p_report = subparsers.add_parser("report", help="Full options analysis report")
    p_report.add_argument("--ticker", required=True)
    p_report.add_argument("--force", action="store_true", help="Bypass schedule check")
    p_report.add_argument("--json", action="store_true")

    p_summary = subparsers.add_parser("summary", help="End-of-day summary")
    p_summary.add_argument("--ticker", required=True)
    p_summary.add_argument("--force", action="store_true", help="Bypass schedule check")

    # ── Paper trading commands ───────────────────────────────────────────────

    p_evaluate = subparsers.add_parser("evaluate", help="Autonomous trading evaluation")
    p_evaluate_group = p_evaluate.add_mutually_exclusive_group(required=True)
    p_evaluate_group.add_argument("--ticker")
    p_evaluate_group.add_argument("--all", action="store_true")
    p_evaluate.add_argument("--force", action="store_true", help="Bypass market hours check")

    p_status = subparsers.add_parser("status", help="Paper trading portfolio status")

    p_buy = subparsers.add_parser("buy", help="Place a buy_to_open order")
    p_buy.add_argument("--ticker", required=True)
    p_buy.add_argument("--type", required=True, choices=["call", "put"])
    p_buy.add_argument("--strike", required=True, type=float)
    p_buy.add_argument("--expiry", required=True, help="YYYY-MM-DD")
    p_buy.add_argument("--quantity", type=int, default=1)
    p_buy.add_argument("--reason", required=True)

    p_sell = subparsers.add_parser("sell", help="Place a sell_to_close order")
    p_sell.add_argument("--ticker", required=True)
    p_sell.add_argument("--type", required=True, choices=["call", "put"])
    p_sell.add_argument("--strike", required=True, type=float)
    p_sell.add_argument("--expiry", required=True, help="YYYY-MM-DD")
    p_sell.add_argument("--quantity", type=int, default=1)
    p_sell.add_argument("--reason", required=True)

    p_trade_history = subparsers.add_parser("trade-history", help="Order history with reasoning")
    p_trade_history.add_argument("--limit", type=int, default=20)

    p_reset = subparsers.add_parser("reset", help="Cancel all orders and close positions (user-only)")
    p_reset.add_argument("--confirm", action="store_true", required=True)

    # ── Dispatch ─────────────────────────────────────────────────────────────

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    handlers = {
        "price": cmd_price,
        "chain": cmd_chain,
        "news": cmd_news,
        "news-research": cmd_news_research,
        "history": cmd_history,
        "report": cmd_report,
        "summary": cmd_summary,
        "evaluate": cmd_evaluate,
        "status": cmd_status,
        "buy": cmd_buy,
        "sell": cmd_sell,
        "trade-history": cmd_trade_history,
        "reset": cmd_reset,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
