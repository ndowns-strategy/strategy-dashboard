# Shape catalog

Insert > Shapes offers Line, Rectangle, Ellipse, Triangle and Polygon. Studied 2026-11-12 in **zz shapes study**
(`C13BD2AE3C42CF99F08C40BAB97241C6`, My Reports). Each shape was inserted and every format option was changed while the
requests were recorded. The editor's own code was then read for the parts the panel hides: defaults, the renderer, and the
dash and arrow values.

## How a shape is stored

A shape is a **field**, like a text box, but with `fieldType 1` and unit type **101**. Inserting one sends three actions plus the
page layout:

```js
{ act: 'addField', createNode: true, nodeKeyParent: 'K53', fieldKey: 'W63', fieldType: 1, nodeKey: 'W64', treeType: 1, fieldName: 'Rectangle' }
{ act: 'editField', fieldValue: '{"t":"Rectangle","e":"","s":{},"n":"Rectangle"}', fieldKey: 'W63', fieldType: 1, nodeKey: 'W64', ... }
{ act: 'format', unitKey: 'W63', unitType: 101, keyContext: '101\u001eW64\u001eW63', fieldKey: 'W63', nodeKey: 'W64',
  format: { FormattingPatterns: { FillStyle: 1 } } }
{ act: 'format', unitKey: 'K53', unitType: 9, format: { FormattingSize: { LayoutXML: … } }, isJson: true }   // tile it on the page
```

Every shape on a page shares one field-group node: the first insert sends `createNode: true` (node `W64`), and later ones send
`createNode: false` with the same `nodeKey`. The unit reads `{ t: 101, n: 'Rectangle', fgk: 'W64' }`.

**The look lives in the field value**, a JSON string `{ t, s, e, n }`:

| key | meaning |
|---|---|
| `t` | drawing type: `Line`, `Rectangle`, `Ellipse`, `Polygon` (a triangle is `t: 'Polygon'`) |
| `n` | the shape's name, which picks the variant: `Triangle` or `Polygon` |
| `s` | shape settings (below); `{}` means the defaults |
| `e` | an SVG string; `""` means the default style (fill `#8AC3FF`, stroke `#35383A`, width 1) |

The renderer (`mstrmojo.vi.ui.rw.DocShape`) parses `e`, takes the svg's last child (the shape element), and reads **only five
style properties** from it: `fill`, `stroke`, `stroke-width`, `fill-opacity` and `stroke-dasharray`. The geometry (points, x/y,
radius) is redrawn from `s` and the box size. So code can write a minimal SVG:

```html
<svg xmlns="http://www.w3.org/2000/svg"><defs/><rect style="fill: #d70e12; stroke: #7a0000; stroke-width: 2px;"/></svg>
```

The editor itself writes the full SVG it drew (points, markers, a height and width). Every format change re-sends the whole
value through `editField` with `altText: ""`.

## Settings (`s`) and format options

| shape | panel | `s` (defaults) | notes |
|---|---|---|---|
| Line | Line (style + color), Weight, Direction, Start, End | `{ arrowStartType: 'LINE_ARROW', arrowEndType: 'LINE_ARROW', direction: 0 }` | direction 0 horizontal, 1 vertical, 2 and 3 diagonal (down / up); arrows `NONE`, `LINE_ARROW`, `TRIANGLE_ARROW` (the code also has `CIRCLE_ARROW`, not in the menu) |
| Rectangle | Fill (color + opacity), Border (style + color), Weight, Radius | `{ p: 0, radius: 0 }` | Radius buttons: none 0, small 15, medium 25, large 35 |
| Ellipse | Fill, Border, Weight, Draw circle | `{ p: 0, toggled: false }` | `toggled: true` = circle |
| Triangle | Fill, Border, Weight, Right angled, direction | `{ p: 0, pos: 0, count: 5, toggled: false, direction: 0 }` | direction 0 up, 1 right, 2 down, 3 left; `toggled: true` = right angled |
| Polygon | Fill, Border, Weight, Sides (3–10) | same as triangle | `count` = sides (the editor sent `"6"` as a string) |

Style values, as written into `e`:

| option | SVG style | values |
|---|---|---|
| Fill / Line color | `fill` / `stroke` | the editor writes `rgb(…)` |
| Fill opacity (%) | `fill-opacity` | 50% → `0.5` (absent at 100%) |
| Weight | `stroke-width` | `3px` (1–100) |
| Border / line style | `stroke-dasharray` | solid `0`, dashed `6, 2`, dotted `2, 2` |

## From code: `insertShape`

```js
await s.insertShape({ shape: 'Rectangle', fieldKey: 'W70', nodeKey: 'W69', layout,
  fill: '#d70e12', stroke: '#7a0000', strokeWidth: 2, settings: { radius: 25 } });
await s.insertShape({ shape: 'Line', fieldKey: 'W72', nodeKey: 'W69', createNode: false, layout, stroke: '#0b5cd6', strokeWidth: 3,
  dash: 'dash', settings: { direction: 2, arrowStartType: 'NONE', arrowEndType: 'TRIANGLE_ARROW' } });
await s.insertShape({ shape: 'Polygon', fieldKey: 'W74', nodeKey: 'W69', createNode: false, layout,
  fill: '#7d3cc8', opacity: 0.5, dash: 'dot', strokeWidth: 4, settings: { count: 6 } });
```

[build-shapes.js](../build-shapes.js) builds one of each: **Shapes (built from code) v2** (`EF11E8788B4B28A1A661759CCD644033`, My Reports).
Verified 2026-11-12 in Library and in the editor, where the format panel read the values back (green fill, Draw circle checked):
- **Rectangle:** red, rounded corners, 2 px border.
- **Ellipse:** green circle.
- **Line:** blue dashed diagonal with only an end arrowhead.
- **Triangle:** orange, pointing right.
- **Polygon:** purple hexagon at 50% with a dotted 4 px border.

Gotchas:
- **`keyContext` on the FillStyle format:** it must be `'101␞<nodeKey>␞<fieldKey>'`. Without it the server ignores FillStyle and
  saves the shape's box with `background-color: #ddd`, a gray tile behind every shape (v1 of the showcase). Shapes inserted in
  the editor carry it.
- **Layout:** shapes sit in the page layout like any other tile; pass the `layout` with the shape's key in it. The editor tiles a
  new shape next to the existing ones.
- **Studying requests:** keep `keyContext` when recording the editor's requests. The recorder used here first dropped it, which
  hid the gotcha above.
