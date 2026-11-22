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
