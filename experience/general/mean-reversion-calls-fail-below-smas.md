# Mean Reversion Calls Fail Below SMAs

**Thesis:** Buying calls for mean reversion fails when a stock is in a sustained downtrend below both its 50-day and 200-day SMAs, regardless of how "oversold" technical indicators appear or how "bullish" fundamental news headlines are.

**Applies to:** general (multi-ticker pattern)

**Tags:** mean-reversion, downtrend, below-sma, technical-analysis, calls, trend-following, bear, dte-long

**Confidence:** high

**Last Updated:** 2026-03-25

## Analysis

Mean reversion as a strategy requires a stable baseline to revert *to*. When a stock is trading below both its 50-day and 200-day SMAs, it signals institutional distribution and structural regime shift.

**The "Good News" Trap:**
Hindsight analysis across BAC, QQQ, NVDA, and IWM in March 2026 has refined this rule: **fundamentals do not matter when technical support is non-existent.** Even when tickers reported strong earnings, massive buybacks (Salesforce), or AI catalysts (Nebius/Iran Attack Pause), price action remained bearish once the SMAs were lost.

**Why Indicators Fail Below SMAs:**
1. **Oversold Persistence:** RSI can stay below 30 for weeks during a floorless drop.
2. **Reclamation Failure:** A "relief rally" that reclaims an SMA but fails to hold it over 24-48 hours is a high-confidence reversal signal indicating a return to a structural bearish regime.
3. **SMA Resistance:** The 200-day SMA acts as a ceiling. Any relief rally usually stalls at this level, killing option theta.

**Core Rule:** Never buy mean-reversion calls below both SMAs. If a position is entered on a reclamation signal and it fails to hold for 48 hours, exit immediately.

## Evidence

### Summary
6 supporting observations across 4 tickers (BAC, IWM, NVDA, QQQ). All mean-reversion call attempts failed or triggered losses if held below dual SMAs (50/200). Early data from March 16 (IWM) confirmed that deep RSI oversold levels (<30) were traps without technical floor support. The March 20 "Tech Wreck" and March 24 "Reclamation Failure" sessions solidified this as the most critical safety filter. Confidence: High.

### Recent
- 2026-03-25 [paper] [supporting] [bear] [dte-short]: IWM $225C and QQQ $590C (peace plan catalyst) exited at loss as intraday "reclamation rallies" above both 50/200 SMAs failed on high-volume downside momentum. QQQ failed a news-driven V-bottom attempt while IWM broke through $252 to $222 (-12% from high to low). Confirms: even structural regime-shifting fundamental catalysts (peace plan) cannot override the lack of long-term technical support. [Q3: Reversal Detection]
- 2026-03-24 [paper] [supporting] [bear] [dte-long]: IWM $235C and NVDA $175C exited at loss as reclamation of 200 SMA (IWM) and psychological floor (NVDA 175) failed after just 24 hours. Confirms: reclamation of key levels below both SMAs is high-risk and needs immediate confirmation or exit. [Q1: Catching a Falling Knife]
- 2026-03-20 [hindsight] [supporting] [bear] [dte-long]: BAC 50C analyzed. -88.6% loss. Bullish news sentiment (+6) could not override the downtrend below both SMAs.
- 2026-03-20 [paper] [supporting] [bear] [dte-short/long]: QQQ mean reversion calls exited at loss upon 200 SMA break.
- 2026-03-19 [paper] [supporting] [bear] [dte-short/long]: QQQ break of 200 SMA triggered exit, saving capital.

## Exceptions & Nuances

- **Double-Bottom Signals:** Only viable if confirmed by a volume spike and RSI divergence.
- **The "Wait for the Bounce" Strategy:** Instead of buying the bottom, buy the first higher-low after reclaiming an SMA.
- **DTE Bucket:** For trades below both SMAs, even LEAPs soffur from volatility crush and theta drain as the stock sideways-grids along lows.
