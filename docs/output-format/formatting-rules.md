# Formatting Rules

General formatting rules that apply across all sections of the report output. The authoritative spec is OUTPUT.md — this document elaborates on the rules defined there.

---

## Dividers

### Major Header Dividers

40 `=` characters. Used for section banners:

```
========================================
```

Used in:
- Section 2: Main header (`🎯 {TICKER} OPTIONS TRADING ANALYZER`)
- Footer: (`✅ REPORT COMPLETE`)

### Sub-Header Dividers

40 `─` characters (Unicode horizontal bar, U+2500). Used for section sub-headers:

```
────────────────────────────────────────
```

Used in:
- Section 4: News headlines
- Section 8: IV summary

Note: Sections 6-7 (options tables) use code blocks with an emoji header instead.

### Count Verification

Both dividers are exactly 40 characters. Verify by counting or using:
```python
major = "=" * 40
minor = "─" * 40
```

---

## Number Formatting

### Prices

Format: `$X.XX` — dollar sign, two decimal places always.

```
$210.45     ← correct
$210.4      ← wrong (missing trailing zero)
$210        ← wrong (missing decimals)
210.45      ← wrong (missing dollar sign)
```

### Percentages

Format: `X.XX%` — two decimal places, percent sign.

```
24.50%      ← correct
24.5%       ← wrong (only one decimal)
0.2450      ← wrong (raw decimal)
```

### Volume and Open Interest

Format: comma-separated integers.

```
12,456      ← correct
12456       ← wrong (no commas)
12,456.00   ← wrong (has decimals)
```

Python formatting: `f"{value:,}"`

---

## Sign Rules

All change values always show their sign:

```
+1.23%      ← positive: explicit plus sign
-0.45%      ← negative: minus sign
+$0.65      ← positive dollar change
-$0.30      ← negative dollar change
+0.15       ← positive ratio change
-0.08       ← negative ratio change
```

Never omit the sign on change values. A positive change without `+` looks like an absolute value, not a change.

---

## Emoji Color System

Four emoji are used as color indicators throughout the report:

| Emoji | Meaning | Used For |
|-------|---------|----------|
| 🟢 | Bullish / Positive / Cheap / Good | Positive price change, IV decrease, low IV, ITM, bullish volume |
| 🟡 | Neutral / Stable / Normal | No change, moderate IV, ATM, balanced ratios, N/A values |
| 🔴 | Bearish / Negative / Expensive / Bad | Negative price change, IV increase, high IV, bearish volume, expanding vol |
| 🔵 | Out-of-the-money | OTM status only |

### Where Each Appears

**🟢 Green**:
- Price change positive (Section 3)
- IV < 20% (Sections 6-7 table)
- IV decreased from previous run (Sections 6-7 IV Chg column)
- Status: ITM (Sections 6-7)
- P/C ratio decreased (Section 8)

**🟡 Yellow**:
- IV 20-35% (Sections 6-7)
- IV unchanged or N/A (Sections 6-7)
- Status: ATM (Sections 6-7)
- Small skew change (Section 8)

**🔴 Red**:
- Price change negative (Section 3)
- IV > 35% (Sections 6-7)
- IV increased from previous run (Sections 6-7)
- P/C ratio increased (Section 8)
- Skew change > 1 (Section 8)

**🔵 Blue**:
- Status: OTM (Sections 6-7)

---

## Indentation

### 5-Space Indent

Used for news article metadata (publisher and date) under each headline:

```
  1. Fed Signals Patience on Rate Cuts
     Reuters • 2026-02-20
```

### 2-Space Indent

Used for warning lines and numbered headlines:

```
  ⚠️  High Fed/monetary policy focus in recent news
  1. Headline text here
```

---

## Headline Truncation

Any news headline longer than 85 characters is truncated at position 85 and appended with `...`:

```python
if len(headline) > 85:
    headline = headline[:85] + "..."
```

The 85-character limit keeps headlines from wrapping too much in Discord's monospace rendering.

---

## Conditional Lines

Lines marked with `← only if ...` in OUTPUT.md are conditional. They MUST:
- Appear when their condition is true
- Be completely absent (not blank, not "N/A") when their condition is false

This keeps the output clean — users don't see irrelevant information.

Examples:
- `IV Change: ...` line in Section 8 → only if previous data exists
- `⚠️  High Fed/monetary policy focus` → only if >= 2 Fed headlines
