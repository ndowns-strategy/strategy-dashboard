"""Spec checks and props for the chart look fields (reference/pie-catalog.md)."""
import json
import unittest
from pathlib import Path

from sdc.constants import chart_look
from sdc.spec import check_structure

ROOT = Path(__file__).parent.parent


def one(**fields):
    it = {'id': 'p', 'type': 'chart', 'vis': 'pie', 'zones': {'angle': 'M', 'sliceBy': 'A'}, 'box': [0, 0, 50, 50], **fields}
    return check_structure({'name': 'x', 'dataset': 'd', 'pages': [{'id': 'pg', 'items': [it]}]})


class ChartLook(unittest.TestCase):
    def test_example_is_valid(self):
        self.assertEqual(check_structure(json.loads((ROOT / 'examples/pie-catalog-test.json').read_text())), [])

    def test_source_chart_v3(self):
        self.assertEqual(chart_look({'position': 'left', 'align': 'bottom', 'shape': 'roundedRectangle', 'title': True},
                                    None, None, 0.8),
                         {'LegendVisibleness': 'Show', 'LegendPosition': '6', 'LegendTitleHide': 'false',
                          'lgdItmShp': 'roundedRectangle', 'SizeType': 'Manual', 'SizeValue': '0.8'})

    def test_legend_false_hides(self):
        self.assertEqual(chart_look(False), {'LegendVisibleness': 'Hide'})

    def test_bad_values(self):
        self.assertTrue(one(legend={'position': 'top', 'align': 'middle'}))
        self.assertTrue(one(legend={'shape': 'star'}))
        self.assertTrue(one(data_labels=['text', 'total']))
        self.assertTrue(one(marker_size=1.5))
        self.assertTrue(one(leader_lines='sometimes'))
        self.assertTrue(one(vis='bar', zones={'xAxis': 'A', 'yAxis': 'M'}, leader_lines='show'))

    def test_good_values(self):
        self.assertEqual(one(legend={'position': 'bottom', 'align': 'right', 'shape': 'line', 'title': False},
                             data_labels='hide', leader_lines='hide', marker_size=1), [])


if __name__ == '__main__':
    unittest.main()
