# Donut chart catalog

The gallery's **Donut Chart** (Pie category) is a **custom visualization (plugin)**: `DonutChart`, class
`CustomVisApplicationViewer` (widget type 7). It isn't the GraphMatrix ring (`VIS.ring`, visType 62).
- The gallery's summary: "Shows the composition of a total value divided by category, with the total displayed in the
  center." It uses 1+ attributes and 1+ metrics.
- Plugin code: `/MicroStrategyLibrary/plugins/DonutChart/javascript/mojo/js/source/` (`DonutChart.js`,
  `DonutChartDropZones.js`).

Studied 2026-11-15 on "Revenue by Category" in **McDonald’s Revenue Overview** (`85D122585148DA9513EE64BDAA0F6CA0`, Shared
Studio › My Reports). The donut in the user's screenshot has:
- a thin ring
- small gaps between slices
- rounded slice ends
- "$14,967.88 / Revenue" in the center
- a legend with each category's value under its name

`insertDonut` builds exactly that, and the result was checked in Library. The center total is the **sum of the slices**:
$14,967.88 here, the same as the screenshot. The page's overall revenue is $14,367.88, because the category totals add up to
more than overall revenue.

## Drop zones (the plugin's order)

| Zone | id | Stored as | Takes |
|---|---|---|---|
| Angle | 3 | `XAxis` | One metric: the slice size |
| Color By | 4 | `YAxis` | One attribute: the slice colors (normally the same as Slice) |
| Slice | 5 | `BreakBy` | One attribute: one slice per element |
| Target | 6 | | One metric: progress-donut mode against a target |
| Break By | 7 | | One attribute: one donut per element |

In the client these are `DONUT_ZONE`. Each zone takes a single object (`maxCapacity 1`).

## Settings: one `unifiedProperty` JSON in `cvp`

| Property | Plugin default | Our look | Effect |
|---|---|---|---|
| `innerRatio` | 80 | 80 | Hole size in percent: 80 is a thin ring, lower is thicker |
| `padding` | 2 | 2 | Gap between slices (px) |
| `shapeRadius` | `'6%'` | `'6%'` | Rounded slice ends |
| `showDataLabel` | true | true | Center label on |
| `dataLabelType` | 6 | 6 | Center content: `DONUT_LABEL` value 2, text 4, **text and value 6** ("$14,967.88" over "Revenue") |
| `showLegend` | true | true | Legend on |
| `showLegendTitle` | **true** | **false** | The screenshot's legend has no title |
| `legendValueType` | 2 | 2 | The value under each legend item |
| `legendContentType` / `textContentType` | `'all'` | `'all'` | |

Other properties (pass in `props`):

**Fonts**
- `allFontOptions`, `labelFontOptions` (the center label, `#909598`), `valueFontOptions` (the center value, bold).
- `lgdAllFontOptions`, `lgdTitleFontOptions`, `lgdLabelFontOptions` (`#575A5D`), `lgdValueFontOptions` (`#35383A`, bold).
- Each takes `{ fontFamily, fontStyle: [bold, italic, underline, strike], fontSize, fontColor }`.

**Colors**
- `shapeOpacities`.
- `vizPaletteId` / `vizPaletteColors`.
- Slice colors are easier with `elementColors` (`colors` in the helper).

**Target mode**
- `targetType: 'fixed'` with `targetFixedValue`.

## Client

```js
await s.insertDonut({ newKey: 'W74', layout, datasetId, metric: M('Revenue'), slice: A('Category'),
  colors: { Beverages: '#FF5A1F', Breakfast: '#FDBF2D', Burgers: '#A9BCC4', … } });
await s.titleBar('W74', false);
// Thicker ring with a legend title: props: { innerRatio: 60, showLegendTitle: true }
// Center shows only the value: props: { dataLabelType: SDC.DONUT_LABEL.value }
```

When to use it: a ring chart with a big total in the middle, often with the metric name under it, and a legend listing values.
Use this plugin rather than `VIS.ring`, because only the plugin puts the total in the center.
