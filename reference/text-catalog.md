# Text and Rich Text

The toolbar's **T** button offers two kinds of text box:
- **Text:** one format for the whole box. Bold, size, color and so on apply to every word.
- **Rich Text:** each word or run of words has its own format, e.g. one phrase bold and red, another italic and underlined.

Studied 2026-11-12 in **zz text study** (`D934FB66A6404A4032CCD8A45A064739`, My Reports, a copy of zz freeform study). I
inserted both kinds, typed into a Rich Text box and formatted single words while recording the requests. Then I read the
editor's own Quill text editor to find which formats it keeps.

## How they are stored

Both are **text fields**: `addField` with `fieldType 3`, and the unit is type **106**. The insert sends:

```js
{ act: 'addField', createNode, nodeKeyParent: 'K53', fieldKey: 'W77', fieldType: 3, nodeKey: 'W69', treeType: 1, fieldName: 'Rich Text 1' }
{ act: 'editField', fieldValue: '', ... }
{ act: 'format', unitKey: 'W77', unitType: 106, keyContext: '106␞W69␞W77',
  format: { FormattingSize: { TextOverflow: 1 }, FormattingAppearance: { TextFieldType: 1 } } }   // Rich Text only
{ act: 'format', ..., format: { FormattingSize: { HeightMode: 0 } } }
```

- **The only structural difference** is `FormattingAppearance.TextFieldType: 1` on Rich Text. Text omits it.
- **Text:** the value is the plain string. Its formatting is the field's `FormattingFont` (Bold, Italic, Size, Color …),
  which covers the whole box. The existing `addText` already does this.
- **Rich Text:** the value is a [Quill](https://quilljs.com) document. Typing and formatting words sends one `editField`
  when you leave the box:

  ```
  Bookings are ⑆up 12%⑆ ⑆this week⑆\n⑆⑀JTVCJTdCJTIyaW5zZXJ0...
  ```

  - The front part is each run's text joined by `⑆` (U+2446), then `⑆⑀` (U+2446 U+2440).
  - The rest is `base64(encodeURIComponent(JSON))` of the Quill Delta:

  ```json
  [{ "insert": "Bookings are ", "attributes": { "color": "#35383a", "size": "size10", "font": "opensans" } },
   { "insert": "up 12%",        "attributes": { "color": "#35383a", "size": "size10", "font": "opensans", "bold": true } },
   { "insert": " ",             "attributes": { … } },
   { "insert": "this week",     "attributes": { … , "underline": true } },
   { "insert": "\n" }]
  ```

  - Every run carries color, size and font. The defaults are `#35383a`, `size10` (10 pt) and `opensans`.
  - A paragraph ends with a `"\n"` insert, which holds that paragraph's formats.

**Formats the viewer keeps.** The viewer's Quill instance allows only these formats; anything else is dropped when the
dashboard loads:

| per run | per paragraph (on the `"\n"`) |
|---|---|
| `bold`, `italic`, `underline`, `strike` (true) | `align`: `center`, `right`, `justify` (left = none) |
| `color`: `#hex` | `header`: 1–6 (the panel's Paragraph drop-down) |
| `size`: `size1` … `size1000` (pt) | `list`: `bullet`, `ordered` |
| `font`: `opensans`, `inter`, `roboto`, `arial`, `tahoma`, `timesnewroman` … (lowercase, no spaces) | `indent`: 1–8 |

Highlight (`background`), links and sub/superscript are registered in Quill but not allowed. A highlight sent from code
was removed when the dashboard loaded.

The Format panel matches this:
- **Rich Text:** Paragraph, font, B / I / U / S, size, color, alignment, then wrap, overflow and padding.
- **Text:** the same font controls, which apply to the whole box, plus Autosize and text Direction.

## From code: `addRichText`

```js
await s.addRichText({ pageKey: 'K53', fieldKey: 'W72', nodeKey: 'W71', runs: [
  { text: 'Parking update: ', bold: true, size: 16, color: '#1b354a' },
  { text: 'Conference Center Garage', bold: true, size: 16, color: '#d70e12' },
  { text: ' is ', size: 16 },
  { text: 'nearly full', italic: true, underline: true, size: 16 },
  { text: '\n' },                                   // new paragraph (may carry align / header / list / indent)
  { text: 'Old guidance: ', size: 11, color: '#6b6f73' },
  { text: 'park anywhere', size: 11, color: '#6b6f73', strike: true },
], align: 'left' });                                // the last paragraph's formats come from the options
```

- `richTextValue(runs, opts)` builds the value. For the editor's own example it gives exactly the editor's string: the
  same text part, and the same Delta once attribute order is ignored.
- `createNode: false` puts the field in an existing field-group node, the way the editor does. Each `addText` creates its own.
- `layout` is optional, as with `insertShape`.

## Verified (2026-11-12)

[build-text.js](../build-text.js) built **Text and Rich Text (built from code)** (`632FA4C4F94EADCF72A6B792B6CD4182`,
My Reports): a bold 14 pt plain Text box, a two-paragraph Rich Text box, and a grid. Saved through `saveAs`, so Auto Summary
is on (the sparkle button is in the viewer toolbar).
- **In Library:**
  - The plain Text box is bold throughout.
  - In the Rich Text box, "Parking update:" is bold navy and "Conference Center Garage" is bold red.
  - "nearly full" is italic and underlined.
  - The second paragraph is 11 pt gray with "park anywhere" struck through.
- **In the editor:** the box opens with the same formatting.
- **Paragraph formats:** header, bullet and numbered lists, indent and center alignment rendered in the viewer's Quill.
  A highlight and a link sent the same way were stripped. The build itself doesn't use the paragraph formats.

Gotchas:
- Clicking the font color swatch in the browser pane didn't open the picker. The color format was read from the Quill
  output instead: it is an inline `color` attribute.
- `addText` names the field after its key (`W70`), so Layers lists it that way. `addRichText` takes a `name`
  (default "Rich Text").
