"""Spec checks and props for the Iconic KPI (reference/iconic-kpi-catalog.md)."""
import json
import unittest
from pathlib import Path

from sdc.constants import iconic_kpi_look
from sdc.spec import check_structure

ROOT = Path(__file__).parent.parent


def one(**fields):
    it = {'id': 'k', 'type': 'iconic_kpi', 'metric': 'M', 'trend': 'A', 'box': [0, 0, 50, 50], **fields}
    return check_structure({'name': 'x', 'dataset': 'd', 'pages': [{'id': 'pg', 'items': [it]}]})


class IconicKpi(unittest.TestCase):
    def test_example_is_valid(self):
        self.assertEqual(check_structure(json.loads((ROOT / 'examples/iconic-kpi-test.json').read_text())), [])

    def test_alone_on_a_page(self):
        # iconic_kpi can take over the page's default visualization, so a page of only Iconic KPIs is fine
        self.assertEqual(one(), [])

    def test_every_option(self):
        self.assertEqual(one(icon='payments-fill.svg', tooltip=False, trend_shape='none', previous_value_label='Prior Month',
                             reference_line={'value': 1000000}, change='amount', fill_opacity=40), [])
        self.assertEqual(one(icon=False, change=False), [])

    def test_bad_values(self):
        self.assertTrue(one(trend_shape='pie'))
        self.assertTrue(one(change='ratio'))
        self.assertTrue(one(icon='truck'))
        self.assertTrue(one(tooltip='yes'))
        self.assertTrue(one(reference_line={'value': 'high'}))
        self.assertTrue(one(fill_opacity=150))
        self.assertTrue(one(metric=None))
        self.assertTrue(any('trend_shape' in x for x in one(trend='area')))

    def test_no_title_bar(self):
        self.assertTrue(any('no title bar' in x for x in one(title_format={'align': 'center'})))

    def test_look(self):
        self.assertEqual(iconic_kpi_look(icon=False, trend='none', change='amount', previous_value_label='Prior Month'),
                         {'showIcon': False, 'trendShape': 'none', 'secondaryMetricName': 'Prior Month',
                          'trendIndicatorEnabled': True, 'trendIndicatorValueType': 'numericValue'})
        self.assertEqual(iconic_kpi_look(change=False), {'trendIndicatorEnabled': False})
        p = iconic_kpi_look(reference_line={'value': 1000000}, metric_id='M1')
        self.assertEqual(p['referenceLineConstantValue'], '1000000')
        self.assertEqual(p['createdReferenceLines']['M1']['line'], {'shape': '1pt dashed', 'color': '#35383A'})
        with self.assertRaises(ValueError):
            iconic_kpi_look(reference_line={'value': 1})   # needs the metric id


    def test_strip_example_is_valid(self):
        self.assertEqual(check_structure(json.loads((ROOT / 'examples/kpi-strip-test.json').read_text())), [])

    def test_strip_fields(self):
        ok = dict(metric=None, metrics=['M', 'N'], content='name_and_value', card_layout='grid', columns=2,
                  card_alignment='middle', background={'color': '#E8EEF9'}, cards={'N': {'background': '#ABABAB'}})
        self.assertEqual(one(**ok), [])
        self.assertTrue(one(**{**ok, 'content': 'label'}))
        self.assertTrue(one(**{**ok, 'card_layout': 'carousel'}))
        self.assertTrue(one(**{**ok, 'columns': 0}))
        self.assertTrue(one(**{**ok, 'cards': {'X': {'background': '#ABABAB'}}}))   # not one of the metrics
        self.assertTrue(one(**{**ok, 'cards': {'N': {'background': 'grey'}}}))
        self.assertTrue(one(**{**ok, 'background': {'color': '#ABABAB', 'opacity': 150}}))
        self.assertTrue(one(**{**ok, 'metric': 'M'}))   # metric and metrics together

    def test_background_defaults_to_full_opacity(self):
        self.assertEqual(iconic_kpi_look(background={'color': '#ABABAB'}),
                         {'areaFillColor': '#ABABAB', 'areaFillOpacity': 100})
        self.assertEqual(iconic_kpi_look(content='nameAndValue', layout='grid', columns=5, alignment='middle'),
                         {'textContentType': 'label', 'layoutType': 0, 'gridColumnCount': '5', 'cardAlignment': 'middle'})


if __name__ == '__main__':
    unittest.main()
