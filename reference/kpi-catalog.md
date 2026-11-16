# KPI (Performance Indicator) catalog

Studied from the demo dashboard **Tec Visual Vocabulary › Performance Indicators** (demo.microstrategy.com, read as a guest, no edits). Exact values are in [kpi-catalog.json](kpi-catalog.json); this page explains how to recognize each variant in an image and how it's built.

Strategy has three native KPI visualizations. They differ in visualization style, drop zones and where their formatting lives.

| Family | Style (`vn`) | Drop zones | Formatting stored in |
|---|---|---|---|
| KPI | `KPICardVisualizationStyle` | Metric **19**, Trend **20**, Break By **5** | `visProp.fmt`: short codes (`dm`, `gcc`, `cks`, `nfts`…) |
| Comparison KPI | `ComparisonKPI` | Metric **3**, Compare With **4**, Break By **5**, Trend **6** | `vp.cvp.properties`: JSON blob (80 keys when the editor writes it) |
| Multi-Metric KPI | `MultiMetricKPI` | Metric **3** (2+ metrics), Trend **5** | `vp.cvp.properties` (same keys as Comparison) |

Bold numbers are the `zoneId`s for `fillZones` (also `KPI_ZONE`, `CMP_ZONE`, `MM_ZONE` in the client).

A fourth card type used elsewhere in this work, **Iconic KPI** (`ImageEnhancedKPI`), is a custom visualization with an icon. It also uses the `cvp` blob.

## The seven variants

| Variant | How to spot it in an image | Build |
|---|---|---|
| **KPI** | Centered metric name and one large value; nothing else | KPI; metric = Revenue; `dm 5`, `gcc 1` |
| **KPI Trend** | Left-aligned value, green/red % badge, italic "Previous Quarter: …", filled area sparkline | KPI; metric + `trend` = Quarter; `cks.chartColor` = sparkline color (#FD6F96) |
| **KPI Break By** | Title "Metric - Element" (Revenue - Technology), pagination dots | KPI; metric + `BreakBy` = Category; `dm 1`, `gcc 3`, `smn true` |
| **Comparison** | Large value, italic "Revenue Target: $x" and a red/green (−0.1%) variance; no chart | Comparison; XAxis Revenue, YAxis Revenue Target; `layoutType 0`, `textContentTypeComparison 'indicator'` |
| **Comparison Trend** | Same plus solid bars along the bottom, left-aligned | + `SliceBy` = Quarter; `trendShape 'bar'`, `trendFillColor #FD6F96`, `cardAlignment 'left'`, `axisScaleComparison 'synced'` |
| **Comparison Break By** | "Metric - Element" title, target + variance, dots | + `BreakBy` = Category; `layoutType 1`, `showMetricName true` |
| **Multi-Metric** | One wide card split into columns, one per metric: value, ↑/↓ numeric change, "Previous Quarter: …", thin line | Multi-Metric; XAxis Revenue/Cost/Profit/Profit Margin, `BreakBy` Quarter; `layoutType 2`, `trendShape 'line'`, `trendIndicatorShape 'arrow'`, `trendIndicatorValueType 'numericValue'` |

## Formatting settings that matter

- **What text shows:** `textContentType` and `textContentTypeComparison` (`all`, `indicator`, `primaryValue`, `secondaryValue`), plus `secondaryMetricName` for the label before the comparison value.
- **Indicators:** `trendIndicatorEnabled`, `comparisonIndicatorEnabled`, `trendIndicatorValueType` (percent or numeric), `trendIndicatorShape` (badge or arrow), and badge colors `#83C962` (up), `#DB6657` (down), `#606060` (flat).
- **Chart:** `shapeType` / `shapeTypeComparison` (on/off), `trendShape` (area, bar, line), `trendFillColor` / `trendFillOpacity`, `axisScale*` (global or synced).
- **Card:** `areaFillColor` (background), `cardAlignment` (center or left), `layoutType` (single, carousel, grid).
- **Fonts:** label is Open Sans; the value is Open Sans SemiBold bold; the secondary value is Open Sans bold italic; the indicator is white. All are #35383A unless noted.
- **KPI-family codes:** `dm` (5 = single, 1 = per element), `gcc` (cards per view), `smn` (show metric name), `cks` (card background and chart color), `nfts` (per-part fonts).

## Page layout used on the demo

Free-form canvas. Cards are 494 × 189 px, three per row (x = 0 / 515 / 1031; y = 100 / 334 / 568), and the Multi-Metric card spans the full width. Title bars are hidden; section headings ("Comparison KPI") and descriptions are separate text boxes, on a light blue-gray background with white cards.

## Building them from code (verified)

Captured from the editor's KPI gallery and verified by [build-kpi-showcase.js](../build-kpi-showcase.js), which rebuilt all seven variants on Shared Studio's Business Insurance dataset in 6.6 s ("zz KPI Showcase v1" in My Reports). Every card rendered like its demo counterpart, and the values matched a reference grid.

| Family | Insert | Settings |
|---|---|---|
| KPI | `s.insertKpiCard({ newKey, layout })` | `s.setKpiCardProps(key, { dm, gcc, tst, smn, ks: 'custom', cks, nfts })` |
| Comparison KPI | `s.insertComparisonKpi({ newKey, layout })` | `s.setKpiProperties(key, { layoutType, secondaryMetricName, ... })` |
| Multi-Metric KPI | `s.insertMultiMetricKpi({ newKey, layout })` | `s.setKpiProperties(key, { layoutType: 2, ... })` |

Then `s.fillZones(key, datasetId, [{ zoneId, unitId, unitType, unitPos }])` with the zone IDs above, and `s.titleBar(key, show, title)` to show or hide the title.

Gotchas:
- `setKpiProperties` takes a partial object; keys you leave out keep the visualization's defaults. The editor sends the full blob, but code doesn't need to.
- In the KPI card's `nfts`, keep `previous_value` to `{ fc }`. Adding `fw` and `fst` rendered the previous-period line struck through.
- The previous-period label uses the trend attribute's name ("Previous Payment Date (Quarter)"). Rename the attribute in the visualization, or use one named "Quarter", for the demo's "Previous Quarter" wording.
