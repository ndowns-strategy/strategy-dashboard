# Reference catalogs

Notes behind the helpers in [`strategy-dashboard-client.js`](../strategy-dashboard-client.js). Each catalog covers one
visualization type or feature. Each was studied by reading a real dashboard (a Strategy demo dashboard read as a guest, or
a study dashboard in our own project) and by recording what the editor sends. Then it was checked by building the same
thing from code and opening it in Library.

## How to use them

When you rebuild a dashboard from an image:

1. **Recognize it.** Most catalogs have a "how to spot it in an image" table. It maps what you see (a % badge, rounded
   slice ends, bubbles of different sizes) to a visualization type and its settings.
2. **Build it.** The "Client" or "Building them from code" section gives the helper call and its options.
3. **Avoid the traps.** The gotchas at the end of each catalog list what broke while it was being built.

## Catalogs

### Charts

| File | Covers | Helpers |
|---|---|---|
| [bar-catalog.md](bar-catalog.md) | Vertical, horizontal and clustered bars; the **title bar** of every visualization except the Iconic KPI (one or two lines, each line's format, justification, wrap); data label position and rotation; reference lines (max, min, average, median, first, last, constant); trend line | `insertChart`, `chartFormat`, `titleFormat`, `referenceLine`, `trendLine` |
| [line-catalog.md](line-catalog.md) | Line charts: straight or curved lines, curve smoothness, markers, data labels | `insertLine` |
| [stacked-bar-catalog.md](stacked-bar-catalog.md) | The gallery's Vertical Stacked Bar Chart (its own type, not a bar chart with a Stacked subtype), rounded segments, white separators | `insertStackedBar` |
| [pie-catalog.md](pie-catalog.md) | GraphMatrix pie and ring: shape, marker size, data labels (text/value/percent), leader lines, legend position/title/key shape. | `chartLook`, spec `legend` / `data_labels` / `leader_lines` / `marker_size` |
| [donut-catalog.md](donut-catalog.md) | The Donut Chart plugin: total in the center, thin ring, rounded slice ends, legend with values. Not the GraphMatrix ring. | `insertDonut` |
| [bubble-catalog.md](bubble-catalog.md) | Bubble and scatter charts: two metric axes, Break By, optional Size By | `insertBubble` |
| [heatmap-catalog.md](heatmap-catalog.md) | Heat Map: nested rectangles sized by one metric and colored by another, percentile color bands | `insertHeatmap` |
| [sankey-catalog.md](sankey-catalog.md) | Sankey Diagram: flows between two or more attribute levels | `insertSankey` |
| [correlation-catalog.md](correlation-catalog.md) | Scatter plot, combo (bar plus line on two axes), bubble, matrix bar | `insertChart`, `chartFormat` |
| [deviation-catalog.md](deviation-catalog.md) | Diverging bars, diverging stacked bar, tornado, stacked area: color by sign, custom origin, negated metrics | `insertChart`, `chartFormat`, `metricThresholds` |
| [ranking-catalog.md](ranking-catalog.md) | Sorted bars, bubble, dot strip, slope and bump charts: sorts and rank metrics | `insertChart`, `sortByMetric` |

### KPIs and grids

| File | Covers | Helpers |
|---|---|---|
| [kpi-catalog.md](kpi-catalog.md) | The three native KPI families (KPI card, Comparison KPI, Multi-Metric KPI) and their seven variants: plain, trend with % badge and sparkline, break by, comparison | `insertKpiCard`, `toKpiCard`, `setKpiCardProps`, `insertComparisonKpi`, `insertMultiMetricKpi`, `setKpiProperties` |
| [iconic-kpi-catalog.md](iconic-kpi-catalog.md) | The Iconic KPI: icon on/off and pinned icons, metric tooltip, trend shape (area, line, bar, none), previous value label, reference line, change indicator (percent or amount); the KPI strip (several metrics, name and value only, grid/stacked/horizontal/vertical, per-card background colors) | `insertKpi`, `toIconicKpi`, `iconicKpiLook`, `kpiCardFormats`, `setKpiIcon` |
| [grid-catalog.md](grid-catalog.md) | The three grid kinds (Grid (Modern) is the default), Modern Grids with column sets and microchart columns | `insertModernGrid`, `buildColumnSetGrid`, `buildModernGrid` |

### Text, shapes and AI

| File | Covers | Helpers |
|---|---|---|
| [text-catalog.md](text-catalog.md) | Text vs Rich Text: how each is stored, which formats the viewer keeps | `addText`, `addRichText` |
| [shape-catalog.md](shape-catalog.md) | Line, rectangle, ellipse, triangle and polygon shapes: fill, stroke, dash, arrows, rounded corners | `insertShape` |
| [auto-summary.md](auto-summary.md) | The Auto Summary button: an AI summary window added to every page | `enableAutoSummary` (called by `saveAs` and `save`) |

### Filters and data

| File | Covers | Helpers |
|---|---|---|
| [filter-catalog.md](filter-catalog.md) | The chapter filter panel: element lists, cascading filters, calendar date filters with dynamic dates, metric filters | `addChapterFilter`, `addDateFilter`, `addMetricFilter` |
| [canvas-selector-catalog.md](canvas-selector-catalog.md) | Element / Value Filter on the page canvas: display styles, targets, filter vs group-by | `addCanvasSelector` |
| [object-selector-catalog.md](object-selector-catalog.md) | Attribute / Metric Selector: swapping one object inside target visualizations | `addObjectSelector` |
| [time-attributes.md](time-attributes.md) | Creating Year, Quarter, Month and other time attributes from a date, and when to (only when the image uses one) | `createTimeAttributes` |

## JSON files

Seven catalogs have a JSON counterpart with the exact values read from the source dashboard: drop zones, widget properties
and formats for every example.

| File | Pairs with |
|---|---|
| [bar-catalog.json](bar-catalog.json) | [bar-catalog.md](bar-catalog.md) |
| [kpi-catalog.json](kpi-catalog.json) | [kpi-catalog.md](kpi-catalog.md) |
| [iconic-kpi-catalog.json](iconic-kpi-catalog.json) | [iconic-kpi-catalog.md](iconic-kpi-catalog.md) |
| [grid-catalog.json](grid-catalog.json) | [grid-catalog.md](grid-catalog.md) |
| [filter-catalog.json](filter-catalog.json) | [filter-catalog.md](filter-catalog.md) |
| [correlation-catalog.json](correlation-catalog.json) | [correlation-catalog.md](correlation-catalog.md) |
| [deviation-catalog.json](deviation-catalog.json) | [deviation-catalog.md](deviation-catalog.md) |
| [ranking-catalog.json](ranking-catalog.json) | [ranking-catalog.md](ranking-catalog.md) |

Use the Markdown file to choose a variant and the JSON when you need a setting's exact value.

## Missing pages

The client's comments also point to `freeform-layout.md`, `link-catalog.md` and `chapter-page-catalog.md`. They aren't
in this folder. Until they're added, the comments on `setFreeformLayout`, `setLink` and the chapter and page helpers in
the client are the reference.

## Adding a catalog

Follow the existing pattern:

1. Study a working example read-only (the REST definition plus the instance JSON from `getServerJSONResults`), or record
   the editor's requests while you build one.
2. Write what it looks like, how it's stored, its drop zones and the settings that matter.
3. Add or extend a helper in the client, build the example from code, and open it in Library.
4. Record the date, the source dashboard and anything that broke.
5. Add a row to the tables above and to the helper index in the [root README](../README.md).
