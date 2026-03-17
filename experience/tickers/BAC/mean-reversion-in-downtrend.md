# Mean Reversion Calls in a Downtrend

**Thesis:** Buying calls on BAC dips driven by "general sector weakness" fails when the stock is in a sustained downtrend below both SMAs.
**Applies to:** BAC
**Tags:** mean-reversion, downtrend, financial-sector, below-sma, calls, bear, dte-long
**Confidence:** medium
**Last Updated:** 2026-03-16

## Analysis

Three BAC mean reversion call trades have now confirmed this pattern, all resulting in losses:
1. 52.5C Jul-17 entered at 47.15, below both SMAs, closed same-day at -8.3%
2. 50C Jul-17 entered at 48.26 on 2026-03-06, held 3 days, closed at -20.6% 
3. 50C Jul-17 entered at 47.39 on 2026-03-12, below both SMAs, closed at -1.4% when thesis invalidated

All trades shared the same entry thesis: "financial sector weakness, no company-specific news, oversold." All failed because the stock was in a sustained downtrend below both 50 SMA (~52.8) and 200 SMA (~50.6). Mean reversion requires a baseline to revert to — when the stock is already well below both moving averages with negative returns across all timeframes, buying calls is catching a falling knife.

The pattern is now confirmed across three independent occasions: financial sector weakness can persist for days, and "no bad news" doesn't equal "due for bounce." Losses were primarily directional (underlying kept dropping), not IV crush. Confidence upgraded to medium based on consistent cross-temporal validation.

## Evidence

### Summary
3 supporting, 0 contradicting observations total across three independent entry occasions. All BAC mean reversion call trades below both SMAs have lost money, with losses ranging from -1.4% to -20.6%. Pattern is consistent: entry below both SMAs during financial sector weakness leads to continued decline, not mean reversion. Confidence upgraded to medium.

### Recent
- 2026-03-16 [hindsight] [supporting] [bear] [dte-long]: BAC 50C Jul-17 exit validation. Sold at -1.4% when stock at $47.13, still below both SMAs. In hindsight, this was correct — BAC ranged $46.72-$47.68 over next 2 days without reclaiming 50 SMA. Previous same-thesis trades lost -8.3% and -20.6% by holding. The validated experience prevented a larger loss. Stock needs to reclaim 50 SMA (~52.8) before mean reversion becomes viable.
- 2026-03-16 [paper] [supporting] [bear] [dte-long]: BAC 50C Jul-17 entered at $47.39 (strike 50, 127 DTE) as mean reversion play. RSI 25.6 (oversold), below both 50 SMA (~52.8) and 200 SMA (~50.6). Stock continued downtrend, thesis invalidated. Closed at -1.4% loss before further damage. Third confirming observation for this pattern — consistent failure when buying calls below both SMAs during sustained downtrend.
- 2026-03-09 [paper] [supporting] [bear] [dte-medium]: BAC 50C Jul-17 (entered 2026-03-06 at 48.26) closed at -20.6% loss. Same thesis: mean reversion on sector weakness, below both SMAs. Stock continued declining from 48.26 to 46.91 over 3 days. Delta decayed from 0.489 to 0.417. Losses were primarily directional, not vol-based.

## Exceptions & Nuances

- Mean reversion may still work for BAC if the stock is near or above at least one SMA — the pattern specifically fails when below both
- Two losses on same-thesis trades strengthens evidence; consider a third confirmation before treating as high confidence
- Financial sector weakness driven by macro events (rate fears, oil shocks) may resolve differently than idiosyncratic sector issues
- Consider waiting for: bounce off lower support, P/C ratio spike indicating extreme bearishness, or RSI oversold (<30) before entry
