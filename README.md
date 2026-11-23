# Strategy dashboard authoring from code

Build Strategy (MicroStrategy) Library dashboards from code instead of clicking through the editor. You give it a picture
of a dashboard and a dataset; it creates the chapters, pages, visualizations, text, images, filters and formatting, then
saves a real dashboard you can open in Library.

There are two ways to run it:

- **The Python builder** ([`sdc/`](sdc/), recommended). Claude turns the image into one JSON spec; one command checks it and
  builds the whole dashboard over REST, with no browser. See [Python builder](#python-builder).
- **The JavaScript client** ([`strategy-dashboard-client.js`](strategy-dashboard-client.js)), run inside a signed-in
  Library page. It has every helper, including the ones not yet ported to Python (Modern Grids with row or column sets, filters, selectors, heat
  map, Sankey, bubble, stacked bar, time attributes). It is also how new visualization types get studied.

[`strategy-dashboard-client.js`](strategy-dashboard-client.js) holds the client. Every helper in it was captured by
recording what the dashboard editor sends, then checked by building real dashboards and reading them back. The
[`reference/`](reference/) folder holds the notes behind each helper: how each visualization type is stored, how to spot it
in an image, and the settings that matter.

Proven on **studio.strategy.com, Library 11.6.1000** (November 2026). Other Library versions may differ.

## Contents

| Path | What it is |
|---|---|
| [`strategy-dashboard-client.js`](strategy-dashboard-client.js) | The client: `client(token, projectId)`, its session helpers, constants (`VIS`, `ZONE`, `KPI_ZONE` …) and a worked example, `buildExample()`. The header comment lists every helper and the known gotchas. |
| [`sdc/`](sdc/) | The Python package: sign-in ([`transport.py`](sdc/transport.py)), the editor actions ported from the JS client ([`session.py`](sdc/session.py)), the spec checks ([`spec.py`](sdc/spec.py)), the builder ([`build.py`](sdc/build.py)) and the command line ([`__main__.py`](sdc/__main__.py)). |
| [`examples/`](examples/) | Specs: [`lincoln.json`](examples/lincoln.json) (the two-page Lincoln hub; checked offline only, never built live: its dataset isn't visible to the current account) and [`retail-test.json`](examples/retail-test.json) (the live test build). |
| [`tests/`](tests/) | Offline tests: parity with the JS client, the builder against a fake server, and the sign-in question. |
| [`spike/auth_spike.py`](spike/auth_spike.py) | The first proof that a Python REST session can drive the editor. |
| [`reference/`](reference/) | One catalog per visualization or feature, plus JSON files of exact settings read from demo dashboards. See [reference/README.md](reference/README.md). |

## Python builder

### What it does

```bash
python3 -m sdc login                          # asks how you sign in (SSO, standard, LDAP), then signs in
python3 -m sdc profile "<dataset name or id>" -o work/ds.json   # the dataset's attributes and metrics
python3 -m sdc check examples/lincoln.json    # validate a spec; builds nothing
python3 -m sdc build examples/lincoln.json    # build, save, re-open and check every item
```

`build` creates a draft on the dataset, adds the pages, builds every item in the order listed (back to front), applies
the free-form layout and number formats, saves with Save As (Auto Summary on), then re-opens the saved dashboard and prints
`[OK]` or `[MISS]` for each item, plus whether each page got its Auto Summary window, with timings. A failure before Save As
leaves nothing behind (the draft is never saved). A `[MISS]` in the check comes after the save: the dashboard exists and
needs fixing or deleting. Narratives return no data, so their check only confirms the visualization answers.

First live run (2026-11-22, Strategy Showcase, "Retail Orders Sales Performance Model (global)"): two pages, 17 items,
**14 seconds**, 62 edit calls, 17 of 17 items OK, Auto Summary on both pages, both page links working in Library.

Requirements: Python 3.10+ and `requests` (listed in [`pyproject.toml`](pyproject.toml)). The tests also need Node.

### Settings and sign-in

Copy [`.env.example`](.env.example) to `.env` (gitignored) and set `SDC_BASE_URL` and `SDC_PROJECT_ID`. Any setting can
also come from the environment, e.g. `SDC_PROJECT_ID=... python3 -m sdc build spec.json` for a one-off project.

**Sign-in is asked up front.** `python3 -m sdc login` always starts with:

```
How do you sign in to Strategy Library?
  1. SSO: sign in through your browser (SAML, OIDC or any other Library sign-in page)
  2. Standard: a Strategy username and password
  3. LDAP: your directory username and password
Choose 1-3:
```

Any other command that finds no session asks the same question before it starts. Run these in a real terminal, not as a
`!` command in the chat, because they read hidden input. `SDC_AUTH=sso|standard|ldap` in `.env` makes that answer the
default (press Enter), and `login --method sso` skips the question.

- **SSO.** Sign in to Library in your browser as usual. The login prints one line to run in that tab's developer console
  (type `allow pasting` first if Chrome asks). The line reads the tab's session token (`GET /api/auth/token`), asks for a
  short-lived identity token (`POST /api/auth/identityToken`) and shows it in a dialog, selected: press Cmd+C and paste it
  at the prompt. Python exchanges it (`POST /api/auth/delegate`, `loginMode -1`) for its own Library session.
- **Standard / LDAP.** Asks for the username and password (hidden). `SDC_USERNAME` and `SDC_PASSWORD` in `.env` become
  the defaults (press Enter). Uses `loginMode` 1 or 16, where the server allows it.

Whichever you pick, the session (token and cookies, never the password) is cached in `~/.config/sdc/`, readable only by
you, and reused by later commands until it expires. `whoami` shows who and which method; `logout` ends it.

For scripts with no terminal: set `SDC_AUTH=standard` (or `ldap`) with `SDC_USERNAME` and `SDC_PASSWORD`, and a command
with no cached session signs in with them without asking. Without those it stops and says to run `sdc login`.

Every command checks first that the session can see `SDC_PROJECT_ID` and lists the projects it can see if not.

Learned on the way (2026-11-22): a cookie-only call to `/api/auth/identityToken` fails ("Access token not provided"), so
the console line reads the token first. DevTools' `copy()` doesn't work after an `await`, hence the dialog. A dataset
must be **published** (cube status bit 32) or creating the draft fails with "Intelligent Cube ... is not published".

### The spec

One JSON file per dashboard. Top level:

| Field | Meaning |
|---|---|
| `name` | Dashboard name. `overwrite: true` replaces one of the same name in the folder. |
| `dataset` | `{"id", "name"}`, or just a name (searched; give the id if the search can't find it). |
| `project_id` | Optional; overrides `SDC_PROJECT_ID` for this spec. |
| `folder` / `folder_id` | Where to save; default My Reports. |
| `auto_summary` | Default `true` (house rule). |
| `number_formats` | `{"<metric>": "<format>"}` or `[{"metrics": [...], "format": "..."}]`. |
| `pages` | `[{"id", "title", "layout": "freeform", "items": [...]}]`. Only free-form layout so far. |

Every item has an `id`, a `type` and a `box`: `[x, y, w, h]` in percent of the page. Items are drawn in list order, back to
front. Text boxes get 2% added to their height (`exact_height: true` to opt out). Visualizations also take `title` (shows
the title bar with that text), `title_bar: false`, `title_format` (below), `border: {"color", "radius"}` and `fill: {"container", "title"}`.

**Title bar (`title_format`).** Every visualization type has a title bar **except the Iconic KPI**. `"title_format":
{"lines": 1|2, "subtitle": "second line", "align": "left"|"center"|"right", "wrap": true|false, "font": {...},
"subtitle_font": {...}}`, plus `subtitle_align` and `subtitle_wrap` to treat the second line differently. Fonts take
`name`, `size`, `bold`, `italic`, `underline` and `color`. Details: [reference/bar-catalog.md](reference/bar-catalog.md).

| Type | Fields |
|---|---|
| `kpi_card` | `metric`, optional `trend` (attribute: sparkline and % badge), `break_by`, `props` (setKpiCardProps settings) |
| `iconic_kpi` | The Iconic KPI (no title bar): `metric`, `trend` (attribute), `icon` (`false`, `true` or a Material Symbols file such as `"payments-fill.svg"`), `tooltip`, `trend_shape` (`area`, `line`, `bar`, `none`), `previous_value_label`, `reference_line` (`{"value", "label", "color", "style"}`), `change` (`"percent"`, `"amount"` or `false`), `fill_opacity`, `props`; see reference/iconic-kpi-catalog.md |
| `chart` | `vis` (`bar`, `hbar`, `clusteredBar`, `clusteredHbar`, `line`, `area`, `pie`, `ring`, `pctHbar`, `stackedBar`, `scatter`, `combo`, ...), `zones` (`{"xAxis": "Region", "yAxis": "Revenue", ...}`, a name or a list), `series_color`, `colors` (element colors on Color By), `metric_colors`, `legend` (`false`, or `{"position": left/right/top/bottom, "align", "title", "shape": circle/square/roundedRectangle/line}`), `data_labels` (`"hide"` or a list from `text`, `value`, `percent`), `leader_lines` (`auto`/`show`/`hide`, pie and ring), `marker_size` (pie size, default 0.6; see reference/pie-catalog.md), `sort: {"metric", "ascending", "axis"}`, `reference_lines` (`[{"type": "average"|"median"|"maximum"|"minimum"|"first"|"last"|"constant", "value", "label": ["type", "metric", "value"], "metric", "color", "style"}]`), `props` (GraphMatrix props) |
| `grid` | A **Grid (Modern)**, always: `rows` (attributes), `columns` (attributes, optional), `metrics`, `merge_column_headers` (default true). Needs rows and/or metrics. |
| `line` | `x`, `metrics`, `break_by`, `style` (`curved` default at 0.3, or `straight`), `smoothness`, `color`, `markers`, `data_labels`, `metric_colors`, `reference_lines`, `props` |
| `donut` | `metric`, `slice`, `color_by`, `target`, `break_by`, `colors`, `props` |
| `narrative` | `sources` (item ids on the same page), `instruction` (no double quotes) |
| `text` | `text`, `font: {"name", "size", "bold", "italic", "color"}`, `align`, `fill` (default none), `link: {"page": "<page id>"}` or `{"url", "new_tab"}`, `tooltip` |
| `rich_text` | `runs` (as `addRichText`), `align`, `header`, `list`, `indent`, `transparent` (default true). No links: use `text`. |
| `image` | `url`, `size_mode` (`fill` default, or `fit`) |
| `shape` | `shape` (`Rectangle`, `Ellipse`, `Line`, `Triangle`, `Polygon`), `fill`, `stroke`, `stroke_width`, `settings`, `opacity`, `dash` |

Names are looked up in the dataset's attributes and metrics separately. When a name is both, write `metric:Name` or
`attribute:Name`. Each page needs at least one `kpi_card`, `iconic_kpi`, `chart` or `line`: the first becomes the page's default
visualization in place. (The default visualization is a classic Grid, so a `grid` item can't take its place; it is
inserted as a new Grid (Modern).)

`check` catches before anything is built: unknown names (with "did you mean"), ambiguous names, unknown types and zones,
boxes off the page, quotes in narrative instructions, links on rich text, links to missing pages, and narrative sources
that are missing, not visualizations, or on another page.

### How the port stays faithful

Each method in [`sdc/session.py`](sdc/session.py) is the same-named JS helper in snake_case and sends the same actions in the
same edit calls. [`tests/harness.js`](tests/harness.js) runs the JS client in Node with the network stubbed and records
what every case in [`tests/cases.json`](tests/cases.json) sends into `tests/golden.json`; [`tests/test_parity.py`](tests/test_parity.py)
runs the same cases through Python and compares call by call. After changing a JS helper or adding a case:

```bash
node tests/harness.js && python3 -m unittest discover tests
```

To port another helper: add its cases to `cases.json`, regenerate the golden file, write the Python method until the tests
pass, then add a spec type for it in `spec.py` and `build.py`.

## How it works (JavaScript client)

The client needs a **Library session**: an `X-MSTR-AuthToken` plus the session cookies issued with it. It calls the same
endpoints the editor uses, with that session. The tested way to get one is to run the client inside a signed-in Library
page, which supplies both and works with single sign-on (the [Python builder](#python-builder) is the
alternative). The calls are:

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

Done: that is the [Python builder](#python-builder). A REST session from `/api/auth/login` or `/api/auth/delegate` (token
plus cookies) is accepted by `/servlet/taskProc`, verified 2026-11-22.

## Helper index

All helpers live on the session that `c.newDashboard()` or `c.open()` returns. The header of the client lists them too.

| Area | Helpers | Notes |
|---|---|---|
| Structure | `addChapter`, `chapterKeys`, `switchChapter`, `addPage`, `renameChapter`, `renamePage`, `structure`, `duplicateChapter`, `deleteChapter`, `moveChapter`, `duplicatePage`, `deletePage`, `movePage` | |
| Layout | `setLayout` (tiled boxes), `setFreeformLayout` (free-form: x / y / width / height in percent, layered back to front) | |
| Charts | `insertChart`, `changeType`, `fillZones`, `chartFormat`, `chartProps` / `setChartProps`, `setMetricColor`, `metricColors`, `elementColors`, `setPalette`, `trendLine`, `referenceLine` | [bar](reference/bar-catalog.md), [line](reference/line-catalog.md), [stacked bar](reference/stacked-bar-catalog.md), [bubble](reference/bubble-catalog.md), [correlation](reference/correlation-catalog.md), [deviation](reference/deviation-catalog.md), [ranking](reference/ranking-catalog.md) |
| Special charts | `insertLine`, `insertStackedBar`, `insertBubble`, `insertDonut`, `insertHeatmap`, `insertSankey`, `insertMapbox` | [donut](reference/donut-catalog.md), [heat map](reference/heatmap-catalog.md), [Sankey](reference/sankey-catalog.md) |
| KPIs | `insertKpiCard`, `toKpiCard`, `setKpiCardProps`, `insertComparisonKpi`, `insertMultiMetricKpi`, `setKpiProperties`, `insertKpi` / `toIconicKpi` (Iconic), `iconicKpiLook`, `setKpiIcon` | [KPI catalog](reference/kpi-catalog.md), [Iconic KPI catalog](reference/iconic-kpi-catalog.md) |
| Grids | `insertModernGrid` (the default grid), `addToGrid` (classic grid only), `moveField`, `sortByMetric`, `attributeThresholds`, `metricThresholds`, `buildModernGrid` (row sets), `buildColumnSetGrid` (column sets and microcharts) | [grid catalog](reference/grid-catalog.md) |
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
- **Grids are always Grid (Modern)** unless the user asks for a classic Grid or a Compound Grid. Use
  `insertModernGrid` / spec type `grid`, or `buildModernGrid` / `buildColumnSetGrid` for row and column sets. The blank
  dashboard's default visualization (K52) is a classic Grid: turn it into a chart rather than filling it with
  `addToGrid`. See [grid-catalog.md](reference/grid-catalog.md#three-kinds-of-grid).
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
