# Bar chart catalog

Plain and clustered bar charts (GraphMatrix **Shape `Bar`**) and the settings that change how one looks:
- **Orientation and clustering:** vertical or horizontal, one metric or several side by side.
- **Title bar:** one or two lines, each line's format, justification and wrap. This applies to every visualization except
  the Iconic KPI.
- **Data labels:** position and rotation.
- **Reference lines:** maximum, minimum, average, median, first, last or a constant.
- **Trend line.**

Stacked bars have their own catalog ([stacked-bar-catalog.md](stacked-bar-catalog.md)). Diverging and ranked bars are in
[deviation-catalog.md](deviation-catalog.md) and [ranking-catalog.md](ranking-catalog.md).

Studied 2026-11-22 on **Viz details** (`646628F3FF49BCCC2BE831BEE4BBB0F3`, Shared Studio), a reference dashboard with
18 bar charts on "IMT Advisor Sales and Opportunity Performance Model":
- Page 1: 14 vertical bars of Advisor Count by Producer Category, one setting changed per chart.
- Page 2: vertical, horizontal and the two clustered forms.

The dashboard's author wrote what each chart shows in its second title line, which made the codes below easy to decode.

How it was read: read-only. I used the REST definition and `getServerJSONResults` on an instance that was never saved, then
looked at both pages in Library. The editor actions for the title bar and reference lines were then taken from Library's
own code, replayed from Python, and checked in Library on a test dashboard (see each **Client** note). Exact values for
every source chart are in [bar-catalog.json](bar-catalog.json).

## How to spot it in an image

| What you see | Type and settings |
|---|---|
| Upright bars, one metric | Vertical bar: `visType 70` (`VIS.bar`). X = attribute, Y = metric |
| Bars running left to right, one metric | Horizontal bar: `visType 71` (`VIS.hbar`). X = metric, Y = attribute |
| Two or more bars side by side per category, upright, with a legend of metric names | Vertical clustered: `visType 7`. X = attribute, Y = 2+ metrics; Metric Names on Color By and Break By |
| The same, running left to right | Horizontal clustered: `visType 10`. X = 2+ metrics, Y = attribute |
| Numbers on or above the bars | Data labels: `DataLabel` with position `bdlp` and rotation `dlrtt` |
| A dashed horizontal line across the plot with a label at its right end ("Average", "Median 62", "Maximum Advisor Count 143") | Reference line: an entry in the metric's `mdls.mod_c` with `tp` 1–7 |
| A straight or curved fitted line through the bar tops | Trend line: `tp 256` (best fit) or `257` (linear) |
| Title centered or right-aligned, a smaller second line under it, or a title that wraps | Title bar format on the visualization container (not a chart prop); any visualization except the Iconic KPI |

## Orientation and clustering

| Chart | Shape / Subtype / visType | Drop zones |
|---|---|---|
| Vertical Bar | Bar / Clustered / **70** | X: Producer Category · Y: Advisor Count |
| Horizontal Bar | Bar / Automatic / **71** | X: Advisor Count · Y: Producer Category |
| Vertical Clustered Bar | Bar / Clustered / **7** | X: Producer Category · Y: YTD External Activity Count, YTD Internal Activity Count · Color By and Break By: Metric Names |
| Horizontal Clustered Bar | Bar / Clustered / **10** | X: YTD Internal, YTD External · Y: Producer Category · Color By and Break By: Metric Names |

Notes:
- The editor writes **Subtype `Clustered`** on a plain vertical bar too. `Automatic` (what `VIS.bar` sends) renders the
  same for one metric.
- In a clustered chart the series colors come from the palette: blue, then yellow, in Library's default theme.
- The horizontal clustered example also has square bar ends (`allShpFmt {'shpRadius':0}`) and value labels outside the bar
  ends.
- The page 2 charts carry a prop `yr` (`<Producer Category id>:1.26`), which the page 1 charts don't. It is probably the
  editor's remembered axis label ratio. It isn't needed to build one.

## Title bar (every visualization except the Iconic KPI)

**This section applies to all visualization types, not only bars:** charts, grids, KPI cards, maps and custom
visualizations. The one exception is the **Iconic KPI** (`ImageEnhancedKPI`), which has no title bar. The bar dashboard is
where it was studied. The title bar has five settings:

1. **One or two lines.** Two lines adds a second line (subtitle) under the title.
2. **The second line's text.**
3. **Each line's formatting:** font, size, style and color, set separately for the title line and the second line.
4. **The justification of the title lines:** left, center or right.
5. **Wrap text:** a long line wraps instead of being cut off.

### How it is stored (read from the source)

| Chart | Title `text-align` | Title lines (`ttlsls`) | Second line (`sttl`) | Wrap (`white-space`) |
|---|---|---|---|---|
| Left Justified | `left` | 1 | "Add bottom line" (stored but hidden: one line) | `nowrap` (off) |
| Centered | `center` | 2 | "uses 2 lines for Title" | `nowrap` (off) |
| Right Justified | `right` | 2 | Second line in a different font: title `italic bold 12pt 'Inter'`, `#c1292f`, underlined; second line `9pt 'Open Sans'` `#35383a` | absent (**on**) |

These are on the visualization **container** (the unit's `ttlsls`, `sttl`, `fmts.ttl`, `fmts.sttl`), not in the chart
props. That's why the three charts have identical chart props. Defaults on a new visualization: one line, title
`12pt 'Open Sans'` `#35383a`, left, no wrap. A new second line gets `9pt 'Open Sans'` `#35383a`.

### The editor's actions (recorded 2026-11-22)

Taken from Library's own editor code (`mojo-dossier.js`: `getTitlesLinesFmts`, `getRenameSubtitleAction`,
`getDefaultSubtitleFormatAction`, `getTitleAlignmentFmts`, the format map `alh` / `atw`). Each was then replayed from
Python on a draft and the stored result read back.

| Setting | Action | Values |
|---|---|---|
| One or two lines | `format`, formatType **1**, `FormattingView.TitlesLines` | 1 or 2. Back to 1 hides the second line and keeps its text |
| Second line's text | `{ act: 'setSubtitle', nodeKey, unitType: 521, subtitle }` | The editor sends it with the default second-line font (next row) |
| Second line's default font | `format`, formatType **3**, `FormattingFont { Bold: 0, Italic: 0, Underline: 0, Strikeout: 0, Size: 9, Color: 3815477, Name: 'Open Sans' }` | |
| Title line font | `format`, formatType **2**, `FormattingFont { Name, Size, Bold, Italic, Underline, Color }` | -1 on, 0 off; Color BGR (`bgr()`), e.g. `'3090881'` = #c1292f |
| Second line font | Same, formatType **3** | |
| Justification | `format`, formatType 2 (and 3 for the second line), `FormattingAlignment.Horizontal` | **0 left, 1 right, 2 center**. 3 and up are rejected (stored blank). Not the 1/2/3 used on text boxes |
| Wrap text | `format`, formatType 2 / 3, `FormattingAlignment.TextWrap` | **-1 wrap**, 0 one line (`white-space: nowrap`) |

`unitType` is 521 for a visualization added in the current session (a draft) and 522 for one already saved in the
dashboard. `setSubtitle` always takes 521. The title text itself is `FormattingView.Title` (`setTitle` / `titleBar`), and
showing the bar is `ShowTitleBar`.

**Client:** `titleFormat(vizKey, { lines, subtitle, align, subtitleAlign, wrap, subtitleWrap, font, subtitleFont, unitType })`
in the JS client, `title_format(...)` in Python, and `"title_format": {...}` on any visualization item in a Python spec.
`align` and `wrap` apply to both lines unless the `subtitle...` options override them. Verified 2026-11-22 in Library on
**SDC bar catalog test** (`2ED6D100854329C94A57038029A60DC0`, Strategy Showcase › My Reports, built from
[examples/bar-catalog-test.json](../examples/bar-catalog-test.json)): left, centered and right titles, second lines, and
the red italic bold underlined Inter title all render as on the source.

## Data labels

| Chart (author's note) | `DataLabel` | `bdlp` (position) | `dlrtt` (rotation) |
|---|---|---|---|
| v1: position and rotation Auto | `Show only values` | `0` | absent |
| v2: Outside End, Vertical | `Show only values` | `1` | `2` |
| v3: Inside Base, Horizontal | `Show only values` | `3` | `0` |

So `bdlp`: 0 Auto, 1 Outside End, 3 Inside Base. `dlrtt`: absent Auto, 0 Horizontal, 2 Vertical. The values in between
(`bdlp 2`, probably Inside End; `dlrtt 1`) weren't on this dashboard. Labels use `dlFntSz 8pt` and `dlFntClr 3815477`
(#35383A) from the base props.

**Client (proven path):** these are GraphMatrix props, so `chartFormat(key, VIS.bar, { DataLabel: 'Show only values',
bdlp: '1', dlrtt: '2' })`. In the Python spec, pass them in a chart's `props`.

## Reference lines

Each reference line is one entry in the **plotted metric's** model list inside the template (`gsi.mx[metric].mdls.mod_c`).
The server computes its value and returns it in the visualization's `trendref`.

| Chart | `tp` | Label shown | `la` | Value (`trendref`) |
|---|---|---|---|---|
| Maximum | **1** | "Maximum Advisor Count 143" | **7** (type + metric + value) | 143 |
| Minimum | **2** | "Minimum" | **1** (type) | 37 |
| Average | **3** | "Average Advisor Count" | **3** (type + metric) | 80.67 |
| Median | **4** | "Median 62" | **5** (type + value) | 62 |
| First | **5** | "First 143" | 5 | 143 (the first category's bar) |
| Last | **6** | "Last 62" | 5 | 62 (the last category's bar) |
| Constant | **7** | "Constant 75" | 5 | 75, from `cst: { vt: 8, vv: "75" }` |

- **`la` is a bitmask** for the label: 1 type name, 2 metric name, 4 value. The labels above were read off the rendered
  charts.
- The other fields are the same on all seven: `lv 1`, `incl 0`, `enabl 1`, `dua 0`.
- The line format (`fms`, HTML-escaped JSON) is a **dashed** (`trdRefLnStyle 1`) `#4D4D4D` (`trdRefLnClr 5066061`) line, 1 px
  thick (`trdRefLnThk 1`), with `trdRefLnCmbStyle 3`.
- The label font is Open Sans 9pt, `#35383A` (`rfLnFntFml`, `rfLnFntSz`, `rfLnFntStyle`, `rfLnFntClr`). Some entries
  store each font value wrapped with a `_tmsp` timestamp, as the editor writes it after a change.
- In Library each line is drawn across the whole plot with its label at the right end, above the line.
- **Constant** needs a typed number. The author's note says it can't take a metric or attribute.

**The editor's action (recorded 2026-11-22):** `operateTRFLine`, the same action as the trend line. The field names come
from Library's chart code (`vi-gm.js`): `refTp` becomes `lineType`, `refLbTp` becomes **`lineLabel`** (the `la` bitmask),
`refCstVl` becomes `lineConstant` and `modix` becomes `lineIndex`:

```js
{ act: 'operateTRFLine', tks: vizKey, lineType: 3, lineLevel: 1, lineLabel: 5, enabled: 1, includeBreakby: 0,
  lineConstant: '' /* or '75' for a constant */, lineIndex: 1 /* 1-based per metric */, metricId,
  format: '{&quot;trdRefLnThk&quot;:1,&quot;trdRefLnClr&quot;:5066061,&quot;trdRefLnStyle&quot;:1,&quot;rfLnFntFml&quot;:&quot;Open Sans&quot;,...,&quot;trdRefLnCmbStyle&quot;:3}' }
```

Replayed on a draft, it stored exactly what the source has (`tp`, `la`, `cst`, `fms`, `enabl 1`), and the server computed
the values (average 4,082.69, constant 5,000, maximum 5,748.89). In Library the labels read "Average Order Total Amount",
"Median 3,673.44", "Maximum Order Total Amount 5,748.89" and "Constant 5,000.00".

**Client:** `referenceLine(vizKey, metricId, { type, value, label, index, color, style, thickness, font })` in the JS
client, `reference_line(...)` in Python, and `"reference_lines": [{"type": "average", "label": ["type", "metric"]},
{"type": "constant", "value": 5000}]` on a chart or line item in a spec. Each line on the same metric needs the next
`index`; the builder numbers them for you.

## Trend line

The chart titled "Trend Line Enabled" (note: "Uses default Mode = Best Fit") stores a best-fit entry (`tp 256`, `la -1`,
`cst vv "2"`, solid line `trdRefLnStyle 0`, `trdRefLnCmbStyle 1`) with **`enabl 0`**. Its `trendref` is empty, and no
trend line shows in Library: the line is stored but switched off. The six reference-line charts after it were copied from
it and carry the same disabled entry before their own line.

**Client (proven path):** `trendLine(key, metricId, { model: 'bestFit' })` (`lineType 256`) or `'linear'` (257); see
[correlation-catalog.md](correlation-catalog.md).

## Base look (all 18 charts)

The 72 props shared by the first chart are in `baseProps` in the JSON:
- **Fonts:** 8pt everywhere: axis titles and labels, data labels, legend, reference-line labels. Text `3815477`
  (#35383A); axis titles bold (`xAxTtFntStyle 1`).
- **Axis lines:** hidden (`xAxLnStyle 99`, `yAxLnStyle 99`, thickness 0).
- **Gridlines:** light (`majorGridLnClr 16053492`, #F4F4F4).
- **Background:** white (`bgFillClr 16777215`).
- **Axis labels:** wrapped and nested (`xAxLbWrapText`, `xAxLbNestedLabel`).
- **Axis range:** stored per chart in `AxisScale`, the value range at save time. It doesn't need to be copied: the server
  recomputes it.

## Python builder

Everything on the source dashboard can be built from a spec. [examples/bar-catalog-test.json](../examples/bar-catalog-test.json)
does it: 8 charts in 9 seconds, all checks OK, viewed in Library.
- **Vertical, horizontal and clustered bars:** `"vis"` `bar`, `hbar`, `clusteredBar` (`visType 7`) or `clusteredHbar`
  (`10`). For the clustered forms, put 2+ metrics on the metric axis; the builder adds Metric Names to Color By and Break By.
- **Title bar:** `"title"` plus `"title_format": {"lines": 2, "subtitle": "...", "align": "center", "wrap": true, "font":
  {"name": "Inter", "size": 12, "bold": true, "italic": true, "underline": true, "color": "#c1292f"}, "subtitle_font":
  {...}}` on any visualization item.
- **Data labels:** `"props": {"DataLabel": "Show only values", "bdlp": "1", "dlrtt": "2"}`.
- **Square ends:** `"props": {"allShpFmt": "{'shpRadius':0}"}`.
- **Reference lines:** `"reference_lines": [...]`, as above.

## Gotchas

- Title alignment is not a chart prop. Diffing chart props alone made the left, center and right charts look identical.
- Title justification uses 0 left, 1 right, 2 center. Text boxes use different numbers (the Lincoln "Back to Home" text box
  is right-aligned with `Horizontal: 3`), so don't copy values between the two.
- The Iconic KPI has no title bar. Don't send `titleFormat` to one.
- A chart titled "...Enabled" can still be off: read `enabl`, not the title.
- `fms` inside `mod_c` is HTML-escaped JSON (`&quot;`). Unescape it before parsing.
- The instance only returns data for the current page. To read page 2's charts, an unsaved instance was switched there with
  `setCurrentPanel` first.
- **Charts scale `,,"M"` formats again.** With `$#,##0.0,,"M"` on a metric, a grid or KPI shows $293.1M, but the chart's
  data labels and axis show **$0.3M**. For a chart, use a derived metric divided by 1,000,000 with the format
  `$#,##0.0"M"`, e.g. `([Rolling 12 Month Total Annuity Opportunity Amount]) / 1000000`. Found 2026-11-23 on
  IMT Advisor Sales and Opportunity Performance (v2) ([examples/imt-advisor-sales-v2.json](../examples/imt-advisor-sales-v2.json)).
- **Short legend names come from derived metric names.** A chart can't rename a metric in the spec, so a derived metric
  named "Year to date" (`[Year To Date Total Sales Amount]`) gives the legend that name. The same derived metric can also
  filter: `Sum(If([Producer Category]@ID = "Active Producer", [Year To Date Total Sales Amount], 0))` gives active
  producers only, checked against the unfiltered total.
- **Metrics can't be the categories.** The spec has no "Metric Names" on an axis, so "sales by product line" where each
  product is its own metric is built as a KPI strip (one card per metric), not a bar chart.
