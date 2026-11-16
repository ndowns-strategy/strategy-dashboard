// Strategy dashboard authoring from code — proven on studio.strategy.com (Library 11.6.1000), 2026-11-10.
//
// Run inside a signed-in Library tab (browser console or Claude in Chrome javascript_tool).
// Auth: write calls need the X-MSTR-AuthToken the Library app uses. Call captureToken(), then let the
// app make any request (e.g. __mstrRouterHistory.push('/MicroStrategyLibrary/app')) — window.__tok is set.
//
// Helper index (all on the session returned by client(...).newDashboard() / .open()); each was captured from the editor
// and verified by building real dashboards (see reference/*.md for the recipes):
//   Structure   addChapter, chapterKeys, switchChapter, addPage, renameChapter, renamePage, structure, duplicateChapter,
//               deleteChapter, moveChapter, duplicatePage, deletePage, movePage (reference/chapter-page-catalog.md), setLayout,
//               setFreeformLayout (free-form page: x/y/width/height in percent, overlap, layer order; adds 2% to every text box's height)
//   Charts      insertChart, changeType, fillZones, setWidgetProps, chartProps/setChartProps, setMetricColor, setPalette
//   Grids       addToGrid, moveField, sortByMetric, attributeThresholds, buildModernGrid (Modern Grid with row sets),
//               buildColumnSetGrid (Modern Grid with column sets + sparkline / bar microchart columns)
//   Image       insertImage (picture from a URL)
//   KPI/custom  insertKpiCard / toKpiCard (draft's K52 in place) + setKpiCardProps, insertComparisonKpi / insertMultiMetricKpi + setKpiProperties,
//               insertDonut (Donut Chart: center total, legend with values, rounded slice ends, slice gaps),
//               insertLine (line chart: straight or curved, Curve Smoothness 0.3 by default),
//               insertStackedBar (Vertical Stacked Bar Chart: per-segment rounded corners + white separator),
//               insertBubble (bubble / scatter: two metric axes, Break By, optional Size By, tooltip metrics),
//               insertSankey (Sankey Diagram: 2+ level attributes, one flow metric),
//               insertHeatmap (Heat Map: grouping attributes, Color By + Size By metrics, percentile color bands),
//               insertKpi (Iconic) / insertCustomVis ('ImageEnhancedKPI', 'AutoNarratives'), setKpiIcon, addNarratives, titleBar
//   Text        addText, addRichText (words formatted separately; transparent: no white box), setLink (link to a page,
//               URL or another dashboard; reference/link-catalog.md), setTitle, rename (display name of a field inside one visualization)
//   Filters     addChapterFilter, addCanvasSelector (on-canvas Element / Value Filter: drop-down, multi-select, title shown by default; 3+ filters grouped together go in the Filter Panel with addChapterFilter instead), addObjectSelector (Attribute / Metric Selector: swaps an object in target visualizations), keepOnly (visualization filter)
//   Data        createDerivedMetric, createDerivedAttribute (plain-text formulas), numberFormat,
//               createTimeAttributes (only the time attributes an image uses that the dataset lacks; renamed "Processed Year" style), renameDatasetAttribute
//   Look        setFill (Container / Title Bar fill: no fill on a same-color background), cardBorder, setWidgetProps (copy a styling blob from another dashboard), chartFormat (type + axis origin,
//               fixed axis range, single-series color); sortByMetric takes { axis: 2 } for a column sort,
//               metricThresholds (value or percent bands that fill cells or chart marks), elementColors, metricColors,
//               trendLine (linear / best-fit trend line on a chart)
//   Save        saveAs, save (both turn on Auto Summary on every page first: enableAutoSummary; opt out with { autoSummary: false })
//
// Proven end to end (each verified by reading the saved object back and viewing it in Library): single- and multi-chapter
// dashboards with grids, Modern Grid row sets, bar/line/pie/ring/100% bar, Iconic KPI cards, AI narratives, text,
// chapter filters, on-canvas selectors, view filters, sorting, thresholds, number formats, layouts, Save As and Save.
//
// The flow:
//   1. POST /api/dossiers/draft/instances             -> new unsaved dashboard (with datasets)
//      POST /api/dossiers/{id}/instances              -> open an existing dashboard
//   2. taskProc getServerJSONResults (messageID=mid)   -> loads instance into the web bean; returns `bs`
//   3. taskProc mojoRWManipulation (rwb=bs, params={actions:[...]})
//                                                      -> the editor's own edit actions; each response returns a new `bs`
//   4. POST /api/documents/{id}/instances/{mid}/saveAs ({name, folderId}) -> 201 {id}
//      POST /api/documents/{id}/instances/{mid}/save   ({})              -> 204, overwrites
//   5. GET /api/v2/dossiers/{id}/definition  (viz keys + types)
//      GET /api/v2/dossiers/{id}/instances/{mid}/chapters/{chapterKey}/visualizations/{vizKey} (rows/cols/data)
//
// Gotchas:
//   - Edits go to /MicroStrategyLibrary/servlet/taskProc, not /api/.
//   - taskProc errors are an empty body + x-mstr-taskerrorcode header. Calling /save on the same instance
//     surfaces the real message (e.g. "The dropzone don't accept metrics").
//   - A failed manipulation leaves the instance broken (every later call 500s). Open a fresh instance.
//   - Change the type BEFORE adding fields: changeType resets drop zones (createDefaultDropZones).
//   - New viz keys are chosen by the client (editor uses W62, W63, ...). Use any key not already on the page.
//   - Field ids: for a saved dashboard use definition.datasets[].availableObjects; for a new draft use
//     GET /api/v2/cubes/{datasetId} -> definition.availableObjects.attributes / .metrics.
//   - Verified 2026-11-10: a new draft built with this file (grid + bar + pie + line, Save As) renders correctly.
//   - copyUnit source 'K51' is the hidden visualization prototype on the blank template's page K53.
//     Read keys from the instance if your dashboard was built from a different template.
//   - Multi-chapter: added chapters get server-assigned keys (read them with chapterKeys); call switchChapter before
//     editing another chapter — partialRetrieval nodes must belong to the current chapter (session.node tracks this).
//   - Derived-metric names must not shadow base metric names used in other formulas.
//   - Embedded ("managed") datasets can't be found by search; take their ids from a dashboard definition.
//   - Selector title formatting in the same edit made the document fail validation; selectors need >= ~11% layout height.
//   - Known gap: KPI icons on derived metrics render as placeholders (icons on base metrics work).
//   - Auto Summary (enableAutoSummary) failed with a 500 when the page had an on-canvas selector on an attribute unrelated to
//     the page's metrics (Month Name on the campus sessions dataset). Pick selector attributes that relate to the metrics.
//   - A text box's background: format unitType 106 { FormattingPatterns: { FillColor: Number(bgr(hex)), FillStyle: 0 } }.
//   - A dataset can have an attribute and a metric with the same name (Sallie Mae: "Annual Income" is both). Look metrics up
//     in availableObjects.metrics and attributes in .attributes, never a combined list: a metric-only zone (Size By) given
//     the attribute fails with a 500 ("The dropzone don't accept template units like attribute"), and other zones take it
//     silently.

const BASE = '/MicroStrategyLibrary';
const APP_ID = 'C2B2023642F6753A2EF159A75E0CFF29'; // applicationId the Library app sends on this server
const BLANK_TEMPLATE = '4802DE4C4C18F434C75BFA84EC8A5E4B';
const UNIT = { attribute: 12, metric: 4 };
// Percent of page height setFreeformLayout adds to every text box's height (house rule: a text box sized exactly to its text
// is cut off in the viewer).
const TEXT_HEIGHT_PAD = 2;

// Drop-zone ids for addDropZoneUnit (charts). Grids use addUnit with axis instead (1 rows, 2 columns).
// From the editor's drop-zone enum: ROWS 1, COLUMNS 2, XAXIS 3, YAXIS 4, BREAKBY 5, SLICEBY 6, COLORBY 7, SIZEBY 8, TOOLTIP 9, ANGLEBY 10.
const ZONE = { rows: 1, columns: 2, xAxis: 3, yAxis: 4, breakBy: 5, sliceBy: 6, colorBy: 7, sizeBy: 8, tooltip: 9, angle: 10 };
// vertical bar/line/area: xAxis = attribute, yAxis = metric.  pie/ring: sliceBy + colorBy = attribute, angle = metric.
// horizontal 100% bar (visType 11, Subtype Percent): xAxis = metric, breakBy + colorBy = attribute.
// Iconic KPI (ImageEnhancedKPI): xAxis = metric, yAxis = trend attribute (sparkline + prior-period comparison).
// Native KPI family (captured from the KPI gallery): KPI card zones differ from charts.
const KPI_ZONE = { metric: 19, trend: 20, breakBy: 5 };            // KPICardVisualizationStyle
const CMP_ZONE = { actual: 3, target: 4, breakBy: 5, trend: 6 };   // ComparisonKPI ('Metric', 'Compare With', 'Break By', 'Trend')
const MM_ZONE = { metrics: 3, trend: 5 };                          // MultiMetricKPI (2+ metrics; trend attribute)
// Microchart columns in a Modern Grid (chartCfg.format defaults the editor writes; override per chart).
const MICROCHART_DEFAULTS = {
  sparkline: { axisScaleScope: 0, axisScaleFunc: 0, lineColor: '#3F95D6', bc: 'TRANSPARENT', bo: 10, highlightLighten: 1.5, defaultPixelsPerValue: 6,
    spotRadius: 3, dataPoints: { type: 1, keyPoints: { first: false, last: false, min: false, max: false } }, highlightSpotColor: '#3B92ED',
    highlightLineColor: '#35383A', spotColor: '#3B92ED', keySpotColor: '#3B92ED', contentHeight: 20, valign: 1 },
  trendBar: { axisScaleScope: 0, axisScaleFunc: 0, barColor: '#3F95D6', lineColor: '#3F95D6', highlightLighten: 1.5, barSpacing: 1,
    contentHeight: 24, valign: 1, zeroAxis: true, negBarColor: '#3F95D6' },
};
// Full drop-zone enum from the Library app (mojo-dossier.js), incl. map zones: Grouping 11, GeoAttribute 12, Layout 13,
// FromItem 14, ToItem 15, ItemSize 16, Latitude 17, Longitude 18, Metric 19, Trend 20, Geometry 21.
// On-canvas selector Display Style (FormattingSelector.Style), from the editor's own enum; 7 metric slider, 8 metric
// qualification, 10 text box, 11 calendar are for metrics, parameters and dates.
const SELECTOR_STYLE = { dropDown: 0, slider: 1, listBox: 2, radio: 3, checkBoxes: 4, buttonBar: 5, linkBar: 6, searchBox: 9 };
const MAP_ZONE = { geo: 12, colorBy: 7, sizeBy: 8, tooltip: 9, latitude: 17, longitude: 18, geometry: 21 };
const MAPBOX_CLASS = 'com.microstrategy.web.vf.viewer.MapboxApplicationViewer';
// Heat Map (treemap of rectangles; reference/heatmap-catalog.md): Grouping = one or more attributes (nested), Color By and
// Size By = one metric each. Widget type 2 (EnumWidgetTypes.HEATMAP), style VIHeatMapVisualizationStyle.
const HEATMAP_ZONE = { grouping: 11, colorBy: 7, sizeBy: 8, tooltip: 9 };
const HEATMAP_CLASS = 'com.microstrategy.web.vf.viewer.HeatMapApplicationViewer';
// Sankey Diagram (custom visualization 'Sankey', plugin mstrmojo.plugins.Sankey; reference/sankey-catalog.md): Levels = 2+
// attributes, left to right; Metric = exactly one (flow width); Tooltip = extra metrics.
const SANKEY_ZONE = { levels: 3, metric: 4, tooltip: 5 };
// Donut Chart (custom visualization 'DonutChart', plugin mstrmojo.plugins.DonutChart; reference/donut-catalog.md). Zones in the
// plugin's order: Angle (metric), Color By (attribute), Slice (attribute), Target (metric), Break By (attribute: one donut each).
const DONUT_ZONE = { angle: 3, colorBy: 4, slice: 5, target: 6, breakBy: 7 };
const DONUT_LABEL = { value: 2, text: 4, textAndValue: 6 };   // dataLabelType: what the center shows
// The editor's default heat map colors, lowest 20% to top 20% of the Color By metric (read from Wawa 08.31 Demo).
const HEATMAP_BANDS = ['#fc6f02', '#fbc85b', '#d9e5f2', '#54bfd9', '#3f95d6'];
const KPI_CARD_CLASS ='com.microstrategy.web.vf.viewer.KPICardApplicationViewer';
const CUSTOM_VIS_CLASS = 'com.microstrategy.web.vf.viewer.CustomVisApplicationViewer';
// The editor's built-in Auto Summary instruction (sent verbatim when the toolbar button is clicked).
const AUTO_SUMMARY_INSTRUCTION = 'Analyze and summarize the overall content of the page. If metrics are available on the page, analyze and '
  + 'summarize the overall content. Sort the data to identify top and bottom performers based on key metrics. Highlight trends, patterns, '
  + 'and anomalies, and generate actionable insights. If no metrics are found, skip calculation and summarize the content.';

// ---- Time attributes (dataset panel > right-click a date > Create Time Attributes; captured 2026-11-15) ----
// The ten types the editor offers, in its order (a lookup list, not a default: create only the types an image uses). Each becomes a derived attribute whose forms call built-in date functions
// on the source date. Formulas are token streams rebuilt here exactly as the editor sends them.
const TIME_ATTRIBUTE_TYPES = ['Year', 'Quarter of Year', 'Quarter', 'Month of Year', 'Month', 'Week of Year', 'Week',
  'Day of Year', 'Day of Month', 'Day of Week'];
const TIME_FN = { year: '6F7DF5F8', quarterOfYear: '6F7DF5F7', monthOfYear: '6F7DF5F6', weekOfYear: '6F7DF5F5', dayOfYear: '6F7DF5F4',
  dayOfWeek: '6F7DF5F3', dayOfMonth: '6F7DF5F2', concat: '6F7DF5FF' };
for (const k of Object.keys(TIME_FN)) TIME_FN[k] += '449111D5BEA300B0D01A55EF';
Object.assign(TIME_FN, { formatDate: 'D1ED29645DEC4DBF99E8E09ED939074B', quarterStart: '59E10CE2ADDD4A6DAC2416A72999A9ED',
  monthStart: '7C63D4E70B2741C3A5B54A2EFD40961B', weekStart: '44681336D0DB4E43AC333FFB3CC4400D' });
const ID_FORM = '45C11FA478E745FEA08D781CEA190FE5'; // the ID form category (also the form of a single-form date attribute)
// Our naming convention for a time attribute: drop the word "Date" from the source name and add the type.
// "Processed Date" + "Year" -> "Processed Year"; "Paid Date" + "Day of Week" -> "Paid Day of Week". A name without "Date"
// keeps its words: "Snapshot" + "Month" -> "Snapshot Month".
function timeAttributeName(sourceName, type) {
  const base = sourceName.replace(/\s*\bDate\b\s*/i, ' ').replace(/\s+/g, ' ').trim();
  return `${base} ${type}`;
}
function timeAttributeForms(type, src) {
  const esc = (v) => v.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const F = (id) => `<tkn v="${id}"><oi did="${id}" t="11" st="2816" n="${id}"></oi></tkn>`;
  const P = (v) => `<tkn v="${esc(v)}" tp="2" lv="1"></tkn>`;
  const S = `<tkn v="${esc(`[${src.name}]@[${src.formName || src.name}]`)}" tp="275" lv="1" exv="${src.formId || ID_FORM}" extp="8">`
    + `<oi did="${src.id}" t="12" n="${esc(src.name)}"></oi></tkn>`;
  const THIS = `<tkn v="This@ID)" tp="2" lv="1" exv="${ID_FORM}" extp="8"></tkn>`;
  const call = (fn) => F(fn) + P('(') + S + P(')');
  const ts = (body) => `<tknstrm ><items><tkn v="!" tp="33" lv="4"></tkn>${body}<tkn v="" tp="-1" lv="4"></tkn></items></tknstrm>`;
  const fmt = (pattern) => F(TIME_FN.formatDate) + P(`<Pattern="${pattern}">(`) + S + P(')');
  const yearTimes = (n, fn) => F(TIME_FN.year) + P('(') + S + P(`) * ${n} + `) + call(fn);
  const label = (letter, fn) => F(TIME_FN.concat) + P(`("${letter}"`) + P(',') + call(fn) + P(',') + P(' ", "') + P(',')
    + F(TIME_FN.year) + P('(') + S + P('))');
  const R = {
    'Year': { ID: call(TIME_FN.year) },
    'Quarter of Year': { ID: call(TIME_FN.quarterOfYear), DESC: F(TIME_FN.concat) + P('("Q"') + P(',') + THIS },
    'Quarter': { ID: yearTimes(10, TIME_FN.quarterOfYear), DESC: label('Q', TIME_FN.quarterOfYear), DATE: call(TIME_FN.quarterStart) },
    'Month of Year': { ID: call(TIME_FN.monthOfYear), DESC: fmt('mmmm') },
    'Month': { ID: yearTimes(100, TIME_FN.monthOfYear), DESC: fmt('mmm yyyy'), DATE: call(TIME_FN.monthStart) },
    'Week of Year': { ID: call(TIME_FN.weekOfYear) },
    'Week': { ID: yearTimes(100, TIME_FN.weekOfYear), DESC: label('W', TIME_FN.weekOfYear), DATE: call(TIME_FN.weekStart) },
    'Day of Year': { ID: call(TIME_FN.dayOfYear) },
    'Day of Month': { ID: call(TIME_FN.dayOfMonth) },
    'Day of Week': { ID: call(TIME_FN.dayOfWeek), DESC: fmt('ddd') },
  }[type];
  if (!R) throw new Error('Unknown time attribute type ' + type);
  return Object.entries(R).map(([n, body]) => ({ n, formula: ts(body), bft: 0 }));
}

// Chart types: Shape + visType (from the editor's enum; more in docs below).
const VIS = {
  bar: { shape: 'Bar', visType: 70 },        // GRAPHMATRIXVERTICALBARAUTOMATIC
  hbar: { shape: 'Bar', visType: 71 },       // GRAPHMATRIXHORIZONTALBARAUTOMATIC
  line: { shape: 'Line', visType: 72 },      // GRAPHMATRIXVERTICALLINEAUTOMATIC
  area: { shape: 'Area', visType: 74 },      // GRAPHMATRIXVERTICALAREAAUTOMATIC (shape name unverified)
  pie: { shape: 'Pie', visType: 61 },        // GRAPHMATRIXPIE
  ring: { shape: 'Ring', visType: 62 },      // GRAPHMATRIXRING
  pctHbar: { shape: 'Bar', visType: 11 },    // GRAPHMATRIXHORIZONTALBARPERCENT (also set Subtype 'Percent')
  stackedBar: { shape: 'Bar', visType: 6, subtype: 'Stacked' },    // Vertical Stacked Bar Chart (gallery; GRAPHMATRIXVERTICALBARSTACKED)
  hbarStacked: { shape: 'Bar', visType: 9, subtype: 'Stacked' },   // horizontal stacked (diverging stacked bar, tornado)
  areaStacked: { shape: 'Area', visType: 30, subtype: 'Stacked' }, // stacked area (diverging area)
  scatter: { shape: 'Circle', visType: 21 },                       // scatter / bubble (add Size By for bubbles)
  combo: { shape: 'Bar', visType: 57, subtype: 'Stacked' },        // dual-axis combo: Metric Names on Rows, metricShapes for lines
};
// Verified end to end: bar, hbar, line, pie, ring, 100% hbar.
// hbar: xAxis = metric, yAxis = attribute. Multi-series line: breakBy + colorBy = attribute.
// Derived objects can also be sent as plain formula text with isTokenStream:false.

function captureToken() {
  const osh = XMLHttpRequest.prototype.setRequestHeader;
  XMLHttpRequest.prototype.setRequestHeader = function (k, v) {
    if (/x-mstr-authtoken/i.test(k)) window.__tok = v;
    return osh.apply(this, arguments);
  };
  const of = window.fetch;
  window.fetch = function (i, o) {
    try {
      new Headers((o && o.headers) || (i && i.headers) || {}).forEach((v, k) => {
        if (k === 'x-mstr-authtoken') window.__tok = v;
      });
    } catch (e) {}
    return of.apply(this, arguments);
  };
}

// '#rrggbb' -> Strategy's BGR integer string used in FormattingFont.Color / FormattingBorder.*Color.
function bgr(hex) {
  let h = hex.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
  return String(b * 65536 + g * 256 + r);
}

// ---- utilities used by the helpers ----
function grabJson(text, start) { // balanced {...} or [...] starting at index `start`
  let d = 0, e = start, q = false;
  for (; e < text.length; e++) { const ch = text[e];
    if (q) { if (ch === '\\') { e++; continue; } if (ch === '"') q = false; continue; }
    if (ch === '"') { q = true; continue; }
    if (ch === '{' || ch === '[') d++; else if (ch === '}' || ch === ']') { d--; if (d === 0) break; } }
  return text.slice(start, e + 1);
}
// Rich Text field value (reference/text-catalog.md): the run texts joined by U+2446, then U+2446 U+2440 and
// base64(encodeURIComponent(JSON of the Quill Delta)). Defaults match the editor: #35383a, 10 pt, Open Sans.
// The viewer's Quill keeps only bold, italic, underline, strike, color, font, size (per run) and align, header, list,
// indent (per paragraph); anything else (highlight, links, sub/superscript) is dropped when the dashboard loads.
function richTextValue(runs, { align, header, list, indent } = {}) {
  const block = (r) => Object.fromEntries(Object.entries({ align: r.align, header: r.header, list: r.list, indent: r.indent }).filter(([, v]) => v !== undefined));
  const ops = runs.map((r) => {
    if (r.text === '\n') { const a = block(r); return Object.keys(a).length ? { insert: '\n', attributes: a } : { insert: '\n' }; }
    const a = { color: r.color || '#35383a', size: 'size' + (r.size || 10), font: r.font || 'opensans' };
    for (const k of ['bold', 'italic', 'underline', 'strike']) if (r[k]) a[k] = true;
    return { insert: r.text, attributes: a };
  });
  const last = block({ align, header, list, indent });
  ops.push(Object.keys(last).length ? { insert: '\n', attributes: last } : { insert: '\n' });
  return ops.map((o) => o.insert).join('⑆') + '⑆⑀' + btoa(encodeURIComponent(JSON.stringify(ops)));
}

function newKey32() { return Array.from(crypto.getRandomValues(new Uint8Array(16))).map((b) => b.toString(16).padStart(2, '0')).join('').toUpperCase(); }
// Find the id the server assigned to a new derived object (name may get a " 1" suffix; "/" comes back as "\/").
function newObjectId(responseText, name) {
  const esc = name.replace(/[.*+?^${}()|[\]\\/]/g, (c) => (c === '/' ? '\\\\?\\/' : '\\' + c));
  const m = responseText.match(new RegExp('"n":"' + esc + '( \\d+)?","did":"([0-9A-F]{32})"'));
  if (!m) throw new Error('new object id not found for ' + name);
  return m[2];
}
// View-filter expression: IsNotNull({attr} (ID)).
function notNullExpr(attrId, attrName, idFormId) {
  return `<exp><nd et="14" fn="19"><nds><nd et="2" fn="55"><a did="${attrId}" t="12" n="${attrName}"></a><fm did="${idFormId}" n="ID"></fm></nd></nds></nd></exp>`;
}

function visFormat(key, unitType, { shape, visType, subtype = 'Automatic' }) {
  return {
    act: 'format', unitKey: key, unitType, formatType: 1,
    format: {
      Visualization: {
        VisualizationsEnabled: -1, ViewMode: 51,
        SelectedVisualization: 'GraphMatrixVisualizationStyle', VisualizationList: 'GraphMatrixVisualizationStyle',
        IPhoneVisualization: '', IPadVisualization: 'IPadGraphMatrix2Style',
        APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false,
      },
      FormattingWidget: {
        ClassName: 'com.microstrategy.flex.viewer.GraphMatrixViewer', Enable: 1,
        WidgetProps: `<props ><widgetProps ><fmt ><visStyle value="GraphMatrixVisualizationStyle" ></visStyle>`
          + `<Shape value="${shape}" ></Shape><Subtype value="${subtype}" ></Subtype>`
          + `<visType value="${visType}" ></visType><userVisType value="${visType}" ></userVisType>`
          + `</fmt></widgetProps></props>`,
      },
    },
  };
}

// Dynamic dates for a calendar (style 11) filter, in the form the editor sends (reference/filter-catalog.md, "Date attribute in
// the filter panel"): isDyn::<type>::<days>::<months>::<month>::<day>::<week>::<weekday>::<resolved M/D/YYYY>::0::0::0.
// type: day = today ± days; week = week of (today ± days), weekday 0 Sun … 6 Sat; month / quarter / year = period of
// (today ± months), day 1 first / -1 last (year: month + day, e.g. 12/31). The resolved date is display only; the server recomputes it.
const DYN_TYPE = { day: 3, week: 4, month: 5, quarter: 14, year: 6 };
function dynDate({ type = 'day', days = 0, months = 0, month = 0, day = 0, week = 0, weekday = 0 }, today = new Date()) {
  const t = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  let d;
  if (type === 'day') d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days);
  else if (type === 'week') { const x = new Date(t.getFullYear(), t.getMonth(), t.getDate() + days); d = new Date(x.getFullYear(), x.getMonth(), x.getDate() - x.getDay() + weekday); }
  else {
    const p = new Date(t.getFullYear(), t.getMonth() + months, 1);
    if (type === 'month') d = day < 0 ? new Date(p.getFullYear(), p.getMonth() + 1, 0) : new Date(p.getFullYear(), p.getMonth(), day || 1);
    else if (type === 'quarter') { const q = p.getMonth() - (p.getMonth() % 3); d = day < 0 ? new Date(p.getFullYear(), q + 3, 0) : new Date(p.getFullYear(), q, day || 1); }
    else d = new Date(p.getFullYear(), (month || 1) - 1, day || 1);
  }
  const shown = `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`;
  return ['isDyn', DYN_TYPE[type], days, months, month, day, week, weekday, shown, 0, 0, 0].join('::');
}
// The calendar presets and their "Last/Next N <unit>" forms as { fn, value } for addDateFilter. Accepts 'today', 'yesterday',
// 'mtd', 'qtd', 'ytd', 'last 7 days', 'next 3 months' (units: days, weeks, months, quarters, years). Strings recorded from
// the editor on 2026-11-12; every preset is a Between (17) of two dynamic dates.
function datePreset(spec, today = new Date()) {
  const s = String(spec).trim().toLowerCase();
  const D = (o) => dynDate(o, today), between = (a, b) => ({ fn: 17, value: D(a) + '\u001e' + D(b) });
  const now = { type: 'day' };
  if (s === 'today') return between(now, now);
  if (s === 'yesterday') return between({ type: 'day', days: -1 }, { type: 'day', days: -1 });
  if (s === 'mtd') return between({ type: 'month', day: 1 }, now);
  if (s === 'qtd') return between({ type: 'quarter', day: 1 }, now);
  if (s === 'ytd') return between({ type: 'year', month: 1, day: 1 }, now);
  const m = s.match(/^(last|next)\s+(\d+)\s+(day|week|month|quarter|year)s?$/);
  if (!m) throw new Error('Unknown date preset: ' + spec);
  const n = +m[2], last = m[1] === 'last', unit = m[3];
  if (unit === 'day') return last ? between({ type: 'day', days: -n }, { type: 'day', days: -1 }) : between({ type: 'day', days: 1 }, { type: 'day', days: n });
  if (unit === 'week') return last ? between({ type: 'week', days: -7 * n }, { type: 'week', days: -7, weekday: 6 })
    : between({ type: 'week', days: 7 }, { type: 'week', days: 7 * n, weekday: 6 });
  const k = { month: 1, quarter: 3, year: 12 }[unit];
  const first = unit === 'year' ? { month: 1, day: 1 } : { day: 1 }, end = unit === 'year' ? { month: 12, day: 31 } : { day: -1 };
  return last ? between({ type: unit, months: -k * n, ...first }, { type: unit, months: -k, ...end })
    : between({ type: unit, months: k, ...first }, { type: unit, months: k * n, ...end });
}

function client(token, projectId) {
  const H = {
    'Content-Type': 'application/json', Accept: 'application/json',
    'X-MSTR-AuthToken': token, 'X-MSTR-ProjectID': projectId, 'X-Requested-With': 'XMLHttpRequest',
  };
  const api = async (method, path, body) => {
    const r = await fetch(BASE + '/api' + path, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
    const t = await r.text();
    if (!r.ok) throw new Error(`${method} ${path} -> ${r.status} ${t.slice(0, 300)}`);
    return t ? JSON.parse(t) : null;
  };
  const task = async (params) => {
    const body = new URLSearchParams({ taskEnv: 'xhr', taskContentType: 'json', jsonMode: 'true',
      xts: String(Date.now()), mstrWeb: 'random', ...params });
    const r = await fetch(BASE + '/servlet/taskProc', { method: 'POST', body: body.toString(), headers: {
      'Content-type': 'application/x-www-form-urlencoded', 'X-MSTR-AuthToken': token,
      'X-MSTR-ProjectID': projectId, 'X-Requested-With': 'XMLHttpRequest' } });
    const t = await r.text();
    if (!r.ok) throw new Error(`taskProc ${params.taskId} -> ${r.status} code=${r.headers.get('x-mstr-taskerrorcode')}`);
    return t;
  };

  async function session(dashboardId, mid) {
    const g = await task({ taskId: 'getServerJSONResults', messageID: mid, styleName: 'ServerJsonRWDStyle',
      resFlags: '0', excludeData: 'false', supportsUndo: 'true', compress: '1', innerHeight: '857', innerWidth: '1920' });
    let bs = g.match(/"bs":"([^"]+)"/)[1];
    const s = {
      dashboardId, mid,
      initial: g, // full server JSON of the instance (definitions, formats, widget props) — useful as a spec
      async edit(actions, nodes) {
        const t = await task({ taskId: 'mojoRWManipulation', messageID: mid, rwb: bs, stateID: '-1',
          styleName: 'RWIVEMojoStyle', zoomFactor: '1',
          params: JSON.stringify({ actions, partialRetrieval: { nodes }, style: { params: { treesToRender: 2 }, name: 'RWIVEMojoStyle' } }) });
        const m = t.match(/"bs":"([^"]+)"/);
        if (m) bs = m[1];
        return t;
      },
      // Grid: axis 1 = rows, 2 = columns. unitPos is 1-based; to fix order afterwards use moveField().
      addToGrid(vizKey, datasetId, unitId, unitType, axis, unitPos = 0) {
        return s.edit([
          { act: 'updateTemplate', keyContext: vizKey, actions: [
            { act: 'addUnit', unitId, unitType, unitPos, dsId: datasetId, isFirst: unitPos === 0, axis }] },
          { act: 'editNode', nodeKey: vizKey, datasetId }], [vizKey]);
      },
      // Charts: fields = [{zoneId, unitId, unitType, unitPos?, ax?}]; ax: 1 puts a metric on the right axis (dual-axis combo).
      fillZones(vizKey, datasetId, fields) {
        return s.edit([
          { act: 'updateTemplate', keyContext: vizKey, actions: fields.map((f, i) => (
            { ax: f.ax || 0, act: 'addDropZoneUnit', zoneId: f.zoneId, datasetId, unitId: f.unitId, unitType: f.unitType, unitPos: f.unitPos || 0 })) },
          { act: 'editNode', nodeKey: vizKey, datasetId }], [vizKey, s.node]);
      },
      // layout: LayoutXML tree, e.g. {t:'b',o:'v',children:[{t:'b',o:'h',l:50,children:[{t:'c',k:'K52',l:50},{t:'c',k:'W62',l:50}]},{t:'c',k:'W64',l:50}]}
      // t: 'b' box / 'c' container, o: 'h' horizontal / 'v' vertical, l: percent share, k: viz key.
      setLayout(pageKey, layout) {
        return s.edit([{ act: 'format', unitKey: pageKey, unitType: 9, formatType: 1,
          format: { FormattingSize: { LayoutXML: layout } }, isJson: true }], [pageKey]);
      },
      // Free-form layout (reference/freeform-layout.md): objects float at x/y with a width and height and may overlap; the
      // order of `items` is the layer order, back to front (the Layers panel lists it front to back). Same as the editor's
      // "Convert to Free-form Layout" plus Position and Size and Bring to Front / Send to Back. Per page; call it after every
      // object is on the page (each insert re-sends whatever layout you hand it), and before saveAs (Auto Summary keeps it).
      // items: [{ k, x, y, w, h }] in percent of the page (x/w of its width, y/h of its height).
      // Text boxes (unit type 106, from addText / addRichText) get TEXT_HEIGHT_PAD (2%) added to h automatically: a box
      // sized to its text is cut off in the viewer. Pass your raw estimate for h; don't add the 2% yourself. Leave room for
      // it: start the object below a text box at least y + h + 2. Opt out per item with { exactHeight: true }.
      // Returns the edit response; s.lastFreeformItems holds the items as sent (padded heights).
      async setFreeformLayout(pageKey, items) {
        const j = await s.serverJson();
        const chapter = j.defn.layouts.find((l) => l.units[pageKey]);
        const fm = chapter.units[pageKey].fmts || {};
        const W = parseFloat(fm.width) || 1594, Hpx = parseFloat(fm.height) || 894;
        const v = (pct, px) => `${pct}|${(pct * px) / 100}px`;
        const isText = (k) => (chapter.units[k] || {}).t === 106;
        const sized = items.map((it) => (isText(it.k) && !it.exactHeight ? { ...it, h: +(it.h + TEXT_HEIGHT_PAD).toFixed(4) } : it));
        s.lastFreeformItems = sized;
        const children = sized.map((it, i) => ({ fixed: '0', k: it.k, rk: pageKey, t: 'flc', zIndex: String(i + 2),
          top: v(it.y, Hpx), left: v(it.x, W), width: v(it.w, W), height: v(it.h, Hpx), l: it.w, hidden: 0 }));
        const layout = { t: 'b', o: 'v', m: 'm', children: [], ifwChildren: [], canvasSize: null,
          floatChildren: { t: 'g', k: newKey32(), zIndex: String(items.length + 1), left: '0|0px', top: '0|0px',
            width: `100|${W}px`, height: `100|${Hpx}px`, children } };
        return s.edit([
          { act: 'format', unitKey: chapter.k, unitType: 1, formatType: 1, format: { FormattingPage: { UsePageWidthAsLayoutWidth: 1, MarginLeft: '0', MarginRight: '0' } } },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true }], [pageKey]);
      },
      // Insert a new chart on a page. newKey must be unused (e.g. 'W70'). layout must include newKey.
      insertChart({ newKey, vis, pageKey = 'K53', protoKey = 'K51', layout }) {
        return s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey, toKey: pageKey },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true },
          { act: 'updateTemplate', keyContext: newKey, actions: [{ act: 'createDefaultDropZones', nodeKey: newKey, treeType: 1, datasetType: 3, widgetType: 1 }] },
          visFormat(newKey, 521, vis),
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: 0 } } },
          { act: 'changeGridDisplayMode', nodeKey: newKey, displayMode: 2 },
        ], [newKey]);
      },
      // Change an existing chart's type. Clears its drop zones — refill afterwards.
      // unitType 522 for a saved dashboard's visualization; 521 turns a new draft's default grid (K52) into a chart.
      changeType(vizKey, vis, unitType = 522) {
        return s.edit([
          { act: 'updateTemplate', keyContext: vizKey, actions: [{ act: 'createDefaultDropZones', nodeKey: vizKey, treeType: 1, datasetType: 3, widgetType: 1 }] },
          visFormat(vizKey, unitType, vis),
          { act: 'format', unitKey: vizKey, unitType, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: 0 } } },
          { act: 'changeGridDisplayMode', nodeKey: vizKey, displayMode: 2 },
        ], [vizKey]);
      },
      // ---- Added 2026-11-10 while rebuilding "Business Insurance" (all verified against the source's numbers) ----
      // Iconic KPI card (custom vis ImageEnhancedKPI). layout must include newKey.
      insertKpi({ newKey, pageKey = 'K53', protoKey = 'K51', layout }) {
        return s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey, toKey: pageKey },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true },
          { act: 'updateTemplate', keyContext: newKey, actions: [{ act: 'createDefaultDropZones', nodeKey: newKey, treeType: 1, datasetType: 3, widgetType: 7 }] },
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: {
            Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: 'ImageEnhancedKPI', VisualizationList: 'ImageEnhancedKPI',
              IPhoneVisualization: '', IPadVisualization: '', APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false },
            FormattingWidget: { ClassName: 'com.microstrategy.web.vf.viewer.CustomVisApplicationViewer', Enable: 1,
              WidgetProps: '<props><widgetProps><fmt><cvp><ftFgGrpA value="1"></ftFgGrpA></cvp></fmt></widgetProps></props>' },
            FormattingView: { ShowTitleBar: 0, ShowWidgetTitleBar: 0 } } },
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: 0 } } },
          { act: 'changeGridDisplayMode', nodeKey: newKey, displayMode: 1 },
        ], [newKey]);
      },
      // KPI icon: file from /images/material-symbols/400/rounded/, e.g. 'payments-fill.svg'.
      setKpiIcon(vizKey, metricId, file) {
        return s.edit([{ act: 'updateElementsPropertiesMap', nodeKey: vizKey, epm: [{ epmk: [{ ob: { did: '', tp: 4 } }],
          epmv: [{ k: { chn: [{ emt: 2, mt: { did: metricId, tp: 4, ql: 0 } }] },
            v: { vv: '', format_config: JSON.stringify({ searchIcon: '/images/material-symbols/400/rounded/' + file }), ov: -1 } }] }] }], [vizKey]);
      },
      setTitle(vizKey, title) {
        return s.edit([{ act: 'format', unitKey: vizKey, unitType: 521, formatType: 1, format: { FormattingView: { Title: title } } }], [vizKey]);
      },
      // Display name of an attribute (type 12) or metric (type 4) inside one visualization.
      rename(vizKey, unitId, unitType, name) {
        return s.edit([{ act: 'updateTemplate', keyContext: vizKey, actions: [{ act: 'renameUnit', id: unitId, type: unitType, name, isDynamicAlias: false }] }], [vizKey]);
      },
      // Display Attribute Forms of one attribute inside one visualization (the editor's addForm / removeForm template actions).
      // add / remove: form ids from availableObjects.attributes[].forms (e.g. drop a customer's Email Address, add a SKU's
      // Product Name). unitPos places an added form (0 first).
      formDisplay(vizKey, attrId, { add = [], remove = [], unitPos = 0 } = {}) {
        const actions = [...remove.map((attFormId) => ({ act: 'removeForm', unitId: attrId, unitType: 12, attFormId })),
          ...add.map((attFormId, i) => ({ act: 'addForm', unitId: attrId, unitType: 12, attFormId, unitPos: unitPos + i }))];
        return s.edit([{ act: 'updateTemplate', keyContext: vizKey, actions }], [vizKey]);
      },
      // Visualization filter: keep only these element names of one attribute.
      keepOnly(vizKey, attrId, values) {
        return s.edit([{ act: 'keepOnly', keyContext: vizKey, selectorObjects: [{ keepOnly: true,
          data: values.map((v) => [{ tid: attrId, eid: 'h' + v + ';' + attrId, fm: '0', v, isDe: false }]) }] }], [vizKey, s.node]);
      },
      // Sort by a metric. axis 1 sorts rows (a horizontal bar's categories), 2 sorts columns (a vertical bar's categories).
      // element { attrId, value } sorts by that element's value of the metric (the demo's dot strip: by Furniture's Revenue).
      // The axis lives in the key ('4!<metric>!!!<h<value>;<attr>>!<axis>'); send one list and the server files it under
      // gsi.sorts [[rowSorts], [colSorts]]. Sending [[], [sort]] yourself fails with a 500.
      sortByMetric(vizKey, metricId, ascending = false, { axis = 1, element } = {}) {
        const el = element ? 'h' + element.value + ';' + element.attrId : '';
        const sort = { key: '4!' + metricId + '!!!' + el + '!' + axis, metricSortKey: '2', isAsc: ascending };
        return s.edit([{ act: 'updateTemplate', keyContext: vizKey, actions: [{ act: 'sort',
          sorts: [[sort]], nodeKey: vizKey, subTotalsPos: [0], stt: -1, rp: null }] }], [vizKey]);
      },
      // Chapter filter (multi-select list) targeting the page area K33, with an initial selection.
      // filterPanel/contentStack: the chapter's FiltersPanel and VisualizationContentPanelStack keys (K49/K33 in a draft's
      // first chapter; for added chapters use chapterKeys().filterPanel and the content stack read the same way).
      // style: 9 search box (default), 0 drop-down, 4 checkbox list, 3 radio, 1 slider, 11 calendar (see reference/filter-catalog.md).
      // selected: element ID values, or [id, display] pairs for readability when the ID differs from what is shown
      // (e.g. ['20260718', '7/18/2026']); only the id is sent.
      // order: position in the filter panel (0 = top). The editor sorts the panel by this z-index; all 0 lists them newest first.
      // cascadeTo: NODE keys of other filters this one narrows (Department -> Category's node W86); the server then stores the
      // child's control key in tks (K33 + W87), as the source shows. Targeting the control key saves a dashboard that won't open.
      async addChapterFilter(attrId, name, selected = [], nodeKey = 'W84', ctlKey = 'W85',
        { filterPanel = 'K49', contentStack = 'K33', style = 9, cascadeTo = [], order = 0 } = {}) {
        const ctx = '1\u001e' + nodeKey + '\u001e' + ctlKey;
        await s.edit([
          { act: 'addControl', parentKey: filterPanel, nodeKey, ctlKey, isUC: true, unitType: 12, unitId: attrId, targetKeys: [contentStack], ctlType: 1, gpType: 1, isParameterSelector: false },
          { act: 'format', unitType: 111, keyContext: ctx, formatType: 1, format: { FormattingSize: { HeightMode: '0', Height: '1.4583', Width: '1.4479' },
            FormattingSelector: { Style: style, ItemWidthMode: 1, ShowElementCount: 1, ExportAsShownOnWeb: 1 }, FormattingAppearance: { Name: name }, FormattingOrder: { ZIndex: order } } },
          { act: 'setControlShowAll', nodeKey, controlKey: ctlKey, showAll: true }], [s.node]);
        // Filter -> filter target: excludeCtp false, as the filter panel's own action sends it.
        for (const tgtKey of cascadeTo) await s.edit([{ act: 'addControlTarget', keyContext: ctx, tgtKey, isUC: true, excludeCtp: false }], [s.node]);
        if (selected.length) {
          // Items are 'h<id>;<attrId>' joined by \u001e (the app's ELEM_SEPARATOR); commas made several items one.
          const el = (v) => 'h' + (Array.isArray(v) ? v[0] : v) + ';' + attrId;
          await s.edit([{ act: 'setSelectorElements', keyContext: ctx, ctlKey,
            elemList: selected.map(el).join('\u001e'), isVisualization: false, include: true, tks: contentStack }], [s.node]);
        }
      },
      // Chapter filter that qualifies a date attribute (selector style 11) instead of listing elements, e.g. "Processed Date
      // after <dynamic date>". fn: 8 greater (after), 17 between. value: a date 'M/D/YYYY', or a dynamic date in the editor's
      // stringified form 'isDyn::<dyt>::<ddo>::<dmo>::<dynamic_month>::<dynamic_day>::0::0::<anchor>::0::0::0'
      // (dyt 6, dmo -12, month 1, day 1 = what the editor writes for the source's "12 months ago" filter).
      // formId: the attribute's date form (read it from the instance JSON, "fid"). Verified 2026-11-11 (read back identical).
      // preset: 'last 7 days', 'ytd', ... (datePreset) instead of fn + value.
      async addDateFilter({ attrId, formId, name, fn = 8, value, preset, nodeKey = 'W89', ctlKey = 'W90', filterPanel = 'K49', contentStack = 'K33' }) {
        if (preset) ({ fn, value } = datePreset(preset));
        const ctx = '1\u001e' + nodeKey + '\u001e' + ctlKey;
        await s.edit([{ act: 'addControl', parentKey: filterPanel, nodeKey, ctlKey, isUC: true, unitType: 12, unitId: attrId, targetKeys: [contentStack],
          ctlType: 1, gpType: 1, isParameterSelector: false },
          { act: 'format', unitType: 111, keyContext: ctx, formatType: 1, format: { FormattingSelector: { Style: 11 }, FormattingAppearance: { Name: name } } }], [s.node]);
        return s.edit([{ act: 'setSelectorExpression', keyContext: ctx, ctlType: 1, objId: attrId, objType: 12, expFunction: fn, expFunctionType: 1,
          include: true, qt: 0, unset: false, partialUpdate: { selectors: [ctlKey] }, expConstants: value, dataType: 14, fid: formId }], [s.node]);
      },
      // Metric filter in the chapter filter panel (reference/filter-catalog.md, "Metric in the filter panel"). The metric is
      // evaluated at the level of the visualizations it targets (e.g. per Parking Lot). style: 'slider' (7, default) or
      // 'qualification' (8: operator drop-down + value box). Condition, optional:
      //   { op: '>=', value: 100 }   ops = < <= > >= <> between, not between, in, not in, is null, is not null
      //   { op: 'between', value: [50, 100] }   { op: 'in', value: [63, 68] }
      //   { rank: 'highest' | 'lowest' | 'highest%' | 'lowest%', value: 2 }   (top 2 / top 25%)
      // include: false = Exclude.
      async addMetricFilter({ metricId, name, style = 'slider', condition, include = true, nodeKey = 'W91', ctlKey = 'W92',
        filterPanel = 'K49', contentStack = 'K33', order }) {
        const ctx = '1\u001e' + nodeKey + '\u001e' + ctlKey;
        const fmt = { FormattingSelector: { Style: style === 'qualification' ? 8 : 7 }, FormattingAppearance: { Name: name } };
        if (order !== undefined) fmt.FormattingOrder = { ZIndex: order };
        await s.edit([{ act: 'addControl', parentKey: filterPanel, nodeKey, ctlKey, isUC: true, unitType: 4, unitId: metricId, targetKeys: [contentStack],
          ctlType: 1, gpType: 1, isParameterSelector: false },
          { act: 'format', unitType: 111, keyContext: ctx, formatType: 1, format: fmt }], [s.node]);
        if (!condition) return;
        const OPS = { '=': 6, '<>': 7, '>': 8, '<': 9, '>=': 10, '<=': 11, between: 17, 'not between': 44, in: 22, 'not in': 57, 'is null': 54, 'is not null': 55 };
        const RANK = { highest: [1, 2, 1], lowest: [2, 2, 2], 'highest%': [3, 3, 1], 'lowest%': [4, 3, 2] }; // qt, expFunctionType, expFunction
        let qt = 0, ft = 1, fn, values;
        if (condition.rank) {
          const r = RANK[condition.rank]; if (!r) throw new Error('Unknown rank ' + condition.rank);
          [qt, ft, fn] = r; values = [ft === 3 ? condition.value + '%' : condition.value];
          if (!include) throw new Error('Exclude with rank: use the opposite rank (highest <-> lowest) instead');
        } else {
          fn = OPS[condition.op]; if (!fn) throw new Error('Unknown operator ' + condition.op);
          values = condition.value === undefined ? [] : [].concat(condition.value);
          // Exclude = the opposite operator + include false, as the editor sends it (include:false alone does not invert).
          if (!include) fn = { 6: 7, 7: 6, 8: 11, 11: 8, 9: 10, 10: 9, 17: 44, 44: 17, 22: 57, 57: 22, 54: 55, 55: 54 }[fn];
        }
        const act = { act: 'setSelectorExpression', keyContext: ctx, ctlType: 1, objId: metricId, objType: 4, expFunction: fn, expFunctionType: ft,
          include, qt, unset: false, partialUpdate: { selectors: [ctlKey] } };
        if (values.length) Object.assign(act, { expConstants: values.join('\u001e'), dataType: 5 });
        return s.edit([act], [s.node]);
      },
      // Move a field within/between axes. unitPos is 1-based (1 = first). axis 1 rows, 2 columns.
      moveField(vizKey, unitId, unitType, axis, unitPos) {
        return s.edit([{ act: 'updateTemplate', keyContext: vizKey, actions: [{ act: 'pivot', unitId, unitType, axis, unitPos }] }], [vizKey]);
      },
      // Metric number format for the whole dashboard. category 7 = custom format string (f), e.g.
      // '[>=1000000]$#,##0.0,,"M";[>=1000]$#,##0.0,"K";0.0;[<=-1000000]#,##0.0,,"M";[<=-1000]#,##0.0,"K"'
      numberFormat(metricIds, f, category = 7) {
        return s.edit(metricIds.map((unitId) => ({ act: 'numberFormat', unitId, unitType: 4, c: category, f })), [s.node]);
      },
      // Container border (style 5 = solid) + rounded corners. Colors are BGR integers (see bgr()).
      cardBorder(vizKey, color = '#ababab', radius = 8, style = 5) {
        const c = bgr(color);
        return s.edit([{ act: 'format', unitKey: vizKey, unitType: 522, formatType: 1, format: {
          FormattingBorder: { TopStyle: style, RightStyle: style, BottomStyle: style, LeftStyle: style, TopColor: c, RightColor: c, BottomColor: c, LeftColor: c },
          FormattingView: { Radius: radius } } }], [vizKey]);
      },
      // Fill of any object's Container and Title Bar (Format panel > Container > Fill and Title Bar > Fill; verified 2026-11-15).
      // Rule: an object that sits on a background of the same color gets 'none' for both (no fill), as text boxes do.
      // container / title: 'none' (FillStyle 1, transparent), a '#hex' (FillStyle 0 + FillColor), or undefined to leave it.
      // titleFont: FormattingFont for the title bar text, e.g. { Color: bgr('#FFFFFF') } on a dark background.
      // unitType: 111 selector (pass keyContext '1\u001e<node>\u001e<ctl>'), 521/522 visualization, 106 text, 101 shape.
      // Format codes from the editor (getContainerFormatCode / getTitleFormatCode): container 1; title bar 5 on a selector
      // (FilterEditorModel) and 2 on a visualization or other object (BaseEditorModel). Sending 5 to a visualization fails with a 500.
      setFill(key, unitType, { container, title, titleFont, keyContext } = {}) {
        const pat = (v) => (v === 'none' ? { FillStyle: 1 } : { FillColor: Number(bgr(v)), FillStyle: 0 });
        const base = { unitKey: key, unitType, ...(keyContext ? { keyContext } : {}) };
        const acts = [];
        if (container !== undefined) acts.push({ act: 'format', ...base, formatType: 1, format: { FormattingPatterns: pat(container) } });
        if (title !== undefined || titleFont) acts.push({ act: 'format', ...base, formatType: unitType === 111 ? 5 : 2, format: {
          ...(title !== undefined ? { FormattingPatterns: pat(title) } : {}), ...(titleFont ? { FormattingFont: titleFont } : {}) } });
        return s.edit(acts, [unitType === 111 ? s.node : key]);
      },
      // Font-color thresholds on attribute elements: rules = [{value:'Open', color:'#333399'}, ...]
      attributeThresholds(vizKey, attrId, attrName, rules) {
        const thresholds = rules.map(({ value, color }) => ({
          expr: `<exp><nd et="14" fn="19"><nds><nd fn="22" et="5"><a did="${attrId}" t="12" st="3072" n="${attrName}"></a>`
            + `<es><e v="${attrId}:${value}" n="${value}"></e></es></nd></nds></nd></exp>`,
          fmt: { FormattingFont: { Color: bgr(color) } } }));
        return s.edit([{ act: 'updateTemplate', keyContext: vizKey, actions: [{ act: 'threshold', nodeKey: vizKey, thresholds,
          thresholdType: -1, basedOnId: attrId, did: attrId, objType: 12 }] }], [vizKey]);
      },
      // Value-band thresholds on a metric (Thresholds dialog, "Value" basis). Fill grid cells, or chart marks when the same
      // metric is also on Color By (diverging bars/areas). bands: [{ color, ceil }, { color, flr, ceil }, ..., { color, flr }]
      // e.g. color by sign: [{ color: '#f8942c', ceil: 0 }, { color: '#035397', flr: 0 }]
      // basis 'value' (thresholdType 7) or 'percent' ("Lowest %", thresholdType 1: flr/ceil are 0-100 percentiles).
      metricThresholds(vizKey, metricId, bands, basis = 'value') {
        // band.font: font color instead of (or with) a fill, e.g. orange text for values >= 1100, black below.
        const thresholds = bands.map(({ color, font, flr, ceil }) => ({ fmt: {
          ...(color ? { FormattingPatterns: { FillColor: Number(bgr(color)), FillStyle: 0 } } : {}),
          ...(font ? { FormattingFont: { Color: bgr(font) } } : {}) },
          ...(flr != null ? { flr: String(flr) } : {}), ...(ceil != null ? { ceil: String(ceil) } : {}) }));
        return s.edit([{ act: 'updateTemplate', keyContext: vizKey, actions: [{ act: 'threshold', nodeKey: vizKey, thresholds,
          thresholdType: basis === 'percent' ? 1 : 7, basedOnId: metricId, did: metricId, objType: 4 }] }], [vizKey]);
      },
      // Format > Trend Line > Enable (model: 'linear' 257 | 'bestFit' 256, or a raw lineType). metricId = the plotted (Y) metric.
      trendLine(vizKey, metricId, { model = 'linear', color = '#4D4D4D', thickness = 1, includeBreakBy = true } = {}) {
        const lineType = typeof model === 'number' ? model : { linear: 257, bestFit: 256 }[model];
        const format = JSON.stringify({ trdRefLnThk: thickness, trdRefLnClr: Number(bgr(color)), trdRefLnStyle: 0, trdRefLnCmbStyle: 1 }).replace(/"/g, '&quot;');
        return s.edit([{ act: 'operateTRFLine', tks: vizKey, lineType, lineLevel: 1, enabled: 1, includeBreakby: includeBreakBy ? 1 : 0,
          lineConstant: 2, lineIndex: 1, format, metricId }], [vizKey]);
      },
      // Dashboard-wide color of attribute elements (Shape Fill Color on a slice/segment); colors = { 'West': '#f8942c', ... }.
      elementColors(attrId, colors, refreshKey = s.node) {
        return s.edit([{ act: 'updateElementsPropertiesMap', epm: [{ epmk: [{ ob: { did: attrId, tp: 12 } }],
          epmv: Object.entries(colors).map(([value, hex]) => ({ v: { vv: JSON.stringify({ color: Number(bgr(hex)) }) },
            k: { chn: [{ emt: 1, ei: 'h' + value + ';' + attrId, at: { did: attrId, tp: 12, ql: 0 } }] } })) }] }], [refreshKey]);
      },
      // Replace a visualization's widget properties wholesale, e.g. copied from another dashboard's visProp.fmt (GraphMatrix)
      // or cvp (custom vis like ImageEnhancedKPI, whose `properties` JSON holds labels such as secondaryMetricName).
      setWidgetProps(vizKey, className, props, wrapper = 'fmt') {
        const esc = (v) => String(v).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const inner = Object.entries(props).filter(([, v]) => typeof v !== 'object').map(([k, v]) => `<${k} value="${esc(v)}"></${k}>`).join('');
        const xml = wrapper === 'cvp' ? `<props><widgetProps><fmt><cvp>${inner}</cvp></fmt></widgetProps></props>`
          : `<props><widgetProps><fmt>${inner}</fmt></widgetProps></props>`;
        return s.edit([{ act: 'format', unitKey: vizKey, unitType: 521, formatType: 1, format: { FormattingWidget: { ClassName: className, Enable: 1, WidgetProps: xml } } }], [vizKey]);
      },
      // Current GraphMatrix widget props of a visualization (visProp.fmt), read from this session's server JSON.
      // Merge into these before calling setWidgetProps, which replaces the whole set.
      chartProps(vizKey) {
        const t = s.initial;
        const grab = (start) => { let d = 0, e = start, q = false; for (; e < t.length; e++) { const ch = t[e];
          if (q) { if (ch === '\\') { e++; continue; } if (ch === '"') q = false; continue; }
          if (ch === '"') { q = true; continue; } if (ch === '{') d++; else if (ch === '}') { d--; if (d === 0) break; } } return t.slice(start, e + 1); };
        return JSON.parse(grab(t.indexOf('"visProp":{', t.indexOf('{"k":"' + vizKey + '","sid"')) + 10)).fmt;
      },
      // Useful GraphMatrix props (values are strings): LegendVisibleness 'Show'|'Hide', LegendPosition '13' (bottom),
      // LegendTitleHide 'true', DataLabel 'Show only values'|'Show both text value'|'Show only text'|'Show only percent'...,
      // xAxTtShw / yAxTtShw 'false' to hide an axis title, Subtype 'Percent' for 100% bars.
      // FitTo 'Content' | 'Window' | 'Compact': 'Content' keeps every bar's height and label and lets the chart scroll (a long
      // category list, e.g. 25 stores); the default squeezes the bars into the panel and skips labels. Stored as the word, not a number.
      setChartProps(vizKey, patch) {
        return s.setWidgetProps(vizKey, 'com.microstrategy.flex.viewer.GraphMatrixViewer', { ...s.chartProps(vizKey), ...patch });
      },
      // Dashboard-wide metric colors, used wherever a chart colors by Metric Names: colors = { metricId: '#hex' }.
      metricColors(colors, refreshKey = s.node) {
        return s.edit([{ act: 'updateElementsPropertiesMap', epm: [{ epmk: [{ ob: { did: '' } }],
          epmv: Object.entries(colors).map(([id, hex]) => ({ v: { vv: JSON.stringify({ color: Number(bgr(hex)) }) },
            k: { chn: [{ emt: 2, mt: { did: id, tp: 4, ql: 0 } }] } })) }] }], [refreshKey]);
      },
      // Chart props for a chart inserted in THIS session (chartProps() only sees charts that existed when the session opened):
      // writes the type plus extra GraphMatrix props. extra.axisOrigin = { metricId: value } moves the zero line (diverging
      // bars around a target), stored as the demo stores it.
      chartFormat(vizKey, { shape, visType, subtype = 'Automatic' }, extra = {}) {
        const p = { visStyle: 'GraphMatrixVisualizationStyle', Shape: shape, Subtype: subtype, visType, userVisType: visType, ...extra };
        if (extra.axisOrigin && typeof extra.axisOrigin === 'object') {
          const e = Object.entries(extra.axisOrigin); // editor form: '@pLd' + metric id, value as a string, plus AllMetrics
          p.axisOrigin = '{' + e.map(([m, v]) => `'@pLd${m}':{'axOriAuto':false,'axOriValue':'${v}'}`)
            .concat(`'AllMetrics':{'axOriAuto':false,'axOriValue':'${e[0][1]}'}`).join(',') + '}';
          p.xAxOriLnShw = 'true'; p.yAxOriLnShw = 'true'; // without these the custom origin is ignored when viewing
        }
        if (extra.axisRange && typeof extra.axisRange === 'object') { // { metricId: [min, max] }: fixed value-axis range
          const e = Object.entries(extra.axisRange);
          const one = (k, [lo, hi]) => `${k}:0:${lo}:${hi}:${lo}:${hi}:false:false:false`;
          p.AxisScale = [one('AllMetrics', e[0][1]), ...e.map(([m, r]) => one(m, r))].join(',');
          p.MinMax = 'Custom'; p.axScaleModified = '1'; p.AxisScaleSyncMode = 'false';
          delete p.axisRange;
        }
        if (extra.seriesColor) { p.modDefFillClr = bgr(extra.seriesColor); delete p.seriesColor; } // fill when nothing is on Color By
        return s.setWidgetProps(vizKey, 'com.microstrategy.flex.viewer.GraphMatrixViewer', p);
      },
      // Single-series color (e.g. one metric on a bar chart): Metric Names on Color By + a dashboard-wide color for the metric
      // (what the editor's "Shape Fill Color" sends), legend hidden. Note the color applies to that metric dashboard-wide
      // wherever it is colored by Metric Names. Color is a BGR integer.
      async setMetricColor(vizKey, metricId, hex, hideLegend = true) {
        await s.edit([{ act: 'updateTemplate', keyContext: vizKey, actions: [
          { ax: 0, act: 'addDropZoneUnit', zoneId: 7, unitId: '00000000000000000000000000000000', unitType: 4, unitPos: 0 }] }], [vizKey]);
        await s.edit([{ act: 'updateElementsPropertiesMap', epm: [{ epmk: [{ ob: { did: '' } }],
          epmv: [{ v: { vv: JSON.stringify({ color: Number(bgr(hex)) }) }, k: { chn: [{ emt: 2, mt: { did: metricId, tp: 4, ql: 0 } }] } }] }] }], [vizKey]);
        if (hideLegend) await s.setChartProps(vizKey, { LegendVisibleness: 'Hide' });
      },
      // Palette for one visualization: {act:'setPreferredPalette', pltid:<id from GET /api/palettes>, nodeKey}. A single-series
      // chart takes the palette's first color.
      setPalette(vizKey, paletteId) {
        return s.edit([{ act: 'setPreferredPalette', pltid: paletteId, nodeKey: vizKey }], [vizKey]);
      },
      // ================= General helpers (captured from the editor 2026-11-10, verified by full builds) =================
      // Node key for partialRetrieval. Must belong to the CURRENT chapter: 'K46' in a draft's first chapter; switchChapter()
      // updates it. Passing another chapter's node makes edits fail with a 500.
      node: 'K46',

      // ---- Derived objects (plain-text formulas work: isTokenStream:false) ----
      // Returns the new metric's id. Gotcha: don't give a derived metric the same name as a base metric that other formulas
      // reference (e.g. naming one "Budget" makes "[Actual] - [Budget]" ambiguous and fails).
      async createDerivedMetric(datasetId, name, formula, numberFormat) {
        const t = await s.edit([{ act: 'addDerivedMetricToDataset', dsid: datasetId, formula, isTokenStream: false, name, dsc: '',
          newObjectIds: ['$GUID_1'] }], [s.node]);
        const id = newObjectId(t, name);
        if (numberFormat) await s.edit([{ act: 'numberFormat', unitId: id, unitType: 4, c: 7, f: numberFormat }], [s.node]);
        return id;
      },
      // forms: [{ n: 'ID'|'DESC'|'DATE', formula, bft }]; returns the new attribute's id (server may append " 1" to the name).
      async createDerivedAttribute(datasetId, name, forms) {
        const t = await s.edit([{ act: 'addDAToDataset', isTokenStream: false, name, dsid: datasetId, forms }], [s.node]);
        return newObjectId(t, name);
      },
      // Rename a dataset attribute (dataset panel > Rename). Works for derived attributes such as time attributes.
      renameDatasetAttribute(datasetId, attrId, name) {
        return s.edit([{ act: 'updateDA', dsid: datasetId, attrId, name }], [s.node]);
      },
      // Dataset panel > right-click a date attribute > Create Time Attributes (reference/time-attributes.md). Creates one derived
      // attribute per type with the editor's own formulas, then renames it by our convention (timeAttributeName):
      // "Processed Date" + Year -> "Processed Year".
      // WHEN TO USE: only for a time attribute the incoming image actually uses (an axis, legend, column or selector named
      // like "Processed Year" / "Paid Month") that the dataset lacks. Create just those types. Never create every type, and
      // never create them for date attributes the image doesn't use.
      // source: { id, name, formId, formName }: the date attribute and its date-typed form (from GET /v2/cubes/{id}
      // availableObjects.attributes[].forms). types (required): the type(s) the image shows, from TIME_ATTRIBUTE_TYPES.
      // Returns { [type]: { id, name } }. Skip types the dataset already has, or the server appends " 1" to the name.
      async createTimeAttributes(datasetId, source, types, { rename = true } = {}) {
        if (!Array.isArray(types) || !types.length) throw new Error('createTimeAttributes: pass only the types the image uses');
        const out = {};
        for (const type of types) {
          const editorName = `${source.name} (${type})`;
          const t = await s.edit([{ act: 'addDAToDataset', isTokenStream: true, name: editorName, dsid: datasetId,
            forms: timeAttributeForms(type, source) }], [s.node]);
          const id = newObjectId(t, editorName);
          const name = rename ? timeAttributeName(source.name, type) : editorName;
          if (rename) await s.renameDatasetAttribute(datasetId, id, name);
          out[type] = { id, name };
        }
        return out;
      },

      // ---- Chapters and pages ----
      // Adds a chapter and returns its structural keys: { chapter, page, pageStack, filterPanel, proto, defaultViz }.
      // A new chapter's page/prototype keys are assigned by the server, so they are read back from the instance JSON.
      // index: 1-based position of the new chapter; 0 appends it at the end.
      async addChapter(chapterKey, title, pageTitle, index = 0) {
        await s.edit([{ act: 'addLayout', nodeKey: chapterKey, titlePattern: 1, index }], [s.node]);
        const k = await s.chapterKeys(chapterKey);
        await s.renameChapter(chapterKey, title);
        if (pageTitle) await s.renamePage(k.page, pageTitle);
        return k;
      },
      async chapterKeys(chapterKey) {
        const g = await task({ taskId: 'getServerJSONResults', messageID: mid, styleName: 'ServerJsonRWDStyle', resFlags: '0',
          excludeData: 'true', supportsUndo: 'true', compress: '1', innerHeight: '857', innerWidth: '1920' });
        const units = JSON.parse(grabJson(g, g.indexOf('"units":{', g.indexOf('"k":"' + chapterKey + '","title"')) + 8));
        const find = (n) => Object.keys(units).find((k) => units[k].n === n);
        const page = find('VisualizationPanel'), filterPanel = find('FiltersPanel');
        return { chapter: chapterKey, page, pageStack: units[page].pnk, filterPanel, filterStack: units[filterPanel].pnk,
          proto: find('SourceGrid'), defaultViz: Object.keys(units).find((k) => units[k].pnk === page && units[k].t === 521) };
      },
      // Make a chapter current (edits to its pages need this) and point partialRetrieval at it.
      async switchChapter(chapterKey, pageKey) {
        await s.edit([{ act: 'setCurrentLayout', unitKey: chapterKey, disablePU: true, panelUnitKey: pageKey }], [chapterKey]);
        s.node = pageKey;
      },
      // Adds a page to a chapter (pageStack from chapterKeys); the page starts with one visualization (vizKey) copied
      // from the chapter's prototype — reuse it or leave it out of the layout. index: 1-based position; 0 appends at the end.
      async addPage({ pageKey, pageStack, proto, vizKey, title, index = 1 }) {
        await s.edit([{ act: 'addPanel', nodeKey: pageKey, titlePattern: 1, parentKey: pageStack, index },
          { act: 'copyUnit', unitKey: proto, unitType: 521, newKey: vizKey, toKey: pageKey },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: { t: 'b', o: 'h', children: [{ t: 'c', f: false, l: 100, k: vizKey }] } } }, isJson: true },
          { act: 'setCurrentPanel', unitKey: pageKey }], [pageKey]);
        if (title) await s.renamePage(pageKey, title);
      },
      renameChapter(chapterKey, title) {
        return s.edit([{ act: 'format', unitKey: chapterKey, unitType: 1, formatType: 1, format: { FormattingView: { Title: title } } }], [chapterKey]);
      },
      renamePage(pageKey, title) {
        return s.edit([{ act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingView: { Title: title } } }], [pageKey]);
      },
      // The dashboard's table of contents, read from the instance: { root, chapters: [{ key, title, pageStack, pages:
      // [{ key, title }] }] } in display order. root is the document root (K3 in a draft), the parent for moveChapter.
      async structure() {
        const d = (await s.serverJson()).defn;
        return { root: d.root.k, chapters: d.layouts.map((l) => {
          const u = l.units, keys = Object.keys(u);
          const pageStack = keys.find((k) => u[k].n === 'VisualizationsPanelStack');
          const pages = keys.filter((k) => u[k].t === 9 && u[k].pnk === pageStack)
            .sort((a, b) => u[a].chdidx - u[b].chdidx).map((k) => ({ key: k, title: u[k].ttl }));
          return { key: l.k, title: l.title, pageStack, pages };
        }) };
      },
      // Duplicate Chapter (chapter menu): copies every page, visualization, filter and format of srcKey into a new chapter
      // destKey (any unused key, e.g. 'W249'). index is the 1-based position of the copy (the editor sends the source's
      // position + 1). Page and visualization keys inside the copy are server-assigned: returns chapterKeys(destKey).
      async duplicateChapter(srcKey, destKey, name, index) {
        await s.edit([{ act: 'duplLayout', srcKey, destKey, name, index, disablePU: true }], [s.node]);
        return s.chapterKeys(destKey);
      },
      // Delete (chapter menu): removes a chapter and all its pages. nextKey is the chapter to make current afterwards
      // (the editor picks the next one, or the previous one when deleting the last). Call switchChapter before editing it.
      deleteChapter(chapterKey, nextKey) {
        return s.edit([{ act: 'removeLayout', unitKey: chapterKey, isCurrent: true }, { act: 'setCurrentLayout', unitKey: nextKey }], []);
      },
      // Reorder chapters (drag in Contents): index is the 0-based target position among chapters. root from structure().
      moveChapter(chapterKey, index, root = 'K3') {
        return s.edit([{ act: 'moveUnit', toKey: root, unitType: 0, unitKey: chapterKey, index }], []);
      },
      // Duplicate Page (page menu): copies a page with all its visualizations into the same chapter. newKey is any unused
      // key; index is the 1-based position of the copy (the editor sends the source's position + 1; 0 appends). The copied visualizations get server-assigned keys
      // (read them from structure()/serverJson). The page is named title, or "<page> copy".
      async duplicatePage({ pageKey, pageStack, newKey, title, index }) {
        await s.edit([{ act: 'duplicatePanel', nodeKey: pageKey, parentKey: pageStack, duplicateKey: title, newKey, index },
          { act: 'setCurrentPanel', unitKey: newKey }], [newKey]);
      },
      // Delete (page menu). nextPageKey becomes the current page (a chapter must keep at least one page).
      deletePage(pageKey, nextPageKey) {
        return s.edit([{ act: 'removeUnit', unitKey: pageKey, unitType: 9 }, { act: 'setCurrentPanel', unitKey: nextPageKey }], [nextPageKey]);
      },
      // Reorder pages inside a chapter (drag in Contents): index is the 0-based target position in pageStack.
      movePage(pageKey, pageStack, index) {
        return s.edit([{ act: 'moveUnit', toKey: pageStack, unitType: 9, unitKey: pageKey, index }, { act: 'setCurrentPanel', unitKey: pageKey }], [pageKey]);
      },

      // ---- Text, selectors, narratives, custom visualizations ----
      // Plain text box on a page. font: FormattingFont props, e.g. { Bold: -1, Size: '14', Italic: -1, Color: bgr('#1b354a') }.
      addText({ pageKey, fieldKey, nodeKey, text, font = {} }) {
        return s.edit([
          { act: 'addField', createNode: true, nodeKeyParent: pageKey, fieldKey, fieldType: 3, nodeKey, treeType: 1, fieldName: fieldKey },
          { act: 'editField', fieldValue: text, fieldKey, fieldType: 3, nodeKey, treeType: 1, fieldName: fieldKey },
          { act: 'format', unitKey: fieldKey, unitType: 106, formatType: 1, fieldKey, nodeKey, keyContext: '106\u001e' + nodeKey + '\u001e' + fieldKey,
            format: { FormattingFont: font, FormattingSize: { TextOverflow: 1, HeightMode: 0 } } }], [pageKey]);
      },
      // Rich Text (Insert > Text > Rich Text; reference/text-catalog.md): each run of words has its own formatting.
      // Same text field as addText plus FormattingAppearance.TextFieldType 1; the value carries a Quill Delta (richTextValue).
      // runs: [{ text, bold, italic, underline, strike, color: '#hex', size: 10 (pt), font: 'opensans' }]. A run
      //   { text: '\n', align: 'center'|'right'|'justify', header: 1-6, list: 'bullet'|'ordered', indent: 1-8 } ends a paragraph
      //   and carries its paragraph formats; the last paragraph takes align / header / list / indent from the options.
      addRichText({ pageKey = 'K53', fieldKey, nodeKey, createNode = true, name = 'Rich Text', runs, align, header, list, indent, layout, transparent = false }) {
        const f = { fieldKey, fieldType: 3, nodeKey, treeType: 1, fieldName: name };
        const kc = '106\u001e' + nodeKey + '\u001e' + fieldKey;
        const acts = [{ act: 'addField', createNode, nodeKeyParent: pageKey, ...f },
          { act: 'editField', fieldValue: richTextValue(runs, { align, header, list, indent }), ...f, altText: '' },
          { act: 'format', unitKey: fieldKey, unitType: 106, formatType: 1, fieldKey, nodeKey, keyContext: kc,
            format: { FormattingSize: { TextOverflow: 1, HeightMode: 0 }, FormattingAppearance: { TextFieldType: 1 },
              ...(transparent ? { FormattingPatterns: { FillStyle: 1 } } : {}) } }];   // transparent: no white box behind the text
        if (layout) acts.push({ act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true });
        return s.edit(acts, [pageKey]);
      },
      // Link on a text box (right-click > Create Link / Edit Link; reference/link-catalog.md). Writes the field's
      // FormattingNavigation.Hyperlinks, the same format action the editor sends when you click Save in the link dialog.
      // to: { page }                      a page in this dashboard (the "< Back to Home" pattern)
      //     { url, newTab = true }        a web page (pass the full URL; the dialog's prefilled 'http://' is not added)
      //     { dashboard, page, newTab = true, passFilterPanel = true, passVizSelections = true, filterPages = [page] }
      //                                   a page in another dashboard (dashboard = its object ID); filterPages are the
      //                                   target pages that receive the selected filters
      //     null                          Remove Link
      // tooltip: the dialog's Tooltip box. nodeKey / fieldKey: the text box's keys (as passed to addText / addRichText).
      setLink({ fieldKey, nodeKey, to, tooltip = '' }) {
        const kc = '106\u001e' + nodeKey + '\u001e' + fieldKey;
        const base = { act: 'format', unitKey: fieldKey, unitType: 106, formatType: 1, fieldKey, nodeKey, keyContext: kc };
        if (!to) return s.edit([{ ...base, format: { FormattingNavigation: { Hyperlinks: '' } } }], [nodeKey]);
        const esc = (v) => String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        const attrs = (o) => Object.entries(o).map(([k, v]) => `${k}="${esc(v)}"`).join(' ');
        let hls, hl, resolved = '';
        if (to.url) {
          hls = to.newTab === false ? '' : ' onw="1"';
          hl = { idf: 1, aopam: 2, dtxt: tooltip, url: to.url, lt: 0, so: 0 };
          resolved = `<hls><hl index="0" url="${esc(to.url)}"/></hls>`;
        } else if (to.dashboard) {
          const { dashboard, page, newTab = true, passFilterPanel = true, passVizSelections = true, filterPages = [page] } = to;
          hls = newTab ? ' onw="1"' : '';
          hl = { idf: 1, so: 2, lt: 1, tid: dashboard, ttp: 55, navpage: page, np: page, psf: passFilterPanel ? 1 : 0,
            pics: passVizSelections ? 1 : 0, aopam: 2, dtxt: tooltip, ftgs: filterPages.join(';') };
        } else {
          hls = '';
          hl = { idf: 1, aopam: 2, dtxt: tooltip, lt: 3, np: to.page, so: 0 };
        }
        // The editor sends the XML HTML-encoded and flags it with isHtmlEncoded.
        const xml = `<hls${hls}><hl ${attrs(hl)}/></hls>`;
        const enc = xml.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&#34;');
        return s.edit([{ ...base, isHtmlEncoded: true, format: { FormattingNavigation: { Hyperlinks: enc, ResolvedHyperlinks: resolved } } }], [nodeKey]);
      },
      // Shape (Insert > Shapes; reference/shape-catalog.md). shape: 'Line' | 'Rectangle' | 'Ellipse' | 'Triangle' | 'Polygon'.
      // A shape is a field (fieldType 1, unit type 101) whose value is JSON { t, s, e, n }: t the drawing type (a triangle is
      // t 'Polygon', n 'Triangle'), s the shape settings, e an SVG the editor reads only the shape element's style from
      // (fill, stroke, stroke-width, fill-opacity, stroke-dasharray); geometry is redrawn from s and the box size.
      // settings: Rectangle { radius: 0|15|25|35 }, Ellipse { toggled: true = circle }, Triangle { direction: 0 up 1 right
      // 2 down 3 left, toggled: true = right angled }, Polygon { count: 3-10 }, Line { direction: 0 horizontal 1 vertical
      // 2/3 diagonal, arrowStartType / arrowEndType: 'NONE' | 'LINE_ARROW' | 'TRIANGLE_ARROW' }.
      // dash: 'solid' | 'dash' | 'dot'. Every shape on a page can share one nodeKey; pass createNode: false after the first.
      insertShape({ shape = 'Rectangle', fieldKey, nodeKey, createNode = true, pageKey = 'K53', layout, settings = {},
        fill = '#8AC3FF', stroke = '#35383A', strokeWidth = 1, opacity, dash }) {
        const T = { Line: ['Line', 'line'], Rectangle: ['Rectangle', 'rect'], Ellipse: ['Ellipse', 'ellipse'], Triangle: ['Polygon', 'polygon'], Polygon: ['Polygon', 'polygon'] }[shape];
        if (!T) throw new Error('Unknown shape ' + shape);
        const D = { Line: { arrowStartType: 'LINE_ARROW', arrowEndType: 'LINE_ARROW', direction: 0 }, Rectangle: { p: 0, radius: 0 }, Ellipse: { p: 0, toggled: false },
          Triangle: { p: 0, pos: 0, count: 5, toggled: false, direction: 0 }, Polygon: { p: 0, pos: 0, count: 5, toggled: false, direction: 0 } }[shape];
        const style = [`fill: ${shape === 'Line' ? 'none' : fill}`, `stroke: ${stroke}`, `stroke-width: ${strokeWidth}px`]
          .concat(opacity !== undefined ? [`fill-opacity: ${opacity}`] : [])
          .concat(dash ? [`stroke-dasharray: ${{ solid: '0', dash: '6, 2', dot: '2, 2' }[dash] || dash}`] : []).join('; ') + ';';
        const value = JSON.stringify({ t: T[0], s: { ...D, ...settings }, e: `<svg xmlns="http://www.w3.org/2000/svg"><defs/><${T[1]} style="${style}"/></svg>`, n: shape });
        const f = { fieldKey, fieldType: 1, nodeKey, treeType: 1, fieldName: shape };
        const acts = [{ act: 'addField', createNode, nodeKeyParent: pageKey, ...f }, { act: 'editField', fieldValue: value, ...f },
          // keyContext is required: without it FillStyle is ignored and the shape's box gets a gray (#ddd) background.
          { act: 'format', unitKey: fieldKey, unitType: 101, formatType: 1, fieldKey, nodeKey, keyContext: '101\u001e' + nodeKey + '\u001e' + fieldKey,
            format: { FormattingPatterns: { FillStyle: 1 } } }];
        if (layout) acts.push({ act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true });
        return s.edit(acts, [pageKey]);
      },
      // Attribute / Metric Selector (Insert > Filter > Attribute / Metric Selector; reference/object-selector-catalog.md).
      // Picking an item swaps one object inside each target visualization. A selector holds attributes OR metrics, never both.
      // objects: candidate ids (all metrics, kind 'metric', or all attributes, kind 'attribute'). targets: [{ key, replace }]
      // where replace is the id of the object in that visualization the selection swaps (the visualization's own object
      // is the first item and the default). title: say what is chosen ("Metric Selector", "Select a Metric"). Defaults:
      // title bar on, Drop-down, single select. style: 0 drop-down, 2 list box, 3 radio, 5 button bar, 6 link bar.
      // selected: an object id to pick (items are 'i<id>;<id>' for metrics, 'U<id>;<id>' for attributes).
      async addObjectSelector({ pageKey, nodeKey, ctlKey, kind = 'metric', objects, targets = [], title, style = SELECTOR_STYLE.dropDown,
        multi = false, showTitle = true, selected }) {
        const ctx = '1\u001e' + nodeKey + '\u001e' + ctlKey, tp = kind === 'metric' ? UNIT.metric : UNIT.attribute;
        await s.edit([{ act: 'addControl', parentKey: pageKey, nodeKey, ctlKey, isUC: false, unitType: -1, unitId: '', targetKeys: [], ctlType: 8, gpType: 3, isParameterSelector: false }], [pageKey]);
        await s.edit([{ act: 'setCandidateObjects', keyContext: ctx, ctlType: 8, units: objects.map((id) => ({ id, tp })) }], [pageKey]);
        await s.edit([{ act: 'format', unitKey: ctlKey, unitType: 111, formatType: 1, keyContext: ctx,
          format: { FormattingSelector: { Style: style, Multiselect: multi && style !== SELECTOR_STYLE.radio ? 1 : 0, Orientation: 1 } } }], [pageKey]);
        await s.edit([{ act: 'format', unitKey: ctlKey, unitType: 111, formatType: 5, format: { FormattingView: { ShowTitleBar: showTitle ? 1 : 0 } }, keyContext: ctx }], [pageKey]);
        if (title) await s.edit([{ act: 'format', unitKey: ctlKey, unitType: 111, formatType: 1, format: { FormattingView: { Title: title } }, keyContext: ctx }], [pageKey]);
        // The editor's Edit Targets for this selector (changeAMSelectorTargets): rplObjId / rplObjTp name the swapped object,
        // and excludeCtp must be left out — with excludeCtp: true the target is recorded but nothing is swapped.
        for (const t of targets) await s.edit([{ act: 'addControlTarget', keyContext: ctx, tgtKey: t.key, isUC: true, rplObjId: t.replace, rplObjTp: tp,
          partialRetrieval: { nodes: [nodeKey] }, partialUpdate: { selectors: [ctlKey] } }], [t.key, nodeKey]);
        if (selected) await s.edit([{ act: 'setSelectorElements', keyContext: ctx, ctlKey, isVisualization: false, include: true,
          elemList: (kind === 'metric' ? 'i' : 'U') + selected + ';' + selected, tks: targets.map((t) => t.key).join(',') }], [pageKey]);
      },
      // On-canvas Element / Value Filter (Insert > Filter > Element / Value Filter; not the Filter Panel).
      // Defaults: Drop-down, multiple selections allowed, title bar shown with `name` as its text.
      // style (FormattingSelector.Style, see SELECTOR_STYLE): 0 drop-down, 1 slider, 2 list box, 3 radio, 4 check boxes,
      // 5 button bar, 6 link bar, 9 search box. Radio is always single-select. name: the title text (normally the attribute
      // name); without it the title bar is blank. targets: visualization keys (for a Modern Grid, its stitched key).
      // selected: element ids. Put ctlKey in the page layout with >= ~11% height. Details: reference/canvas-selector-catalog.md.
      async addCanvasSelector({ pageKey, nodeKey, ctlKey, attrId, name, style = SELECTOR_STYLE.dropDown, multi = true,
        showTitle = true, targets = [], selected = [] }) {
        const ctx = '1\u001e' + nodeKey + '\u001e' + ctlKey;
        const multiselect = style === SELECTOR_STYLE.radio ? 0 : multi ? 1 : 0;
        await s.edit([{ act: 'addControl', parentKey: pageKey, nodeKey, ctlKey, isUC: false, unitType: -1, unitId: '', targetKeys: [], ctlType: 1, gpType: 1, isParameterSelector: false }], [pageKey]);
        await s.edit([{ act: 'setControlSource', keyContext: ctx, unitId: attrId, unitType: 12, ctrlType: 10, removeCGB: [] }], [pageKey]);
        await s.edit([{ act: 'format', unitKey: ctlKey, unitType: 111, formatType: 1, format: { FormattingSelector: { Style: style, Multiselect: multiselect, Orientation: 1 } }, keyContext: ctx }], [pageKey]);
        // The title bar is a formatType 5 format (the editor's toggleTitleBar); a new selector starts with it hidden.
        await s.edit([{ act: 'format', unitKey: ctlKey, unitType: 111, formatType: 5, format: { FormattingView: { ShowTitleBar: showTitle ? 1 : 0 } }, keyContext: ctx }], [pageKey]);
        if (name) await s.edit([{ act: 'format', unitKey: ctlKey, unitType: 111, formatType: 1, format: { FormattingAppearance: { Name: name } }, keyContext: ctx }], [pageKey]);
        await s.edit([{ act: 'setControlShowAll', nodeKey, controlKey: ctlKey, showAll: true }], [pageKey]);
        // excludeCtp false: the selector filters its targets, and "(All)" shows the total. With excludeCtp true (verified
        // 2026-11-15) each target is grouped by the selector's elements instead: KPIs, map and donut legend show only the first
        // element (BROKER: 179,426 of 550,000) even while the drop-down reads "(All)".
        for (const t of targets) await s.edit([{ act: 'addControlTarget', keyContext: ctx, tgtKey: t, isUC: true, excludeCtp: false }], [pageKey]);
        if (selected.length) await s.edit([{ act: 'setSelectorElements', keyContext: ctx, ctlKey, isVisualization: false, include: true,
          elemList: selected.map((v) => 'h' + v + ';' + attrId + ';' + v).join(','), tks: targets.join(',') }], [pageKey]);
      },
      // Custom visualization from the gallery (e.g. 'ImageEnhancedKPI' = Iconic KPI, 'AutoNarratives'). layout must include key.
      insertCustomVis({ newKey, visName, pageKey = 'K53', protoKey = 'K51', layout }) {
        return s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey, toKey: pageKey },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true },
          { act: 'updateTemplate', keyContext: newKey, actions: [{ act: 'createDefaultDropZones', nodeKey: newKey, treeType: 1, datasetType: 3, widgetType: 7 }] },
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: {
            Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: visName, VisualizationList: visName,
              IPhoneVisualization: '', IPadVisualization: '', APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false },
            FormattingWidget: { ClassName: 'com.microstrategy.web.vf.viewer.CustomVisApplicationViewer', Enable: 1,
              WidgetProps: '<props><widgetProps><fmt><cvp><ftFgGrpA value="1"></ftFgGrpA></cvp></fmt></widgetProps></props>' },
            FormattingView: { ShowTitleBar: 0, ShowWidgetTitleBar: 0 } } },
          { act: 'changeGridDisplayMode', nodeKey: newKey, displayMode: 1 }], [newKey]);
      },
      // Mapbox map (widgetType 8 = MAPBOX in the editor's widget enum; class MapboxApplicationViewer). Zones: MAP_ZONE.
      // Its settings are plain fmt props (setWidgetProps with MAPBOX_CLASS): ga = geo attribute id, cmt = Color By metric id,
      // tooltip = concatenated ids, lid 'adm1' = state boundaries, bmt '4' = Mapbox, dv = style URL, mz/mp = zoom/center.
      // Heat Map (verified 2026-11-15 against "Merch Category Breakdown" on Wawa 08.31 Demo). layout must include newKey.
      // grouping: attribute ids, outer first (1 or more); colorBy / sizeBy: metric ids. bands: percentile colors for Color By,
      // lowest 20% first (the editor's defaults; [] to skip). props: HEATMAP_PROPERTIES widget props, merged over the
      // editor's defaults: mv 'true' show metric values, lb 'On'|'Off'|'Proportional' labels, he header type, th theme,
      // hcl header colors, bg background, fts fonts (all as the source stores them).
      async insertHeatmap({ newKey, pageKey = 'K53', protoKey = 'K51', layout, datasetId, grouping, colorBy, sizeBy, bands = HEATMAP_BANDS, props = {} }) {
        await s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey, toKey: pageKey },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true },
          { act: 'updateTemplate', keyContext: newKey, actions: [{ act: 'createDefaultDropZones', nodeKey: newKey, treeType: 1, datasetType: 3, widgetType: 2 }] },
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: {
            Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: 'VIHeatMapVisualizationStyle', VisualizationList: 'VIHeatMapVisualizationStyle',
              IPhoneVisualization: '', IPadVisualization: '', APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false },
            FormattingWidget: { ClassName: HEATMAP_CLASS, Enable: 1, WidgetProps: '<props><widgetProps><fmt></fmt></widgetProps></props>' } } },
          { act: 'changeGridDisplayMode', nodeKey: newKey, displayMode: 1 }], [newKey]);
        // Grouping positions are 1-based: unitPos 0 for every attribute put them in reverse order.
        await s.fillZones(newKey, datasetId, [
          ...grouping.map((id, i) => ({ zoneId: HEATMAP_ZONE.grouping, unitId: id, unitType: 12, unitPos: i + 1 })),
          ...(colorBy ? [{ zoneId: HEATMAP_ZONE.colorBy, unitId: colorBy, unitType: 4 }] : []),
          ...(sizeBy ? [{ zoneId: HEATMAP_ZONE.sizeBy, unitId: sizeBy, unitType: 4 }] : [])]);
        const defaults = { ftFgGrpA: '1', th: '1', mv: 'true', he: '1', lb: 'On',
          hcl: "[{'value':'#EFEFEF','opacity':1},{'value':'#E4E4E4','opacity':1},{'value':'#E4E4E4','opacity':1}]",
          bg: "{'value':'#FFFFFF','opacity':1}",
          fts: "{'headerOnMiddle':{'family':'Open Sans','style':'1'},'headerOnTop':{'header':{'family':'Open Sans','style':'1'},'cell':{'family':'Open Sans','style':'1'}}}" };
        await s.setWidgetProps(newKey, HEATMAP_CLASS, { ...defaults, ...props });
        if (colorBy && bands.length) await s.metricThresholds(newKey, colorBy, bands.map((color, i) => ({ color,
          ...(i ? { flr: (100 * i) / bands.length } : {}), ...(i < bands.length - 1 ? { ceil: (100 * (i + 1)) / bands.length } : {}) })), 'percent');
      },
      // Sankey Diagram (verified 2026-11-15 against "Loan Lifecycle" on Sallie Mae Dashboard). layout must include newKey.
      // levels: attribute ids, first stage first (2 or more); metric: the flow-width metric id; tooltip: extra metric ids.
      // props: the plugin's cvp properties, merged over the source's look (total under each node label, nodes centered and
      // draggable, colored by node, fixed node width 54). Booleans and numbers are sent as strings, as the plugin stores
      // them. Plugin defaults and every property: reference/sankey-catalog.md.
      async insertSankey({ newKey, pageKey = 'K53', protoKey = 'K51', layout, datasetId, levels, metric, tooltip = [], props = {} }) {
        if (!levels || levels.length < 2) throw new Error('A Sankey needs 2 or more level attributes');
        await s.insertCustomVis({ newKey, visName: 'Sankey', pageKey, protoKey, layout });
        await s.fillZones(newKey, datasetId, [
          ...levels.map((id, i) => ({ zoneId: SANKEY_ZONE.levels, unitId: id, unitType: 12, unitPos: i + 1 })),
          { zoneId: SANKEY_ZONE.metric, unitId: metric, unitType: 4 },
          ...tooltip.map((id, i) => ({ zoneId: SANKEY_ZONE.tooltip, unitId: id, unitType: 4, unitPos: i + 1 }))]);
        const look = { ftFgGrpA: '1', showTotalOnLabel: 'true', totalAlignment: 'below', nodeAlignment: 'middle', isDraggingOfNodesEnabled: 'true',
          colorByNode: 'true', showLabelOnNode: 'false', nodeWidthAllMode: 'fixed', nodeWidthAllValue: '54' };
        const all = { ...look, ...props };
        for (const k of Object.keys(all)) if (typeof all[k] !== 'string') all[k] = typeof all[k] === 'object' ? JSON.stringify(all[k]) : String(all[k]);
        await s.setWidgetProps(newKey, CUSTOM_VIS_CLASS, all, 'cvp');
      },
      // Bubble / scatter chart (GraphMatrix Circle, visType 21; reference/bubble-catalog.md; verified 2026-11-15 against
      // "Credit Score vs Status" on Sallie Mae Dashboard). x / y: metric ids (both axes are metrics). breakBy: attribute ids,
      // one bubble per element combination. colorBy: attribute id (defaults to the first breakBy). size: Size By metric id;
      // leave it out for equal-size bubbles, as the source does. tooltip: extra metric ids shown on hover.
      // props: GraphMatrix props merged over the source's look (legend shown, data labels hidden).
      async insertBubble({ newKey, pageKey = 'K53', protoKey = 'K51', layout, datasetId, x, y, breakBy = [], colorBy, size, tooltip = [], props = {} }) {
        await s.insertChart({ newKey, vis: VIS.scatter, pageKey, protoKey, layout });
        const color = colorBy || breakBy[0];
        await s.fillZones(newKey, datasetId, [
          { zoneId: ZONE.xAxis, unitId: x, unitType: 4 }, { zoneId: ZONE.yAxis, unitId: y, unitType: 4 },
          ...breakBy.map((id, i) => ({ zoneId: ZONE.breakBy, unitId: id, unitType: 12, unitPos: i + 1 })),
          ...(color ? [{ zoneId: ZONE.colorBy, unitId: color, unitType: 12 }] : []),
          ...(size ? [{ zoneId: ZONE.sizeBy, unitId: size, unitType: 4 }] : []),
          ...tooltip.map((id, i) => ({ zoneId: ZONE.tooltip, unitId: id, unitType: 4, unitPos: i + 1 }))]);
        await s.chartFormat(newKey, VIS.scatter, { LegendVisibleness: 'Show', DataLabel: 'Hide', ...props });
      },
      // Vertical Stacked Bar Chart (the gallery's own type, visType 6; reference/stacked-bar-catalog.md). Not the plain
      // vertical bar (70) with a Stacked subtype. x: attribute ids on the category axis. metric: one metric stacked by the
      // stackBy attribute, or metrics: 2+ metrics stacked on each other (Metric Names on Color By). colors: { elementOrMetricId:
      // '#hex' } (element names when stacking by an attribute). radius: corner rounding (0-50, 30 = the screenshot's look);
      // separate: true rounds every segment (shpRadiusStyle 0), false rounds the stack as one (1, the editor's default).
      // separator: the segment border, a thin line between segments ('#FFFFFF', 1 px solid); null leaves the default.
      async insertStackedBar({ newKey, pageKey = 'K53', protoKey = 'K51', layout, datasetId, x, metric, metrics, stackBy, colors,
        radius = 30, separate = true, separator = { color: '#FFFFFF', width: 1 }, props = {} }) {
        await s.insertChart({ newKey, vis: VIS.stackedBar, pageKey, protoKey, layout });
        const mets = metrics || [metric];
        await s.fillZones(newKey, datasetId, [
          ...[].concat(x).map((id, i) => ({ zoneId: ZONE.xAxis, unitId: id, unitType: 12, unitPos: i + 1 })),
          ...mets.map((id, i) => ({ zoneId: ZONE.yAxis, unitId: id, unitType: 4, unitPos: i + 1 })),
          ...(stackBy ? [{ zoneId: ZONE.breakBy, unitId: stackBy, unitType: 12 }, { zoneId: ZONE.colorBy, unitId: stackBy, unitType: 12 }]
            : [{ zoneId: ZONE.colorBy, unitId: '00000000000000000000000000000000', unitType: 4 }])]);   // Metric Names
        const t0 = Date.now();
        const shp = [`'shpRadius':${radius}`, `'shpRadius_tmsp':${t0}`];
        if (separator) shp.push(`'shpBdrClr':${Number(bgr(separator.color))}`, `'shpBdrThk':${separator.width || 1}`, `'shpBdrStyle':0`, `'shpBdrCmbStyle':1`);
        await s.chartFormat(newKey, VIS.stackedBar, { allShpFmt: '{' + shp.join(', ') + '}', shpRadiusStyle: separate ? '0' : '1', ...props });
        if (colors) {
          if (stackBy) await s.elementColors(stackBy, colors, newKey); else await s.metricColors(colors, newKey);
        }
      },
      // Line chart (VIS.line, visType 72; reference/line-catalog.md). Format > Data Labels and Shapes > Shape > Style:
      // style 'straight' (shpSmooth 0, the editor's default) or 'curved' (shpSmooth 1) with Curve Smoothness = smoothness.
      // House default: curved at 0.3 (the editor offers 0.6 when you switch to curved). x: attribute ids; metrics: metric ids
      // (2+ make one line each, colored by Metric Names); breakBy: an attribute for one line per element. color: one line's
      // color; markers: show point markers; dataLabels: value labels on the points. The _tmsp keys are written as the editor does.
      async insertLine({ newKey, pageKey = 'K53', protoKey = 'K51', layout, datasetId, x, metrics, metric, breakBy, style = 'curved', smoothness = 0.3,
        color, markers = false, dataLabels = false, props = {} }) {
        const mets = metrics || [metric];
        await s.insertChart({ newKey, vis: VIS.line, pageKey, protoKey, layout });
        await s.fillZones(newKey, datasetId, [
          ...[].concat(x).map((id, i) => ({ zoneId: ZONE.xAxis, unitId: id, unitType: 12, unitPos: i + 1 })),
          ...mets.map((id, i) => ({ zoneId: ZONE.yAxis, unitId: id, unitType: 4, unitPos: i + 1 })),
          ...(breakBy ? [{ zoneId: ZONE.breakBy, unitId: breakBy, unitType: 12 }, { zoneId: ZONE.colorBy, unitId: breakBy, unitType: 12 }]
            : mets.length > 1 ? [{ zoneId: ZONE.colorBy, unitId: '00000000000000000000000000000000', unitType: 4 }] : [])]);
        const t0 = Date.now(), curved = style === 'curved';
        const shp = [`'shpSmooth':${curved ? 1 : 0}`, `'shpSmooth_tmsp':${t0}`];
        if (curved) shp.push(`'shpSmoothStrength':${smoothness}`, `'shpSmoothStrength_tmsp':${t0}`);
        await s.chartFormat(newKey, VIS.line, { allShpFmt: '{' + shp.join(', ') + '}', lnMkShw: markers ? 'true' : 'false',
          ...(dataLabels ? { DataLabel: 'Show only values' } : {}), ...(color && mets.length === 1 && !breakBy ? { seriesColor: color } : {}), ...props });
      },
      // Donut Chart (verified 2026-11-15 on McDonald’s Revenue Overview). layout must include newKey. metric: the slice size
      // (Angle); slice: the attribute whose elements are the slices (also Color By unless colorBy is given). colors: { element:
      // '#hex' }. Settings are one unifiedProperty JSON; props merge over this look: thin ring (innerRatio 80), 2 px gaps
      // (padding), rounded slice ends (shapeRadius '6%'), the total and metric name in the center (dataLabelType 6), a legend
      // with values (legendValueType 2) and no legend title. target / breakBy: the plugin's Target metric and one-donut-per-
      // element attribute. Plugin defaults and every property: reference/donut-catalog.md.
      async insertDonut({ newKey, pageKey = 'K53', protoKey = 'K51', layout, datasetId, metric, slice, colorBy, target, breakBy, colors, props = {} }) {
        await s.insertCustomVis({ newKey, visName: 'DonutChart', pageKey, protoKey, layout });
        await s.fillZones(newKey, datasetId, [
          { zoneId: DONUT_ZONE.angle, unitId: metric, unitType: 4 },
          { zoneId: DONUT_ZONE.colorBy, unitId: colorBy || slice, unitType: 12 },
          { zoneId: DONUT_ZONE.slice, unitId: slice, unitType: 12 },
          ...(target ? [{ zoneId: DONUT_ZONE.target, unitId: target, unitType: 4 }] : []),
          ...(breakBy ? [{ zoneId: DONUT_ZONE.breakBy, unitId: breakBy, unitType: 12 }] : [])]);
        const look = { showLegend: true, showLegendTitle: false, innerRatio: 80, padding: 2, showDataLabel: true, dataLabelType: DONUT_LABEL.textAndValue,
          legendValueType: 2, shapeRadius: '6%', legendContentType: 'all', textContentType: 'all' };
        await s.setWidgetProps(newKey, CUSTOM_VIS_CLASS, { ftFgGrpA: '1', unifiedProperty: JSON.stringify({ ...look, ...props }) }, 'cvp');
        if (colors) await s.elementColors(colorBy || slice, colors, newKey);
      },
      insertMapbox({ newKey, pageKey = 'K53', protoKey = 'K51', layout }) {
        return s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey, toKey: pageKey },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true },
          { act: 'updateTemplate', keyContext: newKey, actions: [{ act: 'createDefaultDropZones', nodeKey: newKey, treeType: 1, datasetType: 3, widgetType: 8 }] },
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: {
            Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: 'MapboxVisualizationStyle', VisualizationList: 'MapboxVisualizationStyle',
              IPhoneVisualization: '', IPadVisualization: '', APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false },
            FormattingWidget: { ClassName: MAPBOX_CLASS, Enable: 1, WidgetProps: '<props><widgetProps><fmt></fmt></widgetProps></props>' } } },
          { act: 'changeGridDisplayMode', nodeKey: newKey, displayMode: 1 }], [newKey]);
      },
      // ---- Native KPI family (captured from the editor's KPI gallery 2026-11-10; see reference/kpi-catalog.md) ----
      // KPI card (KPICardVisualizationStyle). Zones: KPI_ZONE.metric 19, .trend 20 (sparkline + previous period), .breakBy 5.
      insertKpiCard({ newKey, pageKey = 'K53', protoKey = 'K51', layout, title }) {
        return s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey, toKey: pageKey },
          { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true },
          { act: 'updateTemplate', keyContext: newKey, actions: [{ act: 'createDefaultDropZones', nodeKey: newKey, treeType: 1, datasetType: 3, widgetType: 9 }] },
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: {
            Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: 'KPICardVisualizationStyle', VisualizationList: 'KPICardVisualizationStyle',
              IPhoneVisualization: '', IPadVisualization: 'IPhoneKPICardStyle', APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false },
            FormattingWidget: { ClassName: KPI_CARD_CLASS, Enable: 1, WidgetProps: '<props><widgetProps><fmt><dm value="5"></dm><fstr value="1"></fstr></fmt></widgetProps></props>' },
            ...(title ? { FormattingView: { Title: title } } : {}) } },
          { act: 'format', unitKey: newKey, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: 0 } } },
          { act: 'changeGridDisplayMode', nodeKey: newKey, displayMode: 1 },
        ], [newKey]);
      },
      // KPI card settings (replaces the set): dm '5' single / '1' one card per Break By element, gcc cards per view,
      // smn 'true' metric name in the title, tst, ks 'custom' + cks [{bgColor, chartColor,...}], nfts {label, primary_value,
      // previous_value, trend_identity: {fc, fw, ff, fsz...}}. Objects are serialized for you.
      setKpiCardProps(vizKey, props = {}) {
        const p = { dm: '5', fstr: '1', ...props };
        for (const k of Object.keys(p)) if (typeof p[k] === 'object') p[k] = JSON.stringify(p[k]);
        return s.setWidgetProps(vizKey, KPI_CARD_CLASS, p);
      },
      // Turn a new draft's default grid (K52) into a KPI card in place: insertKpiCard without the copy.
      toKpiCard(vizKey = 'K52') {
        return s.edit([
          { act: 'updateTemplate', keyContext: vizKey, actions: [{ act: 'createDefaultDropZones', nodeKey: vizKey, treeType: 1, datasetType: 3, widgetType: 9 }] },
          { act: 'format', unitKey: vizKey, unitType: 521, formatType: 1, format: {
            Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: 'KPICardVisualizationStyle', VisualizationList: 'KPICardVisualizationStyle',
              IPhoneVisualization: '', IPadVisualization: 'IPhoneKPICardStyle', APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false },
            FormattingWidget: { ClassName: KPI_CARD_CLASS, Enable: 1, WidgetProps: '<props><widgetProps><fmt><dm value="5"></dm><fstr value="1"></fstr></fmt></widgetProps></props>' } } },
          { act: 'format', unitKey: vizKey, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: 0 } } },
          { act: 'changeGridDisplayMode', nodeKey: vizKey, displayMode: 1 },
        ], [vizKey]);
      },
      // Image from a URL (Insert > Image): a field with fieldType 2 (unit type 102) whose value is the URL. It can share a
      // field-group node with shapes and text boxes (createNode: false after the first). Verified 2026-11-12.
      // sizeMode = Format > Size (FormattingSize.ImageSizeMode, captured 2026-11-13): 3 Fill Container (the default here:
      // covers the box, cropping the overflow), 2 Fit to Container (the editor's default; letterboxes). Fixed to and Stretch
      // are the menu's other options.
      insertImage({ fieldKey, nodeKey, createNode = true, pageKey = 'K53', url, name = 'Image', sizeMode = 3, layout }) {
        const f = { fieldKey, fieldType: 2, nodeKey, treeType: 1, fieldName: name };
        const acts = [{ act: 'addField', createNode, nodeKeyParent: pageKey, ...f }, { act: 'editField', fieldValue: url, ...f },
          { act: 'format', unitKey: fieldKey, unitType: 102, formatType: 1, fieldKey, nodeKey, keyContext: '102\u001e' + nodeKey + '\u001e' + fieldKey,
            format: { FormattingSize: { ImageSizeMode: sizeMode } } }];
        if (layout) acts.push({ act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true });
        return s.edit(acts, [pageKey]);
      },
      // Comparison KPI (zones: CMP_ZONE.actual 3, .target 4, .breakBy 5, .trend 6) and Multi-Metric KPI (MM_ZONE.metrics 3,
      // .trend 5). Both are custom visualizations; their settings are one `properties` JSON in cvp. Keys you leave out keep
      // the visualization's defaults (layoutType, secondaryMetricName, trendShape, trendFillColor, cardAlignment, ...).
      insertComparisonKpi: (o) => s.insertCustomVis({ ...o, visName: 'ComparisonKPI' }),
      insertMultiMetricKpi: (o) => s.insertCustomVis({ ...o, visName: 'MultiMetricKPI' }),
      setKpiProperties(vizKey, properties) {
        return s.setWidgetProps(vizKey, CUSTOM_VIS_CLASS, { ftFgGrpA: '1', properties: JSON.stringify(properties) }, 'cvp');
      },
      // Show or hide a visualization's title bar, optionally with a title.
      titleBar(vizKey, show = true, title) {
        return s.edit([{ act: 'format', unitKey: vizKey, unitType: 521, formatType: 1, format: {
          FormattingView: { ShowTitleBar: show ? -1 : 0, ShowWidgetTitleBar: show ? -1 : 0, ...(title ? { Title: title } : {}) } } }], [vizKey]);
      },

      // AI narratives summarizing the given visualizations with an instruction (generated when the page renders).
      async addNarratives({ newKey, pageKey = 'K53', protoKey = 'K51', layout, sources, instruction }) {
        await s.insertCustomVis({ newKey, visName: 'AutoNarratives', pageKey, protoKey, layout });
        const cfg = { instruction, hasFormatInstruction: false,
          recommendations: sources.map((k) => ({ vizId: 'nk-re-' + k, skipCalculation: true, removeDataLimit: true, algorithms: {} })) };
        await s.edit([{ act: 'setProperty', nodeKey: newKey, prs: 'Visualization', pri: 17, v: JSON.stringify(cfg).replace(/"/g, '&quot;') },
          { act: 'setGridPropsRMs', nodeKey: newKey, rfMaps: sources.map((k) => ({ key: 'nk-re-' + k, value: k })) },
          { act: 'clearNLGSources', nodeKey: newKey, associatedNodes: [] }, { act: 'setNLGSources', nodeKey: newKey, associatedNodes: sources }], [newKey]);
      },

      // ---- Modern Grid with row sets ----
      // ONE visualization: gridKey is the grid AND row set 1's template; a stitched node (returned as S) holds all row sets.
      // Each row set has its own rows/title/totals and an IsNotNull(<first attribute> (ID)) view filter so other sections'
      // blank rows drop out (needed when sections share one table). Columns are shared: added to every row-set template.
      // For per-category subtotals put the item-level attribute in `totals` (category-level gives one grand total row).
      // rowSets: [{ title, attrs: [attrName...], totals: [attrName...] }]; columns: [[unitId, unitType], ...]
      // Put the returned S (not gridKey) in the page layout. idFormId: the ID form id (from any attribute's "ID" form).
      async buildModernGrid({ datasetId, idOf, gridKey, pageKey, protoKey, rowSets, columns, title, idFormId, columnTotalsOn }) {
        const S = newKey32();
        const off = { VisualizationsEnabled: 0, ViewMode: 0, SelectedVisualization: '', VisualizationList: '', IPhoneVisualization: '',
          IPadVisualization: '', APhoneVisualization: '', ATabletVisualization: '' };
        const G = gridKey;
        await s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey: G, toKey: pageKey },
          { act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { Visualization: off, FormattingWidget: { ClassName: '', Enable: 0, WidgetProps: '<props><widgetProps /></props>' } } },
          { act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: -1 } } },
          { act: 'updateTemplate', keyContext: G, actions: [{ act: 'formatGridZone', nodeKey: G, props: { FormattingAlignment: { TextWrap: 0 } }, units: [], axis: [{ axis: 1, regions: ['g'] }] }] },
          { act: 'setProperty', nodeKey: G, prs: 'Visualization', pri: 13, v: '{&quot;shwdgdz&quot;:true}' },
          { act: 'changeGridToStitched', nodeKey: G, newKey: S },
          { act: 'updateTemplate', keyContext: G, actions: [{ act: 'formatGridZone', nodeKey: G, props: { FormattingAlignment: { Vertical: 3 } }, units: [], axis: [{ axis: 1, regions: ['h'] }, { axis: 2, regions: ['h', 'g'] }] }] },
          { act: 'format', unitKey: S, unitType: 521, formatType: 1, format: { FormattingView: { SectionDisplayMode: 2 } } },
          { act: 'saveViewFilter', nodeKey: G, expr: '<exp><nd et="14" fn="19"></nd></exp>' },
          { act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: -1, MaxRows: 1000 } } },
        ], [G]);
        await s.edit([{ act: 'updateTemplate', keyContext: G, actions: [
          { act: 'addUnit', unitId: idOf(rowSets[0].attrs[0]), unitType: 12, unitPos: 1, dsId: datasetId, isFirst: true, axis: 1 }] }], [G]);
        // the editor's "first Add Row Set" settings (outline/indented mode + row-set display props). Without these the
        // row sets render as one wide grid with every row attribute as a column.
        await s.edit([
          { act: 'updateTemplate', keyContext: G, actions: [{ act: 'advancedProperties', props: { 'Template Formatting': { Indented: 1, MergeCells: -1 } } },
            { act: 'moveSubTotal', nodeKey: G, sorts: [], subTotalsPos: [2, 0, 0], stt: -1, axis: 1 }] },
          { act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: 0 } } },
          { act: 'setProperty', nodeKey: S, prs: 'Visualization', pri: 13, v: '{&quot;shwdgdz&quot;:true,&quot;shwdgrdz&quot;:false,&quot;colInfo&quot;:{},&quot;olmt&quot;:1}' },
          { act: 'updateElementsPropertiesMap', epm: [{ epmk: [{ ob: { did: '' } }], epmv: [{ k: { chn: [] } }] }], nodeKey: G, skipReverseUndo: true },
        ], [G]);
        const keys = [G];
        for (let i = 1; i < rowSets.length; i++) {
          const k = newKey32(); keys.push(k);
          await s.edit([{ act: 'copyUnit', unitKey: G, unitType: 521, newKey: k, toKey: S, stitchType: 2 },
            { act: 'format', unitKey: k, unitType: 521, formatType: 1, format: { FormattingView: { Title: rowSets[i].title },
              FormattingWidget: { WidgetProps: '', ClassName: '', Enable: 0 }, Visualization: { VisualizationsEnabled: 0, ViewMode: 0, SelectedVisualization: '' } } },
            { act: 'updateTemplate', keyContext: k, actions: [{ act: 'moveSubTotal', nodeKey: k, sorts: [], subTotalsPos: [2, 0, 0], stt: -1, axis: 1 }] }], [k]);
        }
        for (let i = 0; i < rowSets.length; i++) {
          const k = keys[i], rs = rowSets[i];
          for (let p = (i === 0 ? 1 : 0); p < rs.attrs.length; p++) {
            await s.edit([{ act: 'updateTemplate', keyContext: k, actions: [
              { act: 'addUnit', unitId: idOf(rs.attrs[p]), unitType: 12, unitPos: p + 1, dsId: datasetId, isFirst: p === 0, axis: 1 }] }], [k]);
          }
          for (const a of rs.totals || []) {
            await s.edit([{ act: 'updateTemplate', keyContext: k, actions: [{ act: 'showTotals', unitId: idOf(a), unitType: 12, subtotalType: [-10], clearSubtotalType: [] }] }], [k]);
          }
          await s.edit([{ act: 'format', unitKey: k, unitType: 521, formatType: 1, format: { FormattingView: { Title: rs.title } } }], [k]);
          await s.edit([{ act: 'saveViewFilter', nodeKey: k, expr: notNullExpr(idOf(rs.attrs[0]), rs.attrs[0], idFormId) }], [k]);
        }
        const gp = { act: 'setProperty', nodeKey: S, prs: 'Visualization', pri: 13, v: '{&quot;colInfo&quot;:{},&quot;olmt&quot;:1,&quot;shwdgdz&quot;:true,&quot;shwdgrdz&quot;:false}' };
        let pos = 1;
        for (const [uid, t] of columns) {
          for (const k of keys) {
            await s.edit([{ act: 'updateTemplate', keyContext: k, actions: [{ act: 'addUnit', unitId: uid, unitType: t, unitPos: pos, dsId: datasetId, isFirst: pos === 1, axis: 2 }] },
              gp, { act: 'setGridPropsRMs', nodeKey: S, rfMaps: [] }], [S]);
          }
          pos++;
        }
        if (columnTotalsOn) { // e.g. a "Year Total" column across Quarter
          for (const k of keys) await s.edit([{ act: 'updateTemplate', keyContext: k, actions: [{ act: 'showTotals', unitId: columnTotalsOn, unitType: 12, subtotalType: [-10], clearSubtotalType: [] }] }], [k]);
        }
        if (title) await s.edit([{ act: 'format', unitKey: S, unitType: 521, formatType: 1, format: { FormattingView: { Title: title } } }], [S]);
        return { gridKey: G, stitchedKey: S, rowSetKeys: keys };
      },
      // ---- Modern Grid with column sets (+ microchart columns) — captured from the editor 2026-11-10 ----
      // Column sets share the ROW attributes; each set has its own columns and metrics. Set 1 is gridKey itself; the editor's
      // "Add > Column Set" is copyUnit(gridKey -> container, no stitchType) + moveUnit. A microchart column is a column set
      // with [metric, attribute] switched to DossierRawValueVisualizationStyle with a chartCfg widget prop.
      // rows: [attrName...]
      // sets: [{ title, attrs: [attrName...], metrics: [metricName...] }            plain set; attrs pivot above the metrics
      //        { title, microchart: { type: 'sparkline'|'trendBar', metric, attr, format: {...} } }]
      // Returns { gridKey, stitchedKey, setKeys }. Put stitchedKey in the page layout.
      async buildColumnSetGrid({ datasetId, idOf, gridKey, pageKey = 'K53', protoKey = 'K51', rows, sets, title, mergeColumnHeaders = true }) {
        const S = newKey32();
        const G = gridKey;
        const off = { VisualizationsEnabled: 0, ViewMode: 0, SelectedVisualization: '', VisualizationList: '', IPhoneVisualization: '',
          IPadVisualization: '', APhoneVisualization: '', ATabletVisualization: '' };
        const hdrZones = [{ axis: 1, regions: ['h'] }, { axis: 2, regions: ['h', 'g'] }];
        await s.edit([
          { act: 'copyUnit', unitKey: protoKey, unitType: 521, newKey: G, toKey: pageKey },
          { act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { Visualization: off, FormattingWidget: { ClassName: '', Enable: 0, WidgetProps: '<props><widgetProps /></props>' } } },
          { act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: -1 } } },
          { act: 'updateTemplate', keyContext: G, actions: [{ act: 'formatGridZone', nodeKey: G, props: { FormattingAlignment: { TextWrap: 0 } }, units: [], axis: [{ axis: 1, regions: ['g'] }] }] },
          { act: 'setProperty', nodeKey: G, prs: 'Visualization', pri: 13, v: '{&quot;shwdgdz&quot;:true}' },
          { act: 'changeGridToStitched', nodeKey: G, newKey: S },
          { act: 'updateTemplate', keyContext: G, actions: [{ act: 'formatGridZone', nodeKey: G, props: { FormattingAlignment: { Vertical: 3 } }, units: [], axis: hdrZones }] },
          { act: 'format', unitKey: S, unitType: 521, formatType: 1, format: { FormattingView: { SectionDisplayMode: 2 } } },
          { act: 'saveViewFilter', nodeKey: G, expr: '<exp><nd et="14" fn="19"></nd></exp>' },
          { act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: -1, MaxRows: 1000 } } },
        ], [G]);
        const add = (k, actions) => s.edit([{ act: 'updateTemplate', keyContext: k, actions }], [S]);
        for (let i = 0; i < rows.length; i++) await add(G, [{ act: 'addUnit', unitId: idOf(rows[i]), unitType: 12, unitPos: i + 1, dsId: datasetId, isFirst: i === 0, axis: 1 }]);
        const keys = [];
        for (let i = 0; i < sets.length; i++) {
          const set = sets[i];
          let k = G;
          if (i > 0) {
            k = newKey32();
            await s.edit([
              { act: 'copyUnit', unitKey: G, unitType: 521, newKey: k, toKey: S },
              { act: 'format', unitKey: k, unitType: 521, formatType: 1, format: { FormattingView: { Title: set.title || 'Column Set ' + (i + 1) },
                FormattingWidget: { WidgetProps: '', ClassName: '', Enable: 0 }, Visualization: { VisualizationsEnabled: 0, ViewMode: 0, SelectedVisualization: '' } } },
              { act: 'updateTemplate', keyContext: k, actions: [{ act: 'formatGridZone', nodeKey: k, props: { FormattingAlignment: { Vertical: 3 } }, units: [], axis: hdrZones }] },
              { act: 'moveUnit', unitKey: k, unitType: 521, toKey: S, index: i }], [S]);
          }
          keys.push(k);
          if (set.microchart) {
            const mc = set.microchart;
            const name = set.title || `${mc.metric} ${mc.type === 'sparkline' ? 'Trend' : 'Comparison'} by ${mc.attr}`;
            await add(k, [{ act: 'addUnit', unitId: idOf(mc.metric), unitType: 4, unitPos: 1, dsId: datasetId, isFirst: false },
              { act: 'addUnit', unitId: idOf(mc.attr), unitType: 12, unitPos: 2, dsId: datasetId, isFirst: false, axis: 2 }]);
            const cfg = [{ type: mc.type, n: name, autoName: !set.title, mid: ['@pLd' + idOf(mc.metric)], aid: ['@pLd' + idOf(mc.attr)],
              format: { ...MICROCHART_DEFAULTS[mc.type], ...(mc.format || {}) } }];
            const dbl = JSON.stringify(cfg).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/&/g, '&amp;'); // double-escaped
            await s.edit([
              { act: 'format', unitKey: k, unitType: 521, formatType: 1, format: { FormattingView: { Title: name },
                FormattingWidget: { WidgetProps: `<props ><widgetProps ><fmt ><chartCfg value="${dbl}" ></chartCfg></fmt></widgetProps></props>`,
                  ClassName: 'DossierRawValueVisualizationStyle', Enable: 1 },
                Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: 'DossierRawValueVisualizationStyle' } } },
              { act: 'setWidgetString', nodeKey: k, skey: 'mcname', wdgs: name }], [S]);
          } else {
            let pos = 1;
            for (const a of set.attrs || []) await add(k, [{ act: 'addUnit', unitId: idOf(a), unitType: 12, unitPos: pos++, dsId: datasetId, isFirst: pos === 2, axis: 2 }]);
            for (const m of set.metrics || []) await add(k, [{ act: 'addUnit', unitId: idOf(m), unitType: 4, unitPos: pos++, dsId: datasetId, isFirst: pos === 2, axis: 2 }]);
            if (i > 0 && set.title) await s.edit([{ act: 'format', unitKey: k, unitType: 521, formatType: 1, format: { FormattingView: { Title: set.title } } }], [S]);
          }
        }
        await s.edit([{ act: 'setProperty', nodeKey: S, prs: 'Visualization', pri: 13, v: '{&quot;shwdgdz&quot;:false,&quot;shwdgrdz&quot;:true}' },
          { act: 'setGridPropsRMs', nodeKey: S, rfMaps: [] }], [S]);
        // Format > Layout > Column headers > Merge repetitive cells: one "Enterprise" header spanning its metrics. Sent to every set.
        if (mergeColumnHeaders) await s.edit(keys.map((k) => ({ act: 'updateTemplate', keyContext: k,
          actions: [{ act: 'advancedProperties', props: { 'Template Formatting': { MergeColumnCells: '-1' } } }] })), [S]);
        if (sets[0].title) await s.edit([{ act: 'format', unitKey: G, unitType: 521, formatType: 1, format: { FormattingView: { Title: sets[0].title } } }], [S]);
        if (title) await s.edit([{ act: 'format', unitKey: S, unitType: 521, formatType: 1, format: { FormattingView: { Title: title } } }], [S]);
        return { gridKey: G, stitchedKey: S, setKeys: keys };
      },
      // Full definition of the instance as the editor sees it (units, page layouts) — parsed server JSON.
      async serverJson() {
        return JSON.parse(await task({ taskId: 'getServerJSONResults', messageID: mid, styleName: 'ServerJsonRWDStyle',
          resFlags: '0', excludeData: 'true', compress: '1', innerHeight: '857', innerWidth: '1920' }));
      },
      // Auto Summary (the sparkle "Auto Summary" toolbar button; reference/auto-summary.md): an information window on the page
      // holding an AutoNarratives visualization that summarizes the page's visualizations in consumption. Captured from the
      // editor 2026-11-12. Turned on for every page by saveAs/save unless { autoSummary: false } is passed. Run it last:
      // it summarizes the visualizations on the page at that moment and adds the window to the page's current layout.
      async enableAutoSummary({ instruction = AUTO_SUMMARY_INSTRUCTION, keyStart = 0 } = {}) {
        const j = await s.serverJson();
        const all = Object.assign({}, ...j.defn.layouts.map((l) => l.units));
        // New keys must clear every key in the instance, not only unit keys: text, image and selector node keys (e.g. a
        // text box's W71 node) are not units, and reusing one makes the edit fail with a 500.
        let next = Math.max(keyStart - 1, ...(JSON.stringify(j).match(/\bW\d+\b/g) || []).map((k) => +k.slice(1))) + 1;
        const done = [];
        for (const [pageKey, page] of Object.entries(all)) {
          if (page.t !== 9 || (all[page.pnk] || {}).n !== 'VisualizationsPanelStack') continue;           // a page
          // A visualization targeted by an Attribute / Metric Selector sits under a group unit (t 11), not the page.
          const groups = Object.keys(all).filter((k) => all[k].t === 11 && all[k].pnk === pageKey);
          const kids = Object.entries(all).filter(([, u]) => u.pnk === pageKey || groups.includes(u.pnk));
          if (kids.some(([, u]) => u.t === 8 && /NLG one click/.test(u.ttl || ''))) continue;             // already on
          const sources = kids.filter(([, u]) => u.t === 521 || u.t === 522).map(([k]) => k); // 522: e.g. KPI cards in a draft
          if (!sources.length) continue;
          const [stack, panel, viz] = ['W' + next++, 'W' + next++, 'W' + next++];
          const layout = { ...(page.layoutXML || { t: 'b', o: 'h', children: sources.map((k) => ({ t: 'c', k, l: Math.floor(100 / sources.length), f: false })) }) };
          layout.ifwChildren = [...(layout.ifwChildren || []),
            { fixed: '0', k: stack, t: 'flc', hidden: 0, width: '50|174px', height: '50|322px', left: '25|87px', top: '25|161px' }];
          const cfg = { instruction, hasFormatInstruction: false, preDefinedNLGInInfoWindow: true,
            recommendations: sources.map((k) => ({ vizId: 'nk-re-' + k, skipCalculation: true, removeDataLimit: true, algorithms: {} })) };
          const W = (format) => ({ act: 'format', unitKey: stack, unitType: 8, formatType: 1, format });
          await s.edit([
            { act: 'addNewPanelStack', parentPanelKey: pageKey, nodeKey: stack, isSelectorPanel: false, isFormPanel: false, isInfoWindow: true },
            { act: 'format', unitKey: pageKey, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: layout } }, isJson: true },
            { act: 'addPanel', nodeKey: panel, titlePattern: 0, parentKey: stack, index: 0, isNavigationPanel: false },
            { act: 'copyUnit', unitKey: 'K51', unitType: 521, newKey: viz, toKey: panel },
            { act: 'format', unitKey: panel, unitType: 9, formatType: 1, format: { FormattingSize: { LayoutXML: { t: 'b', o: 'h', children: [{ t: 'c', f: false, l: 100, k: viz }],
              floatChildren: [], ifwChildren: [], canvasSize: { sizeType: 1, containerLocked: true, sizeSetting: null } } } }, isJson: true },
            { act: 'updateTemplate', keyContext: viz, actions: [{ act: 'createDefaultDropZones', nodeKey: viz, treeType: 1, datasetType: 3, widgetType: 7 }] },
            { act: 'format', unitKey: viz, unitType: 521, formatType: 1, format: {
              Visualization: { VisualizationsEnabled: -1, ViewMode: 51, SelectedVisualization: 'AutoNarratives', VisualizationList: 'AutoNarratives',
                IPhoneVisualization: '', IPadVisualization: '', APhoneVisualization: '', ATabletVisualization: '', ReturnBinaryResult: false },
              FormattingWidget: { ClassName: CUSTOM_VIS_CLASS, Enable: 1, WidgetProps: '<props><widgetProps><fmt><cvp><autoNarrativeAutoRefresh value="true" />'
                + '<isPredefinedNLG value="true"/><preDefinedNLGShowInConsumption value="true"/></cvp></fmt></widgetProps></props>' },
              FormattingView: { ShowTitleBar: 0, ShowWidgetTitleBar: 0 } } },
            { act: 'format', unitKey: viz, unitType: 521, formatType: 1, format: { FormattingIncrementalFetch: { EnableIFOnGrid: 0 } } },
            { act: 'changeGridDisplayMode', nodeKey: viz, displayMode: 1 },
            { act: 'setProperty', nodeKey: viz, prs: 'Visualization', pri: 17, v: JSON.stringify(cfg).replace(/"/g, '&quot;'), isInsertingPredefinedNLG: true },
            { act: 'setGridPropsRMs', nodeKey: viz, rfMaps: sources.map((k) => ({ key: 'nk-re-' + k, value: k })) },
            { act: 'setNLGSources', nodeKey: viz, associatedNodes: sources },
            { act: 'format', unitKey: viz, unitType: 522, formatType: 1, format: { FormattingOrder: { ZIndex: 2 }, FormattingView: { WindowState: 2 } } },
            W({ FormattingBorder: { TopStyle: 0, RightStyle: 0, BottomStyle: 0, LeftStyle: 0 } }),
            W({ FormattingView: { StyleForSwitchingPanel: 6 } }), W({ FormattingView: { TitleBarDisplay: 1 } }),
            W({ FormattingView: { UseAsInformationWindow: 1 } }), W({ FormattingView: { TabCloseToDismissInfoWindow: 0 } }),
            W({ FormattingSelector: { IndependentNodeSelector: 0 } }), W({ FormattingView: { Title: 'Information Window 999999 (NLG one click)' } })], [pageKey]);
          done.push({ pageKey, stack, viz, sources });
        }
        return done;
      },
      // overwrite: replace a dashboard of the same name in the folder (keeps its id); without it a name clash returns 409.
      async saveAs(name, folderId, { autoSummary = true, overwrite = false } = {}) {
        if (autoSummary) await s.enableAutoSummary();
        return api('POST', `/documents/${dashboardId}/instances/${mid}/saveAs`, { name, folderId, saveAsTemplate: false, ...(overwrite ? { overwrite: true } : {}) });
      },
      async save({ autoSummary = true } = {}) {
        if (autoSummary) await s.enableAutoSummary();
        return api('POST', `/documents/${dashboardId}/instances/${mid}/save`, {});
      },
    };
    return s;
  }

  return {
    api, task,
    async myFolder(name = 'My Reports') {
      return (await api('GET', '/folders/myPersonalObjects')).find((f) => f.name === name).id;
    },
    definition: (id) => api('GET', `/v2/dossiers/${id}/definition`),
    async newDashboard(datasets = []) { // datasets: [{id, name}]
      const r = await api('POST', '/dossiers/draft/instances',
        { filters: null, persistViewState: false, resolveOnly: false, applicationId: APP_ID, datasets });
      return session(BLANK_TEMPLATE, r.mid);
    },
    async open(dashboardId) {
      const r = await api('POST', `/dossiers/${dashboardId}/instances`,
        { persistViewState: false, resolveOnly: false, applicationId: APP_ID });
      return session(dashboardId, r.mid);
    },
  };
}

// Example matching "Claude Scratch Dashboard - Code Build 2": grid + bar + pie on top row, line chart below.
async function buildExample(dashboardId, projectId) {
  const c = client(window.__tok, projectId);
  const ds = (await c.definition(dashboardId)).datasets[0];
  const id = (n) => ds.availableObjects.find((o) => o.name === n).id;
  const s = await c.open(dashboardId); // a dashboard with an empty grid K52 on page K53
  await s.addToGrid('K52', ds.id, id('Region'), UNIT.attribute, 1);
  await s.addToGrid('K52', ds.id, id('Claim Count'), UNIT.metric, 2);
  const row = (keys) => ({ t: 'b', o: 'h', l: 50, children: keys.map((k) => ({ t: 'c', k, l: Math.floor(100 / keys.length) })) });
  await s.insertChart({ newKey: 'W62', vis: VIS.bar, layout: { t: 'b', o: 'v', children: [row(['K52', 'W62'])] } });
  await s.fillZones('W62', ds.id, [
    { zoneId: ZONE.xAxis, unitId: id('Claim Status'), unitType: UNIT.attribute },
    { zoneId: ZONE.yAxis, unitId: id('Claim Count'), unitType: UNIT.metric }]);
  await s.insertChart({ newKey: 'W63', vis: VIS.pie, layout: { t: 'b', o: 'v', children: [row(['K52', 'W62', 'W63'])] } });
  await s.fillZones('W63', ds.id, [
    { zoneId: ZONE.colorBy, unitId: id('Region'), unitType: UNIT.attribute },
    { zoneId: ZONE.sliceBy, unitId: id('Region'), unitType: UNIT.attribute },
    { zoneId: ZONE.angle, unitId: id('Claim Count'), unitType: UNIT.metric }]);
  await s.insertChart({ newKey: 'W64', vis: VIS.line,
    layout: { t: 'b', o: 'v', children: [row(['K52', 'W62', 'W63']), { t: 'c', k: 'W64', l: 50 }] } });
  await s.fillZones('W64', ds.id, [
    { zoneId: ZONE.xAxis, unitId: id('Claim Date (Month)'), unitType: UNIT.attribute },
    { zoneId: ZONE.yAxis, unitId: id('Claim Count'), unitType: UNIT.metric }]);
  return s.saveAs('Claude Scratch Dashboard - Built from code', await c.myFolder());
}
