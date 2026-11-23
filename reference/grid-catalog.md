# Grid catalog

## Three kinds of grid

Library has three grid visualizations. **This repo builds Grid (Modern) by default and never the other two unless the
user asks for them.**

| Kind | How it is stored | How to tell (Library's `isModernGrid`) |
|---|---|---|
| **Grid (Modern)** | a grid template inside a stitched container whose `sdm` (SectionDisplayMode) is **2** (`MICRO_CHART`) | `stitchSectionKey` set and `sdm 2` |
| Compound Grid | the same stitched container with `sdm` **1** (`COMPOUND_GRID`) | `stitchSectionKey` set and `sdm 1` |
| Grid (classic) | a bare grid template (`t 521`), no container. The blank dashboard's K52 is one, and `addToGrid` fills it | no `stitchSectionKey` |

The editor makes a Grid (Modern) by copying a grid, calling `changeGridToStitched` on it, and setting
`SectionDisplayMode: MICRO_CHART` on the container. `insertModernGrid` (JS) / `insert_modern_grid` (Python) do that in
one batch, then add the rows, column attributes and metrics, and return `{gridKey, stitchedKey}`.

- Put **`stitchedKey`** in the page layout and read data by it: `GET .../visualizations/<stitchedKey>` returns the values
  under `metricValues.columnSets[]`. REST refuses the inner `gridKey` with ERR006 ("the key of a column set in a compound
  grid visualization"); REST calls every stitched grid compound, whatever its `sdm`.
- Formatting, sorts and thresholds still go to `gridKey`, the template.
- Python spec: `{"type": "grid", "rows": [...], "columns": [...], "metrics": [...]}`.

Verified 2026-11-23 as **SDC modern grid test** (`C6BCF4522B466B783F4375894F4A05C9`, Showcase) from
[examples/grid-test.json](../examples/grid-test.json): both grids saved with `stitchSectionKey` and `sdm 2`, render with
the Modern Grid look, and read back 5 rows each (the second with Product Category across the columns).

## Ranked grid: rank, renames, thresholds, top N

Studied 2026-11-23 on a grid the user built on **IMT Advisor Sales and Opportunity Performance**
(`AAD34112BA477BFF5142508585493EB7`, Shared Studio), to match a generated "Top 15 advisors by year to date sales" table.
It is a Grid (Modern) (stitched container `FFC49199…`, `sdm 2`).

**How a generated table maps to Strategy:**

| In the image | In Strategy |
|---|---|
| A rank column "#" on the far left | Not possible: **attributes always come first, then metrics**. Put the attributes (Advisor, Firm, Level) on the left and make the rank a **derived metric** in the **first metric position** |
| Rank = 1..15 by YTD sales | Derived metric `Rank<ASC=False>([Year To Date Total Sales Amount])` (the source used `Rank<ASC=False, BreakBy={(@auto)*}>(...)`), labelled "Rank" |
| Only 15 rows | A **metric limit** on the rank: `Rank <= 15` (`saveViewFilterLimit`; stored as the grid's `vlexpr`, shown as "Rank of {…} Top 15") |
| Rows in sales order | Sort on the YTD sales metric, descending |
| Short column names ("YTD sales", "Level") | **Renamed in the grid** (`renameUnit`): the dataset names stay as they are |
| A pill or badge around a value ("Platinum", "Gold") | Not possible: values can't get a pill-shaped border. Use **font color thresholds** per element instead (Platinum `#333399`, Gold `#FFCC00`) |
| Change in red or green | Value-band thresholds on the metric, font only: red `ceil 0`, green `flr 0` |
| "new" instead of a change | A **condition threshold that replaces the text**: when Prior YTD = 0, show "new" (`rtp 3`, `rtxt "new"`, font `#339966`). Added **after** the bands: each threshold action is stored ahead of the existing ones, so the last one added is checked first |
| Change % | Derived `([YTD] / [Prior YTD]) - 1` (the same as `([YTD] - [Prior]) / [Prior]`) |
| $686K next to $7.2M in one column | Not possible: Strategy ignores Excel-style conditions such as `[>=1000000]` in number formats. Use one unit per column (`$#,##0.0,,"M"` gives $0.7M) |

**What gets written** (all on the grid template, the `gridKey`, not the stitched key):

| Setting | Action |
|---|---|
| Rename an attribute or metric | `updateTemplate` › `renameUnit {id, type 12 or 4, name}` |
| Number format in this grid only | `numberFormat {unitId, unitType 4, c 7, f, nodeKey: gridKey}`, stored in the grid's `nf`. Without `nodeKey` the format is dashboard-wide |
| Top N | `saveViewFilterLimit {nodeKey, limitExp, limitToRemove: []}`, where `limitExp` is a metric qualification (below) |
| Element font colors | `threshold`, `thresholdType -1`, `objType 12`, an element-list expression per rule (`attributeThresholds`) |
| Value bands | `threshold`, `thresholdType 7`, `flr` / `ceil` per band (`metricThresholds`) |
| Condition on another metric | `threshold`, `thresholdType -1`, `objType 4`, `expr` = a metric qualification, plus `rtp: 3, rtxt: "<text>"` to replace the value (`conditionThresholds`). Each `threshold` action adds to the metric's existing thresholds |

A metric qualification, as `mstrmojo.fe.FilterUtils.getExprXml` writes it (fn: `=` 6, `!=` 7, `>` 8, `<` 9, `>=` 10, `<=` 11):

```xml
<exp><nd et="14" fn="19"><nds><nd et="10" dmt="7" fn="11" node="0"><m did="<metric id>" n="Rank"></m><cs><c v="15" dtp="5"></c></cs></nd></nds></nd></exp>
```

**Spec** (`grid` item):

```json
{"id": "top15", "type": "grid", "title": "Top 15 advisors by year to date sales",
 "title_format": {"subtitle": "Ranked on year to date total sales amount."},
 "rows": ["Advisor", "Firm Name", "Producer Level"],
 "metrics": ["Advisor Rank", "Year To Date Total Sales Amount", "Prior Year To Date Total Sales Amount", "YTD Sales Change"],
 "labels": {"Firm Name": "Firm", "Producer Level": "Level", "Advisor Rank": "Rank", "YTD Sales Change": "Change"},
 "number_formats": {"Year To Date Total Sales Amount": "$#,##0.0,,\"M\""},
 "sort": {"metric": "Year To Date Total Sales Amount", "ascending": false},
 "limit": {"metric": "Advisor Rank", "op": "<=", "value": 15},
 "thresholds": [
   {"on": "Producer Level", "elements": {"Platinum": "#333399", "Gold": "#FFCC00"}},
   {"on": "YTD Sales Change", "bands": [{"font": "#FF0000", "ceil": 0}, {"font": "#008000", "flr": 0}]},
   {"on": "YTD Sales Change", "when": {"metric": "Prior Year To Date Total Sales Amount", "op": "=", "value": 0},
    "replace_text": "new", "font": "#339966"}]}
```

Define the rank and change metrics in the spec's top-level `derived_metrics`.

**Threshold order: list the special case last.** Each `threshold` action is stored *ahead of* the thresholds the
metric already has, and the first stored threshold that matches wins. So the **last** threshold in the spec is checked
first. Put a replace-text rule ("new", "–") after the red/green bands, or the bands match first and the cell shows
-100.0%. Found 2026-11-23 on **IMT Advisor Sales and Opportunity Performance (v3)** (`FB6013E644477FE5553B939D98220266`,
Shared Studio, [examples/imt-advisor-sales-v3.json](../examples/imt-advisor-sales-v3.json)):
- With "new" listed before the bands, the instance stored the bands first (`tid` 1, 2) and "new" third, and Library
  showed -100.0%.
- With "new" listed last, it was stored first, and Library showed "new" for Raj Kapoor and "–" for Prospect.

The earlier example, [examples/imt-advisor-kpis.json](../examples/imt-advisor-kpis.json) ("SDC IMT grid test"), was
recorded as showing "new" with the special case first. The v3 build didn't reproduce that.

## Row and column sets

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
