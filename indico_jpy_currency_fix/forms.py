import re

from wtforms import BooleanField
from wtforms.validators import DataRequired, ValidationError

from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import TextListField
from indico.web.forms.widgets import SwitchWidget

from indico_jpy_currency_fix import _
from indico_jpy_currency_fix.util import normalize_currencies


CURRENCY_CODE_RE = re.compile(r'^[A-Z]{3}$')


class CurrencyCodeListField(TextListField):
    """TextListField normalizing and validating 3-letter ISO 4217 currency codes."""

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        self.data = normalize_currencies(self.data)

    def _validate_item(self, line):
        if not CURRENCY_CODE_RE.match(line):
            raise ValidationError(_('Invalid ISO 4217 currency code: {}').format(line))


class SettingsForm(IndicoForm):
    """Plugin settings form."""

    currencies = CurrencyCodeListField(
        _('Zero-decimal currencies'),
        validators=[DataRequired()],
        description=_('One 3-letter ISO 4217 currency code per line (e.g. JPY, KRW).'),
    )
    fix_regform = BooleanField(
        _('Fix registration form (frontend)'),
        widget=SwitchWidget(),
        description=_('Format prices without .00 in the React registration form and form builder.'),
    )
    fix_transaction_details = BooleanField(
        _('Fix payment transaction details'),
        widget=SwitchWidget(),
        description=_('Format raw transaction Amount without .00 on registration management details.'),
    )
    fix_regform_stats = BooleanField(
        _('Fix registration form stats'),
        widget=SwitchWidget(),
        description=_('Format currency cells without .00 in registration form statistics tables.'),
    )
    preserve_nonzero_decimals = BooleanField(
        _('Preserve non-zero decimals'),
        widget=SwitchWidget(),
        description=_('Keep fractional digits if an amount contains non-zero decimals (e.g. 4000.50).'),
    )
