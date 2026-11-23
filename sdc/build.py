"""Build a dashboard from a spec (see sdc/spec.py and examples/lincoln.json).

Order: resolve the dataset and its names -> check the spec -> new draft -> pages -> items on each page (back to front)
-> narratives -> free-form layout -> number formats -> Save As (with Auto Summary) -> re-open and check every item.

Nothing is saved until the last step, so a failure part way leaves nothing behind in Library (the draft just expires).
"""
import time

from .constants import KPI_ZONE, METRIC_NAMES, VIS, ZONE, chart_look
from .spec import (REUSABLE, Names, SpecError, _as_list, check_data, check_structure, expand_kpi_notes, number_formats,
                   zone_kind)
from .transport import StrategyError
from .util import bgr

SIZE_MODE = {'fill': 3, 'fit': 2}
ALIGN = {'left': 1, 'center': 2, 'right': 3}


class BuildError(RuntimeError):
    def __init__(self, step, err):
        detail = f'{step}: {err}'
        if isinstance(err, StrategyError):
            if err.code:
                detail += f' (x-mstr-taskerrorcode {err.code})'
            if err.actions:
                detail += '\n  actions sent: ' + ', '.join(a.get('act', '?') for a in err.actions)
        super().__init__(detail)
        self.step, self.err = step, err


def font_format(font):
    """Spec font {name, size, bold, italic, underline, color} -> FormattingFont."""
    if not font:
        return {}
    f = {}
    if font.get('name'):
        f['Name'] = font['name']
    if font.get('size') is not None:
        f['Size'] = str(font['size'])
    for k, K in (('bold', 'Bold'), ('italic', 'Italic'), ('underline', 'Underline')):
        if font.get(k):
            f[K] = -1
    if font.get('color'):
        f['Color'] = bgr(font['color'])
    return f


def resolve_dataset(conn, ds):
    """ds: 'name' | {'name'} | {'id', 'name'} -> (id, name)."""
    if isinstance(ds, str):
        ds = {'name': ds}
    if ds.get('id'):
        return ds['id'], ds.get('name') or ds['id']
    hits = [h for h in conn.search(ds['name'], object_type=None) if h.get('name') == ds['name']
            and h.get('type') in (3, 77)]
    if not hits:
        raise SpecError([f'dataset {ds["name"]!r} not found (give its "id" in the spec)'])
    if len({h['id'] for h in hits}) > 1:
        raise SpecError([f'dataset {ds["name"]!r} matches {len(hits)} objects: give its "id" in the spec: '
                         + ', '.join(h['id'] for h in hits)])
    return hits[0]['id'], ds['name']


class Builder:
    def __init__(self, conn, spec, log=print):
        self.conn, self.spec, self.log = conn, expand_kpi_notes(spec), log   # notes become Rich Text items
        self.timings = []
        self.keys = {}        # item id -> {'key', 'node', 'page', 'type'}
        self.page_keys = {}   # page id -> Strategy page key

    # ---- small utilities ----
    def _phase(self, name):
        self.timings.append((name, time.time()))
        self.log(f'  {name}')

    def _alloc(self):
        self.next_key += 1
        return f'W{self.next_key}'

    @staticmethod
    def _flat(keys):
        return {'t': 'b', 'o': 'h', 'children': [{'t': 'c', 'k': k, 'l': 100 // len(keys), 'f': False} for k in keys]}

    def prepare(self):
        """Resolve the dataset and names and check the spec. Raises SpecError with every problem found."""
        problems = check_structure(self.spec)
        if problems:
            raise SpecError(problems)
        self.ds_id, self.ds_name = resolve_dataset(self.conn, self.spec['dataset'])
        cube = self.conn.cube(self.ds_id)
        self.names = Names(cube['definition']['availableObjects'])
        problems = check_data(self.spec, self.names)
        for pg in self.spec['pages']:
            on_page = {it['id'] for it in pg['items']}
            for it in pg['items']:
                if it['type'] == 'narrative':
                    for src in it['sources']:
                        if src not in on_page:
                            problems.append(f'item {it["id"]!r}: source {src!r} must be on the same page')
        if problems:
            raise SpecError(problems)

    # ---- the build ----
    def run(self, verify=True):
        t0 = time.time()
        self._phase('check spec and dataset')
        self.prepare()
        sp = self.spec
        self._phase('create draft')
        s = self.s = self.conn.new_dashboard([{'id': self.ds_id, 'name': self.ds_name}])
        st = s.structure()
        ch = st['chapters'][0]
        self.chapter_key = ch['key']
        self.next_key = max(s.all_keys() | {99})
        first = ch['pages'][0]['key']
        defaults = {}
        self._phase('pages')
        for i, pg in enumerate(sp['pages']):
            if i == 0:
                self.page_keys[pg['id']] = first
                defaults[pg['id']] = 'K52'
                self._step(f'page {pg["id"]}', lambda: s.rename_page(first, pg.get('title') or pg['id']))
            else:
                pk, vk = self._alloc(), self._alloc()
                self.page_keys[pg['id']] = pk
                defaults[pg['id']] = vk
                self._step(f'page {pg["id"]}', lambda: s.add_page(pk, ch['pageStack'], 'K51', vk,
                                                                   pg.get('title') or pg['id'], i + 1))
        if sp.get('chapter_title'):
            s.rename_chapter(self.chapter_key, sp['chapter_title'])
        for pg in sp['pages']:
            self._phase(f'page {pg["id"]}: items')
            self._build_page(pg, defaults[pg['id']])
        for nf in number_formats(sp):
            self._phase('number formats')
            self._step('number_formats', lambda: s.number_format([self.names.metric(m) for m in nf['metrics']],
                                                                 nf['format']))
        self._phase('save')
        s.set_current_panel(first)
        folder = sp.get('folder_id') or self.conn.my_folder(sp.get('folder') or 'My Reports')
        saved = self._step('save_as', lambda: s.save_as(sp['name'], folder, auto_summary=sp.get('auto_summary', True),
                                                         overwrite=sp.get('overwrite', False)))
        self.dashboard_id = saved['id']
        report = self.verify() if verify else []
        self.timings.append(('done', time.time()))
        return {'id': self.dashboard_id, 'name': sp['name'], 'seconds': round(time.time() - t0, 1),
                'edits': s.edits, 'calls': self.conn.calls, 'report': report, 'timings': self._timing_table()}

    def _timing_table(self):
        return [(self.timings[i][0], round(self.timings[i + 1][1] - self.timings[i][1], 1))
                for i in range(len(self.timings) - 1)]

    def _step(self, what, fn):
        try:
            return fn()
        except (StrategyError, KeyError, ValueError) as e:
            raise BuildError(what, e) from e

    def _build_page(self, pg, default_key):
        s, pk = self.s, self.page_keys[pg['id']]
        s.set_current_panel(pk)
        viz_keys, reused, layout_items = [], False, []
        narratives = []
        for it in pg['items']:
            typ = it['type']
            if typ == 'narrative':
                key = self._alloc()
                self.keys[it['id']] = {'key': key, 'page': pk, 'type': typ}
                narratives.append((it, key))
            elif typ in REUSABLE and not reused:
                reused = True
                key = default_key
                self.keys[it['id']] = {'key': key, 'page': pk, 'type': typ}
                viz_keys.append(key)
                self._step(f'item {it["id"]}', lambda: self._viz(it, key, pk, None))
            elif typ in REUSABLE or typ == 'donut':
                key = self._alloc()
                self.keys[it['id']] = {'key': key, 'page': pk, 'type': typ}
                viz_keys.append(key)
                layout = self._flat(viz_keys)
                self._step(f'item {it["id"]}', lambda: self._viz(it, key, pk, layout))
            elif typ == 'grid':   # always a Grid (Modern): a stitched container, never the classic or compound grid
                g = self._alloc()
                r = self._step(f'item {it["id"]}', lambda: self._grid(it, g, pk))
                key = r['stitchedKey']
                self.keys[it['id']] = {'key': key, 'grid': g, 'page': pk, 'type': typ}
                viz_keys.append(key)
            else:
                key, node = self._alloc(), self._alloc()
                self.keys[it['id']] = {'key': key, 'node': node, 'page': pk, 'type': typ}
                self._step(f'item {it["id"]}', lambda: self._field(it, key, node, pk))
            layout_items.append((it, key))
        for it, key in narratives:
            viz_keys.append(key)
            layout = self._flat(viz_keys)
            srcs = [self.keys[x]['key'] for x in it['sources']]
            self._step(f'item {it["id"]}', lambda: s.add_narratives(key, layout, srcs, it['instruction'], pk))
            self._viz_common(it, key)
        ff = [{'k': key, 'x': it['box'][0], 'y': it['box'][1], 'w': it['box'][2], 'h': it['box'][3],
               **({'exactHeight': True} if it.get('exact_height') else {})} for it, key in layout_items]
        self._step(f'page {pg["id"]} layout', lambda: s.set_freeform_layout(pk, ff))

    # ---- visualizations ----
    def _zone_fields(self, zones):
        fields = []
        for z, vals in zones.items():
            vals = _as_list(vals)
            for i, v in enumerate(vals):
                uid, ut = self.names.resolve(v, zone_kind(z))
                fields.append({'zoneId': ZONE[z], 'unitId': uid, 'unitType': ut,
                               **({'unitPos': i + 1} if len(vals) > 1 else {})})
        return fields

    def _viz(self, it, key, pk, layout):
        """layout None = convert the page's default visualization in place."""
        s, N, typ, ds = self.s, self.names, it['type'], self.ds_id
        if typ == 'kpi_card':
            if layout is None:
                s.to_kpi_card(key)
            else:
                s.insert_kpi_card(key, layout, pk)
            f = [{'zoneId': KPI_ZONE['metric'], 'unitId': N.metric(it['metric']), 'unitType': 4}]
            if it.get('trend'):
                f.append({'zoneId': KPI_ZONE['trend'], 'unitId': N.attribute(it['trend']), 'unitType': 12})
            if it.get('break_by'):
                f.append({'zoneId': KPI_ZONE['breakBy'], 'unitId': N.attribute(it['break_by']), 'unitType': 12})
            s.fill_zones(key, ds, f)
            if it.get('props'):
                s.set_kpi_card_props(key, it['props'])
        elif typ == 'iconic_kpi':   # reference/iconic-kpi-catalog.md; no title bar
            if layout is None:
                s.to_iconic_kpi(key)
            else:
                s.insert_kpi(key, layout, pk)
            names = _as_list(it.get('metrics') or it.get('metric'))   # one card per metric
            mids = [N.metric(m) for m in names]
            mid = mids[0]
            f = [{'zoneId': ZONE['xAxis'], 'unitId': m, 'unitType': 4, **({'unitPos': i + 1} if len(mids) > 1 else {})}
                 for i, m in enumerate(mids)]
            if it.get('trend'):
                f.append({'zoneId': ZONE['yAxis'], 'unitId': N.attribute(it['trend']), 'unitType': 12})
            s.fill_zones(key, ds, f)
            icon = it.get('icon')
            look = {'icon': None if icon is None else bool(icon), 'tooltip': it.get('tooltip'),
                    'trend': it.get('trend_shape'), 'previousValueLabel': it.get('previous_value_label'),
                    'referenceLine': it.get('reference_line'), 'change': it.get('change'),
                    'fillOpacity': it.get('fill_opacity'),
                    'content': {'name_and_value': 'nameAndValue', 'all': 'all'}.get(it.get('content')),
                    'layout': it.get('card_layout'), 'columns': it.get('columns'),
                    'alignment': it.get('card_alignment'), 'background': it.get('background')}
            if any(v is not None for v in look.values()) or it.get('props'):
                s.iconic_kpi_look(key, mid, look, it.get('props'))
            per = it.get('cards') or {}
            cards = []
            for name, m in zip(names, mids):
                c = per.get(name) or {}
                ic = c.get('icon') or (icon if isinstance(icon, str) else None)
                if ic or c.get('background'):
                    cards.append({'metricId': m, 'icon': ic, 'background': c.get('background'), 'opacity': c.get('opacity')})
            if cards:
                s.kpi_card_formats(key, cards)
        elif typ == 'chart':
            vis = VIS[it['vis']]
            if layout is None:
                s.change_type(key, vis, 521)
            else:
                s.insert_chart(key, vis, layout, pk)
            zones = dict(it['zones'])
            fields = self._zone_fields(zones)
            if it['vis'] in ('clusteredBar', 'clusteredHbar'):   # 2+ metrics side by side: Metric Names on both zones
                for z in ('colorBy', 'breakBy'):
                    if z not in zones:
                        fields.append({'zoneId': ZONE[z], 'unitId': METRIC_NAMES, 'unitType': 4})
            if it['vis'] in ('pie', 'ring') and 'colorBy' not in zones and zones.get('sliceBy'):
                fields.append({'zoneId': ZONE['colorBy'], 'unitId': N.attribute(_as_list(zones['sliceBy'])[0]),
                               'unitType': 12})   # the editor puts the slice attribute on Color By too
            if it.get('series_color') and 'colorBy' not in zones:
                fields.append({'zoneId': ZONE['colorBy'], 'unitId': METRIC_NAMES, 'unitType': 4})
            s.fill_zones(key, ds, fields)
            props = {**chart_look(it.get('legend'), it.get('data_labels'), it.get('leader_lines'), it.get('marker_size')),
                     **(it.get('props') or {})}
            if props:
                s.chart_format(key, vis, props)
            if it.get('series_color'):
                metric_id = next(f['unitId'] for f in fields if f['unitType'] == 4 and f['unitId'] != METRIC_NAMES)
                s.metric_colors({metric_id: it['series_color']}, key)
            if it.get('colors'):
                attr = _as_list(zones.get('colorBy') or zones.get('sliceBy'))[0]
                s.element_colors(N.attribute(attr), it['colors'], key)
            if it.get('metric_colors'):
                s.metric_colors({N.metric(m): c for m, c in it['metric_colors'].items()}, key)
            if it.get('sort'):
                srt = it['sort']
                s.sort_by_metric(key, N.metric(srt['metric']), srt.get('ascending', False), srt.get('axis', 1))
            first_metric = next((f['unitId'] for f in fields if f['unitType'] == 4 and f['unitId'] != METRIC_NAMES), None)
            self._reference_lines(it, key, first_metric)
        elif typ == 'line':
            kw = dict(x=[N.attribute(a) for a in _as_list(it['x'])],
                      metrics=[N.metric(m) for m in _as_list(it.get('metrics') or it.get('metric'))],
                      break_by=N.attribute(it['break_by']) if it.get('break_by') else None,
                      style=it.get('style', 'curved'), smoothness=it.get('smoothness', 0.3), color=it.get('color'),
                      markers=it.get('markers', False), data_labels=it.get('data_labels', False),
                      props={**chart_look(it.get('legend')), **(it.get('props') or {})})
            if layout is None:
                s.change_type(key, VIS['line'], 521)
                s.line_setup(key, ds, **kw)
            else:
                s.insert_line(key, layout, ds, page_key=pk, **kw)
            if it.get('metric_colors'):
                s.metric_colors({N.metric(m): c for m, c in it['metric_colors'].items()}, key)
            self._reference_lines(it, key, kw['metrics'][0])
        elif typ == 'donut':
            s.insert_donut(key, layout, ds, N.metric(it['metric']), N.attribute(it['slice']), page_key=pk,
                           color_by=N.attribute(it['color_by']) if it.get('color_by') else None,
                           target=N.metric(it['target']) if it.get('target') else None,
                           break_by=N.attribute(it['break_by']) if it.get('break_by') else None,
                           colors=it.get('colors'), props=it.get('props'))
        self._viz_common(it, key)

    def _grid(self, it, g, pk):
        N = self.names
        r = self.s.insert_modern_grid(g, self.ds_id, rows=[N.attribute(a) for a in _as_list(it.get('rows'))],
                                      columns=[N.attribute(a) for a in _as_list(it.get('columns'))],
                                      metrics=[N.metric(m) for m in _as_list(it.get('metrics'))], page_key=pk,
                                      title=it.get('title'),
                                      merge_column_headers=it.get('merge_column_headers', True))
        self._viz_common({k: v for k, v in it.items() if k != 'title'}, r['stitchedKey'])
        return r

    def _reference_lines(self, it, key, default_metric):
        counts = {}
        for rl in it.get('reference_lines') or []:
            mid = self.names.metric(rl['metric']) if rl.get('metric') else default_metric
            counts[mid] = counts.get(mid, 0) + 1          # lineIndex: 1-based per metric
            kw = {k: rl[k] for k in ('value', 'label', 'color', 'style', 'thickness') if k in rl}
            if rl.get('font'):
                kw['font'] = {'family': 'Open Sans', 'size': '9pt', 'color': '#35383A', **rl['font']}
            self.s.reference_line(key, mid, rl['type'], index=counts[mid], **kw)

    def _viz_common(self, it, key):
        s = self.s
        if it.get('type') == 'iconic_kpi':   # no title bar: the title only names it in the editor
            if it.get('title'):
                s.set_title(key, it['title'])
        elif it.get('title'):
            s.title_bar(key, True, it['title'])
        elif it.get('title_bar') is False:
            s.title_bar(key, False)
        tf = it.get('title_format')
        if tf:   # every visualization type has a title bar except the Iconic KPI (rejected by the spec check)
            s.title_format(key, lines=tf.get('lines'), subtitle=tf.get('subtitle'), align=tf.get('align'),
                           subtitle_align=tf.get('subtitle_align'), wrap=tf.get('wrap'),
                           subtitle_wrap=tf.get('subtitle_wrap'),
                           font=font_format(tf.get('font')) or None, subtitle_font=font_format(tf.get('subtitle_font')) or None)
        if it.get('border'):
            b = it['border']
            s.card_border(key, b.get('color', '#ababab'), b.get('radius', 8), b.get('style', 5))
        if it.get('fill'):
            s.set_fill(key, 521, container=it['fill'].get('container'), title=it['fill'].get('title'))

    # ---- text, images, shapes ----
    def _field(self, it, key, node, pk):
        s, typ = self.s, it['type']
        if typ == 'text':
            s.add_text(pk, key, node, it['text'], it.get('formatting_font') or font_format(it.get('font')))
            fmt = {'FormattingPatterns': ({'FillStyle': 1} if it.get('fill', 'none') == 'none'
                                          else {'FillColor': int(bgr(it['fill'])), 'FillStyle': 0})}
            if it.get('align'):
                fmt['FormattingAlignment'] = {'Horizontal': ALIGN[it['align']]}
            s.format_text(key, node, fmt)
            link = it.get('link')
            if link:
                to = dict(link)
                if to.get('page') and not to.get('dashboard'):
                    to = {'page': self.page_keys[to['page']]}
                if 'new_tab' in to:
                    to['newTab'] = to.pop('new_tab')
                s.set_link(key, node, to, it.get('tooltip', ''))
        elif typ == 'rich_text':
            s.add_rich_text(key, node, it['runs'], page_key=pk, name=it.get('name', it['id']), align=it.get('align'),
                            header=it.get('header'), list=it.get('list'), indent=it.get('indent'),
                            transparent=it.get('transparent', True))
        elif typ == 'image':
            sm = it.get('size_mode', 'fill')
            s.insert_image(key, node, it['url'], page_key=pk, name=it.get('name', it['id']),
                           size_mode=SIZE_MODE.get(sm, sm))
        elif typ == 'shape':
            s.insert_shape(key, node, it.get('shape', 'Rectangle'), page_key=pk, settings=it.get('settings'),
                           fill=it.get('fill', '#8AC3FF'), stroke=it.get('stroke', it.get('fill', '#35383A')),
                           stroke_width=it.get('stroke_width', 0 if 'stroke' not in it else 1),
                           opacity=it.get('opacity'), dash=it.get('dash'))

    # ---- check the saved dashboard ----
    def verify(self):
        self._phase('verify')
        d = self.dashboard_id
        s2 = self.conn.open(d)
        text = s2.initial
        chapter = s2.structure()['chapters'][0]['key']
        out = []
        for iid, k in self.keys.items():
            key = k['key']
            if k['type'] in ('text', 'rich_text', 'image', 'shape'):
                ok = f'"{key}"' in text
                out.append((iid, key, ok, 'on page' if ok else 'not found in saved dashboard'))
                continue
            try:
                v = self.conn.api('GET', f'/v2/dossiers/{d}/instances/{s2.mid}/chapters/{chapter}/visualizations/{key}'
                                         '?limit=20')
                data = (v or {}).get('data') or {}
                mvs = data.get('metricValues') or {}
                # A Grid (Modern) is read by its stitched container key (REST refuses the inner grid key with
                # ERR006) and returns its values per column set.
                mv = mvs.get('formatted')
                if mv is None and mvs.get('columnSets'):
                    mv = (mvs['columnSets'][0] or {}).get('formatted')
                first = ', '.join(str(x) for x in mv[0][:4]) + (' …' if len(mv[0]) > 4 else '') if mv else ''
                detail = (f'{len(mv)} row(s), first: {first}' if mv else 'no metric values') if mv is not None \
                    else ('ok' if v else 'empty')
                ok = k['type'] == 'narrative' or bool(mv)
                out.append((iid, key, ok, detail))
            except StrategyError as e:
                out.append((iid, key, False, str(e)[:160]))
        if self.spec.get('auto_summary', True):
            units = {}
            for l in s2.server_json()['defn']['layouts']:
                units.update(l['units'])
            for pid, pk in self.page_keys.items():
                win = [k for k, u in units.items() if u.get('pnk') == pk and u.get('t') == 8
                       and 'NLG one click' in (u.get('ttl') or '')]
                out.append((f'auto summary ({pid})', win[0] if win else '-', bool(win),
                            'on' if win else 'no Auto Summary window on this page'))
        return out
