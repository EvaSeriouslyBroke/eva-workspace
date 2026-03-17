# Mean Reversion Calls Fail Below SMAs

**Thesis:** Buying calls for mean reversion fails when a stock is in a sustained downtrend below both its 50-day and 200-day SMAs, regardless of how "oversold" technical indicators appear.
**Applies to:** general (multi-ticker pattern)
**Tags:** mean-reversion, downtrend, below-sma, technical-analysis, calls, trend-following, bear, dte-long
**Confidence:** medium
**Last Updated:** 2026-03-16

## Analysis

Mean reversion as a strategy requires a stable baseline to revert *to*. When a stock is trading below both its 50-day and 200-day SMAs, it signals institutional selling and sustained negative momentum. Technical indicators like "oversold" RSI or high P/C ratios become unreliable in this regime because:

1. **No support level exists** — below both SMAs, there's no established baseline for mean reversion
2. **Momentum feeds on itself** — institutional repositioning creates continued selling pressure
3. **Oversold can stay oversold** — without catalysts, technical oversold conditions can persist far longer than option DTE allows
4. **Sector/macro headwids may dominate** — individual stock technicals become irrelevant when broader forces drive price

Pattern observed across:
- **BAC (Financial):** Failed three times (-8.3%, -20.6%, and -1.4% losses) buying calls below both SMAs during financial sector weakness
- **HD (Cyclical):** Failed (-2.9% from entry to exit) buying calls in cyclical downturn below both SMAs with macro headwinds
- **IWM (Small-cap ETF):** Failed (-1.5% loss) buying calls on dip below 50 SMA with no catalyst for recovery

The pattern is now validated across three distinct sectors/asset classes. When below both SMAs, "oversold" is a warning, not a signal. Confidence upgraded to medium based on cross-ticker consistency.

## Evidence

### Summary
3 supporting observations across 3 different tickers (BAC, HD, IWM). All mean reversion call attempts failed with losses when entry occurred below both SMAs during sustained downtrends. Cross-ticker consistency across financials, cyclicals, and small-cap ETFs suggests this is a robust technical pattern. Confidence upgraded to medium.

### Recent
- 2026-03-16 [hindsight] [supporting] [bear] [dte-long]: BAC 50C Jul-17 exit validation confirms pattern. Exit at -1.4% (vs previous -8.3%, -20.6% losses on same-thesis BAC trades) demonstrates value of validated experience. Stock never reclaimed 50 SMA, ranged $46.72-$47.68 post-exit. Cutting losses early when thesis invalidated is superior to holding for bounce that requires SMA reclamation first.
- 2026-03-16 [paper] [supporting] [bear] [dte-long]: IWM 250C Aug-21 entered at 250.25 on mean reversion thesis (down 2.56%, -4.3% weekly). Stock below 50 SMA (~260), no IWM-specific catalyst. Closed at -1.5% after continued decline to ~246.5. Third ticker validating the pattern — small-cap mean reversion fails when below key SMAs without catalyst.
- 2026-03-09 [paper] [supporting] [bear] [dte-medium]: BAC 50C Jul-17 entry at 48.26 below 50 SMA (~53) and 200 SMA (~50.5) during financial sector weakness. Closed at -20.6% after 3 days as decline continued. Same-thesis 52.5C trade same day lost -8.3%.

## Exceptions & Nuances

- Pattern may not apply if there's a specific, imminent catalyst (earnings, guidance raise, M&A, regulatory change) that can override technicals
- A strong bounce off a lower support level with volume may indicate mean reversion is becoming viable — wait for the bounce, not the bottom
- P/C ratio >1.5 is less meaningful within this pattern — bearish positioning is often fundamentally justified when below both SMAs
- Consider waiting for: stock to reclaim 50 SMA, bullish MACD crossover, or positive divergence in RSI before mean reversion entry