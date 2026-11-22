"""Small helpers that reproduce JavaScript's string and JSON output exactly.

The editor actions embed JSON and numbers inside strings, so Python must write them the way the JS client (and the
editor) does: no spaces after separators, 50 not 50.0, true not True. The parity tests compare against the JS client.
"""
import base64
import json
import math
import os
import re
from urllib.parse import quote


def js_num(x):
    """String(x) for a JS number: integral floats lose the '.0'."""
    if isinstance(x, bool):
        return 'true' if x else 'false'
    if isinstance(x, float):
        if math.isfinite(x) and x.is_integer() and abs(x) < 1e21:
            return str(int(x))
        return repr(x)
    return str(x)


def js_str(v):
    """String(v) for the values the helpers stringify."""
    if v is None:
        return 'null'
    if isinstance(v, (bool, int, float)):
        return js_num(v)
    return str(v)


def _norm(o):
    if isinstance(o, bool) or o is None:
        return o
    if isinstance(o, float) and math.isfinite(o) and o.is_integer():
        return int(o)
    if isinstance(o, dict):
        return {k: _norm(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_norm(v) for v in o]
    return o


def jdump(o):
    """JSON.stringify(o)."""
    return json.dumps(_norm(o), separators=(',', ':'), ensure_ascii=False)


def bgr(hex_color):
    """'#rrggbb' -> Strategy's BGR integer, as a string (wrap in int() where the JS wraps it in Number())."""
    h = hex_color.replace('#', '', 1)
    if len(h) == 3:
        h = ''.join(c + c for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return str(b * 65536 + g * 256 + r)


def esc_attr(v):
    """The JS helpers' XML attribute escape: & " < > (in that order)."""
    return js_str(v).replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


def parse_float_prefix(s, default):
    """parseFloat(s) || default."""
    m = re.match(r'\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?', str(s or ''))
    v = float(m.group(0)) if m else 0.0
    return v if v else default


def to_fixed_num(x, digits):
    """+x.toFixed(digits)."""
    return float(f'{x:.{digits}f}')


def encode_uri_component(s):
    return quote(s, safe="-_.!~*'()")


def rich_text_value(runs, align=None, header=None, list=None, indent=None):  # noqa: A002 (mirrors the JS option)
    """Rich Text field value: run texts joined by U+2446, then U+2446 U+2440 + base64(encodeURIComponent(Quill Delta))."""
    def block(r):
        return {k: r[k] for k in ('align', 'header', 'list', 'indent') if r.get(k) is not None}

    ops = []
    for r in runs:
        if r.get('text') == '\n':
            a = block(r)
            ops.append({'insert': '\n', 'attributes': a} if a else {'insert': '\n'})
            continue
        a = {'color': r.get('color') or '#35383a', 'size': 'size' + js_num(r.get('size') or 10),
             'font': r.get('font') or 'opensans'}
        for k in ('bold', 'italic', 'underline', 'strike'):
            if r.get(k):
                a[k] = True
        ops.append({'insert': r['text'], 'attributes': a})
    last = block({'align': align, 'header': header, 'list': list, 'indent': indent})
    ops.append({'insert': '\n', 'attributes': last} if last else {'insert': '\n'})
    b64 = base64.b64encode(encode_uri_component(jdump(ops)).encode('ascii')).decode('ascii')
    return '⑆'.join(o['insert'] for o in ops) + '⑆⑀' + b64


def random_key32():
    """32 hex characters, upper case (the editor's GUID-style keys)."""
    return os.urandom(16).hex().upper()
