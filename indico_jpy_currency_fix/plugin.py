import functools

from flask import current_app, has_request_context, request
from flask_pluginengine import render_plugin_template
from jinja2 import pass_context

from indico.core.plugins import IndicoPlugin
from indico.modules.events.payment.models.transactions import PaymentTransaction

from indico_jpy_currency_fix import __version__
from indico_jpy_currency_fix.blueprint import blueprint
from indico_jpy_currency_fix.forms import SettingsForm
from indico_jpy_currency_fix.util import format_stats_number, normalize_currencies, patch_transaction_details_html


class JPYCurrencyFixPlugin(IndicoPlugin):
    """JPY Currency Fix

    Removes forced .00 decimal places for JPY (and configurable zero-decimal
    currencies) in registration forms, payment transaction details, and
    registration statistics tables without overriding Indico core HTML templates.
    """

    configurable = True
    settings_form = SettingsForm
    default_settings = {
        'currencies': ['JPY'],
        'fix_regform': True,
        'fix_transaction_details': True,
        'fix_regform_stats': True,
        'preserve_nonzero_decimals': True,
    }

    def init(self):
        super().init()
        self.template_hook('html-head', self._inject_head_script)
        self._patch_jinja_format_currency()
        self._patch_transaction_render_details()

    def get_blueprints(self):
        return blueprint

    def _inject_head_script(self, **kwargs):
        if not self.settings.get('fix_regform'):
            return ''
        if request.blueprint != 'event_registration':
            return ''
        currencies = normalize_currencies(self.settings.get('currencies'))
        if not currencies:
            return ''
        return render_plugin_template(
            'head_script.html',
            currencies=currencies,
            preserve_nonzero_decimals=bool(self.settings.get('preserve_nonzero_decimals')),
            version=__version__,
        )

    def _patch_jinja_format_currency(self):
        orig_format_currency = current_app.jinja_env.globals.get('format_currency')
        if orig_format_currency is None or getattr(orig_format_currency, '_jpy_currency_fix_wrapped', False):
            return

        @pass_context
        @functools.wraps(orig_format_currency)
        def _wrapped_format_currency(ctx, number, currency, locale=None):
            if (
                currency == ''
                and self.settings.get('fix_regform_stats')
                and has_request_context()
                and request.endpoint == 'event_registration.regform_stats'
            ):
                regform = ctx.get('regform')
                regform_currency = getattr(regform, 'currency', None)
                if regform_currency:
                    return format_stats_number(
                        number,
                        regform_currency,
                        self.settings.get('currencies'),
                        locale=locale,
                        preserve_nonzero_decimals=bool(self.settings.get('preserve_nonzero_decimals')),
                    )
            return orig_format_currency(number, currency, locale=locale)

        _wrapped_format_currency._jpy_currency_fix_wrapped = True
        current_app.jinja_env.globals['format_currency'] = _wrapped_format_currency

    def _patch_transaction_render_details(self):
        if getattr(PaymentTransaction.render_details, '_jpy_currency_fix_wrapped', False):
            return

        orig_render_details = PaymentTransaction.render_details

        @functools.wraps(orig_render_details)
        def _wrapped_render_details(tx):
            html = orig_render_details(tx)
            if not self.settings.get('fix_transaction_details'):
                return html
            return patch_transaction_details_html(
                html,
                tx.amount,
                tx.currency,
                self.settings.get('currencies'),
                preserve_nonzero_decimals=bool(self.settings.get('preserve_nonzero_decimals')),
            )

        _wrapped_render_details._jpy_currency_fix_wrapped = True
        PaymentTransaction.render_details = _wrapped_render_details
