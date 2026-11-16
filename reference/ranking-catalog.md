# Ranking chart catalog

Studied from the demo dashboard **Tec Visual Vocabulary › Ranking** (demo.microstrategy.com, read as a guest, no edits). Exact values are in [ranking-catalog.json](ranking-catalog.json).

All six are standard charts (`GraphMatrixVisualizationStyle`). What makes them "ranking" charts is mostly the **sort** and a **rank metric**, not a special visualization.

| Chart | How to spot it in an image | Build |
|---|---|---|
| **Horizontal Bar Chart** | One solid-color bar per item, longest at the top | Bar, `visType 71`. X = Revenue, Y = Region. Rows sorted by Revenue, descending. Bar color #4E80F4 (`modDefFillClr`) |
| **Vertical Bar Chart** | One solid-color column per item, tallest on the left | Bar, `visType 70`, Stacked. X = Region, Y = Revenue. Columns sorted by Revenue, descending. Same #4E80F4 |
| **Bubble Chart** | Dots of different sizes in three blues on two numeric axes, no axis numbers | Circle, `visType 21`. X = Profit, Y = Revenue, Break By = Region + Category, Color By = Category, Size By = Profit Margin. 70% fill transparency, no borders, axis labels hidden. The same build as the Correlation page's bubble, with different colors |
| **Dot Strip Plot** | One row per item, each with a few dots along a shared value axis; dots colored by a second attribute | Circle, `visType 21`. **Rows = Region**, X = This Year's Revenue, Break By and Color By = Category. With **no Y metric**, each Region gets its own strip. Fill transparency 30% (element overrides 80%), no borders, Y title hidden. Rows sorted by Furniture's Revenue, descending |
| **Slope Chart** | Straight lines from a left column to a right column, one per item, colored by group | Line, `visType 72`, Subtype Absolute. X = Year, limited to **exactly two values** by a visualization filter (`Order Date (Year) in (2019, 2020)`), Y = Revenue, Break By = Subcategory + Category, Color By = Category. Data labels hidden, legend on the right |
| **Bump Chart** | Lines with dot markers that cross as items swap places; the y-axis is rank, with 1 at the top | Line, `visType 72`. X = Year, Y = **Revenue Rank (Negative)** (shown as "Revenue Rank"), Break By = Region, Color By = that rank metric, with 4 threshold bands. Markers on (#1A6698), custom axis min −4 and max −1 |

## Settings worth knowing

- **Sorting is the main ranking setting.** It's stored in the template (`gsi.sorts`), not in the chart format: `[[rowSorts], [columnSorts]]`, each entry `{ key: '4~<metricId>~~~~<axis>~4', isAsc: false }`.
  - The horizontal bar sorts rows (axis 1).
  - The vertical bar sorts columns (axis 2).
  - The dot strip sorts by one element's value: `'4~<metricId>~~~h<element>~<attrId>~1~4'` (Revenue for Category = Furniture).
- **Rank metric with 1 at the top:** a derived metric `Rank<ASC=False, BreakBy={[Year]}>(Revenue) * -1`.
  - The negation puts rank 1 at the top of a normal axis.
  - The custom number format `#,##0; #,##0` hides the minus sign, so the axis reads 1, 2, 3, 4.
  - The same trick should hide the minus signs on the Deviation tornado's left axis (untested).
- **Fixed rank axis:** `MinMax: 'Custom'`, `AxisScale 'AllMetrics:0:-4:-1:…'` (min −4, max −1).
- **Bump colors:** the rank metric is also on Color By, with four value thresholds:
  - below −3: #A4CBE6
  - −3 to −2: #80ADD9
  - −2 to −1: #558DCC
  - −1 and above: #2E78BB
  
  So a band's color shows its rank.
- **Markers:** `lnMkShw: true`, `lnMkClr` #1A6698.
- **Series default color:** `modDefFillClr` is the fill for a chart with no Color By. For example:
  - #4E80F4 on the bars
  - #2171B5 on the dot strip
  - #1F77B4 on the bubble

  This is likely the setting the Correlation scatter needs for its sand dots (untested).
- **Category colors:** three blues, #1A6698, #83B4D4 and #6FBEF2. They come from the dashboard palette, not from per-element color overrides (the dashboard `epm` has only metric colors). To match them in a build, use `elementColors`.
- **Revenue color:** the dashboard sets metric colors for Revenue and This Year's Revenue to #035397, but on this page the bars draw #4E80F4 from `modDefFillClr`.

## Reading an image

- Bars ordered longest to shortest → a sort on the metric. Check which axis is sorted.
- Columns of dots in labeled rows, with no y-axis numbers → a dot strip (Rows = attribute, no Y metric).
- Exactly two x positions joined by straight lines → a slope chart. Add a visualization filter that keeps two values of the time attribute.
- Crossing lines with markers and small whole numbers on the y-axis (1 at the top) → a bump chart with a negated rank metric.

## Building them from code (verified)

[build-ranking-showcase.js](../build-ranking-showcase.js) rebuilt all six charts on Shared Studio's Business Insurance dataset in 6.3 s ("zz Ranking Showcase v3" in My Reports, run straight from the files in this repo). A separate ascending-sort test put West first on both bars, which confirms the sort is applied and not just stored (in this data the descending order happens to be alphabetical). The analogs:
- Payment Amount by Region as sorted horizontal and vertical bars
- bubbles by Region × Customer Segment, sized by Claim Count
- a dot strip with one row per Region and one dot per Customer Segment
- a slope chart of Payment Amount from 2025 to 2026, one line per Region × Customer Segment
- a bump chart of each Region's quarterly payment rank

New pieces:

| Piece | What it sends |
|---|---|
| `sortByMetric(key, metricId, false, { axis: 2 })` | `act sort` with `sorts: [[{ key: '4!<metric>!!!!2', metricSortKey: '2', isAsc }]]`. The axis lives in the key (1 = rows, 2 = columns), and the server files it under the right list |
| `chartFormat(..., { seriesColor })` | `modDefFillClr`: the fill of a chart with nothing on Color By |
| `chartFormat(..., { axisRange: { metricId: [min, max] } })` | `AxisScale 'AllMetrics:0:min:max:min:max:false:false:false,<id>:…'`, plus `MinMax 'Custom'` and `axScaleModified 1` |
| Rank metric | `createDerivedMetric(ds, 'Payment Rank', 'Rank<ASC=False, BreakBy={[Payment Date (Quarter)]}>([Payment Amount]) * -1', '#,##0; #,##0')` |
| Two-point slope | `keepOnly(key, yearId, ['2025', '2026'])` (a visualization filter) |
| Markers | `lnMkShw 'true'`, `lnMkClr` (BGR) |

Gotchas:
- **Don't send `[[], [sort]]`** for a column sort; the server returns a 500. Send `[[sort]]` with axis 2 in the key.
- **Sorting by one element's value fails.** The dot strip's demo sort ("rows by Furniture's Revenue", key `4!<metric>!!!h<element>;<attr>!1`) returns a 500 on Studio 11.6. That happens even with the demo's exact key and a correct element ID. The build sorts the dot strip's rows by the total instead. Capture the editor's element sort before relying on it.
- **Pick a slope break-by with few combinations.** Region × State Code gave about 80 lines, while Region × Customer Segment gives 12.
- **Bump-chart labels:** with the axis fixed at the rank range, the top and bottom labels (1 and 4) fall on the plot edge and aren't drawn, as on the demo.
