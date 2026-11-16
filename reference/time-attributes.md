# Time attributes from a date

**Use:** a dashboard image can show a chart or selector on a time attribute, such as "Processed Year" or "Paid Month". If the
dataset has the date but not that time attribute, create it in the dataset first, then build the visualization on it.

**Rule:** create a time attribute only when the incoming image uses an object with a matching name, on an axis, legend, grid
column, filter or selector, and the dataset doesn't already have it. Create only that type, from only that date. The goal is
never to create every time attribute, or to create them for every date attribute. `createTimeAttributes` requires the list of
types and throws without one. The ten-type run below was a one-off study.

The editor does this from the dataset panel: right-click a date attribute > **Create Time Attributes** > tick types > OK. It
offers ten types. Each becomes a derived attribute in the dataset, built from the editor's built-in date functions. The
client sends the same actions with `createTimeAttributes`.

Studied 2026-11-15 on **Exec Claims Dashboard** (`2DA56C0DAA4AD14B8A31F1B535A57B53`), dataset *Health Claims Model*
(`B3A6DDF8648D4CEF987575C722609CB1`). The steps:
1. All ten types were captured from the editor on Processed Date.
2. `timeAttributeForms` rebuilt every formula byte for byte.
3. On a separate instance, all ten were created from **Board Certification Expiration Date**, renamed, and added to the Page 1
   grid. Saving that instance over the dashboard was blocked as an overwrite of the user's dashboard, so it was not saved.

## Naming

The editor names each one `<date> (<type>)`, for example "Processed Date (Year)". Our convention renames it: drop the word
"Date" from the source name, then add the type.

| Source | Type | Editor name | Our name |
|---|---|---|---|
| Processed Date | Year | Processed Date (Year) | Processed Year |
| Processed Date | Month of Year | Processed Date (Month of Year) | Processed Month of Year |
| Board Certification Expiration Date | Week | … (Week) | Board Certification Expiration Week |

`timeAttributeName(sourceName, type)` applies this rule. To match an image, look for its label: a chart axis that reads
"Processed Year" means the Year type of Processed Date.

## The ten types and how they display

Sample values for 1/20/2025 and 2/6/2025, read from the grid. The form shown in the grid is listed.

| Type | Shows (form) | 1/20/2025 | 2/6/2025 | Forms and formulas |
|---|---|---|---|---|
| Year | ID | 2025 | 2025 | ID `Year(d)` |
| Quarter of Year | DESC | Q1 | Q1 | ID `QuarterOfYear(d)`; DESC `Concat("Q", This@ID)` |
| Quarter | DESC | Q1, 2025 | Q1, 2025 | ID `Year(d)*10 + QuarterOfYear(d)`; DESC `Concat("Q", QuarterOfYear(d), ", ", Year(d))`; DATE quarter start |
| Month of Year | DESC | January | February | ID `MonthOfYear(d)`; DESC `FormatDate<Pattern="mmmm">(d)` |
| Month | DESC | Jan 2025 | Feb 2025 | ID `Year(d)*100 + MonthOfYear(d)`; DESC `FormatDate<Pattern="mmm yyyy">(d)`; DATE month start |
| Week of Year | ID | 4 | 6 | ID `WeekOfYear(d)` |
| Week | DESC | W4, 2025 | W6, 2025 | ID `Year(d)*100 + WeekOfYear(d)`; DESC `Concat("W", WeekOfYear(d), ", ", Year(d))`; DATE week start |
| Day of Year | ID | 20 | 37 | ID `DayOfYear(d)` |
| Day of Month | ID | 20 | 6 | ID `DayOfMonth(d)` |
| Day of Week | DESC | Mon | Thu | ID `DayOfWeek(d)` (sorts Sun..Sat); DESC `FormatDate<Pattern="ddd">(d)` |

The "of Year / of Month / of Week" types repeat every year (Q1, January, Mon). Quarter, Month and Week are tied to a year
(Q1, 2025) and carry a DATE form, so they sort and plot in time order. Pick the one whose labels match the image. "Jan 2025"
is Month; "January" is Month of Year.

## Actions

Create one, which the editor sends as one batch per OK:

```js
{ act: 'addDAToDataset', dsid, name: 'Processed Date (Year)', isTokenStream: true,
  forms: [{ n: 'ID', bft: 0, formula: '<tknstrm ><items>…</items></tknstrm>' }, …] }
```

- A formula is a token stream. Each function is a token `<tkn v="<fnId>"><oi did="<fnId>" t="11" st="2816" …/></tkn>`.
- The source date is the token `<tkn v="[<attr>]@[<form>]" tp="275" exv="<formId>" extp="8"><oi did="<attrId>" t="12" n="<attr>"/></tkn>`.
- Function ids are in `TIME_FN` in the client. `exv` is the source's date-typed form id. For a single-form date attribute
  that is `45C11FA478E745FEA08D781CEA190FE5`, the ID form category.
- If the date attribute has more than one form, such as a Key plus a date (Paid Date has "Paid Date Key" and "Paid Date"),
  pass the date-typed form as `formId` / `formName`. This is untested.

Rename (dataset panel > Rename):

```js
{ act: 'updateDA', dsid, attrId, name: 'Processed Year' }
```

## Client

```js
const src = cube.attributes.find((a) => a.name === 'Board Certification Expiration Date');
const dateForm = src.forms.find((f) => f.dataType === 'date');
// The image's chart is "by Board Certification Expiration Year" and the dataset has no such attribute: create Year only.
const made = await s.createTimeAttributes(datasetId, { id: src.id, name: src.name, formId: dateForm.id, formName: dateForm.name }, ['Year']);
// made.Year = { id, name: 'Board Certification Expiration Year' }
```

Gotchas:
- **Check the dataset first.** The editor's dialog doesn't mark types that already exist. Creating one again adds a
  duplicate, and the server appends " 1" to its name. Exec Claims Dashboard already had Processed Date (Year), Processed
  Month, Processed Quarter and Processed Week, and the line chart uses Processed Month.
- New derived attributes are dataset-level objects. They are saved with the dashboard, not with the cube.
