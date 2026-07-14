"""Canonical low-level financial calculations shared across the project.

The functions in this module are deliberately small and side-effect free.  Data
collection, screening, valuation, and report rendering should build on these
helpers instead of maintaining slightly different local implementations.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


INTEREST_BEARING_DEBT_FIELDS: tuple[str, ...] = (
    "st_borr",
    "lt_borr",
    "bond_payable",
    "non_cur_liab_due_1y",
)

DEPRECIATION_AMORTIZATION_FIELDS: tuple[str, ...] = (
    "depr_fa_coga_dpba",
    "amort_intang_assets",
    "lt_amort_deferred_exp",
)


def safe_float(value: Any) -> float | None:
    """Convert a scalar to a finite float, returning ``None`` when unavailable."""
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def cash_outflow(value: Any) -> float | None:
    """Normalize either cash-flow sign convention to a positive outflow."""
    result = safe_float(value)
    return abs(result) if result is not None else None


def sum_available(
    row: Mapping[str, Any],
    fields: Sequence[str],
) -> float | None:
    """Sum available fields, or return ``None`` when every field is missing."""
    values = [safe_float(row.get(field)) for field in fields]
    available = [value for value in values if value is not None]
    return sum(available) if available else None


def interest_bearing_debt(row: Mapping[str, Any]) -> float | None:
    """Return total interest-bearing debt using the canonical component set."""
    return sum_available(row, INTEREST_BEARING_DEBT_FIELDS)


def depreciation_and_amortization(row: Mapping[str, Any]) -> float | None:
    """Return depreciation and amortization using the canonical component set."""
    return sum_available(row, DEPRECIATION_AMORTIZATION_FIELDS)


def free_cash_flow(operating_cash_flow: Any, capex: Any) -> float | None:
    """Return equity FCF as operating cash flow less normalized cash Capex."""
    ocf = safe_float(operating_cash_flow)
    outflow = cash_outflow(capex)
    if ocf is None or outflow is None:
        return None
    return ocf - outflow
