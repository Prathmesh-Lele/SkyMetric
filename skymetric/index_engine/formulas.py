"""Price index calculation formulas: Jevons, Laspeyres, Chain-Laspeyres."""

import math
from typing import List, Dict


def jevons_index(prices_t: List[float], prices_t0: List[float]) -> float:
    """Jevons index: geometric mean of price relatives.

    I = (product(p_t / p_t0))^(1/n)
    """
    if not prices_t or not prices_t0 or len(prices_t) != len(prices_t0):
        return 0.0

    relatives = []
    for pt, pt0 in zip(prices_t, prices_t0):
        if pt0 > 0 and pt > 0:
            relatives.append(pt / pt0)

    if not relatives:
        return 0.0

    log_sum = sum(math.log(r) for r in relatives)
    return math.exp(log_sum / len(relatives)) * 100


def laspeyres_index(
    prices_t: List[float],
    prices_t0: List[float],
    weights: List[float],
) -> float:
    """Laspeyres index: weighted arithmetic mean of price relatives.

    I = sum(w_i * (p_ti / p_t0i)) / sum(w_i) * 100
    """
    if not prices_t or not prices_t0 or not weights:
        return 0.0
    if len(prices_t) != len(prices_t0) or len(prices_t) != len(weights):
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0
    for pt, pt0, w in zip(prices_t, prices_t0, weights):
        if pt0 > 0 and pt > 0 and w > 0:
            weighted_sum += w * (pt / pt0)
            weight_total += w

    if weight_total == 0:
        return 0.0

    return (weighted_sum / weight_total) * 100


def chain_laspeyres_index(
    period_indices: List[float],
) -> float:
    """Chain-Laspeyres: product of period-to-period link indices.

    Returns cumulative index from the chain of period indices.
    """
    if not period_indices:
        return 100.0

    cumulative = 100.0
    for idx in period_indices:
        cumulative *= idx / 100.0
    return cumulative
