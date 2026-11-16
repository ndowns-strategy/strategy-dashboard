# Bubble chart catalog

A **bubble chart** plots one bubble per element (or combination of elements) on two metric axes. Color can mark a group,
and an optional third metric sets the bubble size. Without a Size By metric, every bubble is the same size, which makes it
a scatter plot. Strategy builds both from the same GraphMatrix chart: **Shape `Circle`, `visType 21`**, which is
`VIS.scatter` in the client. The correlation and ranking showcases also use it (with Size By); see
[correlation-catalog.md](correlation-catalog.md).

Studied 2026-11-15 on **Sallie Mae Dashboard** (`BE8A2C1D69491C68F6A065A4B382045F`, Shared Studio). The source was read only:
I switched pages on a separate instance and saved nothing. The study object is "Credit Score vs Status" (`W182`, Chapter 2 ›
Loan Lifecycle Overview, page `K53`) on *Sallie Mae Student Loan Portfolio Analytics* (`16610384F7B6415A8D6F6EC56E866C35`).

`insertBubble` rebuilt it as **zz Bubble study** (`9276D4792D495F9B77177CB4FB862E64`, My Reports), with Auto Summary on. That
dashboard holds:
- the copy
- a variant sized by Annual Income
- a reference grid

Read back, every drop zone of the copy matches the source (same object ids and types), as do the chart type, legend, data
labels and all five rows of values. Both charts render in Library.

## The source

| Zone | id | Object |
|---|---|---|
| X axis | 3 | Credit Score (metric) |
| Y axis | 4 | Principal Balance (metric) |
| Break By | 5 | Loan Status: one bubble per status (5) |
| Color By | 7 | Loan Status: one color per status, with a legend |
| Size By | 8 | none, so the bubbles are equal-size |
| Tooltip | 9 | Annual Income, Avg Disbursement Amt (stored as `AdditionalMetrics`) |

Settings (`visProp.fmt`, GraphMatrix):
- `Shape: 'Circle'`, `visType` / `userVisType: '21'`.
- `LegendVisibleness: 'Show'`, `DataLabel: 'Hide'`.
- Axis origins on auto.
- The `AxisScale` string holds the axis ranges the editor last measured. Its flags are false and there's no
  `MinMax: 'Custom'`, so the ranges are automatic. Don't copy it.

The rest are theme fonts and colors (8pt, `#35383A`, grid lines `#F4F4F4`).

## Client

```js
await s.insertBubble({ newKey: 'W62', layout, datasetId,
  x: M('Credit Score'), y: M('Principal Balance'),           // both axes are metrics
  breakBy: [A('Loan Status')],                                // one bubble per element; Color By defaults to the first
  tooltip: [M('Annual Income'), M('Avg Disbursement Amt')] });
await s.titleBar('W62', true, 'Credit Score vs Status');
// Bubbles sized by a third metric, semi-transparent:
await s.insertBubble({ …, size: M('Annual Income'), props: { allShpFmt: "{'shpFillTrans':'30'}" } });
```

- `breakBy` takes one or more attributes, outer first. `colorBy` defaults to the first; pass another attribute to color by a
  coarser group. The correlation showcase breaks by Category + Subcategory and colors by Category.
- `props` are GraphMatrix props merged over the source's look (legend shown, data labels hidden). Examples:
  - `allShpFmt` for transparency and borders: `"{'shpFillTrans':'70','shpBdrThk':1,…}"`
  - `xAxTtShw: 'false'` to hide an axis title
  - axis ranges via `chartFormat`'s `axisRange`
- `elementColors(attrId, { Default: '#hex', … })` sets the bubble colors per element.

## Gotchas

- **An attribute and a metric with the same name.** This dataset has an attribute *and* a metric called "Annual Income"
  (and "Annual Income Bucket"). A name lookup that searches attributes first gets the attribute. Size By then fails with a
  500, and the saved message is "The dropzone don't accept template units like attribute". Tooltip and grid columns accept
  the attribute without complaint, so the mistake is silent there. Look up metrics in `availableObjects.metrics` and
  attributes in `availableObjects.attributes`, never a combined list.
- **A narrow Size By range exaggerates differences.** The bubble area spans the metric's own min to max. Annual Income only
  ranges from $132K to $143K, so one bubble is huge and the others are tiny. Pick a Size By metric whose spread is
  meaningful.
- When a design shows equal-size dots on two numeric axes, colored by group with a legend, it's this chart without Size By.
  It isn't the Heat Map or the Sankey.
