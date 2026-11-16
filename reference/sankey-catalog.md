# Sankey Diagram catalog

A **Sankey Diagram** shows flows between stages. Each stage, or **level**, is one attribute, drawn as a column of nodes,
one node per element. Bands of varying width connect the nodes, and a band's width is the metric's value for that path.

Studied 2026-11-15 on **Sallie Mae Dashboard** (`BE8A2C1D69491C68F6A065A4B382045F`, Shared Studio). The source was read only,
from a separate instance; I switched pages on that instance and saved nothing. The study object is "Loan Lifecycle" (`W96`,
Chapter 2 › Loan Lifecycle Overview, page `K53`) on the *Sallie Mae Student Loan Portfolio Analytics* dataset
(`16610384F7B6415A8D6F6EC56E866C35`):
- Levels: Application Status, then Loan Status, then Curr Payment Status (renamed "Last Payment Status" in the
  visualization).
- Metric: Principal Balance.

`insertSankey` rebuilt it on a new draft as **zz Sankey study** (`B8ED32B9BF48B2144CFAC7A8B5C92114`, My Reports), with Auto
Summary on. That dashboard holds:
- the copy, with three levels
- a two-level version that keeps the plugin's own label and width defaults
- a reference grid

Read back, the copy matches the source in all of these:
- levels and their order
- the metric
- the rename
- the 9 flows ($1.9M … $9.4M)
- every setting except `cachedNodesOrder`, which the plugin writes itself (below)

Both Sankeys render in Library.

## What it is

It's a **custom visualization (plugin)**, not a built-in chart:

| | |
|---|---|
| Gallery name | Sankey Diagram (category "More") |
| `SelectedVisualization` | `Sankey` |
| Class | `CustomVisApplicationViewer` (widget type 7) |
| Plugin code | `/MicroStrategyLibrary/plugins/Sankey/javascript/mojo/js/source/` (`Sankey.js`, `SankeyDropZones.js`) |
| Requirement | "2+ attributes and 1+ metrics" |

`insertSankey` uses `insertCustomVis({ visName: 'Sankey' })`.

## Drop zones

| Zone | id | Stored as | Takes |
|---|---|---|---|
| Levels | 3 | `XAxis` | Two or more attributes, first stage first (`minCapacity 2`) |
| Metric | 4 | `YAxis` | Exactly one metric, the band width (`maxCapacity 1`) |
| Tooltip | 5 | `AdditionalMetrics` | Extra metrics shown on hover |

In the client these are `SANKEY_ZONE`. Send level positions 1-based (`unitPos: 1, 2, …`), as for the heat map. A metric
dropped on Tooltip that is already on Metric moves out of Metric, and the reverse.

## Settings (`cvp` widget props)

The source changes four settings from the plugin's defaults:

| Prop | Source | Plugin default | Effect |
|---|---|---|---|
| `showTotalOnLabel` | `true` | `false` | The node's total is printed with its name |
| `totalAlignment` | `below` | `adjacent` | Total under the name instead of beside it |
| `isDraggingOfNodesEnabled` | `true` | `false` | Viewers can drag nodes up and down |
| `nodeWidthAllMode` / `nodeWidthAllValue` | `fixed` / `54` | `auto` | Every node 54 px wide |

The source also stores `colorByNode true`, `showLabelOnNode false` and `nodeAlignment middle`, which are the defaults.

`cachedNodesOrder` is JSON of each level's element ids in their drawn order, for example
`{"<Loan Status id>": ["hDefault;<id>", "hDelinquent;<id>", …]}`. The plugin writes it when it draws or when a viewer drags
nodes, so code doesn't need to send it. Send it only to force a node order.

All values are strings (`'true'`, `'54'`). `insertSankey` converts booleans and numbers for you.

The other plugin defaults (from `Sankey.js`, `setDefaultPropertyValues`) are grouped below. Pass any of them in `props`.

**Layout**
- `isReverseGraphEnabled false`: flows right to left when true.
- `isVerticalScrollEnabled false`.
- `nodeAlignment 'middle'`.
- `density 20` with `densityMode 'auto'`.
- `nodeWidthMode 'all'`; per level: `nodeWidthByLevelMode`, `nodeWidthByLevelData`.

**Labels**
- `showLevelName true`: level names above the columns.
- `showName true`.
- `showTotal true`.
- `sourceLabelAlignment 'right'`, `waypointLabelAlignment 'right'`, `targetLabelAlignment 'left'`.
- `isTextWrapEnabled false`.

**Fonts**
- `fontFamily|Size|Style|Color` for `Global`, `Name`, `Total` and `LevelName`: 8 pt Open Sans, `#35383A`. The level names
  are bold.

**Colors**
- `colorByNode true`.
- `nodeColorPalette '[]'`, or a JSON list of colors.
- `radioForNodeColorPalettes 'nodes'`.
- `groupedNodeColor '#5C5C5C'`.
- Bands: `flowFillType 'gradient'`, `flowOpacityPercent 15`, `flowFillColor '#808080'` (used when the fill isn't a
  gradient).

**Small values**
- `isMinorValuesGroupEnabled false` groups small nodes into "Other". It is set up with:
  - `minorValuesGroupMode 'byValue'`
  - `minorValuesGroupFrom` / `To`
  - `mvgRank*`
- `minorValuesIsHidingEnabled false` hides small nodes instead, below `minorValuesHideThreshold`.

## Client

```js
await s.insertSankey({ newKey: 'W62', layout, datasetId,
  levels: ['Application Status', 'Loan Status', 'Curr Payment Status'].map(id),   // 2 or more, first stage first
  metric: id('Principal Balance') });                                               // the source's look by default
await s.rename('W62', id('Curr Payment Status'), 12, 'Last Payment Status');        // a level's display name
await s.titleBar('W62', true, 'Loan Lifecycle');
// Plugin defaults instead: props: { showTotalOnLabel: false, totalAlignment: 'adjacent', nodeWidthAllMode: 'auto' }
```

When to use it: a design shows columns of colored blocks joined by curved bands of different widths, read left to right
as stages. Each column is one level attribute, in order, and the band width is the metric.

Gotcha: the source's `cachedNodesOrder` lists five Loan Status nodes (including Grace and In School). The current data has
only three of them for approved applications, so both the source and the copy draw three.
