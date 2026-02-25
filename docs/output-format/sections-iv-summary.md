# Section 8: Implied Volatility Summary

This section presents all computed IV metrics, volume ratios, OI ratios, and skew. It forms the third chunk of the report (between the second and third `---SPLIT---` markers).

---

## Sub-Header

```
📊 IMPLIED VOLATILITY SUMMARY
──────────────────────────────────────────────────────────────────────────────────────────
```

---

## Content (in exact order)

### IV Averages Block

```
Average Call IV:      24.50%  (+0.30% change) 🔴
Average Put IV:       26.10%  (-0.20% change) 🟢
Overall Average IV:   25.30%
Overall IV Change:    +0.05% (from previous run) 🔴
```

| Line | Always shown? | Notes |
|------|--------------|-------|
| Average Call IV | Yes | Mean of 5 call IVs |
| Average Call IV change | Only with previous data | In parens after the IV value |
| Average Put IV | Yes | Mean of 5 put IVs |
| Average Put IV change | Only with previous data | In parens after the IV value |
| Overall Average IV | Yes | `(avg_call_iv + avg_put_iv) / 2` |
| Overall IV Change | Only with previous data | Separate line, includes "(from previous run)" label |

### Computations

```
avg_call_iv = mean(call_iv for each of 5 strikes)
avg_put_iv = mean(put_iv for each of 5 strikes)
overall_avg_iv = (avg_call_iv + avg_put_iv) / 2

# If previous data exists:
avg_call_iv_change = avg_call_iv - previous.avg_call_iv
avg_put_iv_change = avg_put_iv - previous.avg_put_iv
overall_iv_change = overall_avg_iv - previous.overall_avg_iv
```

### Change Color Rules

| Change Direction | Emoji | Reason |
|-----------------|-------|--------|
| IV increased (+) | 🔴 | Options more expensive |
| IV decreased (-) | 🟢 | Options cheaper |

---

### Volume Block

```
Total Call Volume:      9,678
Total Put Volume:       8,234
Put/Call Vol Ratio:     0.85  (-0.20 change) 🟢
```

| Line | Always shown? | Notes |
|------|--------------|-------|
| Total Call Volume | Yes | Sum of volume across 5 call strikes |
| Total Put Volume | Yes | Sum of volume across 5 put strikes |
| Put/Call Vol Ratio | Yes | `total_put_vol / total_call_vol` |
| Vol Ratio change | Only with previous data | In parens after ratio |

### Volume Computation

```
total_call_vol = sum(call_volume for each of 5 strikes)
total_put_vol = sum(put_volume for each of 5 strikes)
pc_vol_ratio = total_put_vol / total_call_vol  # handle div by zero → "N/A"
pc_vol_change = pc_vol_ratio - previous.pc_vol_ratio
```

### Volume Change Color

| Direction | Emoji | Reason |
|-----------|-------|--------|
| Ratio increased (+) | 🔴 | More bearish (more puts relative to calls) |
| Ratio decreased (-) | 🟢 | More bullish (more calls relative to puts) |

---

### Open Interest Block

```
Total Call OI:          54,812
Total Put OI:           47,890
Put/Call OI Ratio:      0.87  (+0.05 change) 🔴
```

Same structure as volume block, using open interest instead.

```
total_call_oi = sum(call_oi for each of 5 strikes)
total_put_oi = sum(put_oi for each of 5 strikes)
pc_oi_ratio = total_put_oi / total_call_oi  # handle div by zero → "N/A"
pc_oi_change = pc_oi_ratio - previous.pc_oi_ratio
```

---

### Skew Line

```
Put/Call IV Skew:       +1.60%  (-0.20% change) 🟡
```

### Skew Computation

```
skew = avg_put_iv - avg_call_iv
```

This is always calculated as **put minus call**. A positive skew means puts are priced higher (normal — downside protection demand). A negative skew means calls are priced higher (unusual — bullish speculation).

### Skew Change Color

| Condition | Emoji |
|-----------|-------|
| |skew_change| > 1 | 🔴 |
| |skew_change| <= 1 | 🟡 |

---

## First Run Behavior

When no previous data exists, the section shows:

```
Average Call IV:      24.50%
Average Put IV:       26.10%
Overall Average IV:   25.30%

Total Call Volume:      9,678
Total Put Volume:       8,234
Put/Call Vol Ratio:     0.85

Total Call OI:          54,812
Total Put OI:           47,890
Put/Call OI Ratio:      0.87

Put/Call IV Skew:       +1.60%
```

No change values, no color emoji on changes. Clean and simple.

---

## Footer

Section 8 is the final data section. After the skew line, the report appends a footer and save confirmation:

```
Put/Call IV Skew:       +1.60%  (-0.20% change) 🟡

========================================
✅ REPORT COMPLETE
========================================

✓ Saved IV data for next comparison
```

This is the last chunk — no further `---SPLIT---` marker follows.
