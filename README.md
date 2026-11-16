# Strategy dashboard authoring from code

Build Strategy (MicroStrategy) Library dashboards with JavaScript instead of clicking through the editor. You give it a
picture of a dashboard and a dataset; it creates the chapters, pages, visualizations, text, images, filters and formatting,
then saves a real dashboard you can open in Library.

[`strategy-dashboard-client.js`](strategy-dashboard-client.js) holds the client. Every helper in it was captured by
recording what the dashboard editor sends, then checked by building real dashboards and reading them back. The
[`reference/`](reference/) folder holds the notes behind each helper: how each visualization type is stored, how to spot it
in an image, and the settings that matter.

Proven on **studio.strategy.com, Library 11.6.1000** (November 2026). Other Library versions may differ.

## Contents

| Path | What it is |
|---|---|
| [`strategy-dashboard-client.js`](strategy-dashboard-client.js) | The client: `client(token, projectId)`, its session helpers, constants (`VIS`, `ZONE`, `KPI_ZONE` …) and a worked example, `buildExample()`. The header comment lists every helper and the known gotchas. |
| [`reference/`](reference/) | One catalog per visualization or feature, plus JSON files of exact settings read from demo dashboards. See [reference/README.md](reference/README.md). |

## How it works

The client needs a **Library session**: an `X-MSTR-AuthToken` plus the session cookies issued with it. It calls the same
endpoints the editor uses, with that session. The tested way to get one is to run the client inside a signed-in Library
page, which supplies both and works with single sign-on (see [Running outside a browser](#running-outside-a-browser) for
the alternative). The calls are:

1. `POST /api/dossiers/draft/instances` creates a new, unsaved dashboard with your datasets
   (`POST /api/dossiers/{id}/instances` opens an existing one).
2. `getServerJSONResults` (on `/servlet/taskProc`) loads that instance into the editor's server state.
3. `mojoRWManipulation` (also on `/servlet/taskProc`) applies the editor's own edit actions: insert a chart, fill its drop
   zones, format it, lay out the page, and so on. Each helper sends one or more of these.
4. `POST /api/documents/{id}/instances/{mid}/saveAs` (new) or `/save` (overwrite) stores the result.
5. `GET /api/v2/dossiers/{id}/definition` and the visualization data endpoints read it back for checking.

## Requirements

- A Strategy Library account with permission to create dashboards in the project, and a dataset (cube) to build on.
- A Library session. The tested setup is a browser tab signed in to Library, and a way to run JavaScript in it:
  - **Claude in Chrome** (`javascript_tool`) in your own Chrome is the tested path.
  - The **Claude desktop app's built-in browser** works the same way once you sign in to Library there.
  - A plain **browser console** works too.

  The quick start below assumes this setup.

## Quick start

### 1. Get the client into the page

Library's Content Security Policy blocks `eval()`, `new Function()` and `<script>` tags that lack the page's nonce. So
don't fetch the file and evaluate it. Put the code itself in what you run:

- **Browser console:** paste the whole file and press Enter.
- **Claude in Chrome or the built-in browser:** paste the helpers you need, copied verbatim from the file, into a
  `javascript_tool` call body. Wrap them in a function that ends with `window.SDC = { client, bgr, VIS, ZONE, … }`, so
  later calls can use them. A trimmed copy (the utilities plus the session methods your build uses) keeps the call small.

Copying the page's nonce onto your own `<script>` tag also gets past the policy, but it's a way around the page's
security. Don't do it (Claude Code's auto mode refuses it).

### 2. Capture the auth token

Write calls need the `X-MSTR-AuthToken` the Library app sends.

```js
captureToken();                       // patches fetch and XMLHttpRequest to copy the token into window.__tok
// Now make the app send a request: open a dashboard, or push a *different* in-app route, e.g.
__mstrRouterHistory.push('/MicroStrategyLibrary/app/home');
// then check:
!!window.__tok                        // must be true before you go on
```

Pushing the route you're already on sends nothing. The token isn't in localStorage or sessionStorage, so don't go
looking for it there.

### 3. Find the project and dataset ids

- **Project id:** the first id in a Library dashboard URL (`/MicroStrategyLibrary/app/<projectId>/<dashboardId>`).
- **Dataset id:** search for it by name, or read it from a dashboard that already uses it.

```js
const H = { 'X-MSTR-AuthToken': window.__tok, 'X-MSTR-ProjectID': projectId, Accept: 'application/json' };
await (await fetch('/MicroStrategyLibrary/api/searches/results?name=My%20Dataset&pattern=4', { headers: H })).json();
// or: (await c.definition(dashboardId)).datasets
```

Then list its fields. Look metrics up in `.metrics` and attributes in `.attributes`, never a combined list: a dataset can
have an attribute and a metric with the same name.

```js
const cube = await (await fetch(`/MicroStrategyLibrary/api/v2/cubes/${datasetId}`, { headers: H })).json();
const ao = cube.definition.availableObjects;
const M = (n) => ao.metrics.find((x) => x.name === n).id;
const A = (n) => ao.attributes.find((x) => x.name === n).id;
```

### 4. Build and save

```js
const c = client(window.__tok, projectId);
const s = await c.newDashboard([{ id: datasetId, name: 'My Dataset' }]);   // page K53, default grid K52

await s.toKpiCard('K52');                                                   // reuse the default visualization
await s.fillZones('K52', datasetId, [{ zoneId: KPI_ZONE.metric, unitId: M('Revenue'), unitType: UNIT.metric }]);

await s.insertChart({ newKey: 'W62', vis: VIS.bar, layout: { t: 'b', o: 'h', children: [
  { t: 'c', k: 'K52', l: 50 }, { t: 'c', k: 'W62', l: 50 }] } });
await s.fillZones('W62', datasetId, [
  { zoneId: ZONE.xAxis, unitId: A('Region'), unitType: UNIT.attribute },
  { zoneId: ZONE.yAxis, unitId: M('Revenue'), unitType: UNIT.metric }]);

const saved = await s.saveAs('My dashboard (built from code)', await c.myFolder());
saved.id;                                                                   // the new dashboard's id
```

`buildExample()` at the end of the client is a longer worked example: a grid, a bar chart, a pie chart and a line chart.

### 5. Check it

Read the saved dashboard back (`c.definition(id)`, then the visualization data endpoints) and compare the numbers with
your source image. Then open it in Library and look at every page. Do this last: any full page load clears the client,
the session and the token from the page (see [Troubleshooting](#troubleshooting)).

## Running outside a browser

The client is plain `fetch` against Library's endpoints, so a script (Node, for example) could run it with its own
session. **This hasn't been tested.** It would take:

1. **A REST login.** `POST /api/auth/login` with a username and password returns the token in the `X-MSTR-AuthToken`
   response header. That works where standard or LDAP login is allowed. On a server that signs you in through SAML or
   OIDC single sign-on, ask an administrator for an API or identity token instead. Read credentials from environment
   variables; never put them in the code.
2. **A cookie jar.** The token is tied to the session cookies set by the same login. Send them with every later call,
   including the `/servlet/taskProc` edit calls. Whether `taskProc` accepts a session created this way is the untested
   part.
3. **Full URLs.** Set `BASE` to the server's address, e.g. `https://studio.strategy.com/MicroStrategyLibrary`.
4. **No page-only helpers.** `captureToken()` and `__mstrRouterHistory` exist only in a Library page. Pass the token
   from the login to `client(token, projectId)` instead.

If you try this, record what worked here and in the client's header.

## Helper index

All helpers live on the session that `c.newDashboard()` or `c.open()` returns. The header of the client lists them too.

| Area | Helpers | Notes |
|---|---|---|
| Structure | `addChapter`, `chapterKeys`, `switchChapter`, `addPage`, `renameChapter`, `renamePage`, `structure`, `duplicateChapter`, `deleteChapter`, `moveChapter`, `duplicatePage`, `deletePage`, `movePage` | |
| Layout | `setLayout` (tiled boxes), `setFreeformLayout` (free-form: x / y / width / height in percent, layered back to front) | |
| Charts | `insertChart`, `changeType`, `fillZones`, `chartFormat`, `chartProps` / `setChartProps`, `setMetricColor`, `metricColors`, `elementColors`, `setPalette`, `trendLine` | [line](reference/line-catalog.md), [stacked bar](reference/stacked-bar-catalog.md), [bubble](reference/bubble-catalog.md), [correlation](reference/correlation-catalog.md), [deviation](reference/deviation-catalog.md), [ranking](reference/ranking-catalog.md) |
| Special charts | `insertLine`, `insertStackedBar`, `insertBubble`, `insertDonut`, `insertHeatmap`, `insertSankey`, `insertMapbox` | [donut](reference/donut-catalog.md), [heat map](reference/heatmap-catalog.md), [Sankey](reference/sankey-catalog.md) |
| KPIs | `insertKpiCard`, `toKpiCard`, `setKpiCardProps`, `insertComparisonKpi`, `insertMultiMetricKpi`, `setKpiProperties`, `insertKpi` (Iconic), `setKpiIcon` | [KPI catalog](reference/kpi-catalog.md) |
| Grids | `addToGrid`, `moveField`, `sortByMetric`, `attributeThresholds`, `metricThresholds`, `buildModernGrid` (row sets), `buildColumnSetGrid` (column sets and microcharts) | [grid catalog](reference/grid-catalog.md) |
| Text, images, shapes | `addText`, `addRichText`, `setLink`, `insertImage`, `insertShape` | [text](reference/text-catalog.md), [shapes](reference/shape-catalog.md) |
| AI | `addNarratives` (an AI summary on the canvas), `enableAutoSummary` (the Auto Summary button) | [Auto Summary](reference/auto-summary.md) |
| Filters | `addChapterFilter`, `addDateFilter`, `addMetricFilter` (filter panel), `addCanvasSelector` (on the canvas), `addObjectSelector` (swaps attributes or metrics), `keepOnly` (one visualization) | [filter panel](reference/filter-catalog.md), [canvas selector](reference/canvas-selector-catalog.md), [object selector](reference/object-selector-catalog.md) |
| Data | `createDerivedMetric`, `createDerivedAttribute`, `createTimeAttributes`, `renameDatasetAttribute`, `numberFormat` | [time attributes](reference/time-attributes.md) |
| Look | `setTitle`, `titleBar`, `setFill`, `cardBorder`, `setWidgetProps`, `rename`, `formDisplay` | |
| Save | `saveAs`, `save` (both turn on Auto Summary first unless you pass `{ autoSummary: false }`) | |

## Key ideas

- **Keys.** Every object on a page has a key. A new draft has page `K53` with a default visualization `K52`; `K51` is a
  hidden prototype that new visualizations are copied from. New keys are yours to choose (`W62`, `W63` …): use any key
  that isn't already in the instance. That includes node keys of text boxes and images, not only visualization keys.
- **Drop zones.** Charts take attributes and metrics in numbered zones (`ZONE` for standard charts; `KPI_ZONE`,
  `DONUT_ZONE`, `HEATMAP_ZONE`, `SANKEY_ZONE` and so on for others). `UNIT.attribute` is 12, `UNIT.metric` is 4.
- **Change the type before adding fields.** `changeType` resets a visualization's drop zones.
- **Several chapters.** Call `switchChapter` before editing another chapter's pages.
- **Free-form layout last.** Call `setFreeformLayout` per page after every object is on it, before saving. It adds 2% to
  each text box's height, because a box sized exactly to its text is cut off in the viewer.
- **Colors** are sent as BGR integers; `bgr('#rrggbb')` converts them.

## House rules

These are conventions for dashboards built with this repo:

- Every saved dashboard gets **Auto Summary** (`saveAs` and `save` turn it on).
- **Line charts** are curved with a smoothness of 0.3 unless the source image shows straight lines.
- **Time attributes** ("Processed Year", "Paid Month") are created only when the source image uses one the dataset
  lacks, and only those types.
- An object on a background of the same color gets **no fill** (`setFill(..., { container: 'none' })`).
- **Linked labels** (a "‹ Back to Home" or a card title that opens a page) are plain Text boxes, not Rich Text.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Every edit fails with a 500 after one failed | A failed edit can leave the instance broken. Try one small harmless edit; if that fails too, open a fresh instance and start over. |
| A taskProc call returns 500 with no message | taskProc reports errors only in the `x-mstr-taskerrorcode` header. Calling `save` on the same instance usually surfaces the real message. |
| `window.__tok` stays false | The app hasn't sent a request since `captureToken()`. Open a dashboard or push a different route. |
| The client, session and token are gone | A full page load (navigate, reload, a link that leaves the app) clears them. Finish and save before viewing. To edit again, re-run `captureToken()`, trigger a request with `__mstrRouterHistory.push` (no reload), and `c.open(dashboardId)`. |
| A link on a text box does nothing | `setLink` only works on plain Text boxes. On Rich Text the link saves, but clicking it just selects the box. |
| `addNarratives` fails with a 500 | The instruction contains double quotes. Remove them. |
| A selector breaks the document | Give on-canvas selectors at least ~11% of the page height, and don't format a selector's title in the same edit that creates it. |
| Auto Summary fails with a 500 | A page has an on-canvas selector on an attribute unrelated to the page's metrics. Pick a selector attribute that relates to them. |
| A metric-only zone rejects a field | The dataset has an attribute and a metric with the same name and the attribute was sent. Look the id up in `availableObjects.metrics`. |

More gotchas are in the header of [`strategy-dashboard-client.js`](strategy-dashboard-client.js) and at the end of each
catalog.

## Not in this repo

Some comments and catalogs mention files that aren't checked in:

- The build scripts that verified each catalog (`build-kpi-showcase.js`, `build-text.js`, `build-shapes.js`,
  `build-filter-panel.js`, `build-grids-showcase.js`, `build-correlation-showcase.js`, `build-deviation-showcase.js`,
  `build-ranking-showcase.js`).
- Three reference pages: `reference/freeform-layout.md`, `reference/link-catalog.md` and
  `reference/chapter-page-catalog.md`. The comments on `setFreeformLayout`, `setLink` and the chapter and page helpers
  in the client cover the same ground.

Dashboard and object ids in the catalogs (for example "zz shapes study") point to dashboards in the Strategy projects
where each helper was studied, and may not exist in yours.
