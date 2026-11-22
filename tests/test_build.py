"""The spec checks and the builder, run offline against a fake server (no Library needed)."""
import copy
import json
import unittest
from pathlib import Path

from sdc.build import Builder
from sdc.spec import Names, SpecError, check_data, check_structure

ROOT = Path(__file__).parent.parent
SERVER = (Path(__file__).parent / 'fixtures' / 'server.json').read_text()
LINCOLN = json.loads((ROOT / 'examples' / 'lincoln.json').read_text())
ATTRS = ['Year Month', 'Product Line', 'Product Type', 'State Code']
METRICS = ['Premium Amount', 'Face Amount', 'Gross Deposits', 'Net Flows', 'Earned Premium', 'Withdrawals And Surrenders']
AVAILABLE = {'attributes': [{'name': n, 'id': f'A{i:031d}'} for i, n in enumerate(ATTRS)],
             'metrics': [{'name': n, 'id': f'M{i:031d}'} for i, n in enumerate(METRICS)]}


class FakeConn:
    def __init__(self):
        self.edits, self.apis, self.calls = [], [], 0

    def task(self, params):
        if params['taskId'] == 'mojoRWManipulation':
            e = json.loads(params['params'])
            self.edits.append(e)
            return '{"bs":"BS1"}'
        # Serve the fixture plus every page the build has added, as the real instance would.
        j = json.loads(SERVER)
        units = j['defn']['layouts'][0]['units']
        for e in self.edits:
            for a in e['actions']:
                if a.get('act') == 'addPanel':
                    units[a['nodeKey']] = {'t': 9, 'pnk': a['parentKey'], 'chdidx': a['index']}
                for k in ('newKey', 'fieldKey', 'nodeKey'):   # every key the build used shows up somewhere
                    if a.get(k):
                        j.setdefault('used', []).append(a[k])
        return json.dumps(j, separators=(',', ':'))

    def api(self, method, path, body=None):
        self.apis.append((method, path, body))
        if path.startswith('/v2/cubes/'):
            return {'definition': {'availableObjects': AVAILABLE}}
        if path == '/folders/myPersonalObjects':
            return [{'name': 'My Reports', 'id': 'FOLDER'}]
        if path.endswith('/saveAs'):
            return {'id': 'SAVED'}
        return {'mid': 'MID'}

    def search(self, name, object_type=None):
        return []

    def cube(self, ds):
        return self.api('GET', f'/v2/cubes/{ds}')

    def my_folder(self, name='My Reports'):
        return 'FOLDER'

    def new_dashboard(self, datasets=(), **kw):
        from sdc.session import Session
        self.api('POST', '/dossiers/draft/instances', {'datasets': list(datasets)})
        return Session(self, 'BLANK', 'MID', now=lambda: 1, key32=lambda: 'K' * 32)


def acts(conn):
    return [a for e in conn.edits for a in e['actions']]


class BuildLincoln(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = FakeConn()
        cls.result = Builder(cls.conn, copy.deepcopy(LINCOLN), log=lambda *_: None).run(verify=False)
        cls.acts = acts(cls.conn)

    def test_saved(self):
        self.assertEqual(self.result['id'], 'SAVED')
        save = [a for a in self.conn.apis if a[1].endswith('/saveAs')][0]
        self.assertEqual(save[2]['name'], LINCOLN['name'])

    def test_default_vizs_reused(self):
        # The draft's K52 and the new page's default visualization become the first KPI cards in place.
        conv = [a for a in self.acts if a.get('act') == 'updateTemplate'
                and a['actions'][0].get('act') == 'createDefaultDropZones' and a['actions'][0]['widgetType'] == 9]
        keys = [a['keyContext'] for a in conv]
        self.assertIn('K52', keys)
        copied = [a['newKey'] for a in self.acts if a.get('act') == 'copyUnit']
        self.assertNotIn('K52', copied)

    def test_freeform_layout_per_page(self):
        layouts = [a for a in self.acts if a.get('act') == 'format' and a.get('isJson')
                   and isinstance(a['format']['FormattingSize']['LayoutXML'].get('floatChildren'), dict)]
        self.assertEqual(len(layouts), 2)
        counts = [len(a['format']['FormattingSize']['LayoutXML']['floatChildren']['children']) for a in layouts]
        self.assertEqual(counts, [len(p['items']) for p in LINCOLN['pages']])

    def test_links_point_at_page_keys(self):
        links = [a['format']['FormattingNavigation']['Hyperlinks'] for a in self.acts
                 if a.get('act') == 'format' and 'FormattingNavigation' in a.get('format', {})]
        self.assertEqual(len(links), 2)
        self.assertIn('np=&#34;K53&#34;', links[1])          # Back to Home -> the first page
        self.assertNotIn('np=&#34;home&#34;', ''.join(links))

    def test_narrative_sources(self):
        nlg = [a for a in self.acts if a.get('act') == 'setNLGSources' and 'nk-re' not in str(a)]
        self.assertTrue(any(len(a['associatedNodes']) == 8 for a in nlg))

    def test_keys_unique(self):
        new = [a['newKey'] for a in self.acts if a.get('act') == 'copyUnit']
        fields = [a['fieldKey'] for a in self.acts if a.get('act') == 'addField']
        self.assertEqual(len(new + fields), len(set(new + fields)))


class SpecChecks(unittest.TestCase):
    def test_lincoln_is_clean(self):
        self.assertEqual(check_structure(LINCOLN), [])
        self.assertEqual(check_data(LINCOLN, Names(AVAILABLE)), [])

    def test_problems_found(self):
        bad = copy.deepcopy(LINCOLN)
        items = bad['pages'][1]['items']
        next(i for i in items if i['id'] == 'brief')['instruction'] = 'Say "hi"'
        next(i for i in items if i['id'] == 'page_title')['link'] = {'page': 'home'}
        next(i for i in items if i['id'] == 'by_line')['zones']['yAxis'] = 'Product Lines'
        next(i for i in items if i['id'] == 'bg')['box'] = [0, 0, 100, 120]
        p = check_structure(bad)
        self.assertTrue(any('double quotes' in x for x in p))
        self.assertTrue(any('links only work on plain text' in x for x in p))
        self.assertTrue(any('outside the page' in x for x in p))
        d = check_data(bad, Names(AVAILABLE))
        self.assertTrue(any("did you mean 'Product Line'" in x for x in d), d)

    def test_same_name_attribute_and_metric(self):
        av = {'attributes': [{'name': 'Annual Income', 'id': 'A1'}], 'metrics': [{'name': 'Annual Income', 'id': 'M1'}]}
        n = Names(av)
        with self.assertRaises(KeyError):
            n.resolve('Annual Income')
        self.assertEqual(n.resolve('metric:Annual Income'), ('M1', 4))
        self.assertEqual(n.resolve('Annual Income', 'attribute'), ('A1', 12))

    def test_missing_default_viz_candidate(self):
        bad = copy.deepcopy(LINCOLN)
        bad['pages'][0]['items'] = [i for i in bad['pages'][0]['items'] if i['type'] != 'kpi_card']
        self.assertTrue(any('needs at least one kpi_card' in x for x in check_structure(bad)))


if __name__ == '__main__':
    unittest.main()
