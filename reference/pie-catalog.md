# Pie and ring chart catalog

GraphMatrix pie and ring charts (**Shape `Pie`**, visType 61, and **Shape `Ring`**, visType 62) and the settings that
change how one looks:
- **Graph shape:** pie or ring. This is the only difference between the two.
- **Marker size:** how much of the box the pie fills (default 0.6).
- **Data labels:** any mix of text, value and percent, and the leader lines that join a label to its slice.
- **Legend:** on or off, where it sits, its title, and the shape of its color keys.
- **Title bar:** one or two lines, each line's format, justification and wrap. This applies to pie and ring like every
  other visualization except the Iconic KPI; see [bar-catalog.md](bar-catalog.md#title-bar).

A ring with a **total in the center** is not this chart: that is the Donut Chart plugin, in
[donut-catalog.md](donut-catalog.md).

Studied 2026-11-22 on **Viz details** (`646628F3FF49BCCC2BE831BEE4BBB0F3`, Shared Studio), page **Pie/Ring Charts**
(`W178`), four charts of Advisor Count by Producer Category on "IMT Advisor Sales and Opportunity Performance Model".
Read-only: the REST definition and `getServerJSONResults` on an instance that was never saved, plus the page in Library.
The enums come from Library's own chart code (`mstrmojo.gm.EnumLegendSlot`, `EnumLeaderLineMode`, the `DataLabel` table).
Exact values for every source chart are in [pie-catalog.json](pie-catalog.json).

## How to spot it in an image

| What you see | Type and settings |
|---|---|
| A full circle cut into slices | Pie: `visType 61` (`VIS.pie`) |
| The same with a hole in the middle, and **nothing** in the hole | Ring: `visType 62` (`VIS.ring`) |
| A ring with a big total (and often the metric name) in the hole | Not GraphMatrix: the Donut Chart plugin ([donut-catalog.md](donut-catalog.md)) |
| Labels outside the slices, joined by short thin lines | Data labels with leader lines (auto shows them when labels sit outside) |
| "Active Producer 143 (59.09%)" | Labels text + value + percent |
| "Active Producer (59.09%)" | Labels text + percent |
| "59.09%" | Labels percent only |
| "Active Producer" | Labels text only |
| The pie fills most of its box | Marker size above 0.6 (0.8 and 0.9 in the source) |
| A vertical list of colors at the left or right, at its top, middle or bottom | Legend left/right with top/middle/bottom |
| A horizontal row of colors above or below the chart, at its left, center or right | Legend top/bottom with left/center/right |
| Round dots, squares, small pill shapes or short dashes beside the legend names | Legend shape circle, square, roundedRectangle or line |
| The attribute name above the legend items ("Producer Category") | Legend title on (the default) |

## Drop zones

| Zone | Spec zone | Source chart |
|---|---|---|
| Angle | `angle` (10) | Advisor Count |
| Slice By | `sliceBy` (6) | Producer Category |
| Color By | `colorBy` (7) | Producer Category, the same attribute as Slice By |

All four source charts put the same attribute on Slice By and Color By. The Python builder copies `sliceBy` to `colorBy`
for pie and ring when the spec leaves Color By out.

## The four source charts

| Chart | Shape | Data labels (`DataLabel`) | Legend (`LegendPosition`, `lgdItmShp`, title) | Marker size |
|---|---|---|---|---|
| v1 (`K62`) | Pie | text, value, percent (`Show text value percent`) | left top (4), circle, title on | default |
| V2 (`W179`) | Ring | percent (`Show only percent`) | left middle (5), square, title on | default |
| v3 (`W182`) | Pie | not set: renders text + percent there | left bottom (6), roundedRectangle, title on (`LegendTitleHide 'false'`) | 0.8 |
| v4 (`W186`) | Ring | text (`Show only text`) | right top (1), line, title off (`LegendTitleHide 'true'`) | 0.9 |

Everything else in the four charts' `fmt` is identical, including `pdlll '1'` (leader lines auto), `pso '4'` (pie sort
order) and `pnsr '1'`.

## Settings: GraphMatrix `fmt` props

All of these go through `chartFormat` / `chart_format` (a `FormattingWidget` edit). Values are strings.

### Shape

`Shape 'Pie'` + `visType/userVisType '61'`, or `Shape 'Ring'` + `'62'`, with `Subtype 'Automatic'`. Use `VIS.pie` or
`VIS.ring`.

### Marker size

| Prop | Value |
|---|---|
| `SizeType` | `'Manual'` (absent = automatic) |
| `SizeValue` | `'0.8'`, `'0.9'`, ... The editor default is 0.6 and is never stored |

Both props are needed: `SizeValue` alone is ignored.

### Data labels

`DataLabel` takes the editor's string. The strings are bits: value 2, text 4, percent 8 (hide is 1).

| Parts | Code | `DataLabel` |
|---|---|---|
| hide | 1 | `Hide` |
| value | 2 | `Show only values` |
| text | 4 | `Show only text` |
| text, value | 6 | `Show both text value` |
| percent | 8 | `Show only percent` |
| value, percent | 10 | `Show both value percent` |
| text, percent | 12 | `Show both text percent` |
| text, value, percent | 14 | `Show text value percent` |

Don't leave `DataLabel` unset and expect a fixed result: the source chart v3 has none and shows text + percent, but a
new chart built with none (the test dashboard below) shows text only. Always set it.

### Leader lines

`pdlll` (pie data label leader line): `'1'` auto (the default), `'2'` show, `'3'` hide. Auto draws them only when
Library moves labels away from their slices (all four source charts do; the smaller test charts mostly don't), so use
`show` when the image has them and the chart is roomy. Pie label position is a separate
prop, `pdlp`: 1 inside, 2 outside.

### Legend

| Prop | Values |
|---|---|
| `LegendVisibleness` | `'Show'` or `'Hide'` |
| `LegendPosition` | a slot, below |
| `LegendTitleHide` | `'true'` hides the title; absent or `'false'` shows it |
| `lgdItmShp` | `'circle'`, `'square'`, `'roundedRectangle'`, `'line'` |

`LegendPosition` slots (`mstrmojo.gm.EnumLegendSlot`). Left and right legends are laid out vertically; top and bottom
legends horizontally.

| Side | top / left | middle / center | bottom / right |
|---|---|---|---|
| right | 1 | 2 | 3 |
| left | 4 | 5 | 6 |
| top | 9 | 10 | 11 |
| bottom | 12 | 13 | 14 |

The enum also has bare `LEFT 7`, `RIGHT 8`, `TOP 15` and `BOTTOM 16`; the format panel's side + alignment choices
produce 1–6 and 9–14, so use those.

These legend props are the same on every GraphMatrix chart (bar, line, area, scatter, ...), not just pie and ring.

## Verified

Built as **SDC pie catalog test** (`D177897E86429DA9C06BCB9BAD454C4D`, Shared Studio › Showcase, Retail Orders Sales
Performance Model, Order Total Amount by Region) from
[examples/pie-catalog-test.json](../examples/pie-catalog-test.json) and checked in Library: the four source charts, plus
leader lines show (lines drawn) and hide (none), a top-center legend and a bottom-right legend (both one horizontal row,
with the title at the start of the row). Every prop read back exactly as sent.

## Client

```js
// Source chart v1: pie, all three label parts, legend left top with circles
await s.chartFormat('W80', SDC.VIS.pie, SDC.chartLook({
  dataLabels: ['text', 'value', 'percent'],
  legend: { position: 'left', align: 'top', shape: 'circle' } }));
// Source chart v4: ring, text only, legend right top with lines and no title, marker size 0.9
await s.chartFormat('W81', SDC.VIS.ring, SDC.chartLook({
  dataLabels: ['text'], markerSize: 0.9,
  legend: { position: 'right', align: 'top', shape: 'line', title: false } }));
```

`chartLook` returns the props; anything passed after it in the same object wins.

## Python builder (spec)

```json
{"id": "v4", "type": "chart", "vis": "ring", "title": "Pie/Ring Chart v4",
 "zones": {"angle": "Order Total Amount", "sliceBy": "Region"},
 "data_labels": ["text"], "leader_lines": "auto", "marker_size": 0.9,
 "legend": {"position": "right", "align": "top", "shape": "line", "title": false},
 "box": [50, 50, 50, 50]}
```

| Field | Values |
|---|---|
| `data_labels` | a list from `text`, `value`, `percent`, or `"hide"` |
| `leader_lines` | `auto`, `show`, `hide` (pie and ring only) |
| `marker_size` | a number above 0 and up to 1 (the default is 0.6) |
| `legend` | `false`, or `{position: left/right/top/bottom, align: top/middle/bottom (left/right) or left/center/right (top/bottom), title: true/false, shape: circle/square/roundedRectangle/line}` |

`legend`, `data_labels` and `marker_size` work on any chart item. Explicit `props` win over all of them.
See [examples/pie-catalog-test.json](../examples/pie-catalog-test.json).
