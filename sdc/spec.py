"""The dashboard spec (JSON) and the checks that run before anything is built.

A spec describes the whole dashboard: one dataset, pages, and on each page a list of items drawn back to front. Claude
writes it from an image; `python3 -m sdc check spec.json` validates it and `python3 -m sdc build spec.json` builds it.
See examples/lincoln.json and the README for every field.

check_structure() needs no server. check_data() resolves every attribute and metric name against the dataset's own
lists, attributes and metrics looked up separately (a dataset can have both with the same name).
"""
from .constants import KPI_CHANGE, LEADER_LINE, LEGEND_SHAPES, LEGEND_SLOT, TREND_SHAPES, VIS, ZONE

VIZ_TYPES = {'kpi_card', 'iconic_kpi', 'chart', 'line', 'donut', 'narrative', 'grid'}   # grid = Grid (Modern), always
FIELD_TYPES = {'text', 'rich_text', 'image', 'shape'}
REUSABLE = {'kpi_card', 'iconic_kpi', 'chart', 'line'}   # can become a page's default visualization in place
METRIC_ONLY_ZONES = {'angle', 'sizeBy'}
ATTRIBUTE_DEFAULT_ZONES = {'sliceBy', 'colorBy', 'breakBy', 'rows'}
SHAPES = {'Line', 'Rectangle', 'Ellipse', 'Triangle', 'Polygon'}
ALIGNS = {'left', 'center', 'right'}
REF_TYPES = {'maximum', 'minimum', 'average', 'median', 'first', 'last', 'constant'}
REF_LABELS = {'type', 'metric', 'value'}


def check_title_format(w, tf):
    """title_format works on every visualization type except the Iconic KPI (iconic_kpi, which has no title bar)."""
    p = []
    if not isinstance(tf, dict):
        return [f'{w}: title_format must be an object']
    unknown = set(tf) - {'lines', 'subtitle', 'align', 'subtitle_align', 'wrap', 'subtitle_wrap', 'font', 'subtitle_font'}
    if unknown:
        p.append(f'{w}: unknown title_format field(s) {sorted(unknown)}')
    if tf.get('lines') not in (None, 1, 2):
        p.append(f'{w}: title_format.lines must be 1 or 2')
    if tf.get('lines') == 1 and tf.get('subtitle'):
        p.append(f'{w}: title_format has a subtitle but lines 1 (the second line would be hidden)')
    for k in ('align', 'subtitle_align'):
        if tf.get(k) is not None and tf[k] not in ALIGNS:
            p.append(f'{w}: title_format.{k} must be left, center or right')
    for k in ('wrap', 'subtitle_wrap'):
        if tf.get(k) is not None and not isinstance(tf[k], bool):
            p.append(f'{w}: title_format.{k} must be true or false')
    return p


def check_reference_lines(w, lines):
    p = []
    for i, rl in enumerate(lines or []):
        ww = f'{w} reference_lines[{i}]'
        if rl.get('type') not in REF_TYPES:
            p.append(f'{ww}: type must be one of {sorted(REF_TYPES)}')
        if rl.get('type') == 'constant' and not isinstance(rl.get('value'), (int, float)):
            p.append(f'{ww}: a constant line needs a numeric "value" (a metric or attribute is not allowed)')
        lab = rl.get('label', ['type', 'value'])
        if not isinstance(lab, int) and not set(lab) <= REF_LABELS:
            p.append(f'{ww}: label items must be from {sorted(REF_LABELS)}')
    return p


ICONIC_FIELDS = {'icon', 'tooltip', 'trend_shape', 'previous_value_label', 'reference_line', 'change', 'fill_opacity'}


def check_iconic_kpi(w, it):
    """Iconic KPI fields (reference/iconic-kpi-catalog.md)."""
    p = []
    if not it.get('metric'):
        p.append(f'{w}: "metric" is required')
    if it.get('trend') in TREND_SHAPES:
        p.append(f'{w}: "trend" is the trend attribute; the shape {it["trend"]!r} goes in "trend_shape"')
    if it.get('title_format') is not None:
        p.append(f'{w}: the Iconic KPI has no title bar, so title_format does not apply')
    icon = it.get('icon')
    if icon is not None and icon is not False and icon is not True and not (isinstance(icon, str) and icon.endswith('.svg')):
        p.append(f'{w}: icon must be false, true or a material-symbols file such as "delivery_truck_speed-fill.svg"')
    if it.get('tooltip') is not None and not isinstance(it['tooltip'], bool):
        p.append(f'{w}: tooltip must be true or false')
    if it.get('trend_shape') is not None and it['trend_shape'] not in TREND_SHAPES:
        p.append(f'{w}: trend_shape must be one of {", ".join(TREND_SHAPES)}')
    if it.get('previous_value_label') is not None and not isinstance(it['previous_value_label'], str):
        p.append(f'{w}: previous_value_label must be text')
    rl = it.get('reference_line')
    if rl is not None:
        if not isinstance(rl, dict) or not isinstance(rl.get('value'), (int, float)) or isinstance(rl.get('value'), bool):
            p.append(f'{w}: reference_line must be {{"value": <number>, "label", "color", "style"}}')
    ch = it.get('change')
    if ch is not None and ch is not False and ch not in KPI_CHANGE:
        p.append(f'{w}: change must be "percent", "amount" or false')
    fo = it.get('fill_opacity')
    if fo is not None and (not isinstance(fo, (int, float)) or isinstance(fo, bool) or not 0 <= fo <= 100):
        p.append(f'{w}: fill_opacity must be a number from 0 to 100')
    return p


def check_chart_look(w, it):
    """legend, data_labels, leader_lines, marker_size on chart items (reference/pie-catalog.md)."""
    p = []
    lg = it.get('legend')
    if lg is not None and lg is not False:
        if not isinstance(lg, dict):
            p.append(f'{w}: legend must be false or an object')
        else:
            unknown = set(lg) - {'position', 'align', 'title', 'shape'}
            if unknown:
                p.append(f'{w}: unknown legend field(s) {sorted(unknown)}')
            pos = lg.get('position')
            if pos is not None and pos not in LEGEND_SLOT:
                p.append(f'{w}: legend.position must be left, right, top or bottom')
            elif lg.get('align') is not None:
                ok = LEGEND_SLOT[pos or 'right']
                if lg['align'] not in ok:
                    p.append(f'{w}: legend.align for {pos or "right"} must be one of {", ".join(ok)}')
            if lg.get('title') is not None and not isinstance(lg['title'], bool):
                p.append(f'{w}: legend.title must be true or false')
            if lg.get('shape') is not None and lg['shape'] not in LEGEND_SHAPES:
                p.append(f'{w}: legend.shape must be one of {", ".join(LEGEND_SHAPES)}')
    dl = it.get('data_labels')
    if dl is not None and it.get('type') == 'chart' and dl != 'hide' and not (
            isinstance(dl, list) and set(dl) <= {'text', 'value', 'percent'}):
        p.append(f'{w}: data_labels must be "hide" or a list from text, value, percent')
    if it.get('leader_lines') is not None:
        if it.get('leader_lines') not in LEADER_LINE:
            p.append(f'{w}: leader_lines must be auto, show or hide')
        if it.get('type') != 'chart' or it.get('vis') not in ('pie', 'ring'):
            p.append(f'{w}: leader_lines only work on pie and ring charts')
    ms = it.get('marker_size')
    if ms is not None and (isinstance(ms, bool) or not isinstance(ms, (int, float)) or not 0 < ms <= 1):
        p.append(f'{w}: marker_size must be a number above 0 and up to 1 (the default is 0.6)')
    if it.get('type') not in ('chart', 'line'):
        for k in ('legend', 'leader_lines', 'marker_size'):
            if it.get(k) is not None:
                p.append(f'{w}: {k} only works on chart items')
    elif it.get('type') == 'line' and it.get('marker_size') is not None:
        p.append(f'{w}: marker_size only works on chart items')
    return p


class SpecError(ValueError):
    def __init__(self, problems):
        super().__init__('\n'.join(problems))
        self.problems = problems


def _as_list(v):
    return [] if v is None else v if isinstance(v, list) else [v]


def items(spec):
    for page in spec.get('pages', []):
        for it in page.get('items', []):
            yield page, it


def check_structure(spec):
    """Problems that need no server. Returns a list of strings (empty = fine)."""
    p = []
    if not spec.get('name'):
        p.append('spec: "name" is required')
    ds = spec.get('dataset')
    if not ds or not (isinstance(ds, str) or ds.get('id') or ds.get('name')):
        p.append('spec: "dataset" needs a name or {"id", "name"}')
    pages = spec.get('pages') or []
    if not pages:
        p.append('spec: at least one page is required')
    page_ids = [pg.get('id') for pg in pages]
    ids = {}
    for pg in pages:
        where = f'page {pg.get("id")!r}'
        if not pg.get('id'):
            p.append('page: "id" is required')
        if pg.get('layout', 'freeform') != 'freeform':
            p.append(f'{where}: only layout "freeform" is supported so far')
        its = pg.get('items') or []
        if not any(it.get('type') in REUSABLE for it in its):
            p.append(f'{where}: needs at least one kpi_card, iconic_kpi, chart or line item (the page\'s default visualization, a '
                     f'classic Grid, becomes the first one; grid items are always new Modern Grids)')
        for it in its:
            iid, typ = it.get('id'), it.get('type')
            w = f'{where} item {iid!r}'
            if not iid:
                p.append(f'{where}: every item needs an "id"')
            elif iid in ids:
                p.append(f'{w}: duplicate id')
            ids[iid] = it
            if typ not in VIZ_TYPES | FIELD_TYPES:
                p.append(f'{w}: unknown type {typ!r}')
                continue
            box = it.get('box')
            if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)):
                p.append(f'{w}: "box" must be [x, y, w, h] in percent of the page')
            else:
                x, y, bw, bh = box
                if min(x, y) < 0 or bw <= 0 or bh <= 0 or x + bw > 100.5 or y + bh > 100.5:
                    p.append(f'{w}: box {box} falls outside the page')
            if typ == 'chart':
                if it.get('vis') not in VIS:
                    p.append(f'{w}: vis must be one of {sorted(VIS)}')
                for z in (it.get('zones') or {}):
                    if z not in ZONE:
                        p.append(f'{w}: unknown zone {z!r} (zones: {sorted(ZONE)})')
                if not it.get('zones'):
                    p.append(f'{w}: "zones" is required')
            if typ == 'iconic_kpi':
                p += check_iconic_kpi(w, it)
            elif typ in VIZ_TYPES and it.get('title_format') is not None:
                p += check_title_format(w, it['title_format'])
            p += check_chart_look(w, it)
            if it.get('reference_lines'):
                if typ not in ('chart', 'line'):
                    p.append(f'{w}: reference_lines only work on chart and line items')
                p += check_reference_lines(w, it['reference_lines'])
            if typ == 'grid':
                if not (it.get('rows') or it.get('metrics')):
                    p.append(f'{w}: a grid needs "rows" and/or "metrics"')
                if it.get('kind', 'modern') != 'modern':
                    p.append(f'{w}: only the Grid (Modern) is built; classic and compound grids are not used')
            if typ == 'kpi_card' and not it.get('metric'):
                p.append(f'{w}: "metric" is required')
            if typ == 'line' and not (it.get('x') and (it.get('metrics') or it.get('metric'))):
                p.append(f'{w}: "x" and "metrics" are required')
            if typ == 'donut' and not (it.get('metric') and it.get('slice')):
                p.append(f'{w}: "metric" and "slice" are required')
            if typ == 'narrative':
                ins = it.get('instruction') or ''
                if not ins:
                    p.append(f'{w}: "instruction" is required')
                if '"' in ins:
                    p.append(f'{w}: instruction must not contain double quotes (the edit fails with a 500)')
                if not it.get('sources'):
                    p.append(f'{w}: "sources" (item ids) is required')
            if typ == 'text' and 'text' not in it:
                p.append(f'{w}: "text" is required')
            if typ == 'rich_text':
                if not it.get('runs'):
                    p.append(f'{w}: "runs" is required')
                if it.get('link'):
                    p.append(f'{w}: links only work on plain text; use type "text" with "font" instead of rich_text')
            if typ == 'image' and not it.get('url'):
                p.append(f'{w}: "url" is required')
            if typ == 'shape' and it.get('shape', 'Rectangle') not in SHAPES:
                p.append(f'{w}: shape must be one of {sorted(SHAPES)}')
            link = it.get('link')
            if link and typ == 'text':
                if not (link.get('url') or link.get('page') or link.get('dashboard')):
                    p.append(f'{w}: link needs "page", "url" or "dashboard"')
                if link.get('page') and not link.get('dashboard') and link['page'] not in page_ids:
                    p.append(f'{w}: link page {link["page"]!r} is not a page id in this spec')
    for _pg, it in items(spec):
        if it.get('type') == 'narrative':
            for src in it.get('sources') or []:
                if src not in ids:
                    p.append(f'item {it.get("id")!r}: source {src!r} is not an item id')
                elif ids[src].get('type') not in VIZ_TYPES - {'narrative'}:
                    p.append(f'item {it.get("id")!r}: source {src!r} is a {ids[src].get("type")}, not a visualization')
    return p


class Names:
    """Attribute and metric ids by name, kept apart. resolve() takes 'metric:Name' / 'attribute:Name' to force a kind."""

    def __init__(self, available):
        self.attributes = {o['name']: o for o in available.get('attributes', [])}
        self.metrics = {o['name']: o for o in available.get('metrics', [])}

    def resolve(self, name, kind=None):
        """Returns (id, unitType 12|4). kind: 'attribute', 'metric' or None (whichever exists; error if both)."""
        if ':' in name and name.split(':', 1)[0] in ('metric', 'attribute'):
            kind, name = name.split(':', 1)
        in_a, in_m = name in self.attributes, name in self.metrics
        if kind == 'metric' or (kind is None and in_m and not in_a):
            if not in_m:
                raise KeyError(f'no metric named {name!r}{self._near(name, self.metrics)}')
            return self.metrics[name]['id'], 4
        if kind == 'attribute' or (kind is None and in_a and not in_m):
            if not in_a:
                raise KeyError(f'no attribute named {name!r}{self._near(name, self.attributes)}')
            return self.attributes[name]['id'], 12
        if in_a and in_m:
            raise KeyError(f'{name!r} is both an attribute and a metric: write "attribute:{name}" or "metric:{name}"')
        raise KeyError(f'no attribute or metric named {name!r}{self._near(name, {**self.attributes, **self.metrics})}')

    def metric(self, name):
        return self.resolve(name, 'metric')[0]

    def attribute(self, name):
        return self.resolve(name, 'attribute')[0]

    @staticmethod
    def _near(name, pool):
        import difflib
        close = difflib.get_close_matches(name, list(pool), n=3, cutoff=0.6)
        return f' (did you mean {", ".join(repr(c) for c in close)}?)' if close else ''


def zone_kind(zone):
    if zone in METRIC_ONLY_ZONES:
        return 'metric'
    if zone in ATTRIBUTE_DEFAULT_ZONES:
        return 'attribute'
    return None


def check_data(spec, names):
    """Resolve every name in the spec. Returns a list of problems."""
    p = []

    def need(where, name, kind=None):
        try:
            names.resolve(name, kind)
        except KeyError as e:
            p.append(f'{where}: {e.args[0]}')

    for _pg, it in items(spec):
        w, typ = f'item {it.get("id")!r}', it.get('type')
        if typ in ('kpi_card', 'iconic_kpi'):
            need(w, it['metric'], 'metric')
            for k in ('trend', 'break_by'):
                if it.get(k):
                    need(w, it[k], 'attribute')
        elif typ == 'chart':
            for z, vals in (it.get('zones') or {}).items():
                for v in _as_list(vals):
                    need(f'{w} zone {z}', v, zone_kind(z))
            if it.get('sort'):
                need(f'{w} sort', it['sort']['metric'], 'metric')
            for m in (it.get('metric_colors') or {}):
                need(f'{w} metric_colors', m, 'metric')
        if typ == 'grid':
            for k, kind in (('rows', 'attribute'), ('columns', 'attribute'), ('metrics', 'metric')):
                for v in _as_list(it.get(k)):
                    need(f'{w} {k}', v, kind)
        if typ in ('chart', 'line'):
            for rl in it.get('reference_lines') or []:
                if rl.get('metric'):
                    need(f'{w} reference_lines', rl['metric'], 'metric')
        if typ == 'line':
            for v in _as_list(it.get('x')):
                need(w, v, 'attribute')
            for v in _as_list(it.get('metrics') or it.get('metric')):
                need(w, v, 'metric')
            if it.get('break_by'):
                need(w, it['break_by'], 'attribute')
            for m in (it.get('metric_colors') or {}):
                need(f'{w} metric_colors', m, 'metric')
        elif typ == 'donut':
            need(w, it['metric'], 'metric')
            need(w, it['slice'], 'attribute')
            for k, kind in (('color_by', 'attribute'), ('target', 'metric'), ('break_by', 'attribute')):
                if it.get(k):
                    need(w, it[k], kind)
    for nf in number_formats(spec):
        for m in nf['metrics']:
            need('number_formats', m, 'metric')
    return p


def number_formats(spec):
    """Normalizes "number_formats": either {"<metric>": "<format>"} or [{"metrics": [...], "format": "..."}]."""
    nf = spec.get('number_formats') or []
    if isinstance(nf, dict):
        groups = {}
        for m, f in nf.items():
            groups.setdefault(f, []).append(m)
        return [{'metrics': ms, 'format': f} for f, ms in groups.items()]
    return nf
