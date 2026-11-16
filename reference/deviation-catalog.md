# Deviation chart catalog

Studied from the demo dashboard **Tec Visual Vocabulary › Deviation** (demo.microstrategy.com, read as a guest, no edits). Exact values are in [deviation-catalog.json](deviation-catalog.json).

All five are standard charts (`GraphMatrixVisualizationStyle`). What makes them "deviation" charts is not the chart type; it comes from four techniques:

| Technique | How it's done | Used by |
|---|---|---|
| **Color by sign** | The value metric goes on **Color By** too, plus two **value thresholds** on it: below the breakpoint fills orange `#f8942c`, at or above it fills blue `#035397` | Diverging bars (both), stacked area |
| **Custom origin** | `axisOrigin: { <metric>: { axOriAuto: false, axOriValue: 0.2 } }` in the chart properties, so the bars grow either side of 20% instead of 0 | Diverging bar (horizontal) |
| **Negated metric** | A "Last Year's Revenue Negative" metric plots to the left. The format `"$"#,##0;"$"#,##0` hides the minus sign | Tornado |
| **Signed segments** | Negative responses carry negative values, so they stack left of 0. Each Response element has its own dashboard-level color | Diverging stacked bar |

## The five charts

| Chart | How to spot it in an image | Build |
|---|---|---|
| **Diverging Bar (Horizontal)** | Sorted horizontal bars, blue right and orange left of a reference line that isn't at zero | Bar, `visType 71`. X = Profit Margin, Y = Subcategory, Color By = Profit Margin. Origin 0.2; thresholds below/above 0.2; sorted descending; `0%;(0%)` |
| **Diverging Stacked Bar** | One bar per year with four segments: two orange shades left of 0, two blue right. Percent axis with negatives in parentheses | Bar Stacked, `visType 9`. X = % of Respondents (signed), Y = Year, Break By + Color By = Response. Element colors: Very Dissatisfied #f8942c, Dissatisfied #f9b167, Satisfied #3e6d95, Very Satisfied #035397 |
| **Tornado (Butterfly)** | Two series back to back from a center line, orange left and blue right, largest at the top, dollar labels positive on both sides | Bar Stacked, `visType 9`. X = Last Year's Revenue Negative + This Year's Revenue, Y = Subcategory, Columns + Color By = Metric Names. Metric colors #f89427 / #035397; sorted by This Year's Revenue descending |
| **Diverging Bar (Vertical)** | Bars over time, blue above 0, orange below | Bar, `visType 70`. X = Month, Y = Surplus/Deficit, Color By = Surplus/Deficit, with two thresholds |
| **Stacked Area** | A filled area over time, blue above 0 and orange below, with a gradient where it crosses zero | Area Stacked, `visType 30`. Same zones and thresholds as the vertical bar |

## Formatting that matters

- Two colors carry the meaning: orange `#f8942c` is negative or below target, blue `#035397` is positive or above.
- Number formats put negatives in parentheses: `0%;(0%)`, `"$"#,##0_);("$"#,##0)`.
- The legend is on, with small swatches on the right. Axis titles are shown.
- Page: the same free-form, blue-gray layout as the other pages, with the "DEVIATION" heading in orange.

## Building them from code (verified)

[build-deviation-showcase.js](../build-deviation-showcase.js) rebuilt all five charts on Shared Studio's Business Insurance dataset in 6.8 s ("zz Deviation Showcase v2" in My Reports). The analogs:
- Paid to Reserve by Policy Type, diverging around 33%
- signed Claim Status segments by Region
- Reserve (left) vs Payment Amount by Policy Type, as the tornado
- Surplus/Deficit against a $2.8M monthly target, as both bars and area

New client helpers, each captured from the editor:

| Helper | What the editor sends |
|---|---|
| `metricThresholds(key, metricId, bands)` | Thresholds dialog with the "Value" basis: `threshold`, `thresholdType 7`, bands of `{ fmt: { FormattingPatterns: { FillColor } }, flr, ceil }`. Fills the bars or area when the metric is also on Color By |
| `elementColors(attrId, { West: '#f8942c' })` | Shape Fill Color on an element: a dashboard-level element-properties update with `emt 1` |
| `metricColors({ metricId: hex })` | Dashboard-level metric colors (`emt 2`), wherever a chart colors by Metric Names |
| `chartFormat(key, vis, { axisOrigin: { metricId: 0.33 } })` | Chart type for a chart inserted in this session, plus a custom origin `{'@pLd<id>': {axOriAuto: false, axOriValue: '0.33'}, 'AllMetrics': {...}}` |
| `VIS.hbarStacked`, `VIS.areaStacked` | `{ Bar, 9, Stacked }` and `{ Area, 30, Stacked }` |

Gotchas:
- A custom axis origin also needs `xAxOriLnShw` / `yAxOriLnShw` set to `'true'`. Without them the editor still draws it, but viewing ignores it. `chartFormat` sets both.
- **Signed segments** come from a derived metric: `If(([Claim Status]@ID = "Denied") Or ([Claim Status]@ID = "In Litigation"), -1, 1) * [Claim Count]`. `ApplySimple` was rejected.
- **Tornado**: put Metric Names on **both** Columns and Color By to get side-by-side panels. With Color By alone, the two metrics stack as row panels.
- Not done yet: the tornado's left axis still shows negative labels ($-70M). The demo hides the sign on the axis too.
