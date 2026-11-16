# Correlation chart catalog

Studied from the demo dashboard **Tec Visual Vocabulary › Correlation** (demo.microstrategy.com, read as a guest, no edits). Exact values are in [correlation-catalog.json](correlation-catalog.json).

All four are standard charts (`GraphMatrixVisualizationStyle`).

| Chart | How to spot it in an image | Build |
|---|---|---|
| **Scatter Plot** | One same-size, same-color dot per item on two numeric axes, with a thin straight trend line | Circle, `visType 21`. X = Cost, Y = Revenue, Break By = Subcategory. Fixed size (`SizeType Manual`, `SizeValue 0.15`), 80% fill transparency, origin lines off, linear **trend line** |
| **Combo Chart** | Bars for one metric and a line for another, each with its own y-axis (left and right) | Bar, `visType 57`. X = Quarter, Y = Revenue + Profit, **Metric Names on Rows** and Color By. `metricShapes { Profit: 2 }` makes Profit a line. Bars #E8D39B, line #457359 |
| **Bubble Chart** | Dots of different sizes in three colors, semi-transparent with thin borders | Circle, `visType 21`. X = Profit, Y = Revenue, Break By = Category + Subcategory, Color By = Category, **Size By** = Profit Margin. 70% transparency, border 1. Category colors #E9D39B / #735E2A / #BFAD80 |
| **Matrix Bar Chart** | A grid of solid squares: one attribute across the top, another down the side, three shades light to dark, no axis numbers | Bar, `visType 71`, with **no metric on X**, so every bar fills its cell. Columns = Category, Y = Region, Color By = Revenue with three percent bands (0–35% #E9D39B, 35–65% #BFAD80, 65–100% #735E2A). No bar borders |

## Settings worth knowing

- **Trend line:** stored on the X metric inside the template (`mdls.mod_c`), with `tp 257`, line thickness 1 and color #4D4D4D. The server then computes a hidden `TrendLine_DM_<metric>` metric (a linear fit, R² 0.97 on the demo).
- **Line in a bar chart:** `metricShapes` maps a metric ID to a shape; `2` is a line.
- **Dual axis:** `visType 57`, with the line metric on the **right axis** and Metric Names on Rows (see below).
- **Transparency and borders:** `allShpFmt { shpFillTrans: '70', shpBdrThk: 1 }`, applied to the whole chart.
- **Fixed dot size:** `SizeType: 'Manual'`, `SizeValue: 0.15`.
- **Colors:** all dashboard-level (element and metric colors), from a sand and olive palette: #E9D39B, #BFAD80, #735E2A, plus #457359 green.
- The demo's combo line is flat because its Profit isn't split by quarter. When reading an image, check whether the line actually moves.

## Building them from code (verified)

[build-correlation-showcase.js](../build-correlation-showcase.js) rebuilt all four charts on Shared Studio's Business Insurance dataset in 4.7 s ("zz Correlation Showcase v2" in My Reports). The analogs:
- Initial Reserve vs Payment by State Code, with a linear trend line
- Payment bars plus a Claim Count line on a right axis, by quarter
- bubbles by Customer Segment × Region, sized by Claim Count
- Customer Segment × Region squares in three percentile shades

New pieces, each captured from the editor:

| Piece | What the editor sends |
|---|---|
| `trendLine(key, metricId, { model: 'linear' })` | Format > Trend Line > Enable: `operateTRFLine` with `lineType` 257 (linear) or 256 (best fit), plus the line format, on the plotted (Y) metric |
| `metricThresholds(..., 'percent')` | "Lowest %" basis: `thresholdType 1` with 0–100 bands. The value basis is 7 |
| `fillZones` field `ax: 1` | Right-click a metric > **Right Axis** puts it on the second y-axis |
| `VIS.scatter`, `VIS.combo` | `{ Circle, 21 }`, `{ Bar, 57, Stacked }` |

Gotchas:
- A **dual-axis combo** needs the line metric on the right axis (`ax: 1`), plus Metric Names on Rows and Color By, plus `metricShapes { '@pLd<id>': 2 }`. Without the right axis, the two metrics draw as two stacked panels.
- The **matrix bar** works with no metric on X. Each bar fills its cell, and Color By with percent thresholds carries the value.
- Not done yet: the scatter's dot color. The build leaves the default blue, while the demo's dots are sand.
