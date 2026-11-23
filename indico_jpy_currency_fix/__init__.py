from importlib.metadata import PackageNotFoundError, version

from indico.util.i18n import make_bound_gettext

try:
    __version__ = version('indico-plugin-jpy-currency-fix')
except PackageNotFoundError:
    __version__ = '0.0.0.dev0'

_ = make_bound_gettext('jpy_currency_fix')
