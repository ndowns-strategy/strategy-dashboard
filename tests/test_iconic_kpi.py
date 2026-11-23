"""Spec checks and props for the Iconic KPI (reference/iconic-kpi-catalog.md)."""
import json
import unittest
from pathlib import Path

from sdc.constants import iconic_kpi_look
from sdc.spec import check_structure, expand_kpi_notes, tokens

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


    def test_notes_example_is_valid(self):
        self.assertEqual(check_structure(json.loads((ROOT / 'examples/kpi-notes-test.json').read_text())), [])

    def test_tokens(self):
        self.assertEqual(tokens('On Time % {[On Time %]}  with a Target of {[On-Time Target]}'),
                         ['On Time %', 'On-Time Target'])
        self.assertEqual(tokens('plain'), [])

    def test_notes_become_rich_text_on_the_cards(self):
        kpi = {'id': 'k', 'type': 'iconic_kpi', 'metrics': ['A', 'B', 'C'], 'columns': 3, 'box': [0, 7, 100, 17],
               'notes': {'A': 'x {[D]}', 'C': {'text': 'y', 'color': '#c1292f'}}}
        its = expand_kpi_notes({'pages': [{'id': 'p', 'items': [kpi]}]})['pages'][0]['items']
        self.assertEqual([i['id'] for i in its], ['k', 'k_note1', 'k_note2'])
        a, c = its[1], its[2]
        self.assertEqual((a['type'], a['align'], a['runs']), ('rich_text', 'center', [{'text': 'x {[D]}', 'size': 9}]))
        self.assertEqual(a['box'], [0, 19.58, 33.333, 4.42])        # first card: under its value
        self.assertEqual(c['box'][0], 66.667)                       # third card
        self.assertEqual(c['runs'][0]['color'], '#c1292f')

    def test_notes_two_rows(self):
        kpi = {'id': 'k', 'type': 'iconic_kpi', 'metrics': ['A', 'B', 'C'], 'columns': 2, 'box': [0, 30, 60, 34],
               'notes': {'C': 'z'}}
        note = expand_kpi_notes({'pages': [{'id': 'p', 'items': [kpi]}]})['pages'][0]['items'][1]
        self.assertEqual(note['box'], [0, 59.58, 30, 4.42])          # second row, first column

    def test_bad_notes(self):
        self.assertTrue(one(metric=None, metrics=['M'], notes={'X': 'not a metric of the item'}))
        self.assertTrue(one(metric=None, metrics=['M'], notes={'M': ''}))
        self.assertTrue(one(metric=None, metrics=['M'], card_layout='stacked', notes={'M': 'moves'}))
        auto = {'name': 'x', 'dataset': 'd', 'pages': [{'id': 'pg', 'layout': 'auto', 'items': [
            {'id': 'k', 'type': 'iconic_kpi', 'metrics': ['M'], 'notes': {'M': 'n'}, 'box': [0, 0, 50, 50]}]}]}
        self.assertTrue(any('free-form' in x for x in check_structure(auto)))


    def test_imt_example_is_valid(self):
        self.assertEqual(check_structure(json.loads((ROOT / 'examples/imt-advisor-kpis.json').read_text())), [])

    def test_note_runs_and_alignment(self):
        kpi = {'id': 'k', 'type': 'iconic_kpi', 'metrics': ['A'], 'card_alignment': 'left', 'box': [0, 0, 50, 20],
               'notes': {'A': {'runs': [{'text': '{[Chg]}', 'color': '#2E7D32'}, {'text': ' vs last year'}]}}}
        note = expand_kpi_notes({'pages': [{'id': 'p', 'items': [kpi]}]})['pages'][0]['items'][1]
        self.assertEqual(note['runs'], [{'size': 9, 'text': '{[Chg]}', 'color': '#2E7D32'}, {'size': 9, 'text': ' vs last year'}])
        self.assertEqual(note['align'], 'center')     # no trend: the plugin centers the card whatever cardAlignment says
        kpi['trend'] = 'Month'
        note = expand_kpi_notes({'pages': [{'id': 'p', 'items': [kpi]}]})['pages'][0]['items'][1]
        self.assertEqual(note['align'], 'left')

    def test_labels(self):
        self.assertEqual(one(metric=None, metrics=['M'], labels={'M': 'SALES'}), [])
        self.assertTrue(one(metric=None, metrics=['M'], labels={'X': 'SALES'}))
        self.assertTrue(one(metric=None, metrics=['M'], labels={'M': ''}))

    def test_derived_metrics_structure(self):
        base = {'name': 'x', 'dataset': 'd', 'pages': [{'id': 'pg', 'items': [
            {'id': 'k', 'type': 'iconic_kpi', 'metric': 'M', 'box': [0, 0, 50, 50]}]}]}
        self.assertEqual(check_structure({**base, 'derived_metrics': [{'name': 'D', 'formula': '[M] * 2', 'format': '#,##0'}]}), [])
        self.assertTrue(check_structure({**base, 'derived_metrics': [{'name': 'D'}]}))
        self.assertTrue(check_structure({**base, 'derived_metrics': [{'name': 'D[1]', 'formula': '1'}]}))


if __name__ == '__main__':
    unittest.main()
