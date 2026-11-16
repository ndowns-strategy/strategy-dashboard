# Auto Summary

The sparkle button at the right end of the editor toolbar, **Auto Summary**, turns on an AI summary of the page for people
consuming the dashboard. **Every dashboard built from code gets it:** `saveAs` and `save` call `enableAutoSummary()` first,
unless you pass `{ autoSummary: false }`.

Captured 2026-11-12 by clicking the button in **zz shapes study** (`C13BD2AE3C42CF99F08C40BAB97241C6`, My Reports, saved with
it on) and recording the request.

## What the button does

It adds an **information window** to the current page (a floating panel stack, shown in consumption as the Auto Summary
pop-up). The window holds one **AutoNarratives** visualization whose sources are the page's visualizations. One
`mojoRWManipulation` sends:

| step | action |
|---|---|
| info window | `addNewPanelStack { parentPanelKey: <page>, nodeKey: <stack>, isInfoWindow: true }` |
| place it | the page's layout re-sent with `ifwChildren: [{ k: <stack>, t: 'flc', fixed: '0', hidden: 0, width: '50\|174px', height: '50\|322px', left: '25\|87px', top: '25\|161px' }]` |
| panel | `addPanel { nodeKey: <panel>, parentKey: <stack>, index: 0, titlePattern: 0 }` and its layout = the narrative at 100% |
| narrative | `copyUnit K51 → <viz>`, `createDefaultDropZones` (widgetType 7), visualization `AutoNarratives` with `CustomVisApplicationViewer` and `cvp` props `autoNarrativeAutoRefresh`, `isPredefinedNLG`, `preDefinedNLGShowInConsumption` = true; title bars off; `EnableIFOnGrid 0`; `changeGridDisplayMode 1` |
| instruction | `setProperty pri 17` with `{ instruction, hasFormatInstruction: false, preDefinedNLGInInfoWindow: true, recommendations: [{ vizId: 'nk-re-<viz>', skipCalculation: true, removeDataLimit: true, algorithms: {} }] }`, `isInsertingPredefinedNLG: true` |
| sources | `setGridPropsRMs` (`nk-re-<viz>` → `<viz>`) and `setNLGSources { associatedNodes: [<page's visualizations>] }` |
| window look | narrative container `ZIndex 2, WindowState 2`; stack: no borders, `StyleForSwitchingPanel 6`, `TitleBarDisplay 1`, `UseAsInformationWindow 1`, `TabCloseToDismissInfoWindow 0`, `IndependentNodeSelector 0`, Title **"Information Window 999999 (NLG one click)"** |

The built-in instruction is in the client as `AUTO_SUMMARY_INSTRUCTION`: it asks for an overall summary, top and bottom performers,
trends, patterns, anomalies and actionable insights.

Saved, the page reads `ck: { <stack>: 1 }` and `layoutXML.ifwChildren`. The stack is `{ t: 8, ifw: "true", ttl: "Information Window
999999 (NLG one click)" }`. The narrative is `{ t: 522, vis: { vn: 'AutoNarratives' }, an: [{ k: <source> }] }`.

## From code

```js
await s.enableAutoSummary();                 // every page that has visualizations and no Auto Summary yet
await s.saveAs(name, folderId);              // does it for you
await s.saveAs(name, folderId, { autoSummary: false });   // opt out
```

`enableAutoSummary` reads the instance (`serverJson()`). For each page (a panel under `VisualizationsPanelStack`) it:
- skips the page if it already has an "NLG one click" window, or has no visualizations;
- takes the page's direct visualizations (unit type 521) as sources;
- picks the next free `W` keys;
- adds the window to the page's **current** `layoutXML`, so it runs last, after the layout is final.

Shapes, text and selectors are not sources, matching the editor.

## Verified (2026-11-12)

**Auto Summary test (built from code)** (`996CDCAD35499C4B81B449A0950D8265`, My Reports) is a grid saved with `saveAs`. Read back,
it has the window `W1` "Information Window 999999 (NLG one click)" on page K53 (`ck` + `ifwChildren`), and the AutoNarratives
`W3` with source K52. A second `enableAutoSummary()` added nothing. In Library the sparkle **Auto Summary** button appears in
the viewer toolbar (a dashboard saved without it has none) and opens a **Page Summary** of the grid: sorted performance,
trends and insights.

**Two pages.** "Auto Summary test 2 pages (built from code)" (`DA82249DBF411080DBCCF68F66BFF4C9`) has two pages:
- Page 1: Parking Lot grid.
- Page 2: Lot Type grid.

`saveAs` gave each page its own window, each summarizing only its own grid (page 1: K52; page 2: W81). In Library, the page 2
Auto Summary summarizes Lot Type (Garage 570, Surface 175).
