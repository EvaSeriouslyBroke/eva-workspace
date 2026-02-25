# Sections 5-7: Expiry Selection, Call Table, Put Table

These three sections form the second chunk of the report (between the first and second `---SPLIT---` markers).

---

## Section 5: Target Expiration

Two lines identifying the selected expiry and ATM strike:

```
Target Expiration: 2026-05-16 (85 days)
ATM Strike: $210
```

### Expiry Selection Logic

1. Fetch all available expirations from yfinance: `ticker.options`
2. Compute DTE for each: `(expiry_date - today).days`
3. Select the one closest to 120 DTE
4. If equidistant, pick the later expiry

### ATM Strike

```
ATM = round(current_price)
```

Rounded to nearest integer. This determines the center of the 5-strike window.

---

## Section 6: Call Options — Stacked Cards

### Sub-Header

The emoji header sits outside the code block so it renders as an emoji on Discord:

```
📈 CALLS
```

### Card Format (inside code block)

Each strike is a 3-line card separated by a blank line:

~~~
```
$212 OTM | IV: 24.50%
  Chg: +1.10% (+5.0%) | B/A: $3.20/$3.45
  Last: $3.30 | Vol: 1,245 | OI: 8,901

$211 OTM | IV: 23.80%
  Chg: N/A | B/A: $3.85/$4.10
  Last: $3.95 | Vol: 2,100 | OI: 12,345

$210 ATM | IV: 23.20%
  Chg: N/A | B/A: $4.50/$4.75
  Last: $4.60 | Vol: 3,456 | OI: 15,678

$209 ITM | IV: 22.90%
  Chg: N/A | B/A: $5.20/$5.45
  Last: $5.30 | Vol: 1,890 | OI: 10,234

$208 ITM | IV: 22.50%
  Chg: N/A | B/A: $5.90/$6.15
  Last: $6.00 | Vol: 987 | OI: 7,654
```
~~~

### Card Rules

- **Exactly 5 cards** — the 5 strikes closest to ATM
- **Sorted descending** by strike price (highest first)
- **Line 1**: `$STRIKE STATUS | IV: XX.XX%`
- **Line 2**: `  Chg: {change} | B/A: $bid/$ask`
- **Line 3**: `  Last: $X.XX | Vol: N,NNN | OI: N,NNN`
- **Max width**: ~42 characters per line (mobile-friendly)

### Card Field Specifications

#### Strike + Status (Line 1)

Format: `$XXX STATUS` where STATUS is `ITM`, `ATM`, or `OTM`.

No emoji for status — inside a code block, emoji don't render well.

#### IV (Line 1)

Format: `IV: XX.XX%`

Source: `impliedVolatility * 100` from yfinance.

#### IV Chg (Line 2)

Compact format without emoji:

| Condition | Display |
|-----------|---------|
| IV increased | `+1.10% (+5.0%)` |
| IV decreased | `-1.10% (-4.8%)` |
| No previous data | `N/A` |
| Strike not in previous run | `N/A` |

The two-part format:
- First: absolute change in percentage points (`current_iv - previous_iv`)
- Second (parens): relative change (`((current - previous) / previous) * 100`)

#### B/A (Line 2)

Format: `B/A: $X.XX/$X.XX` — bid/ask side by side.

#### Last, Vol, OI (Line 3)

- Last: `$X.XX` — two decimal places
- Vol: comma-separated integer
- OI: comma-separated integer

#### Status (for Calls)

| Condition | Label |
|-----------|-------|
| strike < current_price | ITM |
| strike = ATM_strike | ATM |
| strike > current_price | OTM |

---

## Section 7: Put Options — Stacked Cards

### Sub-Header

```
📉 PUTS
```

### Card Format

Same 3-line card format as calls. Same 5 strikes, same sorting (descending).

### Status Rules for Puts (REVERSED from calls)

| Condition | Label |
|-----------|-------|
| strike > current_price | ITM |
| strike = ATM_strike | ATM |
| strike < current_price | OTM |

### Example

For IWM at $210.45 (ATM = $210):

~~~
```
$212 ITM | IV: 26.80%
  Chg: N/A | B/A: $5.10/$5.35
  Last: $5.20 | Vol: 890 | OI: 6,543

$211 ITM | IV: 26.20%
  Chg: N/A | B/A: $4.40/$4.65
  Last: $4.50 | Vol: 1,200 | OI: 8,901

$210 ATM | IV: 25.80%
  Chg: N/A | B/A: $3.80/$4.05
  Last: $3.90 | Vol: 2,890 | OI: 13,456

$209 OTM | IV: 25.30%
  Chg: N/A | B/A: $3.20/$3.45
  Last: $3.30 | Vol: 1,567 | OI: 9,876

$208 OTM | IV: 24.80%
  Chg: N/A | B/A: $2.70/$2.95
  Last: $2.80 | Vol: 734 | OI: 5,432
```
~~~

---

## Chunk Boundary

After Section 7, insert the second `---SPLIT---` marker.

Sections 5-7 together target ~1200 chars with the card format (well under the 2000-char Discord limit).
