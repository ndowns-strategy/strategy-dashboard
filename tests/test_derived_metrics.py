"""check_data for derived metrics: formula names resolve and the new name becomes usable."""
import unittest

from sdc.spec import Names, check_data


def names():
    return Names({'attributes': [{'name': 'Producer Category', 'id': 'A1'}],
                  'metrics': [{'name': 'Advisor Count', 'id': 'M1'}]})


class DerivedMetrics(unittest.TestCase):
    def spec(self, dms, metric):
        return {'derived_metrics': dms, 'pages': [{'id': 'p', 'items': [
            {'id': 'k', 'type': 'iconic_kpi', 'metric': metric, 'box': [0, 0, 50, 50]}]}]}

    def test_new_name_resolves(self):
        dm = {'name': 'Active Producers', 'formula': 'Sum(If([Producer Category]@ID = "Active Producer", 1, 0))'}
        self.assertEqual(check_data(self.spec([dm], 'Active Producers'), names()), [])

    def test_unknown_formula_name(self):
        p = check_data(self.spec([{'name': 'D', 'formula': '[Advisor Cnt] * 2'}], 'D'), names())
        self.assertTrue(any('Advisor Cnt' in x for x in p))

    def test_name_clash(self):
        p = check_data(self.spec([{'name': 'Advisor Count', 'formula': '[Advisor Count] * 2'}], 'Advisor Count'), names())
        self.assertTrue(any('already exists' in x for x in p))


if __name__ == '__main__':
    unittest.main()
