"""An open dashboard instance and the editor actions that change it.

Each method is a port of the same-named helper in strategy-dashboard-client.js (camelCase there, snake_case here) and
sends the same actions in the same edit calls; tests/test_parity.py checks that against the JS client. The comments in
the JS file and reference/*.md explain each helper; only Python-specific notes are repeated here.

Pass 1 (2026-11-22) ports the core, pages and the helpers the Lincoln dashboard used. The rest of the JS helpers
(Modern Grids, filters, selectors, heat map, Sankey, bubble, stacked bar, time attributes) are still JS-only.
"""
import json
import re
import time

from .constants import (AUTO_SUMMARY_INSTRUCTION, CUSTOM_VIS_CLASS, DONUT_LABEL, DONUT_ZONE, GRAPH_MATRIX_CLASS,
                        KPI_CARD_CLASS, METRIC_NAMES, TEXT_HEIGHT_PAD, VIS, ZONE)
from .transport import StrategyError
from .util import (bgr, esc_attr, jdump, js_num, js_str, parse_float_prefix, random_key32, rich_text_value,
                   to_fixed_num)

_BS = re.compile(r'"bs":"([^"]+)"')
_JSON_RESULTS = {'taskId': 'getServerJSONResults', 'styleName': 'ServerJsonRWDStyle', 'resFlags': '0',
                 'compress': '1', 'innerHeight': '857', 'innerWidth': '1920'}


def vis_format(key, unit_type, vis):
    shape, vis_type, subtype = vis['shape'], vis['visType'], vis.get('subtype', 'Automatic')
    return {
        'act': 'format', 'unitKey': key, 'unitType': unit_type, 'formatType': 1,
        'format': {
            'Visualization': {
                'VisualizationsEnabled': -1, 'ViewMode': 51,
                'SelectedVisualization': 'GraphMatrixVisualizationStyle',
                'VisualizationList': 'GraphMatrixVisualizationStyle',
                'IPhoneVisualization': '', 'IPadVisualization': 'IPadGraphMatrix2Style',
                'APhoneVisualization': '', 'ATabletVisualization': '', 'ReturnBinaryResult': False,
            },
            'FormattingWidget': {
                'ClassName': GRAPH_MATRIX_CLASS, 'Enable': 1,
                'WidgetProps': '<props ><widgetProps ><fmt ><visStyle value="GraphMatrixVisualizationStyle" ></visStyle>'
                               f'<Shape value="{shape}" ></Shape><Subtype value="{subtype}" ></Subtype>'
                               f'<visType value="{vis_type}" ></visType><userVisType value="{vis_type}" ></userVisType>'
                               '</fmt></widgetProps></props>',
            },
        },
    }


def _layout_action(page_key, layout):
    return {'act': 'format', 'unitKey': page_key, 'unitType': 9, 'formatType': 1,
            'format': {'FormattingSize': {'LayoutXML': layout}}, 'isJson': True}


def _custom_vis_format(key, vis_name, widget_props='<props><widgetProps><fmt><cvp><ftFgGrpA value="1"></ftFgGrpA>'
                                                   '</cvp></fmt></widgetProps></props>'):
    return {'act': 'format', 'unitKey': key, 'unitType': 521, 'formatType': 1, 'format': {
        'Visualization': {'VisualizationsEnabled': -1, 'ViewMode': 51, 'SelectedVisualization': vis_name,
                          'VisualizationList': vis_name, 'IPhoneVisualization': '', 'IPadVisualization': '',
                          'APhoneVisualization': '', 'ATabletVisualization': '', 'ReturnBinaryResult': False},
        'FormattingWidget': {'ClassName': CUSTOM_VIS_CLASS, 'Enable': 1, 'WidgetProps': widget_props},
        'FormattingView': {'ShowTitleBar': 0, 'ShowWidgetTitleBar': 0}}}


def _kpi_card_format(key, title=None):
    fmt = {
        'Visualization': {'VisualizationsEnabled': -1, 'ViewMode': 51,
                          'SelectedVisualization': 'KPICardVisualizationStyle',
                          'VisualizationList': 'KPICardVisualizationStyle', 'IPhoneVisualization': '',
                          'IPadVisualization': 'IPhoneKPICardStyle', 'APhoneVisualization': '',
                          'ATabletVisualization': '', 'ReturnBinaryResult': False},
        'FormattingWidget': {'ClassName': KPI_CARD_CLASS, 'Enable': 1,
                             'WidgetProps': '<props><widgetProps><fmt><dm value="5"></dm><fstr value="1"></fstr>'
                                            '</fmt></widgetProps></props>'}}
    if title:
        fmt['FormattingView'] = {'Title': title}
    return {'act': 'format', 'unitKey': key, 'unitType': 521, 'formatType': 1, 'format': fmt}


def _drop_zones(key, widget_type):
    return {'act': 'updateTemplate', 'keyContext': key, 'actions': [
        {'act': 'createDefaultDropZones', 'nodeKey': key, 'treeType': 1, 'datasetType': 3, 'widgetType': widget_type}]}


def _incremental_fetch_off(key, unit_type=521):
    return {'act': 'format', 'unitKey': key, 'unitType': unit_type, 'formatType': 1,
            'format': {'FormattingIncrementalFetch': {'EnableIFOnGrid': 0}}}


class Session:
    """One open instance (mid) of a dashboard. dashboard_id is BLANK_TEMPLATE for a new draft.

    transport: anything with api(method, path, body) and task(params) (a Connection, or a fake in tests).
    now / key32: the clock (ms) and 32-hex key generator, injectable so tests are repeatable.
    """

    def __init__(self, transport, dashboard_id, mid, now=None, key32=None):
        self.t = transport
        self.dashboard_id, self.mid = dashboard_id, mid
        self.now = now or (lambda: int(time.time() * 1000))
        self.key32 = key32 or random_key32
        self.node = 'K46'  # partialRetrieval node of the current chapter (K46 in a draft's first chapter)
        self.edits = 0
        self.last_freeform_items = None
        g = self.t.task({**_JSON_RESULTS, 'messageID': mid, 'excludeData': 'false', 'supportsUndo': 'true'})
        m = _BS.search(g)
        if not m:
            raise StrategyError('no bs in getServerJSONResults response')
        self.bs = m.group(1)
        self.initial = g

    # ---- transport ----
    def edit(self, actions, nodes):
        params = {'actions': actions, 'partialRetrieval': {'nodes': nodes},
                  'style': {'params': {'treesToRender': 2}, 'name': 'RWIVEMojoStyle'}}
        try:
            t = self.t.task({'taskId': 'mojoRWManipulation', 'messageID': self.mid, 'rwb': self.bs, 'stateID': '-1',
                             'styleName': 'RWIVEMojoStyle', 'zoomFactor': '1', 'params': jdump(params)})
        except StrategyError as e:
            e.actions = actions
            raise
        self.edits += 1
        m = _BS.search(t)
        if m:
            self.bs = m.group(1)
        return t

    def server_json(self):
        return json.loads(self.t.task({**_JSON_RESULTS, 'messageID': self.mid, 'excludeData': 'true'}))

    def all_keys(self):
        """Every W<number> key used anywhere in the instance (units, text nodes, fields, selectors)."""
        return {int(k[1:]) for k in re.findall(r'\bW\d+\b', jdump(self.server_json()))}

    # ---- layout ----
    def set_layout(self, page_key, layout):
        return self.edit([_layout_action(page_key, layout)], [page_key])

    def set_freeform_layout(self, page_key, items):
        """items: [{k, x, y, w, h, exactHeight?}] in percent of the page, back to front."""
        j = self.server_json()
        chapter = next((l for l in j['defn']['layouts'] if page_key in l['units']), None)
        if chapter is None:
            raise StrategyError(f'page {page_key} is not in the instance')
        fm = chapter['units'][page_key].get('fmts') or {}
        W = parse_float_prefix(fm.get('width'), 1594)
        H = parse_float_prefix(fm.get('height'), 894)

        def v(pct, px):
            return f'{js_num(pct)}|{js_num((pct * px) / 100)}px'

        def is_text(k):
            return (chapter['units'].get(k) or {}).get('t') == 106

        sized = [({**it, 'h': to_fixed_num(it['h'] + TEXT_HEIGHT_PAD, 4)} if is_text(it['k']) and not it.get('exactHeight')
                  else it) for it in items]
        self.last_freeform_items = sized
        children = [{'fixed': '0', 'k': it['k'], 'rk': page_key, 't': 'flc', 'zIndex': str(i + 2),
                     'top': v(it['y'], H), 'left': v(it['x'], W), 'width': v(it['w'], W), 'height': v(it['h'], H),
                     'l': it['w'], 'hidden': 0} for i, it in enumerate(sized)]
        layout = {'t': 'b', 'o': 'v', 'm': 'm', 'children': [], 'ifwChildren': [], 'canvasSize': None,
                  'floatChildren': {'t': 'g', 'k': self.key32(), 'zIndex': str(len(items) + 1), 'left': '0|0px',
                                    'top': '0|0px', 'width': f'100|{js_num(W)}px', 'height': f'100|{js_num(H)}px',
                                    'children': children}}
        return self.edit([
            {'act': 'format', 'unitKey': chapter['k'], 'unitType': 1, 'formatType': 1,
             'format': {'FormattingPage': {'UsePageWidthAsLayoutWidth': 1, 'MarginLeft': '0', 'MarginRight': '0'}}},
            _layout_action(page_key, layout)], [page_key])

    # ---- charts ----
    def insert_chart(self, new_key, vis, layout, page_key='K53', proto_key='K51'):
        return self.edit([
            {'act': 'copyUnit', 'unitKey': proto_key, 'unitType': 521, 'newKey': new_key, 'toKey': page_key},
            _layout_action(page_key, layout),
            _drop_zones(new_key, 1),
            vis_format(new_key, 521, vis),
            _incremental_fetch_off(new_key),
            {'act': 'changeGridDisplayMode', 'nodeKey': new_key, 'displayMode': 2},
        ], [new_key])

    def change_type(self, viz_key, vis, unit_type=522):
        return self.edit([
            _drop_zones(viz_key, 1),
            vis_format(viz_key, unit_type, vis),
            _incremental_fetch_off(viz_key, unit_type),
            {'act': 'changeGridDisplayMode', 'nodeKey': viz_key, 'displayMode': 2},
        ], [viz_key])

    def fill_zones(self, viz_key, dataset_id, fields):
        """fields: [{zoneId, unitId, unitType, unitPos?, ax?}]."""
        return self.edit([
            {'act': 'updateTemplate', 'keyContext': viz_key, 'actions': [
                {'ax': f.get('ax') or 0, 'act': 'addDropZoneUnit', 'zoneId': f['zoneId'], 'datasetId': dataset_id,
                 'unitId': f['unitId'], 'unitType': f['unitType'], 'unitPos': f.get('unitPos') or 0} for f in fields]},
            {'act': 'editNode', 'nodeKey': viz_key, 'datasetId': dataset_id}], [viz_key, self.node])

    def add_to_grid(self, viz_key, dataset_id, unit_id, unit_type, axis, unit_pos=0):
        return self.edit([
            {'act': 'updateTemplate', 'keyContext': viz_key, 'actions': [
                {'act': 'addUnit', 'unitId': unit_id, 'unitType': unit_type, 'unitPos': unit_pos, 'dsId': dataset_id,
                 'isFirst': unit_pos == 0, 'axis': axis}]},
            {'act': 'editNode', 'nodeKey': viz_key, 'datasetId': dataset_id}], [viz_key])

    def set_title(self, viz_key, title):
        return self.edit([{'act': 'format', 'unitKey': viz_key, 'unitType': 521, 'formatType': 1,
                           'format': {'FormattingView': {'Title': title}}}], [viz_key])

    def title_bar(self, viz_key, show=True, title=None):
        view = {'ShowTitleBar': -1 if show else 0, 'ShowWidgetTitleBar': -1 if show else 0}
        if title:
            view['Title'] = title
        return self.edit([{'act': 'format', 'unitKey': viz_key, 'unitType': 521, 'formatType': 1,
                           'format': {'FormattingView': view}}], [viz_key])

    def title_format(self, viz_key, lines=None, subtitle=None, align=None, subtitle_align=None, wrap=None,
                     subtitle_wrap=None, font=None, subtitle_font=None, unit_type=521):
        """Title bar format: 1 or 2 lines, the second line's text, each line's font, alignment and wrap.

        Works on every visualization type EXCEPT the Iconic KPI (ImageEnhancedKPI), which has no title bar.
        align: 'left' | 'center' | 'right' (Horizontal 0 / 2 / 1). wrap: True wraps (TextWrap -1), False keeps one line.
        Format type 2 is the title line, 3 the second line. See titleFormat in the JS client and
        reference/bar-catalog.md "Title bar"."""
        H = {'left': 0, 'right': 1, 'center': 2}

        def f(formatType, fmt):
            return {'act': 'format', 'unitKey': viz_key, 'unitType': unit_type, 'formatType': formatType, 'format': fmt}

        def align2(a, w):
            x = {}
            if a is not None:
                x['Horizontal'] = H[a]
            if w is not None:
                x['TextWrap'] = -1 if w else 0
            return x

        two = lines == 2 or (lines is None and subtitle is not None)
        acts = []
        if lines is not None or subtitle is not None:
            acts.append(f(1, {'FormattingView': {'TitlesLines': 2 if two else 1}}))
        if subtitle is not None:
            acts += [{'act': 'setSubtitle', 'nodeKey': viz_key, 'unitType': 521, 'subtitle': subtitle},
                     f(3, {'FormattingFont': {'Bold': 0, 'Italic': 0, 'Underline': 0, 'Strikeout': 0, 'Size': 9,
                                              'Color': 3815477, 'Name': 'Open Sans'}})]
        if font:
            acts.append(f(2, {'FormattingFont': font}))
        if subtitle_font:
            acts.append(f(3, {'FormattingFont': subtitle_font}))
        a1 = align2(align, wrap)
        a2 = align2(subtitle_align if subtitle_align is not None else align,
                    subtitle_wrap if subtitle_wrap is not None else wrap)
        if a1:
            acts.append(f(2, {'FormattingAlignment': a1}))
        if a2 and (two or subtitle_align is not None or subtitle_wrap is not None):
            acts.append(f(3, {'FormattingAlignment': a2}))
        return self.edit(acts, [viz_key])

    REF_TYPES = {'maximum': 1, 'minimum': 2, 'average': 3, 'median': 4, 'first': 5, 'last': 6, 'constant': 7}

    def reference_line(self, viz_key, metric_id, type='average', value=None, label=('type', 'value'), index=1,  # noqa: A002
                       color='#4D4D4D', style='dashed', thickness=1, font=None):
        """Reference line (maximum ... constant) on a chart's metric: operateTRFLine. label: any of 'type', 'metric',
        'value' (bitmask 1/2/4), or the number. index: 1-based position in the metric's line list. See referenceLine in
        the JS client and reference/bar-catalog.md "Reference lines"."""
        font = font or {'family': 'Open Sans', 'size': '9pt', 'color': '#35383A'}
        line_type = self.REF_TYPES.get(type)
        if not line_type:
            raise ValueError('Unknown reference line type ' + str(type))
        if type == 'constant' and (value is None or value == ''):
            raise ValueError('A constant reference line needs a value')
        bits = {'type': 1, 'metric': 2, 'value': 4}
        line_label = label if isinstance(label, int) else sum(bits.get(k, 0) for k in set(label))
        fmt = {'trdRefLnThk': thickness, 'trdRefLnClr': int(bgr(color)), 'trdRefLnStyle': 0 if style == 'solid' else 1,
               'rfLnFntFml': font['family'], 'rfLnFntSz': font['size'], 'rfLnFntStyle': 0,
               'rfLnFntClr': int(bgr(font['color'])), 'trdRefLnCmbStyle': 3}
        return self.edit([{'act': 'operateTRFLine', 'tks': viz_key, 'lineType': line_type, 'lineLevel': 1,
                           'lineLabel': line_label, 'enabled': 1, 'includeBreakby': 0,
                           'lineConstant': js_str(value) if type == 'constant' else '', 'lineIndex': index,
                           'format': jdump(fmt).replace('"', '&quot;'), 'metricId': metric_id}], [viz_key])

    def set_widget_props(self, viz_key, class_name, props, wrapper='fmt'):
        inner = ''.join(f'<{k} value="{esc_attr(v)}"></{k}>' for k, v in props.items()
                        if v is not None and not isinstance(v, (dict, list)))
        xml = (f'<props><widgetProps><fmt><cvp>{inner}</cvp></fmt></widgetProps></props>' if wrapper == 'cvp'
               else f'<props><widgetProps><fmt>{inner}</fmt></widgetProps></props>')
        return self.edit([{'act': 'format', 'unitKey': viz_key, 'unitType': 521, 'formatType': 1, 'format': {
            'FormattingWidget': {'ClassName': class_name, 'Enable': 1, 'WidgetProps': xml}}}], [viz_key])

    def chart_format(self, viz_key, vis, extra=None):
        extra = dict(extra or {})
        p = {'visStyle': 'GraphMatrixVisualizationStyle', 'Shape': vis['shape'], 'Subtype': vis.get('subtype', 'Automatic'),
             'visType': vis['visType'], 'userVisType': vis['visType'], **extra}
        if isinstance(extra.get('axisOrigin'), dict):
            e = list(extra['axisOrigin'].items())
            parts = [f"'@pLd{m}':{{'axOriAuto':false,'axOriValue':'{js_str(v)}'}}" for m, v in e]
            parts.append(f"'AllMetrics':{{'axOriAuto':false,'axOriValue':'{js_str(e[0][1])}'}}")
            p['axisOrigin'] = '{' + ','.join(parts) + '}'
            p['xAxOriLnShw'] = 'true'
            p['yAxOriLnShw'] = 'true'
        if isinstance(extra.get('axisRange'), dict):
            e = list(extra['axisRange'].items())

            def one(k, r):
                lo, hi = js_str(r[0]), js_str(r[1])
                return f'{k}:0:{lo}:{hi}:{lo}:{hi}:false:false:false'
            p['AxisScale'] = ','.join([one('AllMetrics', e[0][1])] + [one(m, r) for m, r in e])
            p['MinMax'] = 'Custom'
            p['axScaleModified'] = '1'
            p['AxisScaleSyncMode'] = 'false'
            del p['axisRange']
        if extra.get('seriesColor'):
            p['modDefFillClr'] = bgr(extra['seriesColor'])
            del p['seriesColor']
        return self.set_widget_props(viz_key, GRAPH_MATRIX_CLASS, p)

    def insert_line(self, new_key, layout, dataset_id, x, metrics=None, metric=None, page_key='K53', proto_key='K51',
                    break_by=None, style='curved', smoothness=0.3, color=None, markers=False, data_labels=False,
                    props=None):
        self.insert_chart(new_key, VIS['line'], layout, page_key, proto_key)
        return self.line_setup(new_key, dataset_id, x, metrics, metric, break_by, style, smoothness, color, markers,
                               data_labels, props)

    def line_setup(self, viz_key, dataset_id, x, metrics=None, metric=None, break_by=None, style='curved',
                   smoothness=0.3, color=None, markers=False, data_labels=False, props=None):
        """insert_line without the insert: fills and formats an existing line chart (e.g. a page's default
        visualization after change_type(key, VIS['line'], 521))."""
        new_key = viz_key
        mets = metrics or [metric]
        xs = x if isinstance(x, list) else [x]
        fields =[{'zoneId': ZONE['xAxis'], 'unitId': a, 'unitType': 12, 'unitPos': i + 1} for i, a in enumerate(xs)]
        fields += [{'zoneId': ZONE['yAxis'], 'unitId': m, 'unitType': 4, 'unitPos': i + 1} for i, m in enumerate(mets)]
        if break_by:
            fields += [{'zoneId': ZONE['breakBy'], 'unitId': break_by, 'unitType': 12},
                       {'zoneId': ZONE['colorBy'], 'unitId': break_by, 'unitType': 12}]
        elif len(mets) > 1:
            fields.append({'zoneId': ZONE['colorBy'], 'unitId': METRIC_NAMES, 'unitType': 4})
        self.fill_zones(new_key, dataset_id, fields)
        t0, curved = self.now(), style == 'curved'
        shp = [f"'shpSmooth':{1 if curved else 0}", f"'shpSmooth_tmsp':{t0}"]
        if curved:
            shp += [f"'shpSmoothStrength':{js_num(smoothness)}", f"'shpSmoothStrength_tmsp':{t0}"]
        extra = {'allShpFmt': '{' + ', '.join(shp) + '}', 'lnMkShw': 'true' if markers else 'false'}
        if data_labels:
            extra['DataLabel'] = 'Show only values'
        if color and len(mets) == 1 and not break_by:
            extra['seriesColor'] = color
        extra.update(props or {})
        return self.chart_format(new_key, VIS['line'], extra)

    def element_colors(self, attr_id, colors, refresh_key=None):
        return self.edit([{'act': 'updateElementsPropertiesMap', 'epm': [{'epmk': [{'ob': {'did': attr_id, 'tp': 12}}],
            'epmv': [{'v': {'vv': jdump({'color': int(bgr(hx))})},
                      'k': {'chn': [{'emt': 1, 'ei': 'h' + value + ';' + attr_id,
                                     'at': {'did': attr_id, 'tp': 12, 'ql': 0}}]}} for value, hx in colors.items()]}]}],
            [refresh_key or self.node])

    def metric_colors(self, colors, refresh_key=None):
        return self.edit([{'act': 'updateElementsPropertiesMap', 'epm': [{'epmk': [{'ob': {'did': ''}}],
            'epmv': [{'v': {'vv': jdump({'color': int(bgr(hx))})},
                      'k': {'chn': [{'emt': 2, 'mt': {'did': mid, 'tp': 4, 'ql': 0}}]}} for mid, hx in colors.items()]}]}],
            [refresh_key or self.node])

    def sort_by_metric(self, viz_key, metric_id, ascending=False, axis=1, element=None):
        el = ('h' + element['value'] + ';' + element['attrId']) if element else ''
        sort = {'key': '4!' + metric_id + '!!!' + el + '!' + str(axis), 'metricSortKey': '2', 'isAsc': ascending}
        return self.edit([{'act': 'updateTemplate', 'keyContext': viz_key, 'actions': [{'act': 'sort',
            'sorts': [[sort]], 'nodeKey': viz_key, 'subTotalsPos': [0], 'stt': -1, 'rp': None}]}], [viz_key])

    def number_format(self, metric_ids, f, category=7):
        return self.edit([{'act': 'numberFormat', 'unitId': u, 'unitType': 4, 'c': category, 'f': f} for u in metric_ids],
                         [self.node])

    def card_border(self, viz_key, color='#ababab', radius=8, style=5):
        c = bgr(color)
        return self.edit([{'act': 'format', 'unitKey': viz_key, 'unitType': 522, 'formatType': 1, 'format': {
            'FormattingBorder': {'TopStyle': style, 'RightStyle': style, 'BottomStyle': style, 'LeftStyle': style,
                                 'TopColor': c, 'RightColor': c, 'BottomColor': c, 'LeftColor': c},
            'FormattingView': {'Radius': radius}}}], [viz_key])

    def set_fill(self, key, unit_type, container=None, title=None, title_font=None, key_context=None):
        def pat(v):
            return {'FillStyle': 1} if v == 'none' else {'FillColor': int(bgr(v)), 'FillStyle': 0}
        base = {'unitKey': key, 'unitType': unit_type, **({'keyContext': key_context} if key_context else {})}
        acts = []
        if container is not None:
            acts.append({'act': 'format', **base, 'formatType': 1, 'format': {'FormattingPatterns': pat(container)}})
        if title is not None or title_font:
            fmt = {}
            if title is not None:
                fmt['FormattingPatterns'] = pat(title)
            if title_font:
                fmt['FormattingFont'] = title_font
            acts.append({'act': 'format', **base, 'formatType': 5 if unit_type == 111 else 2, 'format': fmt})
        return self.edit(acts, [self.node if unit_type == 111 else key])

    # ---- custom visualizations and KPIs ----
    def insert_custom_vis(self, new_key, vis_name, layout, page_key='K53', proto_key='K51'):
        return self.edit([
            {'act': 'copyUnit', 'unitKey': proto_key, 'unitType': 521, 'newKey': new_key, 'toKey': page_key},
            _layout_action(page_key, layout),
            _drop_zones(new_key, 7),
            _custom_vis_format(new_key, vis_name),
            {'act': 'changeGridDisplayMode', 'nodeKey': new_key, 'displayMode': 1}], [new_key])

    def insert_donut(self, new_key, layout, dataset_id, metric, slice, page_key='K53', proto_key='K51',  # noqa: A002
                     color_by=None, target=None, break_by=None, colors=None, props=None):
        self.insert_custom_vis(new_key, 'DonutChart', layout, page_key, proto_key)
        fields = [{'zoneId': DONUT_ZONE['angle'], 'unitId': metric, 'unitType': 4},
                  {'zoneId': DONUT_ZONE['colorBy'], 'unitId': color_by or slice, 'unitType': 12},
                  {'zoneId': DONUT_ZONE['slice'], 'unitId': slice, 'unitType': 12}]
        if target:
            fields.append({'zoneId': DONUT_ZONE['target'], 'unitId': target, 'unitType': 4})
        if break_by:
            fields.append({'zoneId': DONUT_ZONE['breakBy'], 'unitId': break_by, 'unitType': 12})
        self.fill_zones(new_key, dataset_id, fields)
        look = {'showLegend': True, 'showLegendTitle': False, 'innerRatio': 80, 'padding': 2, 'showDataLabel': True,
                'dataLabelType': DONUT_LABEL['textAndValue'], 'legendValueType': 2, 'shapeRadius': '6%',
                'legendContentType': 'all', 'textContentType': 'all', **(props or {})}
        self.set_widget_props(new_key, CUSTOM_VIS_CLASS, {'ftFgGrpA': '1', 'unifiedProperty': jdump(look)}, 'cvp')
        if colors:
            self.element_colors(color_by or slice, colors, new_key)

    def insert_kpi_card(self, new_key, layout, page_key='K53', proto_key='K51', title=None):
        return self.edit([
            {'act': 'copyUnit', 'unitKey': proto_key, 'unitType': 521, 'newKey': new_key, 'toKey': page_key},
            _layout_action(page_key, layout),
            _drop_zones(new_key, 9),
            _kpi_card_format(new_key, title),
            _incremental_fetch_off(new_key),
            {'act': 'changeGridDisplayMode', 'nodeKey': new_key, 'displayMode': 1},
        ], [new_key])

    def to_kpi_card(self, viz_key='K52'):
        return self.edit([
            _drop_zones(viz_key, 9),
            _kpi_card_format(viz_key),
            _incremental_fetch_off(viz_key),
            {'act': 'changeGridDisplayMode', 'nodeKey': viz_key, 'displayMode': 1},
        ], [viz_key])

    def set_kpi_card_props(self, viz_key, props=None):
        p = {'dm': '5', 'fstr': '1', **(props or {})}
        p = {k: (jdump(v) if isinstance(v, (dict, list)) else v) for k, v in p.items()}
        return self.set_widget_props(viz_key, KPI_CARD_CLASS, p)

    def add_narratives(self, new_key, layout, sources, instruction, page_key='K53', proto_key='K51'):
        if '"' in instruction:
            raise ValueError('narrative instruction must not contain double quotes (the edit fails with a 500)')
        self.insert_custom_vis(new_key, 'AutoNarratives', layout, page_key, proto_key)
        cfg = {'instruction': instruction, 'hasFormatInstruction': False,
               'recommendations': [{'vizId': 'nk-re-' + k, 'skipCalculation': True, 'removeDataLimit': True,
                                    'algorithms': {}} for k in sources]}
        return self.edit([
            {'act': 'setProperty', 'nodeKey': new_key, 'prs': 'Visualization', 'pri': 17,
             'v': jdump(cfg).replace('"', '&quot;')},
            {'act': 'setGridPropsRMs', 'nodeKey': new_key, 'rfMaps': [{'key': 'nk-re-' + k, 'value': k} for k in sources]},
            {'act': 'clearNLGSources', 'nodeKey': new_key, 'associatedNodes': []},
            {'act': 'setNLGSources', 'nodeKey': new_key, 'associatedNodes': sources}], [new_key])

    # ---- text, images, shapes, links ----
    def add_text(self, page_key, field_key, node_key, text, font=None):
        return self.edit([
            {'act': 'addField', 'createNode': True, 'nodeKeyParent': page_key, 'fieldKey': field_key, 'fieldType': 3,
             'nodeKey': node_key, 'treeType': 1, 'fieldName': field_key},
            {'act': 'editField', 'fieldValue': text, 'fieldKey': field_key, 'fieldType': 3, 'nodeKey': node_key,
             'treeType': 1, 'fieldName': field_key},
            {'act': 'format', 'unitKey': field_key, 'unitType': 106, 'formatType': 1, 'fieldKey': field_key,
             'nodeKey': node_key, 'keyContext': '106\u001e' + node_key + '\u001e' + field_key,
             'format': {'FormattingFont': font or {}, 'FormattingSize': {'TextOverflow': 1, 'HeightMode': 0}}}],
            [page_key])

    def add_rich_text(self, field_key, node_key, runs, page_key='K53', create_node=True, name='Rich Text', align=None,
                      header=None, list=None, indent=None, layout=None, transparent=False):  # noqa: A002
        f = {'fieldKey': field_key, 'fieldType': 3, 'nodeKey': node_key, 'treeType': 1, 'fieldName': name}
        kc = '106\u001e' + node_key + '\u001e' + field_key
        fmt = {'FormattingSize': {'TextOverflow': 1, 'HeightMode': 0}, 'FormattingAppearance': {'TextFieldType': 1}}
        if transparent:
            fmt['FormattingPatterns'] = {'FillStyle': 1}
        acts = [{'act': 'addField', 'createNode': create_node, 'nodeKeyParent': page_key, **f},
                {'act': 'editField', 'fieldValue': rich_text_value(runs, align, header, list, indent), **f, 'altText': ''},
                {'act': 'format', 'unitKey': field_key, 'unitType': 106, 'formatType': 1, 'fieldKey': field_key,
                 'nodeKey': node_key, 'keyContext': kc, 'format': fmt}]
        if layout:
            acts.append(_layout_action(page_key, layout))
        return self.edit(acts, [page_key])

    def set_link(self, field_key, node_key, to, tooltip=''):
        """to: {'page': key} | {'url', 'newTab'} | {'dashboard', 'page', 'newTab', 'passFilterPanel',
        'passVizSelections', 'filterPages'} | None (remove). Use on plain text (add_text) only."""
        kc = '106\u001e' + node_key + '\u001e' + field_key
        base = {'act': 'format', 'unitKey': field_key, 'unitType': 106, 'formatType': 1, 'fieldKey': field_key,
                'nodeKey': node_key, 'keyContext': kc}
        if not to:
            return self.edit([{**base, 'format': {'FormattingNavigation': {'Hyperlinks': ''}}}], [node_key])

        def attrs(o):
            return ' '.join(f'{k}="{esc_xml(v)}"' for k, v in o.items())

        def esc_xml(v):
            return js_str(v).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

        resolved = ''
        if to.get('url'):
            hls = '' if to.get('newTab') is False else ' onw="1"'
            hl = {'idf': 1, 'aopam': 2, 'dtxt': tooltip, 'url': to['url'], 'lt': 0, 'so': 0}
            resolved = f'<hls><hl index="0" url="{esc_xml(to["url"])}"/></hls>'
        elif to.get('dashboard'):
            page = to.get('page')
            new_tab = to.get('newTab', True)
            hls = ' onw="1"' if new_tab else ''
            hl = {'idf': 1, 'so': 2, 'lt': 1, 'tid': to['dashboard'], 'ttp': 55, 'navpage': page, 'np': page,
                  'psf': 1 if to.get('passFilterPanel', True) else 0,
                  'pics': 1 if to.get('passVizSelections', True) else 0, 'aopam': 2, 'dtxt': tooltip,
                  'ftgs': ';'.join(to.get('filterPages') or [page])}
        else:
            hls = ''
            hl = {'idf': 1, 'aopam': 2, 'dtxt': tooltip, 'lt': 3, 'np': to['page'], 'so': 0}
        xml = f'<hls{hls}><hl {attrs(hl)}/></hls>'
        enc = xml.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&#34;')
        return self.edit([{**base, 'isHtmlEncoded': True,
                           'format': {'FormattingNavigation': {'Hyperlinks': enc, 'ResolvedHyperlinks': resolved}}}],
                         [node_key])

    def format_text(self, field_key, node_key, fmt):
        """Extra formats on a plain text box (not in the JS client as a helper; the same action the Lincoln fix sent
        2026-11-16): e.g. {'FormattingPatterns': {'FillStyle': 1}} for no fill, {'FormattingAlignment': {'Horizontal': 3}}
        to right-align (1 left, 2 center, 3 right)."""
        return self.edit([{'act': 'format', 'unitKey': field_key, 'unitType': 106, 'formatType': 1, 'fieldKey': field_key,
                           'nodeKey': node_key, 'keyContext': '106\u001e' + node_key + '\u001e' + field_key,
                           'format': fmt}], [node_key])

    def insert_image(self, field_key, node_key, url, create_node=True, page_key='K53', name='Image', size_mode=3,
                     layout=None):
        f = {'fieldKey': field_key, 'fieldType': 2, 'nodeKey': node_key, 'treeType': 1, 'fieldName': name}
        acts = [{'act': 'addField', 'createNode': create_node, 'nodeKeyParent': page_key, **f},
                {'act': 'editField', 'fieldValue': url, **f},
                {'act': 'format', 'unitKey': field_key, 'unitType': 102, 'formatType': 1, 'fieldKey': field_key,
                 'nodeKey': node_key, 'keyContext': '102\u001e' + node_key + '\u001e' + field_key,
                 'format': {'FormattingSize': {'ImageSizeMode': size_mode}}}]
        if layout:
            acts.append(_layout_action(page_key, layout))
        return self.edit(acts, [page_key])

    _SHAPES = {'Line': ('Line', 'line'), 'Rectangle': ('Rectangle', 'rect'), 'Ellipse': ('Ellipse', 'ellipse'),
               'Triangle': ('Polygon', 'polygon'), 'Polygon': ('Polygon', 'polygon')}
    _SHAPE_DEFAULTS = {
        'Line': {'arrowStartType': 'LINE_ARROW', 'arrowEndType': 'LINE_ARROW', 'direction': 0},
        'Rectangle': {'p': 0, 'radius': 0}, 'Ellipse': {'p': 0, 'toggled': False},
        'Triangle': {'p': 0, 'pos': 0, 'count': 5, 'toggled': False, 'direction': 0},
        'Polygon': {'p': 0, 'pos': 0, 'count': 5, 'toggled': False, 'direction': 0}}

    def insert_shape(self, field_key, node_key, shape='Rectangle', create_node=True, page_key='K53', layout=None,
                     settings=None, fill='#8AC3FF', stroke='#35383A', stroke_width=1, opacity=None, dash=None):
        if shape not in self._SHAPES:
            raise ValueError('Unknown shape ' + shape)
        T = self._SHAPES[shape]
        style = [f'fill: {"none" if shape == "Line" else fill}', f'stroke: {stroke}', f'stroke-width: {js_num(stroke_width)}px']
        if opacity is not None:
            style.append(f'fill-opacity: {js_num(opacity)}')
        if dash:
            style.append(f'stroke-dasharray: {({"solid": "0", "dash": "6, 2", "dot": "2, 2"}).get(dash) or dash}')
        value = jdump({'t': T[0], 's': {**self._SHAPE_DEFAULTS[shape], **(settings or {})},
                       'e': f'<svg xmlns="http://www.w3.org/2000/svg"><defs/><{T[1]} style="{"; ".join(style)};"/></svg>',
                       'n': shape})
        f = {'fieldKey': field_key, 'fieldType': 1, 'nodeKey': node_key, 'treeType': 1, 'fieldName': shape}
        acts = [{'act': 'addField', 'createNode': create_node, 'nodeKeyParent': page_key, **f},
                {'act': 'editField', 'fieldValue': value, **f},
                {'act': 'format', 'unitKey': field_key, 'unitType': 101, 'formatType': 1, 'fieldKey': field_key,
                 'nodeKey': node_key, 'keyContext': '101\u001e' + node_key + '\u001e' + field_key,
                 'format': {'FormattingPatterns': {'FillStyle': 1}}}]
        if layout:
            acts.append(_layout_action(page_key, layout))
        return self.edit(acts, [page_key])

    # ---- chapters and pages ----
    def structure(self):
        d = self.server_json()['defn']
        chapters = []
        for l in d['layouts']:
            u = l['units']
            page_stack = next((k for k in u if u[k].get('n') == 'VisualizationsPanelStack'), None)
            pages = sorted((k for k in u if u[k].get('t') == 9 and u[k].get('pnk') == page_stack),
                           key=lambda k: u[k].get('chdidx', 0))
            chapters.append({'key': l['k'], 'title': l.get('title'), 'pageStack': page_stack,
                             'pages': [{'key': k, 'title': u[k].get('ttl')} for k in pages]})
        return {'root': d['root']['k'], 'chapters': chapters}

    def add_page(self, page_key, page_stack, proto, viz_key, title=None, index=1):
        self.edit([{'act': 'addPanel', 'nodeKey': page_key, 'titlePattern': 1, 'parentKey': page_stack, 'index': index},
                   {'act': 'copyUnit', 'unitKey': proto, 'unitType': 521, 'newKey': viz_key, 'toKey': page_key},
                   _layout_action(page_key, {'t': 'b', 'o': 'h', 'children': [{'t': 'c', 'f': False, 'l': 100, 'k': viz_key}]}),
                   {'act': 'setCurrentPanel', 'unitKey': page_key}], [page_key])
        if title:
            self.rename_page(page_key, title)

    def set_current_panel(self, page_key):
        return self.edit([{'act': 'setCurrentPanel', 'unitKey': page_key}], [page_key])

    def rename_chapter(self, chapter_key, title):
        return self.edit([{'act': 'format', 'unitKey': chapter_key, 'unitType': 1, 'formatType': 1,
                           'format': {'FormattingView': {'Title': title}}}], [chapter_key])

    def rename_page(self, page_key, title):
        return self.edit([{'act': 'format', 'unitKey': page_key, 'unitType': 9, 'formatType': 1,
                           'format': {'FormattingView': {'Title': title}}}], [page_key])

    # ---- Auto Summary and saving ----
    def enable_auto_summary(self, instruction=AUTO_SUMMARY_INSTRUCTION, key_start=0):
        j = self.server_json()
        all_units = {}
        for l in j['defn']['layouts']:
            all_units.update(l['units'])
        used = [int(k[1:]) for k in re.findall(r'\bW\d+\b', jdump(j))]
        nxt = max([key_start - 1] + used) + 1
        done = []
        for page_key, page in list(all_units.items()):
            if page.get('t') != 9 or (all_units.get(page.get('pnk')) or {}).get('n') != 'VisualizationsPanelStack':
                continue
            groups = [k for k, u in all_units.items() if u.get('t') == 11 and u.get('pnk') == page_key]
            kids = [(k, u) for k, u in all_units.items() if u.get('pnk') == page_key or u.get('pnk') in groups]
            if any(u.get('t') == 8 and 'NLG one click' in (u.get('ttl') or '') for _, u in kids):
                continue
            sources = [k for k, u in kids if u.get('t') in (521, 522)]
            if not sources:
                continue
            stack, panel, viz = f'W{nxt}', f'W{nxt + 1}', f'W{nxt + 2}'
            nxt += 3
            layout = dict(page.get('layoutXML') or {'t': 'b', 'o': 'h', 'children': [
                {'t': 'c', 'k': k, 'l': 100 // len(sources), 'f': False} for k in sources]})
            layout['ifwChildren'] = list(layout.get('ifwChildren') or []) + [
                {'fixed': '0', 'k': stack, 't': 'flc', 'hidden': 0, 'width': '50|174px', 'height': '50|322px',
                 'left': '25|87px', 'top': '25|161px'}]
            cfg = {'instruction': instruction, 'hasFormatInstruction': False, 'preDefinedNLGInInfoWindow': True,
                   'recommendations': [{'vizId': 'nk-re-' + k, 'skipCalculation': True, 'removeDataLimit': True,
                                        'algorithms': {}} for k in sources]}

            def W(fmt):
                return {'act': 'format', 'unitKey': stack, 'unitType': 8, 'formatType': 1, 'format': fmt}
            self.edit([
                {'act': 'addNewPanelStack', 'parentPanelKey': page_key, 'nodeKey': stack, 'isSelectorPanel': False,
                 'isFormPanel': False, 'isInfoWindow': True},
                _layout_action(page_key, layout),
                {'act': 'addPanel', 'nodeKey': panel, 'titlePattern': 0, 'parentKey': stack, 'index': 0,
                 'isNavigationPanel': False},
                {'act': 'copyUnit', 'unitKey': 'K51', 'unitType': 521, 'newKey': viz, 'toKey': panel},
                _layout_action(panel, {'t': 'b', 'o': 'h', 'children': [{'t': 'c', 'f': False, 'l': 100, 'k': viz}],
                                       'floatChildren': [], 'ifwChildren': [],
                                       'canvasSize': {'sizeType': 1, 'containerLocked': True, 'sizeSetting': None}}),
                _drop_zones(viz, 7),
                {'act': 'format', 'unitKey': viz, 'unitType': 521, 'formatType': 1, 'format': {
                    'Visualization': {'VisualizationsEnabled': -1, 'ViewMode': 51, 'SelectedVisualization': 'AutoNarratives',
                                      'VisualizationList': 'AutoNarratives', 'IPhoneVisualization': '',
                                      'IPadVisualization': '', 'APhoneVisualization': '', 'ATabletVisualization': '',
                                      'ReturnBinaryResult': False},
                    'FormattingWidget': {'ClassName': CUSTOM_VIS_CLASS, 'Enable': 1,
                                         'WidgetProps': '<props><widgetProps><fmt><cvp><autoNarrativeAutoRefresh value="true" />'
                                                        '<isPredefinedNLG value="true"/><preDefinedNLGShowInConsumption value="true"/>'
                                                        '</cvp></fmt></widgetProps></props>'},
                    'FormattingView': {'ShowTitleBar': 0, 'ShowWidgetTitleBar': 0}}},
                _incremental_fetch_off(viz),
                {'act': 'changeGridDisplayMode', 'nodeKey': viz, 'displayMode': 1},
                {'act': 'setProperty', 'nodeKey': viz, 'prs': 'Visualization', 'pri': 17,
                 'v': jdump(cfg).replace('"', '&quot;'), 'isInsertingPredefinedNLG': True},
                {'act': 'setGridPropsRMs', 'nodeKey': viz, 'rfMaps': [{'key': 'nk-re-' + k, 'value': k} for k in sources]},
                {'act': 'setNLGSources', 'nodeKey': viz, 'associatedNodes': sources},
                {'act': 'format', 'unitKey': viz, 'unitType': 522, 'formatType': 1,
                 'format': {'FormattingOrder': {'ZIndex': 2}, 'FormattingView': {'WindowState': 2}}},
                W({'FormattingBorder': {'TopStyle': 0, 'RightStyle': 0, 'BottomStyle': 0, 'LeftStyle': 0}}),
                W({'FormattingView': {'StyleForSwitchingPanel': 6}}), W({'FormattingView': {'TitleBarDisplay': 1}}),
                W({'FormattingView': {'UseAsInformationWindow': 1}}), W({'FormattingView': {'TabCloseToDismissInfoWindow': 0}}),
                W({'FormattingSelector': {'IndependentNodeSelector': 0}}),
                W({'FormattingView': {'Title': 'Information Window 999999 (NLG one click)'}})], [page_key])
            done.append({'pageKey': page_key, 'stack': stack, 'viz': viz, 'sources': sources})
        return done

    def save_as(self, name, folder_id, auto_summary=True, overwrite=False):
        if auto_summary:
            self.enable_auto_summary()
        body = {'name': name, 'folderId': folder_id, 'saveAsTemplate': False}
        if overwrite:
            body['overwrite'] = True
        return self.t.api('POST', f'/documents/{self.dashboard_id}/instances/{self.mid}/saveAs', body)

    def save(self, auto_summary=True):
        if auto_summary:
            self.enable_auto_summary()
        return self.t.api('POST', f'/documents/{self.dashboard_id}/instances/{self.mid}/save', {})
