# Line chart catalog

The line chart is GraphMatrix **Shape `Line`, `visType 72`** (`VIS.line`). This file covers how the line is drawn. That's set
under Format > **Data Labels and Shapes** > Shape:
- **Style:** straight lines between points, or a curve.
- **Curve Smoothness:** only for the curve.
- **Line:** dash style and color.
- **Show marker:** points on or off.

Studied 2026-11-15 on "Revenue by Month" in **McDonald’s Revenue Overview** (`85D122585148DA9513EE64BDAA0F6CA0`, Shared
Studio › My Reports). The defaults below were read from the chart engine (`vi-gm.js`). `insertLine` was then checked both
ways:
- Curved: on the dashboard, viewed in Library.
- Straight with markers: on a draft, read back.

## Line style

**Rule:** when a design shows a curved line, use the curve with **Curve Smoothness 0.3**. The editor offers 0.6 when you
switch to the curve, so 0.3 has to be set explicitly. A line with corners at each point is the straight style.

| Format panel | Prop (in `allShpFmt`) | Values |
|---|---|---|
| Style: straight (first button) | `shpSmooth` | `0`, the engine default |
| Style: curve (second button) | `shpSmooth` | `1` |
| Curve Smoothness | `shpSmoothStrength` | 0 to 1; engine default 0.6; **ours 0.3** |

Each setting is written with a timestamp twin, as the editor does: `shpSmooth_tmsp`, `shpSmoothStrength_tmsp`. The same
pattern made `shpRadius` apply on bars. Stored on the McDonald's line:

```
allShpFmt "{'shpSmooth':1, 'shpSmooth_tmsp':…, 'shpSmoothStrength':0.3, 'shpSmoothStrength_tmsp':…}"
```

## Other shape settings

| Format panel | Prop | Engine default |
|---|---|---|
| Show marker | `lnMkShw` (chart prop) | `false` |
| Marker shape / size | `lnMkShp` / `lnMkSz` | 4 / 3 |
| Marker color same as line | `lnMkClrEq` | `true` |
| Line thickness | `shpBdrThk` | 2 |
| Line color (one line, nothing on Color By) | `modDefFillClr` (BGR), sent by `chartFormat`'s `seriesColor` | the palette's first color |
| Show data labels | `DataLabel` | `'Show only values'` turns value labels on |

With more than one line, the color comes from Color By instead:
- **Metric Names**, for one line per metric: color with `metricColors`.
- **An attribute**, for one line per element: color with `elementColors`.

## Client

```js
await s.insertLine({ newKey: 'W72', layout, datasetId, x: A('Transaction Date (Month)'), metric: M('Revenue'),
  color: '#FF5A1F', dataLabels: true });               // curved, smoothness 0.3, no markers: the defaults
await s.insertLine({ …, style: 'straight', markers: true });         // straight segments with point markers
await s.insertLine({ …, metrics: [M('Revenue'), M('Cost')] });      // one curved line per metric
await s.insertLine({ …, breakBy: A('Region') });                     // one curved line per region
```

`insertLine` sends `insertChart(VIS.line)`, the drop zones and one `chartFormat`. Pass other GraphMatrix props in `props`,
such as `LegendVisibleness`, `xAxTtShw` and `yAxLbShw`. A trend or reference line goes on afterwards with `trendLine`.
