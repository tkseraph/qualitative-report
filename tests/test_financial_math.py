"""Tests for canonical low-level financial calculations."""

from __future__ import annotations

import math

from financial_math import (
    cash_outflow,
    depreciation_and_amortization,
    free_cash_flow,
    interest_bearing_debt,
    safe_float,
)


def test_safe_float_rejects_missing_and_non_finite_values():
    assert safe_float(None) is None
    assert safe_float("not-a-number") is None
    assert safe_float(float("nan")) is None
    assert safe_float(float("inf")) is None
    assert safe_float(-float("inf")) is None
    assert safe_float("12.5") == 12.5


def test_cash_outflow_normalizes_both_sign_conventions():
    assert cash_outflow(25) == 25
    assert cash_outflow(-25) == 25
    assert cash_outflow(None) is None


def test_interest_bearing_debt_uses_canonical_components():
    row = {
        "st_borr": 10,
        "lt_borr": 20,
        "bond_payable": None,
        "non_cur_liab_due_1y": 5,
        "total_liab": 999,
    }
    assert interest_bearing_debt(row) == 35
    assert interest_bearing_debt({}) is None


def test_depreciation_and_amortization_ignores_unavailable_components():
    row = {
        "depr_fa_coga_dpba": 8,
        "amort_intang_assets": 2,
        "lt_amort_deferred_exp": math.nan,
    }
    assert depreciation_and_amortization(row) == 10
    assert depreciation_and_amortization({}) is None


def test_free_cash_flow_requires_ocf_and_capex_and_is_sign_invariant():
    assert free_cash_flow(100, 30) == 70
    assert free_cash_flow(100, -30) == 70
    assert free_cash_flow(None, 30) is None
    assert free_cash_flow(100, None) is None
