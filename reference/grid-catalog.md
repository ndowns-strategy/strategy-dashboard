# Grid catalog

Studied from the demo dashboard **Tec Visual Vocabulary › Grids** (demo.microstrategy.com, read as a guest, no edits). Exact values are in [grid-catalog.json](grid-catalog.json).

Both grids on the page are **Modern Grids with column sets** (definition type `microcharts`). It's the same structure as the row-set grid in the P&L build, turned sideways:

| | Row sets (P&L Income Statement) | Column sets (this page) |
|---|---|---|
| Container | stitched node, `stitchType 2` | stitched node, `stitchType 1` |
| Shared across sets | columns | row attributes |
| Each set has its own | row attributes and view filter | columns and metrics |

Each set is a normal grid template (`rows`, `cols`, metrics, sorts, thresholds, formats). The container's `sortIndex` names the set whose sort orders the rows.

## The two variants

| Variant | How to spot it in an image | Build |
|---|---|---|
| **Grid with Column Sets** | Shared row headers (Category with merged cells, Subcategory), then column groups side by side. One group is plain metrics; another has element headers (Consumer / Corporate / Home Office) above repeated metric headers | Set 1: rows Category, Subcategory; columns Metrics = Sales Rank, Revenue, Quantity Sold. Set 2: same rows; columns **Segment, Metrics** = Revenue, Profit Margin |
| **Grid with Microcharts** | Plain metric columns followed by columns of tiny charts in each row: grouped bars (one per category) and a line with dots (one per year) | Set 1: rows State; Metrics = Sales Rank, Revenue, Quantity Sold, Profit Margin, sorted ascending by Sales Rank. Set 2: columns Metrics + Category, Revenue, `chartCfg` type `trendBar`. Set 3: columns Metrics + Order Date (Year), Profit, `chartCfg` type `sparkline` |

## Microchart settings

A microchart set stores its chart in `vp.chartCfg`, an HTML-escaped JSON array:

```json
[{ "type": "trendBar" | "sparkline", "n": "Revenue Comparison by Category", "autoName": true,
   "mid": ["<metric id>"], "aid": ["<attribute id>"], "format": { ... } }]
```

- **Bar (`trendBar`):** `barColor`, `negBarColor`, `barSpacing`, `zeroAxis`, `contentHeight` 24, `valign` 1. On the demo each bar's color comes from **thresholds** on Revenue, one per Category element: Furniture #9586BC, Office Supplies #54457A, Technology #BCB1E2. These override `barColor` (#159B98).
- **Sparkline:** `lineColor` #54457A, `spotRadius` 3, spot and highlight colors #3B92ED, `dataPoints.keyPoints` (first, last, min, max are all off), `defaultPixelsPerValue` 6.
- `axisScaleScope` / `axisScaleFunc` 0: each row is scaled on its own.

## Formatting that matters

- Number formats: Revenue `"$"#,##0;("$"#,##0)`, Profit Margin `0.00%;(0.00%)` (negatives in parentheses), counts `#,##0`.
- Row headers: Open Sans 10pt, #35383A, white background, light #EBEBEB row dividers. Column headers: bold and wrapped, with a darker #ABABAB rule underneath. Banding is off.
- "Sales Rank" is a renamed Revenue Rank metric; use `rename()` for display names.
- Page: the same free-form, blue-gray layout as the KPI page, with a heading and a one-line description above each grid.

## Building them from code (verified)

Captured from the editor on 2026-11-10 and verified by [build-grids-showcase.js](../build-grids-showcase.js). It built both grids on Shared Studio's Business Insurance dataset in 7.1 s ("zz Grids Showcase v1" in My Reports).

```js
const { stitchedKey } = await s.buildColumnSetGrid({ datasetId, idOf, gridKey: 'W70', title: 'Grid with Column Sets',
  rows: ['Region', 'State Code'],
  sets: [
    { title: 'Totals', metrics: ['Claim Count', 'Payment Amount'] },
    { title: 'By Customer Segment', attrs: ['Customer Segment'], metrics: ['Payment Amount', 'Deductible Amount'] },
    { microchart: { type: 'trendBar', metric: 'Payment Amount', attr: 'Customer Segment', format: { barColor: '#9586BC' } } },
    { microchart: { type: 'sparkline', metric: 'Payment Amount', attr: 'Payment Date (Quarter)', format: { lineColor: '#54457A' } } },
  ] });
// put stitchedKey (not gridKey) in the page layout
```

What the editor sends, which the helper replays:

| Step | Action |
|---|---|
| Insert Grid (Modern) | `copyUnit` K51, turn the visualization style off, `changeGridToStitched`. This is the same start as row sets |
| Add > Column Set | `copyUnit` of the grid into its container **without** `stitchType` (row sets use 2), title/format, `moveUnit` to its index |
| Set columns | `addUnit` with `axis: 2` on that set's own template, attributes first, then metrics |
| Add > Microchart | A column set holding [metric, attribute], switched to `DossierRawValueVisualizationStyle` (ViewMode 51) with `<chartCfg value="…">`. The JSON is escaped twice and the IDs are prefixed `@pLd`. Then `setWidgetString` `mcname` = the chart's name |
| Merge repetitive column headers | `advancedProperties` `{ 'Template Formatting': { MergeColumnCells: '-1' } }` on every set |

Gotchas:
- Without `MergeColumnCells`, a pivoted set repeats the element name over each metric ("Enterprise Enterprise"). The helper sets it by default.
- Set 1 is the grid key itself, so its title is the first set's title. The container's title is the visualization title.
- Not done yet: per-element bar colors. The demo colors each bar with a threshold per Category element, and the helper uses one `barColor`.
