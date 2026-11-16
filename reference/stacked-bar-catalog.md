# Vertical Stacked Bar Chart catalog

The gallery's **Vertical Stacked Bar Chart** (Bar category, second row, first tile) is its own chart type. The gallery
describes it as using "2+ attributes and 1+ metrics": one attribute on the category axis and one that splits each column
into stacked segments. It is **not** the plain Vertical Bar Chart with a Stacked subtype.

Studied 2026-11-15 from the user's McDonald's screenshot, where the "Revenue by Transaction Date Month" columns stack a black
segment under an orange one:
- Each segment has its own rounded corners.
- A thin white line separates the two segments.

The settings were read from the editor code (`mojo-dossier.js`, `vi-gm.js`). The chart was then rebuilt on
**McDonald’s Revenue Overview** (`85D122585148DA9513EE64BDAA0F6CA0`, Shared Studio › My Reports), where it renders like the
screenshot.

## The type

| | Plain vertical bar | Vertical Stacked Bar Chart |
|---|---|---|
| Template (`EnumVisualizationTemplates`) | `GRAPHMATRIXVERTICALBARAUTOMATIC` | `GRAPHMATRIXVERTICALBARSTACKED` **6** |
| `visType` / `userVisType` | 70 | **6** |
| `Subtype` | Automatic | Stacked |
| Client preset | `VIS.bar` | **`VIS.stackedBar`** |

The first McDonald's build used `{ ...VIS.bar, subtype: 'Stacked' }`. It stacked, but it is a different chart type from the
one in the gallery.

## What stacks

| Zone | id | Takes |
|---|---|---|
| X axis | 3 | The category attribute (Transaction Quarter) |
| Y axis | 4 | The metric (Revenue) |
| Break By + Color By | 5 + 7 | The stacking attribute (Item Type: Beverages / Food) |

Stacking two **metrics** with Metric Names on Color By also works. Don't do it when the metrics use different units. Revenue
(dollars) stacked with Quantity (item counts) drew columns with meaningless proportions.

When the dataset has no attribute with the segments the image shows, create a derived attribute. For example:

```
Item Type = If([Category]@[Category] = "Beverages", "Beverages", "Food")
```

Beverages is about 27% of revenue, the black share in the screenshot.

## Rounded segments and the white separator

| Setting | Where | Value |
|---|---|---|
| Corner rounding | `allShpFmt.shpRadius` (with `shpRadius_tmsp`) | 0 to 50; 30 matches the screenshot |
| **Round each segment** | chart prop **`shpRadiusStyle`** | `'0'` (`EnumShapeRadiusStyle.SEPARATE`): every segment gets its own corners |
| Round the stack as one | `shpRadiusStyle` | `'1'` (`COMBINE`, the editor's default): only the stack's outer corners are rounded |
| Separator line | `allShpFmt.shpBdrClr` / `shpBdrThk` / `shpBdrStyle` / `shpBdrCmbStyle` | white `16777215` (BGR), 1, 0 (solid), 1 |

Bars already default to a 1 px light gray border (`shpBdrClr 15461355`, `#EBEBEB`), so the separator is that border turned
white. The stored props read back as:

```
visType '6', Subtype 'Stacked', shpRadiusStyle '0',
allShpFmt "{'shpRadius':30, 'shpRadius_tmsp':…, 'shpBdrClr':16777215, 'shpBdrThk':1, 'shpBdrStyle':0, 'shpBdrCmbStyle':1}"
```

## Client

```js
await s.insertStackedBar({ newKey: 'W73', layout, datasetId,
  x: A('Transaction Quarter'), metric: M('Revenue'), stackBy: A('Item Type'),
  colors: { Beverages: '#111111', Food: '#FF5A1F' },          // element names when stacking by an attribute
  radius: 30, separate: true, separator: { color: '#FFFFFF', width: 1 },
  props: { LegendVisibleness: 'Hide', yAxLbShw: 'false' } });
// Stacking metrics instead: metrics: [M('A'), M('B')], colors: { [M('A')]: '#hex', … }
```

The same `shpRadiusStyle` and border settings apply to the horizontal stacked bar (`VIS.hbarStacked`, visType 9).

When to use it: columns split into colored segments, often with a gap between segments, means a stacked bar. Read the
segment colors as the stacking attribute's elements, and look for one whose shares match the segment heights.
