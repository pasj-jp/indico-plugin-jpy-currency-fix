(() => {
  'use strict';

  const script = document.currentScript;
  let currencies = ['JPY'];
  let preserveNonZeroDecimals = true;

  if (script) {
    try {
      if (script.dataset.currencies) {
        currencies = JSON.parse(script.dataset.currencies).map(c => String(c).trim().toUpperCase());
      }
      if (script.dataset.preserveNonzeroDecimals !== undefined) {
        preserveNonZeroDecimals = JSON.parse(script.dataset.preserveNonzeroDecimals);
      }
    } catch {
      // Fall back to defaults if dataset attributes cannot be parsed.
    }
  }

  const targetCurrencies = new Set(currencies.filter(Boolean));
  if (targetCurrencies.size === 0 || typeof Intl === 'undefined' || !Intl.NumberFormat) {
    return;
  }

  const OriginalNumberFormat = Intl.NumberFormat;

  function hasNonZeroFraction(value) {
    const num = Number(value);
    return Number.isFinite(num) && num % 1 !== 0;
  }

  function PatchedNumberFormat(locales, options) {
    if (
      options &&
      options.style === 'currency' &&
      options.currency &&
      targetCurrencies.has(String(options.currency).toUpperCase()) &&
      options.minimumFractionDigits === 2 &&
      options.maximumFractionDigits === 2
    ) {
      const zeroOpts = {
        ...options,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      };
      const zeroFormatter = new OriginalNumberFormat(locales, zeroOpts);
      if (!preserveNonZeroDecimals) {
        return zeroFormatter;
      }

      const decimalFormatter = new OriginalNumberFormat(locales, options);
      return new Proxy(zeroFormatter, {
        get(target, prop) {
          if (prop === 'format') {
            return value =>
              (hasNonZeroFraction(value) ? decimalFormatter : target).format(value);
          }
          if (prop === 'formatToParts') {
            return value =>
              (hasNonZeroFraction(value) ? decimalFormatter : target).formatToParts(value);
          }
          const val = Reflect.get(target, prop, target);
          return typeof val === 'function' ? val.bind(target) : val;
        },
      });
    }

    return new OriginalNumberFormat(locales, options);
  }

  PatchedNumberFormat.prototype = OriginalNumberFormat.prototype;
  PatchedNumberFormat.supportedLocalesOf =
    OriginalNumberFormat.supportedLocalesOf.bind(OriginalNumberFormat);
  Intl.NumberFormat = PatchedNumberFormat;
})();
