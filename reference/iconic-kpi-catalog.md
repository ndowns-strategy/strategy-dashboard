# Iconic KPI catalog

The **Iconic KPI** (`ImageEnhancedKPI`, REST type `image_enhanced_kpi`) is a KPI card with an icon in a colored circle,
the metric name, one large value, the previous value, a change indicator and a small trend chart. It is a custom
visualization plugin and **has no title bar**: the metric name on the card is its heading, so `titleFormat` does not
apply. The other KPI types are in [kpi-catalog.md](kpi-catalog.md).

Studied 2026-11-23 on **KPI Disscovery** (`11C1652C384B435BFAFC5FA3ADB2D273`, Shared Studio), four Iconic KPIs of
Delivery Cost by Calendar Date (Month) on "Costco Logistics". This was read-only: the REST definition, plus
`getServerJSONResults` on an instance that was never saved. The plugin's own code
(`plugins/ImageEnhancedKPI/.../ImageEnhancedKPI.js`) explained the icon behavior. Exact values are in
[iconic-kpi-catalog.json](iconic-kpi-catalog.json).

## What can change

| Setting | Values | Stored as (cvp `properties`) |
|---|---|---|
| **Icon** | on or off; a pinned icon file | `showIcon` true/false; the file is a per-metric element map entry (below) |
| **Metric tooltip** | on or off: a (?) after the metric name that shows the **metric's description** | `metricTooltipEnabled` true/false |
| **Trend shape** | area, line, bar, none | `trendShape` `'area'`, `'line'`, `'bar'`, `'none'` |
| **Previous value label** | the text before the previous value. Empty shows "Previous <trend attribute>", e.g. "Previous Calendar Date (Month)" | `secondaryMetricName`, plus the template's widget string `previousValueLabel` |
| **Reference line** | a constant line across the trend, with a label ("Target $1,000,000") | `createdReferenceLines[<metric id>]`, `referenceLineConstantValue`, `referenceLineLabel` |
| **Change indicator** | on or off; percent change (79.8%) or the actual difference (-$1,163,410) | `trendIndicatorEnabled`; `trendIndicatorValueType` `'percentValue'` or `'numericValue'` |
| Trend fill opacity | 0–100 | `trendFillOpacity` (40 on the source, 100 on its line) |

Container border (one source card has `1pt dashed #db6657`, another `1pt solid #000`) is a normal container format, not
a KPI setting: spec `border`, `cardBorder` in the client.

Drop zones: **X Axis (3)** = the metric, **Y Axis (4)** = the trend attribute (the sparkline, and the previous period for
the comparison).

## How to spot it in an image

| What you see | Setting |
|---|---|
| A big colored circle with a white symbol left of the metric name | `icon` on (`showIcon true`) |
| Only the metric name and value at the top left | `icon` off |
| A small (?) right after the metric name | `tooltip` on |
| A soft filled wave under the values | `trend: 'area'` |
| A row of light bars under the values | `trend: 'bar'` |
| A thin line under the values (often with a dashed line and a label like "Target $1,000,000") | `trend: 'line'`, plus `referenceLine` |
| Nothing under the values: a taller card with a bigger value | `trend: 'none'` |
| "Previous <attribute name>: $x" | the default previous value label |
| "Previous Month: $x", "Prior Month: $x" | `previousValueLabel` |
| A red or green pill with an arrow and a percent | `change: 'percent'` |
| The same pill with a currency amount ("-$1,163,410") | `change: 'amount'` |
| No pill | `change: false` |

## The four source cards

| Card | Icon | Tooltip | Trend | Previous value label | Change | Other |
|---|---|---|---|---|---|---|
| `K52` | on | on | area | default ("Previous Calendar Date (Month)") | percent | border 1pt dashed #db6657 |
| `W62` | on | off | bar | default | percent | |
| `W65` | off | on | line | "Previous Month" | off | reference line 1,000,000 "Target", fill opacity 100 |
| `W69` | off | off | none | "Prior Month" | amount (`numericValue`) | border 1pt solid #000 |

The other 90+ properties are the same on all four: Open Sans text, #35383A, card alignment left, the arrow
indicator shape, and badge colors #D9232E (down), #20A76C (up) and #575A5D (flat). These badge colors belong to the Iconic KPI
and differ from the Comparison KPI's.

## The icon

The icon is an element map entry on the metric (`updateElementsPropertiesMap`, emt 2), and its `format_config` names a
Material Symbols file under `/images/material-symbols/400/rounded/`.

- **`searchIcon` is the icon Library recommends.** On every render the plugin asks
  `POST /api/searches/recommendation/icons` for an icon for the metric name and **overwrites `searchIcon`** with it.
  The source's truck is almost certainly Library's own pick for "Delivery Cost" (read from the plugin code, not tested).
- **To pin an icon, write `imageSrc`** (and `imageName`) with the file's path. The plugin draws
  `imageSrc || searchIcon` and leaves an entry with an `imageSrc` (or an uploaded `image_id`) alone. `setKpiIcon` /
  `set_kpi_icon` do this. Before 2026-11-23 they wrote `searchIcon`, and the card showed the recommended icon instead.
- `icon: true` with no file shows the recommended icon. File names use underscores, e.g.
  `delivery_truck_speed-fill.svg`, `payments-fill.svg`.

## Gotchas

- `properties` can be partial: keys left out keep the defaults. The editor sends all ~100 keys, but code doesn't need to.
- `secondaryMetricName` alone is enough for the label: a test card with only that property showed it. The source
  also stores the label as the widget string `previousValueLabel`, so `iconicKpiLook` writes both.
- `trendFillOpacity` is a number (the source has `"40"` as a string on one card, but both render the same).
- `showMetricName` is `true` on one source card and absent on the others, and they look the same. Leave it out.
- `createdReferenceLines` is keyed by the metric id, which suggests one line per metric. Only one line was tested.

## Verified

Built as **SDC iconic KPI test** (`9E579093634297E805095AAFA35AE55B`, Shared Studio › Showcase, Retail Orders Sales
Performance Model, Order Total Amount by Order Date) from [examples/iconic-kpi-test.json](../examples/iconic-kpi-test.json)
and checked in Library:
- The page's default grid K52 was converted in place.
- Every setting above rendered as sent, and every property read back exactly.
- The pinned truck and payments icons showed.
- The tooltip showed the metric's description.

## Client

```js
// Source card W65: no icon, tooltip, line with a Target line, "Previous Month", no change indicator
await s.insertKpi({ newKey: 'W70', layout });                    // or s.toIconicKpi('K52') for the page's default grid
await s.fillZones('W70', dsId, [{ zoneId: ZONE.xAxis, unitId: metricId, unitType: 4 },
                                { zoneId: ZONE.yAxis, unitId: monthId, unitType: 12 }]);
await s.iconicKpiLook('W70', metricId, { icon: false, tooltip: true, trend: 'line', previousValueLabel: 'Previous Month',
  referenceLine: { value: 1000000, label: 'Target' }, change: false, fillOpacity: 100 });
// Source card K52 with the truck pinned
await s.iconicKpiLook('K52', metricId, { icon: true, tooltip: true, trend: 'area', change: 'percent' });
await s.setKpiIcon('K52', metricId, 'delivery_truck_speed-fill.svg');
```

`iconicKpiLook(look)` (module level) returns the properties; the session method writes them, and a fourth argument of raw
properties wins over the look.

## Python builder (spec)

```json
{"id": "w69", "type": "iconic_kpi", "metric": "Delivery Cost", "trend": "Calendar Date (Month)",
 "icon": false, "tooltip": false, "trend_shape": "none", "previous_value_label": "Prior Month", "change": "amount",
 "border": {"color": "#000000", "radius": 0}, "box": [50, 50, 50, 50]}
```

| Field | Values |
|---|---|
| `metric` | required |
| `trend` | the trend attribute (Y Axis) |
| `icon` | `false` (off), `true` (on, with Library's recommended icon) or a file such as `"delivery_truck_speed-fill.svg"` (on, pinned) |
| `tooltip` | `true` / `false` |
| `trend_shape` | `area`, `line`, `bar`, `none` |
| `previous_value_label` | text |
| `reference_line` | `{"value": <number>, "label": "Target", "color": "#35383A", "style": "1pt dashed"}` |
| `change` | `"percent"`, `"amount"` or `false` |
| `fill_opacity` | 0–100 |
| `props` | raw cvp properties; they win |

`title` only names the visualization in the editor, and `title_format` is rejected. An `iconic_kpi` can take over the
page's default grid, so a page can hold only Iconic KPIs.
