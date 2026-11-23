import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import vm from 'node:vm';

const scriptPath = path.resolve(
  import.meta.dirname,
  '../indico_jpy_currency_fix/static/js/jpy_currency_fix.js'
);
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function loadPatchedIntl({currencies = ['JPY'], preserveNonzeroDecimals = true} = {}) {
  const context = {
    Intl: {
      NumberFormat: Intl.NumberFormat,
    },
    document: {
      currentScript: {
        dataset: {
          currencies: JSON.stringify(currencies),
          preserveNonzeroDecimals: JSON.stringify(preserveNonzeroDecimals),
        },
      },
    },
  };
  vm.createContext(context);
  vm.runInContext(scriptCode, context);
  return context.Intl;
}

test('formats JPY without .00 across locales', () => {
  const PatchedIntl = loadPatchedIntl();
  const fmtJa = new PatchedIntl.NumberFormat('ja', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const fmtEn = new PatchedIntl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  assert.equal(fmtJa instanceof PatchedIntl.NumberFormat, true);
  assert.equal(fmtJa.format(4000), '￥4,000');
  assert.equal(fmtJa.format('4000.00'), '￥4,000');
  assert.equal(fmtEn.format(4000), 'JP¥4,000');
});

test('preserves non-zero decimals by default and rounds when disabled', () => {
  const preserveIntl = loadPatchedIntl({preserveNonzeroDecimals: true});
  const fmtPreserve = new preserveIntl.NumberFormat('ja', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  assert.equal(fmtPreserve.format(4000.5), '￥4,000.50');

  const truncateIntl = loadPatchedIntl({preserveNonzeroDecimals: false});
  const fmtTruncate = new truncateIntl.NumberFormat('ja', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  assert.equal(fmtTruncate.format(4000.5), '￥4,001');
});

test('does not alter non-configured currencies like USD', () => {
  const PatchedIntl = loadPatchedIntl({currencies: ['JPY']});
  const fmtUsd = new PatchedIntl.NumberFormat('ja', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  assert.equal(fmtUsd.format(4000), '$4,000.00');
});
