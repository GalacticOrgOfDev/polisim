"""Economic calculations module for policy simulation.

This module contains core economic functions for calculating revenues,
expenditures, and their impacts.
"""


def calculate_revenues_and_outs(internal_revenues, internal_outs, current_gdp, scale_factor, inflation_factor):
    """
    Calculate revenues and expenditure surpluses for a given year.

    CRITICAL FIX: Non-percent outs now scale with GDP growth + inflation (scale_factor),
    not just inflation. This prevents unrealistic surplus accumulation in growing economies.
    
    Args:
        internal_revenues: List of revenue dicts with 'name', 'is_percent', 'value'
        internal_outs: List of expenditure dicts with 'name', 'is_percent', 'value', 'allocations'
        current_gdp: Current GDP value
        scale_factor: Scale factor combining GDP growth and inflation
        inflation_factor: Pure inflation factor (1 + inflation_rate)
    
    Returns:
        Tuple of (category_surplus dict, rev_totals dict)
    """
    rev_totals = {}
    for rev in internal_revenues:
        if rev['is_percent']:
            rev_total = (rev['value'] / 100) * current_gdp
        else:
            rev['value'] *= scale_factor  # Scale with GDP growth + inflation
            rev_total = rev['value']
        rev_totals[rev['name']] = rev_total

    category_surplus = {}
    for out in internal_outs:
        funded = 0
        for alloc in out['allocations']:
            source = alloc['source']
            if source in rev_totals:
                funded += (alloc['percent'] / 100) * rev_totals[source]
        if out['is_percent']:
            target = (out['value'] / 100) * current_gdp
        else:
            # FIXED: Was inflation_factor only, now scale_factor (GDP growth + inflation)
            # Rationale: In growing economies, expenditures should scale with GDP, not just inflate
            out['value'] *= scale_factor
            target = out['value']
        category_surplus[out['name']] = funded - target

    return category_surplus, rev_totals
