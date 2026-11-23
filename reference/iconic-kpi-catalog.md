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

## KPI strip: several metrics, name and value only

**How to spot it in an image:** a row of equal tiles, each with only a metric name above a large value, centered. There is
no icon, no previous value, no change badge and no trend. The tiles are often each a different color. This is
**one** Iconic KPI with all the metrics on X Axis (one card per metric), not one visualization per tile.

Studied on KPI Disscovery **Page 2** (`W89`), visualization `W94`. Five metrics: Delivery Cost, Customer Rating, Failed
Stops, Minutes Late and Planned Route Miles. The container is 1914 × 195 px with 8 px rounded corners.

| Setting (format panel) | Value on the source | Stored as (cvp `properties`) |
|---|---|---|
| Text content: metric name and value only | on | `textContentType 'label'` (others: `all` the default, `primaryValue`, `secondaryValue`, `indicator`) |
| Layout | Grid | `layoutType` 0 grid, 1 stacked, 2 horizontal, 3 vertical (`LAYOUT_TYPES` in the plugin) |
| Columns (grid) | 5, one per metric | `gridColumnCount '5'` (a grid shows min(cards, columns) per row; default 4) |
| Card alignment | middle | `cardAlignment` `left`, `middle`, `right` |
| Icon, metric tooltip | off | `showIcon false`, `metricTooltipEnabled false` |
| Trend | none drawn: no trend attribute on Y Axis | (`trendShape` stays `area`; leave the icon and trend settings on Auto) |

**Layouts.** These were all built and checked:
- **Grid:** rows of `columns` cards.
- **Horizontal:** every card in one row.
- **Vertical:** one card per row.
- **Stacked:** one card at a time, with paging dots.

**Card background (Text and Form › Card Appearance).** The panel sets either all cards or one picked card:

| Scope | Stored as | Helper |
|---|---|---|
| All cards | `areaFillColor` + `areaFillOpacity` in `properties` | look `background: {color, opacity}` |
| One card | that metric's element map entry: `format_config.areaFillColor` + `areaFillOpacity` (a string, e.g. `"100"`). It wins over the all-cards value | `kpiCardFormats` / `kpi_card_formats`, spec `cards` |
| Auto (nothing set) | `areaFillColor 'AUTO'`, `areaFillOpacity 10` | the card's palette color at 10%: a pale tint, a different one per card |

On the source, only Delivery Cost has a set color (`#ABABAB` at 100%). The other four tints are Auto.

**Always use transparency 100%** unless asked otherwise: the color then shows exactly as given. The helpers default to
100. An icon and a background on the same card share one `format_config`, so `kpiCardFormats` writes both together.

Verified as **SDC KPI strip test** (`9A7B3386784F40A5D0C9C49773B74929`, Showcase) from
[examples/kpi-strip-test.json](../examples/kpi-strip-test.json): a three-card grid strip with one exact color per card,
plus vertical (one color for all cards), horizontal (one card colored, two on Auto) and stacked. Every setting read back
as sent. `card_alignment: "left"` on the vertical strip still drew centered text; this was not investigated further.

```js
await s.toIconicKpi('K52');
await s.fillZones('K52', dsId, metricIds.map((id, i) => ({ zoneId: ZONE.xAxis, unitId: id, unitType: 4, unitPos: i + 1 })));
await s.iconicKpiLook('K52', metricIds[0], { content: 'nameAndValue', icon: false, tooltip: false,
  layout: 'grid', columns: metricIds.length, alignment: 'middle' });
await s.kpiCardFormats('K52', [{ metricId: metricIds[0], background: '#ABABAB' },
                               { metricId: metricIds[1], background: '#FFF4D6' }]);   // opacity defaults to 100
```

```json
{"id": "strip", "type": "iconic_kpi", "metrics": ["Delivery Cost", "Customer Rating", "Failed Stops", "Minutes Late", "Planned Route Miles"],
 "content": "name_and_value", "icon": false, "tooltip": false, "card_layout": "grid", "columns": 5, "card_alignment": "middle",
 "cards": {"Delivery Cost": {"background": "#ABABAB"}, "Customer Rating": {"background": "#FFF8E6"}},
 "box": [0, 0, 100, 24]}
```

## Bare KPIs with text layered on top

**The pattern.** Generated dashboards (including ones Claude makes) often show KPI tiles that mix metrics: a big value
with a line of other numbers under it, such as "On Time % 93.39% with a Target of 93.75%". There's no trend. No single
visualization looks like that. Build it as a **bare Iconic KPI plus transparent Rich Text boxes on top of its cards**:
- The KPI draws the tiles, names and values.
- Each text box adds the extra line.
- Text boxes can hold live metric values, so other metrics and words can be layered onto any card.

**This only works on a free-form page.** Layering needs objects that can overlap. An auto (tiled) layout puts every object in its own slot beside the others, so a text box can never sit on top of a card. Use `"layout": "freeform"` (the builder's only page layout so far, and `check` rejects `notes` on any other).

Studied on KPI Disscovery **Page 3** (`W101`):

| Object | What it is |
|---|---|
| `W102`, Iconic KPI | Three metrics (On Time Stops, Units, Order Value), grid, no trend attribute, `showIcon false`, `metricTooltipEnabled false`, all cards `areaFillColor #EBEBEB` at `areaFillOpacity 100`. 1914 × 137 px at the top |
| `W106`, Rich Text | `On Time % {[On Time %]}  with a Target of {[On-Time Target]}`, 9pt Open Sans #35383a, centered, on card 1 (left 0, width 600 px) |
| `W104`, Rich Text | `Average Order Value {[Average Item Value]}`, same format, on card 3 |

Both text boxes are placed after the KPI, so they sit above it. Each one's top is about 74% of the way down the card,
under the value, and it is about 26% of the card's height. Average Item Value isn't on the KPI at all: a text box can
show any metric in the dataset.

**Dynamic text.** In a Text or Rich Text value, `{[Metric Name]}` shows that metric's formatted value (93.39%,
$1,849.00), computed for the whole dataset under the current filters. The field value stores the `{[...]}` text
(the server JSON's `rv`), and `v` holds the rendered result. No other action is needed: `addRichText` /
`add_rich_text` with the token in a run's text works as is. `check` resolves every `{[...]}` name against the dataset.

**Spec: `notes`.** On an `iconic_kpi`, `notes` places the text boxes for you, one per card:

```json
{"id": "kpis", "type": "iconic_kpi", "metrics": ["On Time Stops", "Units", "Order Value"],
 "icon": false, "tooltip": false, "card_layout": "grid", "columns": 3, "background": {"color": "#EBEBEB"},
 "notes": {"On Time Stops": "On Time % {[On Time %]}  with a Target of {[On-Time Target]}",
           "Order Value": {"text": "Average Order Value {[Average Item Value]}", "size": 9, "color": "#35383a"}},
 "box": [0, 7, 100, 17]}
```

**How the notes are placed:**
- The builder works out each card's box from the KPI's `box`, `card_layout` and `columns`. That works for grid,
  horizontal and vertical layouts, but not stacked.
- It adds a centered, transparent Rich Text item `<id>_note<n>` right after the KPI: 74% of the way down the card,
  26% of the card's height, and as wide as the card.
- Keep the KPI box short, about 17% of the page height per row as on the source, so the note lands under the value.
- For a free-form layout, use plain `rich_text` items with your own boxes instead.
- **Cards without a trend are always centered.** The plugin ignores `cardAlignment` unless a trend attribute is on Y
  Axis: it always adds its `left-alignment` class and leaves the rest to CSS. So notes default to centered on those
  KPIs (and follow `card_alignment` when there is a trend). A note's own `align` wins.
- Numbers the dataset lacks, such as a change percent, an average or a count filtered to one element, come from
  top-level `derived_metrics`. Example: [examples/imt-advisor-kpis.json](../examples/imt-advisor-kpis.json) rebuilds a
  generated six-KPI header on the IMT Advisor model, with every value and note matching the source image.

Verified as **SDC KPI notes test** (`F521BCC0054B29ADED50589275FE9480`, Showcase) from
[examples/kpi-notes-test.json](../examples/kpi-notes-test.json):
- A three-card row matches Page 3's layout, and "Quantity 382 at 10,669.88 per unit" draws under the first value.
- A two-row grid puts notes on its second and third cards, one of them red.

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
| `metrics` | several metrics instead of `metric`: one card each (see "KPI strip") |
| `content` | `"all"` (default) or `"name_and_value"` (only the metric name and value) |
| `card_layout` | `grid`, `stacked`, `horizontal`, `vertical` |
| `columns` | cards per row in a grid (use the number of metrics for one row) |
| `card_alignment` | `left`, `middle`, `right` |
| `background` | `{"color": "#E8EEF9", "opacity": 100}`: every card. Opacity defaults to 100 |
| `cards` | `{"<metric>": {"background": "#ABABAB", "opacity": 100, "icon": "route-fill.svg"}}`: per card; wins over `background` |
| `labels` | `{"<metric>": "YEAR TO DATE SALES"}`: the name shown on that card (`renameUnit` in the visualization) |
| `notes` | `{"<metric>": "text with {[Metric]} values"}`, `{"text", "size", "color", "align"}` or `{"runs": [{"text", "color", "bold"}, ...]}` (e.g. a green change before gray text): a Rich Text line layered under that card's value (see "Bare KPIs with text layered on top") |
| `props` | raw cvp properties; they win |

`title` only names the visualization in the editor, and `title_format` is rejected. An `iconic_kpi` can take over the
page's default grid, so a page can hold only Iconic KPIs.
