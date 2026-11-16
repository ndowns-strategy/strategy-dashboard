# Heat Map catalog

A **Heat Map** shows one rectangle per attribute element. The rectangle's **size** comes from one metric and its **color**
from another, so big-and-orange or small-and-blue cells stand out at a glance. With two or more Grouping attributes, the
rectangles are nested: each outer element gets a header, and its inner elements are tiled under it.

Studied 2026-11-15 on **Wawa 08.31 Demo** (`F7539615AA4DD9CFF3C04BB19DA85035`, Shared Studio). The source was read only,
from a separate instance. Its heat map is "Merch Category Breakdown" (`W62`, Overview page) on the *Wawa Sales Performance
Model* (`A5200AE1A0CC49D4B0EBCC4442DD58F7`).
- Grouping: Merchandise Category 3, then Merchandise Category 4.
- Color By: Retail Quantity.
- Size By: Retail Net Amount.

`insertHeatmap` rebuilt it on a new draft as **zz Heat map study** (`8947459AB9451C2D010F238F04C0FD80`, My Reports), with
Auto Summary on. That dashboard holds:
- the copy, with two Grouping attributes
- a one-attribute version
- a reference grid

Read back, the copy matches the source in all of these:
- visualization style
- Grouping order
- Color By and Size By
- the five color bands

Both maps render in Library.

## Drop zones

| Zone | id | Takes |
|---|---|---|
| Grouping | 11 | One or more attributes, outer first. One is enough; two or more nest the rectangles. |
| Color By | 7 | One metric |
| Size By | 8 | One metric |
| Tooltip | 9 | Extra metrics |

In the client these are `HEATMAP_ZONE`. Send Grouping positions 1-based (`unitPos: 1, 2, …`). With `unitPos: 0` for every
attribute, the server put them in reverse order.

## How it is stored

```
vis: { wcn: 'com.microstrategy.web.vf.viewer.HeatMapApplicationViewer', vn: 'VIHeatMapVisualizationStyle', vm: 51 }
dz:  { Grp: { TemplateUnit: [{ t: 12, id, idx: 0 }, { t: 12, id, idx: 1 }] },
       ColorBy: { TemplateMetric: [{ t: 4, id }] }, SizeBy: { TemplateMetric: [{ t: 4, id }] }, visProp: { fmt: {…} } }
gsi.thresholds: { <Color By metric id>: [5 bands, "Lowest %" (ttp 1/3), 0-20 … 80-100] }
```

**Insert:** the same steps as other visualizations:
1. `copyUnit` of the page's prototype.
2. `createDefaultDropZones` with **`widgetType: 2`** (`EnumWidgetTypes.HEATMAP`).
3. A `format` with `SelectedVisualization: 'VIHeatMapVisualizationStyle'` and the HeatMap viewer class.
4. `changeGridDisplayMode 1`.

**Color:** the colors are thresholds on the Color By metric: five percentile bands, lowest 20% first. The source's bands,
kept as `HEATMAP_BANDS`, run orange to blue:

| Band | Color |
|---|---|
| 0–20% | `#fc6f02` orange |
| 20–40% | `#fbc85b` yellow |
| 40–60% | `#d9e5f2` pale blue |
| 60–80% | `#54bfd9` teal |
| 80–100% | `#3f95d6` blue |

Adding a metric to Color By from code does not create these bands, so `insertHeatmap` adds them with `metricThresholds`
(percent). Pass your own `bands` (any count; each covers an equal share) to recolor, or `[]` to skip.

## Format props (widget props, `HEATMAP_PROPERTIES` in the editor)

| Prop | Meaning | Source value |
|---|---|---|
| `mv` | Show metric values in the cells | `'true'` |
| `lb` | Labels: `On`, `Off`, `Proportional` | `'On'` |
| `he` | Header type (where the group headers sit) | `'1'` |
| `th` | Theme | `'1'` |
| `la` | Layout | (not set) |
| `hcl` | Header colors, one per level | `[{'value':'#EFEFEF','opacity':1},{'value':'#E4E4E4',…},…]` |
| `bg` | Background | `{'value':'#FFFFFF','opacity':1}` |
| `fts` | Fonts (header on middle / header on top) | Open Sans, style 1 |
| `showLegend`, `lgd*` | Legend visibility and look | legend fill `#EEEEEE`, 8pt Open Sans |
| `rwHdrFill*`, `colHdrFill*`, `outBdrClr` | Header fills and outer border | `#EEEEEE`, border `#CECECE` |

`insertHeatmap` writes the first block as its defaults. Pass `props` to override any of them. The source also has the
`lgd*` / `*HdrFill*` / `outBdrClr` props, written when someone edits the Format panel; the defaults look the same.

## Client

```js
await s.insertHeatmap({ newKey: 'W62', layout, datasetId,
  grouping: [id('Merchandise Category 3'), id('Merchandise Category 4')],   // one attribute is fine too
  colorBy: id('Retail Quantity'), sizeBy: id('Retail Net Amount') });
await s.titleBar('W62', true, 'Merch Category Breakdown');
```

When to use it: a design shows tiled rectangles of different sizes and colors, often with group headers. That's a heat map
(a treemap). Read the outer headers as the first Grouping attribute. A grid shaded by value is a grid with thresholds, not
a heat map.
