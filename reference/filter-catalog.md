# Filter panel catalog

Source: **Retail Merchandising** (Shared Studio, `8CE7405AF94E129887D2098C896A4E45`), chapter **Merchandising Reports**, studied
2026-11-12 from the REST definition and the instance JSON of a separate read-only instance (`getServerJSONResults`). Nothing was
saved. Dataset: *Retail Weekly Sales and Inventory Model* (`CEEB9D41D253404AA05EF70F64C4B97C`).

## What the panel shows

| # in panel | Filter | Looks like | Selection | Applies to |
|---|---|---|---|---|
| 1 | Week Start Date | drop-down, multi-select | 3 of 6 weeks: 7/18, 7/25, 8/1/2026 | every page of the chapter (K33) |
| 2 | Vendor | checkbox list (9 items) | (All) | every page |
| 3 | Season | drop-down | (All) | every page |
| 4 | Department | drop-down | (All) | every page **and the Category filter** |
| 5 | Category | drop-down | (All) | every page |
| 6 | Style Description | checkbox list (100 items) | (All) | every page |

The count after each name ("Vendor (9)", "Week Start Date (3 of 6)") is the element count the panel draws itself: the total, or
"selected of total" once a selection is made.

## How each filter is stored

Every filter is a selector unit (`t: 111`) inside the chapter's FiltersPanel (`K49`), with a node/control key pair
(`W126`/`W127`, `W128`/`W129`, ...). Its key context is `'1\u001e<node>\u001e<control>'`.

| Filter | control | `style` | `multi` | `ckgi`/`ckgo` | `tks` (targets) | notes |
|---|---|---|---|---|---|---|
| Week Start Date | W127 | 0 | true | 0/0 | K33 | attribute "Week Start Date" (the unit `n` says "Week"); forms Calendar Date + Key (integer yyyymmdd); display form `BAAF93F5…`; elements by ID `h20260718;<attr>` |
| Department | W129 | 0 | true | 3/0 | K33, **W131** | targets the Category selector too (cascading) |
| Category | W131 | 0 | true | 3/1 | K33 | grouped with Department |
| Vendor | W133 | 4 | true | 1/0 | K33 | `sos: true`, `dsid` + `sfs` (element source = the dataset) |
| Style Description | W135 | 4 | true | 4/0 | K33 | same as Vendor |
| Season | W140 | 0 | true | 2/0 | K33 | |

Common to all: `ct "1"` (element selector), `include: true`, `showall: true` (an "(All)" item), `httl: true` (title shown),
`dfm: 1`, `sces: 2`, `btot: true`. Default size in the panel: 208 px wide, 80 px tall for a drop-down, 235 px for the checkbox
list; title 12pt Open Sans with a 1pt #cecece top border; panel background #ebebeb.

### Selector `style`

| style | renders as | evidence |
|---|---|---|
| 0 | drop-down | Week Start Date, Season, Department, Category in this panel |
| 3 | radio buttons | `addCanvasSelector` (verified earlier, P&L build) |
| 4 | checkbox list | Vendor, Style Description in this panel |
| 1 | slider (range between the data's min and max) | Display Style > Slider on a date filter (sends `Multiselect 1, Orientation 1`, height 1.0417 in) |
| 9 | search box (selected items shown as chips) | `addChapterFilter` default; Display Style > Search Box (sends `Multiselect 1, Orientation 0`, height 1.4583 in) |
| 11 | calendar: date qualification ("After 1/1/2025") | `addDateFilter` (verified 2026-11-11); the Self Service chapter's Week Start Date (W155) |

### Order in the panel

The panel is drawn by `ckgi` (group index), then `ckgo` (position within the group), not by the definition order (`chdidx`).
That is why the panel reads Week, Vendor, Season, Department, Category, Style Description while the definition lists Week,
Department, Category, Vendor, Style, Season. Department and Category share group 3: a parent filter and the filter it narrows.

### Cascading (Department narrows Category)

Department's targets are `K33` (the pages) **and** `W131` (the Category selector), so choosing a department limits the Category
list to that department's categories. The editor adds a target with `addControlTarget` (`tgtKey`), as `addCanvasSelector`
already does for visualization targets.

### Selection state

From the instance's selector data (`{"k":"W127","wid":1,"elms":[...],"ces":[...]}`):
- `elms`: the items, first `{v:"u;", n:"(All)", t:14}`, then `{v:"h<id>;<attrId>", n:"<display>"}`.
- `ces`: the current selection. Week Start Date: `h20260718`, `h20260725`, `h20260801` (ID form, yyyymmdd). The other filters:
  `[{v:"u;", n:"(ALL)"}]` with `unset: true`.
- To set a selection from code: `setSelectorElements` with `elemList` items `'h<id>;<attrId>'` joined by `\u001e`.
  For Week Start Date the id is the yyyymmdd Key form, not the displayed date.

## Second chapter (Self Service): other selector kinds

| Filter | control | kind | notes |
|---|---|---|---|
| Select your Attributes | W95 | object parameter selector (`ct "8"`, `isps: true`, `paraid`) | swaps attributes in the DIY grid |
| Select your Metrics | W97 | object parameter selector (`ct "8"`) | swaps metrics |
| Week Start Date | W155 | date qualification (`style 11`) | targets the page `K85` only |

`ct "8"` selectors are object/parameter pickers, not element filters; the client does not build them yet.

## Building it from code (verified 2026-11-12)

[build-filter-panel.js](../build-filter-panel.js) rebuilt the panel on the same dataset in 4.1 s ("Filter Panel (built from code) v4",
My Reports). Read back, every stored value matches the source: styles 0/4/0/0/0/4, `ckgi`/`ckgo` 0, 1, 2, 3/0, 3/1, 4 (the server
groups Department and Category by itself once the cascade is added), Department `tks` = K33 + Category, Week Start Date selection
20260718 / 20260725 / 20260801. In the editor the panel reads Week Start Date (3 of 6), Vendor (9), Season (2), Department (5),
Category (17), Style Description (100), as in the source.

`s.addChapterFilter(attrId, title, selected, nodeKey, ctlKey, { style, order, cascadeTo })`:

| Want | How | Gotcha found while building |
|---|---|---|
| filter style | `style` 0 drop-down / 4 checkbox / 9 search box / 3 radio / 1 slider / 11 calendar, sent as `FormattingSelector.Style` | |
| panel order | `order` = 0, 1, 2 … (`FormattingOrder.ZIndex`) | the editor sorts the panel by this z-index; leaving all at 0 lists the filters newest first |
| initial selection | `selected` ids → `setSelectorElements elemList 'h<id>;<attrId>'` joined by `\u001e` | commas (what the old helper sent) turn several items into one; Week Start Date uses its integer Key form (yyyymmdd) |
| cascade | `addControlTarget { keyContext: parent ctx, tgtKey: <child NODE key>, isUC: true, excludeCtp: false }` | targeting the child's control key saves a dashboard that will not open ("Item '%1' cannot be found"); the server stores the control key in `tks` |
| date condition | `addDateFilter` (style 11 + `setSelectorExpression`) | |

Not built yet: the Self Service chapter's object parameter selectors (`ct "8"`), and the checkbox list's taller default size
(235 px in the source).

## Date attribute in the filter panel (calendar filter)

Studied 2026-11-12 in **Base Grid** (`384671ECCD4A4968BB0D6FAB04CDD76A`, dataset *Company Campus Session & Parking Reservations*,
`6AD04CFB…`). Read from the open editor's model; nothing was saved there. Every option below was then applied in a scratch copy,
**zz date filter study** (`5AAB9C642F412A67F3D62984F692206D`, My Reports), and the request each one sent was recorded.

### How it is stored

A date attribute (`Calendar Date`, `469FC6F6…`, one form `ID` of data type date, `45C11FA478E745FEA08D781CEA190FE5`) dropped
on the filter panel becomes a selector unit with **`style: 11`** (Calendar), `ct "1"`, `multi: true`, `srct 12`, `srcst 3072`,
`sfs [{did: <date form>}]`. With nothing applied it shows **1/1/1900 – 12/31/2035**. Those are not the data's range: the selector
data carries `min: 2, max: 49674`, day serials from 12/30/1899 (2 = 1/1/1900, 49674 = 12/31/2035), with `dt 14` (date) and
`qt 0`. Once applied, the data adds `ft 1`, `f <function>` and `cs` (the constants).

Every Calendar choice is one `setSelectorExpression` (what `addDateFilter` sends) with `dataType 14`, `fid <date form>` and
`expFunctionType 1`. Only `expFunction` and `expConstants` change. Clearing it is `unsetSelector { keyContext, ctlKey, scs: 0 }`.

| UI | `expFunction` | `expConstants` |
|---|---|---|
| Custom > Between | 17 | `from␞to` (␞ = `\u001e`) |
| Custom > On | 17 | the same date twice: `3/15/2026␞3/15/2026` |
| Custom > Before | 9 | one date |
| Custom > After | 8 | one date |

A typed date is sent as plain `M/D/YYYY`. A dynamic date (the calendar icon with the arrow; the presets) is sent as an
`isDyn::…` string instead.

### Dynamic dates: `isDyn::` string

`isDyn::<type>::<days>::<months>::<month>::<day>::<week>::<weekday>::<resolved M/D/YYYY>::0::0::0`

The instance data names the same values: `dyt`, `ddo` (day offset), `dmo` (month offset), `dynamic_month`, `dynamic_day`,
`dynamic_week`, `dynamic_day_of_week`, then hour/minute/second. The resolved date is only for display; the server recomputes it.

| `type` | anchor | used with |
|---|---|---|
| 3 | today ± `days` | Today, Yesterday, Last/Next N days |
| 4 | week of (today ± `days`) | `weekday` 0 = Sunday … 6 = Saturday |
| 5 | month of (today ± `months`) | `day` 1 = first day, -1 = last day |
| 14 | quarter of (today ± `months`) | `day` 1 / -1; quarters are counted in months (7 quarters = -21) |
| 6 | year of (today ± `months`) | `month`/`day` 1/1 = January 1, 12/31 = December 31; years in months (-12 = last year) |

All of the presets are a Between (17) of two dynamic dates. Here is what each sent on 11/12/2026:

| Preset | from | to |
|---|---|---|
| Today | `isDyn::3::0::0::0::0::0::0` | same |
| Yesterday | `isDyn::3::-1::0::0::0::0::0` | same |
| Last 7 days | `isDyn::3::-7::0::0::0::0::0` (11/5) | `isDyn::3::-1::0::0::0::0::0` (11/11) |
| Last 7 weeks | `isDyn::4::-49::0::0::0::0::0` (Sunday, 9/20) | `isDyn::4::-7::0::0::0::0::6` (Saturday, 11/7) |
| Last 7 months | `isDyn::5::0::-7::0::1::0::0` (4/1) | `isDyn::5::0::-1::0::-1::0::0` (10/31) |
| Last 7 quarters | `isDyn::14::0::-21::0::1::0::0` (1/1/2025) | `isDyn::14::0::-3::0::-1::0::0` (9/30/2026) |
| Last 7 years | `isDyn::6::0::-84::1::1::0::0` (1/1/2019) | `isDyn::6::0::-12::12::31::0::0` (12/31/2025) |
| Next 7 months | `isDyn::5::0::1::0::1::0::0` (12/1/2026) | `isDyn::5::0::7::0::-1::0::0` (6/30/2027) |
| MTD | `isDyn::5::0::0::0::1::0::0` (11/1) | today (`isDyn::3::0…`) |
| QTD | `isDyn::14::0::0::0::1::0::0` (10/1) | today |
| YTD | `isDyn::6::0::0::1::1::0::0` (1/1/2026) | today |
| Before today (Custom, dynamic) | fn 9: `isDyn::3::0::0::0::0::0::0` | |

"Last N" always ends at the last *complete* period (yesterday, last Saturday, end of last month), and "Next N" starts at the next
one. The preset pill takes its label from what is applied ("Last 7 weeks"). The Health Claims build's
`isDyn::6::0::-12::1::1…` with fn 8 reads "After January 1 of last year".

### Display Style on a date attribute

The ⋮ menu offers Check Boxes, Slider, Search Box, Radio Buttons, Drop-down and Calendar. Each choice is one `format` action
(`FormattingSelector.Style`, plus a height in inches):

| Choice | sends |
|---|---|
| Calendar | `Style 11`, height 0.5625 |
| Slider | `Style 1, Multiselect 1, Orientation 1`, height 1.0417; draws a range over 1/1/1900 – 12/31/2035 |
| Search Box | `Style 9, Multiselect 1, Orientation 0`, height 1.4583; lists every date in the applied range as a chip |

Any style change away from Calendar first warns "This attribute has 5845 distinct values…", which is why the Calendar is the
default for a date. **The date condition survives style changes:** after Calendar → Slider → Search Box → Calendar, the dynamic
"Next 7 months" range was still applied. After the change the unit also gets `isNewDynamicFilter: true`, `sos: true` and `dsid`
(element source = the dataset). Slider and Search Box add element-list items to the menu (Sort, Show Option for All, Dynamic
Selection, Selection Required, Allow Multiple Selections, and for the search box, Allow Instant Search and Pre-load Elements).

### From code

`datePreset(spec)` in the client turns a preset name into `{ fn, value }`, and `addDateFilter` takes it as `preset`. `dynDate({...})`
builds a single dynamic date.

```js
await s.addDateFilter({ attrId: CAL_DATE, formId: '45C11FA478E745FEA08D781CEA190FE5', name: 'Calendar Date', preset: 'last 7 days' });
// presets: 'today', 'yesterday', 'mtd', 'qtd', 'ytd', 'last|next <n> days|weeks|months|quarters|years'
await s.addDateFilter({ ..., fn: 8, value: dynDate({ type: 'year', months: -12, month: 1, day: 1 }) }); // after Jan 1 of last year
await s.addDateFilter({ ..., fn: 17, value: '1/1/2026\u001e6/30/2026' });                               // fixed range
```

Tested 2026-11-12:
- With "today" set to 11/12/2026, `datePreset` reproduces all 11 strings recorded from the editor, character for character,
  including the resolved dates.
- "Next N days" and "Next N weeks" are not recorded from the editor; they follow the same pattern as the recorded presets.
- On an unsaved draft, the server accepted "next 3 days" (+1 to +3), "next 2 weeks" (Sunday 11/15 to Saturday 11/28) and
  "next 1 years" (1/1/2027 to 12/31/2027) and resolved them as intended.

Verified from code on an unsaved draft: the "Last 7 days" call above came back as `f 17`, `dyt 3`, `ddo -7 / -1`, `isDyn: true`. The
server recomputes the resolved dates (11/6 – 11/12 there, versus 11/5 – 11/11 in the editor a few minutes earlier): the
server's "today" can be a day ahead of the browser's, so the resolved date in the string does not matter.

## Metric in the filter panel

Studied 2026-11-12: a metric (*Active Booking Count*, `B8225521…`) dropped on the filter panel. Every option was recorded in a
scratch copy, **zz metric filter study** (`579BEB09D64A959D04E8C7B02D069151`, My Reports). Its grid is Parking Lot ×
Active Booking Count: 570, 44, 63, 68.

### How it is stored

It is a selector unit like the attribute filters (`t 111`, `ct "1"`), but its source is the metric: `srct 4`, `srcst 1033`, plus the
metric's number format (`numFmts`). The editor's default **`style` is 7 (Slider)**, with `horiz: true`. The selector data gives the
slider's range, computed at the level of the visualizations the filter targets: `min 44, max 570, cnt 4, dt 6` (one value per
parking lot). With nothing applied the slider reads "All".

**The filter needs a visualization that runs.** In *zz date filter study* the grid hit the cartesian-join error, and the same metric
filter got `min ""`, `max ""` and `nov: true` (no values), so it could not be used.

### Menu

Apply Selections To, Disable Interactions in Library, Include / Exclude, Unset Filter, **Qualify on Value / Qualify on Rank**,
**Display Style (Slider / Qualification)**, Delete, Advanced Options (Selector Name and Key only). Qualification hides
Include/Exclude, because its operator list already has the negative forms.

| Display Style | sends |
|---|---|
| Slider | `Style 7` |
| Qualification | `Style 8`, height 0.8958 in: an operator (or rank) drop-down and a value box (two boxes for Between) |

### Conditions: one `setSelectorExpression`

The action carries `objType 4` and `dataType 5`. `expConstants` holds the values joined by `\u001e`. In the UI you type an In
list with `;` (a comma is rejected as "Invalid characters").

**Qualify on Value** (`qt 0`, `expFunctionType 1`):

| operator | `expFunction` | how the slider sends it |
|---|---|---|
| Equals | 6 | |
| Does not equal | 7 | |
| Greater than | 8 | |
| Less than | 9 | |
| Greater than or equal to | 10 | dragging only the low handle (`88.83`, unrounded) |
| Less than or equal to | 11 | |
| Between | 17 | dragging both handles (`88.83␞498.27`) |
| Not between | 44 | Exclude on the slider (`include: false`) |
| In | 22 | |
| Not In | 57 | |
| Is Null / Is Not Null | 54 / 55 | no constants |

**Qualify on Rank**: the slider becomes a rank, 1 … element count (or 0 – 100%), with a Highest / Lowest / Highest % /
Lowest % drop-down.

| choice | `qt` | `expFunctionType` | `expFunction` | constant |
|---|---|---|---|---|
| Highest | 1 | 2 | 1 | `2` = top 2 (the slider sends unrounded values such as `1.94`) |
| Lowest | 2 | 2 | 2 | `1` = bottom 1 |
| Highest % | 3 | 3 | 1 | `25%`, with the % sign |
| Lowest % | 4 | 3 | 2 | `48.3%` |

Switching between value and rank sends the new `qt`/`expFunctionType` with `unset: true, changeQual: true` (the value is
cleared). Include/Exclude carries over: Exclude + Highest sent `expFunction 4, include false`. The instance data afterwards
reports a rank as `f 11, ft 1` with the number (`0.25` for 25%), so read the stored condition back from the definition, not
from that data.

### From code: `addMetricFilter`

```js
await s.addMetricFilter({ metricId, name: 'Active Booking Count' });                                   // slider, nothing applied
await s.addMetricFilter({ metricId, name, style: 'qualification', condition: { op: '>', value: 60 } });
await s.addMetricFilter({ metricId, name, condition: { rank: 'highest', value: 2 } });                // top 2
await s.addMetricFilter({ metricId, name, condition: { rank: 'highest%', value: 25 } });              // top 25%
await s.addMetricFilter({ metricId, name, condition: { op: 'in', value: [63, 68] }, include: false }); // exclude
```

Tested 2026-11-12 on unsaved drafts (grid rows read back from the instance):

| condition | rows left |
|---|---|
| none | all 4 |
| > 60 | Conference Center Garage, West, Visitor |
| top 2 | Conference Center Garage, Visitor |
| bottom 1 | East |
| top 25% | Conference Center Garage |
| in 63;68 | West, Visitor |
| exclude between 50–100 | Conference Center Garage, East |
| exclude in 63;68 | Conference Center Garage, East |

Gotchas:
- **Exclude:** `include: false` alone does not invert the condition. The first test kept West and Visitor. The helper does what
  the editor does: it sends the opposite operator (17 → 44, 22 → 57, > → <=, and so on) together with `include: false`. For a
  rank, ask for the opposite rank instead.
- **Selector name:** `addControl` alone leaves the selector name (`n`) empty, which Advanced Options shows as a blank name. The
  helper sets it with `FormattingAppearance.Name`.
