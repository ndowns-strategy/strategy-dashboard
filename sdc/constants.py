"""Constants recorded from the Library editor. Mirrors the top of strategy-dashboard-client.js; the comments there
(and reference/*.md) explain each value."""

APP_ID = 'C2B2023642F6753A2EF159A75E0CFF29'          # applicationId the Library app sends on studio.strategy.com
BLANK_TEMPLATE = '4802DE4C4C18F434C75BFA84EC8A5E4B'   # what a new draft is built from (page K53, prototype K51, grid K52)
UNIT = {'attribute': 12, 'metric': 4}
METRIC_NAMES = '00000000000000000000000000000000'     # the "Metric Names" pseudo-object (Color By metrics)

# Percent of page height setFreeformLayout adds to every text box (a box sized exactly to its text is cut off).
TEXT_HEIGHT_PAD = 2

ZONE = {'rows': 1, 'columns': 2, 'xAxis': 3, 'yAxis': 4, 'breakBy': 5, 'sliceBy': 6, 'colorBy': 7, 'sizeBy': 8,
        'tooltip': 9, 'angle': 10}
KPI_ZONE = {'metric': 19, 'trend': 20, 'breakBy': 5}
CMP_ZONE = {'actual': 3, 'target': 4, 'breakBy': 5, 'trend': 6}
MM_ZONE = {'metrics': 3, 'trend': 5}
DONUT_ZONE = {'angle': 3, 'colorBy': 4, 'slice': 5, 'target': 6, 'breakBy': 7}
DONUT_LABEL = {'value': 2, 'text': 4, 'textAndValue': 6}
SELECTOR_STYLE = {'dropDown': 0, 'slider': 1, 'listBox': 2, 'radio': 3, 'checkBoxes': 4, 'buttonBar': 5, 'linkBar': 6,
                  'searchBox': 9}

GRAPH_MATRIX_CLASS = 'com.microstrategy.flex.viewer.GraphMatrixViewer'
KPI_CARD_CLASS = 'com.microstrategy.web.vf.viewer.KPICardApplicationViewer'
CUSTOM_VIS_CLASS = 'com.microstrategy.web.vf.viewer.CustomVisApplicationViewer'

AUTO_SUMMARY_INSTRUCTION = (
    'Analyze and summarize the overall content of the page. If metrics are available on the page, analyze and '
    'summarize the overall content. Sort the data to identify top and bottom performers based on key metrics. Highlight '
    'trends, patterns, and anomalies, and generate actionable insights. If no metrics are found, skip calculation and '
    'summarize the content.')

# Chart types: Shape + visType (+ Subtype) for GraphMatrix charts.
VIS = {
    'bar': {'shape': 'Bar', 'visType': 70},
    'hbar': {'shape': 'Bar', 'visType': 71},
    'line': {'shape': 'Line', 'visType': 72},
    'area': {'shape': 'Area', 'visType': 74},
    'pie': {'shape': 'Pie', 'visType': 61},
    'ring': {'shape': 'Ring', 'visType': 62},
    'pctHbar': {'shape': 'Bar', 'visType': 11},
    'stackedBar': {'shape': 'Bar', 'visType': 6, 'subtype': 'Stacked'},
    'hbarStacked': {'shape': 'Bar', 'visType': 9, 'subtype': 'Stacked'},
    'areaStacked': {'shape': 'Area', 'visType': 30, 'subtype': 'Stacked'},
    'scatter': {'shape': 'Circle', 'visType': 21},
    'combo': {'shape': 'Bar', 'visType': 57, 'subtype': 'Stacked'},
    'clusteredBar': {'shape': 'Bar', 'visType': 7, 'subtype': 'Clustered'},    # Metric Names on Color By + Break By
    'clusteredHbar': {'shape': 'Bar', 'visType': 10, 'subtype': 'Clustered'},
}

# GraphMatrix chart look (reference/pie-catalog.md; Library's mstrmojo.gm enums). Mirrors LEGEND_SLOT etc. in the JS client.
LEGEND_SLOT = {'right': {'top': 1, 'middle': 2, 'bottom': 3}, 'left': {'top': 4, 'middle': 5, 'bottom': 6},
               'top': {'left': 9, 'center': 10, 'right': 11}, 'bottom': {'left': 12, 'center': 13, 'right': 14}}
LEGEND_SHAPES = ('circle', 'square', 'roundedRectangle', 'line')          # lgdItmShp
DATA_LABEL = {1: 'Hide', 2: 'Show only values', 4: 'Show only text', 6: 'Show both text value', 8: 'Show only percent',
              10: 'Show both value percent', 12: 'Show both text percent', 14: 'Show text value percent'}
DATA_LABEL_BIT = {'value': 2, 'text': 4, 'percent': 8}
LEADER_LINE = {'auto': 1, 'show': 2, 'hide': 3}                          # pdlll


def chart_look(legend=None, data_labels=None, leader_lines=None, marker_size=None):
    """GraphMatrix props from friendly names (same output as chartLook() in the JS client)."""
    from .util import js_num
    p = {}
    if legend is False:
        p['LegendVisibleness'] = 'Hide'
    elif legend:
        p['LegendVisibleness'] = 'Show'
        pos = legend.get('position')
        if pos:
            side = LEGEND_SLOT.get(pos)
            if not side:
                raise ValueError('legend position must be left, right, top or bottom')
            align = legend.get('align') or ('top' if pos in ('left', 'right') else 'center')
            if align not in side:
                raise ValueError(f'legend align for {pos} must be one of {", ".join(side)}')
            p['LegendPosition'] = str(side[align])
        if legend.get('title') is False:
            p['LegendTitleHide'] = 'true'
        elif legend.get('title') is True:
            p['LegendTitleHide'] = 'false'
        if legend.get('shape'):
            if legend['shape'] not in LEGEND_SHAPES:
                raise ValueError('legend shape must be one of ' + ', '.join(LEGEND_SHAPES))
            p['lgdItmShp'] = legend['shape']
    if data_labels == 'hide' or data_labels == []:
        p['DataLabel'] = 'Hide'
    elif data_labels:
        code = 0
        for k in data_labels:
            code |= DATA_LABEL_BIT[k]
        p['DataLabel'] = DATA_LABEL[code]
    if leader_lines:
        p['pdlll'] = str(LEADER_LINE[leader_lines])
    if marker_size is not None:
        p['SizeType'] = 'Manual'
        p['SizeValue'] = js_num(marker_size)
    return p


# Iconic KPI (ImageEnhancedKPI) look (reference/iconic-kpi-catalog.md). Mirrors iconicKpiLook() in the JS client.
TREND_SHAPES = ('area', 'line', 'bar', 'none')                         # trendShape
KPI_CHANGE = {'percent': 'percentValue', 'amount': 'numericValue'}    # trendIndicatorValueType
KPI_CONTENT = {'all': 'all', 'nameAndValue': 'label'}                  # textContentType
KPI_LAYOUT = {'grid': 0, 'stacked': 1, 'horizontal': 2, 'vertical': 3}  # layoutType
KPI_ALIGN = ('left', 'middle', 'right')                                # cardAlignment


def iconic_kpi_look(icon=None, tooltip=None, trend=None, previous_value_label=None, reference_line=None, change=None,
                    fill_opacity=None, metric_id=None, content=None, layout=None, columns=None, alignment=None,
                    background=None):
    """cvp properties for an Iconic KPI from friendly names (same output as iconicKpiLook() in the JS client).
    change: 'percent' | 'amount' | False. reference_line: {value, label='Target', color='#35383A', style='1pt dashed'}."""
    p = {}
    if icon is not None:
        p['showIcon'] = bool(icon)
    if tooltip is not None:
        p['metricTooltipEnabled'] = bool(tooltip)
    if trend is not None:
        if trend not in TREND_SHAPES:
            raise ValueError('trend must be one of ' + ', '.join(TREND_SHAPES))
        p['trendShape'] = trend
    if previous_value_label is not None:
        p['secondaryMetricName'] = previous_value_label
    if reference_line:
        if not metric_id:
            raise ValueError('referenceLine needs metricId')
        from .util import js_num
        v = js_num(reference_line['value'])
        label = reference_line['label'] if reference_line.get('label') is not None else 'Target'
        color = reference_line.get('color') or '#35383A'
        p['createdReferenceLines'] = {metric_id: {
            'value': v, 'label': label,
            'font': {'fontFamily': 'Open Sans', 'style': [False, False, False, False], 'size': 9, 'color': color},
            'line': {'shape': reference_line.get('style') or '1pt dashed', 'color': color}}}
        p['referenceLineConstantValue'] = v
        p['referenceLineLabel'] = label
    if change is False:
        p['trendIndicatorEnabled'] = False
    elif change is not None:
        if change not in KPI_CHANGE:
            raise ValueError('change must be percent, amount or false')
        p['trendIndicatorEnabled'] = True
        p['trendIndicatorValueType'] = KPI_CHANGE[change]
    if fill_opacity is not None:
        p['trendFillOpacity'] = fill_opacity
    if content is not None:
        if content not in KPI_CONTENT:
            raise ValueError('content must be all or nameAndValue')
        p['textContentType'] = KPI_CONTENT[content]
    if layout is not None:
        if layout not in KPI_LAYOUT:
            raise ValueError('layout must be one of ' + ', '.join(KPI_LAYOUT))
        p['layoutType'] = KPI_LAYOUT[layout]
    if columns is not None:
        from .util import js_num
        p['gridColumnCount'] = js_num(columns)
    if alignment is not None:
        if alignment not in KPI_ALIGN:
            raise ValueError('alignment must be left, middle or right')
        p['cardAlignment'] = alignment
    if background:
        p['areaFillColor'] = background['color']
        p['areaFillOpacity'] = background['opacity'] if background.get('opacity') is not None else 100
    return p
