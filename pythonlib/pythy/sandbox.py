"""
Pythy sandbox compatibility module.
Provides mock hooks for web requests without depending on deprecated standard
library features (such as 'imp'). Real security and isolation is enforced at
the container level.
"""

import sys
import re
import io
from collections.abc import Mapping

_fixed_currencies = {
    '100:EUR': '{lhs: "100 U.S. dollars",rhs: "75.7002271 Euros",error: "",icc: true}',
    '89.32:GBP': '{lhs: "89.32 U.S. dollars",rhs: "58.4669765 British pounds",error: "",icc: true}',
    '1.0:JPY': '{lhs: "1.00 U.S. dollar",rhs: "93.3096949 Japanese yen",error: "",icc: true}',
    '99:UAH': '{lhs: "99 U.S. dollars",rhs: "805.926408 Ukrainian grivnas",error: "",icc: true}'
}

def _safe_urlopen(url, *args, **kwargs):
    url_str = getattr(url, 'full_url', str(url))
    m = re.match(r"http://www.google.com/ig/calculator\?(?:hl=en&)?q=([0-9.]+)USD=\?(.*)", url_str)
    if m:
        groups = m.groups()
        amount = groups[0]
        currency = groups[1]
        key = amount + ':' + currency
        if key in _fixed_currencies:
            return io.StringIO(_fixed_currencies[key])
        else:
            return io.StringIO('{lhs: "100 U.S. dollars",rhs: "75.7002271 Euros",error: "",icc: true}')
    elif re.match(r"http://people.cs.vt.edu/allevato/cs2984-python/project2/words.txt", url_str):
        return io.StringIO('sampleword\n')
    else:
        raise AssertionError(f"The URL you requested was formatted incorrectly or not allowed: '{url_str}'")

_sandboxed_urlopen = _safe_urlopen

def call_urlopen(url, *args, **kwargs):
    return _sandboxed_urlopen(url, *args, **kwargs)

def set_urlopen(target):
    """
    Configures the mock handler for urllib.request.urlopen.

    Args:
        target: May be:
            1. A mapping (dict) of {url_string: mock_response_text_or_bytes}.
            2. A callable (function) accepting `url, *args, **kwargs` returning
               a file-like object (e.g., io.StringIO or io.BytesIO).
            3. None to reset to default built-in URL mocks.
    """
    global _sandboxed_urlopen

    if isinstance(target, Mapping):
        url_dict = dict(target)

        def _dict_urlopen(url, *args, **kwargs):
            url_str = getattr(url, 'full_url', str(url))
            if url_str in url_dict:
                val = url_dict[url_str]
                if isinstance(val, bytes):
                    return io.BytesIO(val)
                return io.StringIO(str(val))
            # Fall back to default course mocks or raise informative error
            try:
                return _safe_urlopen(url, *args, **kwargs)
            except AssertionError:
                raise AssertionError(
                    f"Requested URL '{url_str}' was not found in the configured mock URL dictionary."
                )

        _sandboxed_urlopen = _dict_urlopen
    elif callable(target):
        _sandboxed_urlopen = target
    elif target is None:
        _sandboxed_urlopen = _safe_urlopen
    else:
        raise TypeError(
            f"set_urlopen expects a dict/mapping, a callable function, or None (got {type(target).__name__})"
        )

try:
    import urllib.request
    urllib.request.urlopen = call_urlopen
except Exception:
    pass
