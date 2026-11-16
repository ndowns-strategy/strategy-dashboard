# On-canvas selector catalog (Element / Value Filter)

The toolbar Filter button (Insert > Filter) offers Element / Value Filter, Attribute / Metric Selector, Legend Selector,
Panel Selector and Parameter Selector. This file covers **Element / Value Filter**: a selector placed on the page canvas.
It is separate from the chapter Filter Panel (see [filter-catalog.md](filter-catalog.md)).

**When to use the canvas at all:** if a design shows 3 or more filters near each other, such as a sidebar of drop-downs or a
row of filters, put every one of them in the Filter Panel (`addChapterFilter`) instead of on the canvas. Use on-canvas
selectors only for one or two filters that stand alone.

Studied 2026-11-15 on **Base Grid** (`384671ECCD4A4968BB0D6FAB04CDD76A`, project `1FC5A43B374C963CC773C285DF86E2F6`).
Dataset: *Company Campus Session & Parking Reservations* (`6AD04CFB3B3B467E9A7A7BD76B5324CC`). Each Display Style was
switched in the editor's Format panel while the requests were recorded, then set back. A test filter was inserted and then
undone. The editor's code was read for the parts the panel hides. The new defaults were built on a separate instance and read
back. Nothing was saved.

## Defaults for every build

| Setting | Value | How it is sent |
|---|---|---|
| Title bar | **shown**, with the attribute name as its text | `format` formatType **5** `FormattingView.ShowTitleBar: 1`, plus formatType 1 `FormattingAppearance.Name` |
| Allow multiple selections | **on** | `FormattingSelector.Multiselect: 1` |
| Display Style | **Drop-down** unless the design shows another | `FormattingSelector.Style: 0` |

`addCanvasSelector` uses these defaults. Pass `name` (the attribute's display name), or the title bar is blank.

The editor does not use these defaults on its own:
- A new filter is inserted with `ShowTitleBar: 0`.
- When an attribute is dropped on it, the editor picks the style from the attribute's element count. Up to 15 elements gets
  Link Bar, up to 100 gets Check Boxes, and anything larger gets Search Box (`getCtrlStyleFromDatasetUnit`).

## The sample selector (Session, `W63`)

The REST definition (`pages[].selectors[]`) shows a summary of the selector:

```
{ key: 'W63', name: 'Session', selectorType: 'attribute_element_list', displayStyle: 'combo_box', hasAllOption: true,
  targets: [{ key: 'K52' }], multiSelectionAllowed: true,
  currentSelection: { selectionStatus: 'included', elements: [{ id: 'hSES-2026-002;F606BF27…', name: 'AI in Investment Operations' }] } }
```

The instance JSON (`getServerJSONResults`) has the full unit:

| key | value | meaning |
|---|---|---|
| `t` | 111 | selector unit |
| `ct` | `"1"` | element selector (`"8"` is an object/parameter selector) |
| `ck` | `1\u001eW62\u001eW63` | key context: `1`, node key, control key |
| `style` | 0 | Display Style (table below) |
| `multi` | true | Allow Multiple Selections |
| `httl` / `ttl` / `n` | true / `Session` / `Session` | title bar shown, title text, name |
| `showall` | true | an "(All)" item |
| `include` | true | Include (false = Exclude) |
| `tks` | `K52` | targets |
| `sync` | false | Sync Selections Across Pages |
| `srcid` / `srct` | attribute id / 12 | source attribute |
| `horiz` | true | Orientation 1 (horizontal) |

The format block (`fmts`) holds the look:
- The box: 8pt Open Sans, `#35383a`, white background.
- The title (`fmts.ttl`): 12pt Open Sans, 16px high, with a 1pt `#cecece` top border.
- Selected items (`fmts.selection`): the highlight is `#0e6ff9`.

In the page layout the selector is a fixed box 118 px high.

## Display Style values

Recorded from the Format panel's Style list. Each change sends exactly one action:

```js
{ act: 'format', unitKey: 'W63', unitType: 111, formatType: 1, keyContext: '1\u001eW62\u001eW63',
  format: { FormattingSelector: { Style: <n>, Multiselect: <0|1>, Orientation: 1 } } }
```

| Menu item | `Style` | `Multiselect` the editor sends | Format panel extras |
|---|---|---|---|
| Drop-down | 0 | 1 (keeps the current setting) | Show option for all, Alias |
| Slider | 1 | 1 | Data Labels, Position |
| List Box | 2 | 0 | Show option for all, Alias |
| Radio Buttons | 3 | **always 0** | Make all items the same width |
| Check Boxes | 4 | **always 1** | Make all items the same width |
| Button Bar | 5 | 1 | Make all items the same width |
| Link Bar | 6 | 1 | Make all items the same width |
| Search Box | 9 | 1 | Hint |

Other values in the editor's enum:
- 7 metric slider and 8 metric qualification are used for metrics.
- 10 text box is used for value parameters.
- 11 is a date qualification (calendar), which `addDateFilter` uses.
- 13 is an event time range.

In the client these values are the `SELECTOR_STYLE` constant.

## Menu options and their actions

The **⋮** menu on the selector, read from the editor's code (`mojo-dossier.js`):

| Menu item | Action |
|---|---|
| Include / Exclude | `{ act: 'setSelectorInclude', keyContext, ctlKey, ctlType, include }` |
| Allow Multiple Selections | `format` formatType 1 `FormattingSelector.Multiselect` (shown above) |
| Display Style | `format` formatType 1 `FormattingSelector.Style` (shown above) |
| Hide / Show Title Bar | `format` **formatType 5** `{ FormattingView: { ShowTitleBar: 0/1 } }` (`toggleTitleBar`) |
| Rename | `format` formatType 1 `{ FormattingAppearance: { Name } }` (the title text follows the name) |
| Sync Selections Across Pages | `{ act: 'setControlSynchronized', nodeKey, ctrlKey, sync }` |
| Selection Required / Dynamic Selection | `{ act: 'setSelectorStatus', nodeKey, ctrlKey, cacs }` (`cacs` is a bit mask) |
| Unset Filter | `{ act: 'unsetSelector', keyContext, ctlKey }` |
| Display Attribute Forms | `{ act: 'setControlAttributeForms', keyContext, ctrlKey, treeType: '1', fs: [formIds] }` |
| Sort Ascending / Descending By | `{ act: 'setControlAttributeSort', nodeKey, ctrlKey, … }`; Clear sort is `clearSelectorSort` |
| Limit Element Source | `{ act: 'changeControlElementSource', keyContext, ctlElementSrc }` |
| Edit Targets… | `addControlTarget` / `removeControlTarget` (`tgtKey`) |
| "(All)" option | `{ act: 'setControlShowAll', nodeKey, controlKey, showAll }` |
| Pick elements | `{ act: 'setSelectorElements', keyContext, ctlKey, include, elemList: 'h<id>;<attrId>…' }` |

## What the editor sends on insert

Insert > Filter > Element / Value Filter sends one batch:

```js
{ act: 'addControl', parentKey: 'K53', nodeKey: 'W67', ctlKey: 'W68', isUC: false, unitType: -1, unitId: '', targetKeys: [],
  ctlType: 1, gpType: 1, isParameterSelector: false }
{ act: 'format', unitKey: 'W68', unitType: 111, formatType: 5, format: { FormattingView: { ShowTitleBar: 0 } }, keyContext }
{ act: 'format', unitKey: 'W68', unitType: 111, formatType: 1, format: { FormattingSelector: { ItemWidthMode: 0, ExportAsShownOnWeb: 1 },
  FormattingView: { Title: 'Filter 2' } }, keyContext }
{ act: 'format', … FormattingSelector: { Orientation: 1 } }          // for this selector and for each other selector on the page
{ act: 'format', unitKey: 'K53', unitType: 9, … LayoutXML }           // new box at the top: { t: 'c', f: true, l: 42, k: 'W68' }
```

Dropping an attribute on the selector adds `setControlSource` (`unitType 12`, `ctrlType 10`). It also adds the
`getCtrlActionsByStyle` formats: the style picked by element count, the name, `ExportAsShownOnWeb`, and `ItemWidthMode 1` for
large lists. Last comes `setControlShowAll`, except for Radio Buttons.

## The code path, verified

`addCanvasSelector` sends these steps in order:
1. `addControl`
2. `setControlSource`
3. `format` Style 0 / Multiselect 1 / Orientation 1
4. `format` formatType 5 ShowTitleBar 1
5. `format` Name
6. `setControlShowAll`
7. `addControlTarget` (`excludeCtp: false`; see the gotcha below)

Built on a separate instance of Base Grid, the selector read back as `style 0, multi true, httl true, n "Session",
ttl "Session", showall true, tks "K52"`. Without step 5, `n` and the title were empty.

## Gotcha: `excludeCtp` decides filter vs group-by (2026-11-15)

`addCanvasSelector` sends `addControlTarget` with **`excludeCtp: false`**. Found while building **Portfolio Health Overview**
(`B60534410443F131C8C351818390A005`, Shared Studio › My Reports) on the Agent Performance Model:
- With `excludeCtp: true`, each target is grouped by the selector's elements (the selector's `cgb` group units).
  - With nothing picked, the drop-down showed the first element (BROKER), and every target showed BROKER only.
  - With "(All)" picked, Iconic KPIs, the map and the donut legend still showed only the first group (Policy Count 24,100,
    not 63,777).
- With `excludeCtp: false`, or the key left out, the selector filters its targets. "(All)" gives the total (550,000 policies;
  MIDWEST gives 63,777), and every visualization matched the source screenshot.

To pick "(All)" explicitly, send `setSelectorElements` with `elemList: 'u;'`, the editor's `ELEM_ALL_ID`.
