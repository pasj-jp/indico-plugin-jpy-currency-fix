from decimal import Decimal
import sys
import types


def _ensure_indico_stubs():
    try:
        import indico.util.i18n  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    indico_mod = sys.modules.setdefault('indico', types.ModuleType('indico'))
    util_mod = sys.modules.setdefault('indico.util', types.ModuleType('indico.util'))
    indico_mod.util = util_mod

    i18n_mod = types.ModuleType('indico.util.i18n')
    i18n_mod.make_bound_gettext = lambda _name: (lambda s: s)
    util_mod.i18n = i18n_mod
    sys.modules['indico.util.i18n'] = i18n_mod

    date_time_mod = types.ModuleType('indico.util.date_time')
    date_time_mod.format_number = lambda val, locale=None: f'num:{val}:{locale}'
    date_time_mod.format_currency = lambda val, cur, locale=None: f'cur:{val}:{cur}:{locale}'
    util_mod.date_time = date_time_mod
    sys.modules['indico.util.date_time'] = date_time_mod


_ensure_indico_stubs()

from indico_jpy_currency_fix.util import (  # noqa: E402
    format_stats_number,
    format_transaction_amount,
    is_whole_number,
    is_zero_decimal_currency,
    normalize_currencies,
    patch_transaction_details_html,
)


def test_normalize_currencies():
    assert normalize_currencies([' jpy ', 'USD', 'jpy', '', 'krw']) == ['JPY', 'USD', 'KRW']
    assert normalize_currencies([]) == []
    assert normalize_currencies(None) == []


def test_is_zero_decimal_currency():
    assert is_zero_decimal_currency('JPY', ['JPY'])
    assert is_zero_decimal_currency('jpy', ['JPY', 'KRW'])
    assert not is_zero_decimal_currency('USD', ['JPY'])
    assert not is_zero_decimal_currency('', ['JPY'])
    assert not is_zero_decimal_currency('JPY', [])


def test_is_whole_number():
    assert is_whole_number(Decimal('4000.00'))
    assert is_whole_number(4000.0)
    assert is_whole_number('4000.00')
    assert not is_whole_number(Decimal('4000.50'))
    assert not is_whole_number('invalid')


def test_format_transaction_amount():
    assert format_transaction_amount(Decimal('10000.00'), 'JPY', ['JPY']) == '10000'
    assert format_transaction_amount(Decimal('10000.50'), 'JPY', ['JPY'], preserve_nonzero_decimals=True) == '10000.50'
    assert format_transaction_amount(Decimal('10000.50'), 'JPY', ['JPY'], preserve_nonzero_decimals=False) == '10000'
    assert format_transaction_amount(Decimal('10000.00'), 'USD', ['JPY']) == '10000.00'


def test_patch_transaction_details_html():
    raw_html = '<dl class="i-data-list">\n  <dt>Amount</dt>\n  <dd>10000.00 JPY</dd>\n  <dt>Paid amount</dt>\n  <dd>¥10,000</dd>\n</dl>'
    patched = patch_transaction_details_html(raw_html, Decimal('10000.00'), 'JPY', ['JPY'])
    assert '<dd>10000 JPY</dd>' in patched
    assert '<dd>¥10,000</dd>' in patched

    # Non-target currency stays untouched
    usd_html = '<dl><dt>Amount</dt><dd>100.00 USD</dd></dl>'
    assert patch_transaction_details_html(usd_html, Decimal('100.00'), 'USD', ['JPY']) == usd_html

    # Non-zero decimal stays untouched when preserve_nonzero_decimals=True
    frac_html = '<dl><dt>Amount</dt><dd>10000.50 JPY</dd></dl>'
    assert patch_transaction_details_html(frac_html, Decimal('10000.50'), 'JPY', ['JPY'], preserve_nonzero_decimals=True) == frac_html


def test_format_stats_number():
    fake_date_time = types.ModuleType('indico.util.date_time')
    fake_date_time.format_number = lambda val, locale=None: f'num:{val}:{locale}'
    fake_date_time.format_currency = lambda val, cur, locale=None: f'cur:{val}:{cur}:{locale}'

    old = sys.modules.get('indico.util.date_time')
    sys.modules['indico.util.date_time'] = fake_date_time
    try:
        assert format_stats_number(4000.0, 'JPY', ['JPY'], locale='ja') == 'num:4000:ja'
        assert format_stats_number(4000.5, 'JPY', ['JPY'], locale='ja', preserve_nonzero_decimals=True) == 'cur:4000.5::ja'
        assert format_stats_number(4000.5, 'JPY', ['JPY'], locale='ja', preserve_nonzero_decimals=False) == 'num:4000:ja'
        assert format_stats_number(4000.0, 'USD', ['JPY'], locale='ja') == 'cur:4000.0::ja'
    finally:
        if old is None:
            sys.modules.pop('indico.util.date_time', None)
        else:
            sys.modules['indico.util.date_time'] = old
