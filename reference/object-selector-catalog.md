# Attribute / Metric Selector catalog

Insert > Filter > **Attribute / Metric Selector** puts a selector on the canvas that swaps objects, not elements. It lists
attributes or metrics, never both. Picking an item replaces one object inside each target visualization. For example, picking
"Attended Count" redraws a line chart of Active Booking Count as a line chart of Attended Count.

Studied 2026-11-15 on **Base Grid** (`384671ECCD4A4968BB0D6FAB04CDD76A`, project `1FC5A43B374C963CC773C285DF86E2F6`).
Its "Metric Selector" (`W68`) targets the line chart "Visualization 1" (`K52`, Active Booking Count by Event Start Date).
These were recorded in the editor and then undone:
- each Display Style
- an insert
- a pick in consumption mode

The insert, candidate, target and pick actions were then built on drafts and read back. A scratch dashboard,
**zz Object selector study** (`D972ABEEE84AF0F09C74FEBEC32A1791`, My Reports), holds two selectors built with
`addObjectSelector`:
- a metric selector (Drop-down) that swaps the line chart's metric
- an attribute selector (Radio Buttons) that swaps the grid's row attribute

Both swapped correctly in Library, and Auto Summary is on.

## Rules for every build

- **Title bar on**, with a title that names the kind of object being chosen: "Metric Selector", "Attribute Selector" or a
  wording that fits the design ("Select a Metric", "View by"). The editor inserts it with the title bar hidden and the title
  "Selector N".
- **Targets:** choose the visualization(s) whose object the selector should swap. Judge this from the design: usually the
  chart directly below or beside the selector, or every chart that shows the same metric. For each target, name the object
  to replace (`replace`): the metric (or attribute) that visualization shows now.
- **Candidates:** the other objects to offer. The target's own object is listed first and is the default, so the Base Grid
  selector offers 5 metrics while holding 4 candidates.
- **Display Style:** Drop-down unless the design shows another.

## How it is stored

```
W68: { t: 111, ct: '8', ck: '1\u001eW67\u001eW68', style: 0, multi: false, httl: true, ttl: 'Metric Selector', n: '',
       tks: 'K52', cgb: { 0: 'K68' }, showall: false,
       elms: [{ v: 'i<metricId>;<metricId>', n: 'Attended Count', t: 2, did }, …] }
K68: { t: 11, pnk: 'K53', replace_object: '<Active Booking Count id>', replace_object_type: 4, scs: [{ ckey: 'W68' }] }
K52: { pnk: 'K68', … }                 // the target now sits under the group unit, not the page
```

- `ct "8"` marks an object selector. An element selector has `ct "1"`.
- The REST definition reports it as `selectorType: 'object_replacement'` with `availableObjectItems`.
- Items are written `i<id>;<id>` for metrics (`t 2`) and `U<id>;<id>` for attributes (`t 18`).
- Each target gets a group unit (`t 11`) holding the replaced object. The target visualization moves under that group.
  Code that walks a page's units must look one level down. `enableAutoSummary` does this, and before that fix it skipped
  targeted visualizations.

## Actions

| Step | Action |
|---|---|
| Insert | `{ act: 'addControl', parentKey, nodeKey, ctlKey, isUC: false, unitType: -1, unitId: '', targetKeys: [], ctlType: 8, gpType: 3, isParameterSelector: false }` |
| Candidates | `{ act: 'setCandidateObjects', keyContext, ctlType: 8, units: [{ id, tp: 4 }] }` (`tp 12` for attributes) |
| Target | `{ act: 'addControlTarget', keyContext, tgtKey, isUC: true, rplObjId: <object in the target>, rplObjTp: 4 }` |
| Change the replaced object | `{ act: 'replaceControlTarget', ctlType: 8, rplObjId, rplObjTp, nodeKey: <group key> }` |
| Title bar | `format` formatType **5** `{ FormattingView: { ShowTitleBar: 1 } }` |
| Title | `format` formatType 1 `{ FormattingView: { Title: 'Metric Selector' } }` |
| Display Style | `format` formatType 1 `{ FormattingSelector: { Style, Multiselect, Orientation: 1 } }` |
| Pick | `{ act: 'setSelectorElements', keyContext, ctlKey, elemList: 'i<id>;<id>', include: true, isVisualization: false, tks }` |

**Gotcha:** leave `excludeCtp` out of `addControlTarget`. The element selector sends `excludeCtp: true`. On this selector,
that records the target (`tks`), but no group is made and picks change nothing. The editor's `changeAMSelectorTargets`
leaves it unset.

What the editor sends on insert:
- `addControl` (above).
- `ShowTitleBar: 0`.
- `{ ItemWidthMode: 0, ExportAsShownOnWeb: 1, Style: 6, Multiselect: 0 }` with `Title: 'Selector N'`. Link Bar is the
  insert default.
- `Orientation: 1`.
- A new layout box `{ t: 'c', f: true, l: 42, k }` at the top of the page.

Dropping objects from the dataset then sends `setCandidateObjects` with the full list.

## Display styles

Only five are offered. Each sends one `format` action:

| Style | `Style` | Format panel extras |
|---|---|---|
| Link Bar | 6 | Make all items the same width |
| Button Bar | 5 | Make all items the same width |
| List Box | 2 | |
| Radio Buttons | 3 | Make all items the same width; no "Allow multiple selections" |
| Drop-down | 0 | |

Check Boxes, Slider and Search Box are not offered. The editor sends `Multiselect: 0` for every style, but the Format panel
still has "Allow multiple selections" for all of them except Radio Buttons.

The ⋮ menu is shorter than an element selector's:
- Unset Selector
- Display Style
- Edit Targets
- Hide Title Bar
- Hide Context Menu
- Duplicate, Copy to, Format, Copy / Paste Formatting, Rename, Delete

It has no Include / Exclude, sorting, Selection Required or Sync.

## Client

```js
await s.addObjectSelector({ pageKey: 'K53', nodeKey: 'W90', ctlKey: 'W91', kind: 'metric', title: 'Metric Selector',
  objects: ['Attended Count', 'Seat Capacity', 'Parking Requested', 'Attended (incl. walk-ins)'].map(id),
  targets: [{ key: 'W62', replace: id('Active Booking Count') }] });            // Drop-down, title bar on by default
await s.addObjectSelector({ pageKey: 'K53', nodeKey: 'W92', ctlKey: 'W93', kind: 'attribute', title: 'Attribute Selector',
  style: SELECTOR_STYLE.radio, objects: ['Building Name', 'Event Type'].map(id), targets: [{ key: 'K52', replace: id('Campus Name') }] });
```

Pass `selected: <id>` to start on one of the candidates instead of the visualization's own object.
