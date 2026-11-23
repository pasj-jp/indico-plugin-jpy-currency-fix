from decimal import Decimal, InvalidOperation
import re

try:
    from markupsafe import Markup
except ImportError:  # pragma: no cover - standalone test fallback
    Markup = None


def normalize_currencies(currencies):
    """Return an uppercase, deduplicated list of currency codes preserving order."""
    if not currencies:
        return []
    seen = set()
    result = []
    for item in currencies:
        code = str(item).strip().upper()
        if code and code not in seen:
            seen.add(code)
            result.append(code)
    return result


def is_zero_decimal_currency(currency, configured_currencies):
    """Return True if currency is in the configured zero-decimal currency list."""
    if not currency or not configured_currencies:
        return False
    return str(currency).strip().upper() in {c.upper() for c in configured_currencies}


def _to_decimal(amount):
    if isinstance(amount, Decimal):
        return amount
    try:
        return Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        return None


def is_whole_number(amount):
    """Return True if amount represents an integer value (e.g. 4000 or 4000.00)."""
    dec = _to_decimal(amount)
    if dec is None:
        return False
    return dec == dec.to_integral_value()


def format_transaction_amount(amount, currency, configured_currencies, preserve_nonzero_decimals=True):
    """Format a payment transaction amount string without trailing .00 when applicable."""
    if not is_zero_decimal_currency(currency, configured_currencies):
        return str(amount)

    dec = _to_decimal(amount)
    if dec is None:
        return str(amount)

    if dec == dec.to_integral_value():
        return str(int(dec))

    if not preserve_nonzero_decimals:
        return str(round(dec))

    return str(amount)


def patch_transaction_details_html(html, amount, currency, configured_currencies, preserve_nonzero_decimals=True):
    """Rewrite raw ``<dd>10000.00 JPY</dd>`` in rendered transaction details without template overrides."""
    formatted = format_transaction_amount(
        amount,
        currency,
        configured_currencies,
        preserve_nonzero_decimals=preserve_nonzero_decimals,
    )
    raw_amount = str(amount)
    if formatted == raw_amount:
        return html

    pattern = re.compile(rf'(>\s*){re.escape(raw_amount)}(\s+{re.escape(str(currency))}\s*<)')
    updated = pattern.sub(rf'\g<1>{formatted}\g<2>', str(html), count=1)
    if Markup is not None and isinstance(html, Markup):
        return Markup(updated)
    return updated


def format_stats_number(amount, currency, configured_currencies, locale=None, preserve_nonzero_decimals=True):
    """Format a registration stats currency cell using Indico's locale-aware helpers."""
    from indico.util.date_time import format_currency, format_number

    if not is_zero_decimal_currency(currency, configured_currencies):
        return format_currency(amount, '', locale=locale)

    dec = _to_decimal(amount)
    if dec is None:
        return format_currency(amount, '', locale=locale)

    if dec == dec.to_integral_value():
        return format_number(int(dec), locale=locale)

    if not preserve_nonzero_decimals:
        return format_number(round(dec), locale=locale)

    return format_currency(amount, '', locale=locale)
