# Indico JPY Currency Fix Plugin

Fixes trailing `.00` decimal display for `JPY` (and optionally other zero-decimal ISO 4217 currencies) in Indico **without overriding any Indico core HTML templates**:

1. **Registration form frontend (React)**: Patches `Intl.NumberFormat` on registration pages via `html-head` so Indico's hardcoded `minimumFractionDigits: 2, maximumFractionDigits: 2` does not force `.00` on `JPY` (e.g. `￥4,000` instead of `￥4,000.00`). Compatible with `CSP_ENABLED = True` and requires no Webpack/Node.js build step.
2. **Payment transaction details**: Wraps `PaymentTransaction.render_details` to strip `.00` from the rendered raw `Amount` (e.g. `10000 JPY` instead of `10000.00 JPY`), working across manual payments and payment plugins (such as Stripe) without shadowing `transaction_details.html`.
3. **Registration form stats**: Wraps Jinja's `format_currency` global on `event_registration.regform_stats` when currency is `''`, formatting currency cells with `regform.currency` via Indico's `format_number` (e.g. `4,000` instead of `4,000.00`) without shadowing `regform_stats.html`.

## Configuration

Configurable from the Indico admin **Plugins** settings page:

- **Zero-decimal currencies**: List of 3-letter ISO 4217 currency codes (one per line, default `JPY`).
- **Fix registration form (frontend)**: Toggle the React registration form fix.
- **Fix payment transaction details**: Toggle the payment transaction `Amount` formatting fix.
- **Fix registration form stats**: Toggle the registration stats table formatting fix.
- **Preserve non-zero decimals**: Keep decimal digits if an amount actually contains a non-zero fractional part (e.g. `4000.50`).

## Build & Installation

Build a wheel (no Node.js / Indico source checkout required):

```bash
pip wheel . --no-deps -w dist/
```

Install in your Indico Python environment and enable `jpy_currency_fix` in `indico.conf`:

```python
PLUGINS = {'jpy_currency_fix'}
```

Then restart `indico-uwsgi` (and `indico-celery` if needed).
