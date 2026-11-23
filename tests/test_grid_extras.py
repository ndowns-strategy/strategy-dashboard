"""Spec checks for a ranked grid's labels, formats, sort, limit and thresholds (reference/grid-catalog.md "Ranked grid")."""
import json
import unittest
from pathlib import Path

from sdc.session import metric_qual_expr
from sdc.spec import check_structure

ROOT = Path(__file__).parent.parent


def grid(**fields):
    it = {'id': 'g', 'type': 'grid', 'rows': ['Advisor', 'Producer Level'], 'metrics': ['Rank', 'YTD', 'Prior', 'Change'],
          'box': [0, 0, 100, 50], **fields}
    kpi = {'id': 'k', 'type': 'iconic_kpi', 'metric': 'YTD', 'box': [0, 60, 20, 20]}
    return check_structure({'name': 'x', 'dataset': 'd', 'pages': [{'id': 'p', 'items': [kpi, it]}]})


class GridExtras(unittest.TestCase):
    def test_imt_example_is_valid(self):
        self.assertEqual(check_structure(json.loads((ROOT / 'examples/imt-advisor-kpis.json').read_text())), [])

    def test_ranked_grid(self):
        self.assertEqual(grid(
            labels={'Producer Level': 'Level', 'Rank': '#'}, number_formats={'YTD': '$#,##0.0,,"M"'},
            sort={'metric': 'YTD', 'ascending': False}, limit={'metric': 'Rank', 'op': '<=', 'value': 15},
            thresholds=[{'on': 'Producer Level', 'elements': {'Platinum': '#333399'}},
                        {'on': 'Change', 'when': {'metric': 'Prior', 'op': '=', 'value': 0}, 'replace_text': 'new'},
                        {'on': 'Change', 'bands': [{'font': '#FF0000', 'ceil': 0}, {'font': '#008000', 'flr': 0}]}]), [])

    def test_bad_fields(self):
        self.assertTrue(grid(labels={'Firm': 'x'}))                                   # not on the grid
        self.assertTrue(grid(number_formats={'Advisor': '0'}))                        # not a metric of the grid
        self.assertTrue(grid(limit={'metric': 'Rank', 'op': '~', 'value': 15}))
        self.assertTrue(grid(limit={'metric': 'Rank', 'value': 'top'}))
        self.assertTrue(grid(thresholds=[{'on': 'Change'}]))                          # no elements/bands/when
        self.assertTrue(grid(thresholds=[{'on': 'Change', 'when': {'metric': 'Prior', 'op': '=', 'value': 0}}]))
        self.assertTrue(grid(thresholds=[{'on': 'Firm', 'elements': {'A': '#000000'}}]))

    def test_metric_qual_expr(self):
        self.assertEqual(metric_qual_expr('M1', 'Rank', '<=', 15),
                         '<exp><nd et="14" fn="19"><nds><nd et="10" dmt="7" fn="11" node="0"><m did="M1" n="Rank"></m>'
                         '<cs><c v="15" dtp="5"></c></cs></nd></nds></nd></exp>')
        with self.assertRaises(ValueError):
            metric_qual_expr('M1', 'Rank', 'top', 15)


if __name__ == '__main__':
    unittest.main()
