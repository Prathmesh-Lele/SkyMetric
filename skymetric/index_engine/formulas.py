"""Price index calculation formulas: Jevons, Laspeyres, Paasche, Fisher, Torqvist, Chain."""

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
    """Laspeyres index: fixed base-period quantity weights.

    I_L = sum(w_i * (p_ti / p_t0i)) / sum(w_i) * 100
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


def paasche_index(
    prices_t: List[float],
    prices_t0: List[float],
    weights_t: List[float],
) -> float:
    """Paasche index: current-period quantity weights.

    I_P = sum(w_ti * p_ti) / sum(w_ti * p_t0i) * 100
    """
    if not prices_t or not prices_t0 or not weights_t:
        return 0.0
    n = len(prices_t)
    if len(prices_t0) != n or len(weights_t) != n:
        return 0.0

    num = 0.0
    den = 0.0
    for pt, pt0, w in zip(prices_t, prices_t0, weights_t):
        if pt > 0 and pt0 > 0 and w > 0:
            num += w * pt
            den += w * pt0

    if den == 0:
        return 0.0

    return (num / den) * 100


def fisher_index(
    prices_t: List[float],
    prices_t0: List[float],
    weights: List[float],
) -> float:
    """Fisher Ideal index: geometric mean of Laspeyres and Paasche.

    I_F = sqrt(I_L * I_P)
    Resolves consumer substitution bias.
    """
    il = laspeyres_index(prices_t, prices_t0, weights)
    ip = paasche_index(prices_t, prices_t0, weights)

    if il <= 0 or ip <= 0:
        return 0.0

    return math.sqrt(il * ip)


def torqvist_index(
    prices_t: List[float],
    prices_t0: List[float],
    shares_t: List[float],
    shares_t0: List[float],
) -> float:
    """Tornqvist index: symmetric average of expenditure share weights.

    I_T = product((p_ti/p_t0i)^((s_ti + s_t0i)/2)) * 100
    """
    if not prices_t or not prices_t0:
        return 0.0
    n = len(prices_t)
    if len(prices_t0) != n or len(shares_t) != n or len(shares_t0) != n:
        return 0.0

    log_sum = 0.0
    count = 0
    for pt, pt0, st, st0 in zip(prices_t, prices_t0, shares_t, shares_t0):
        if pt > 0 and pt0 > 0 and (st + st0) > 0:
            log_sum += ((st + st0) / 2) * math.log(pt / pt0)
            count += 1

    if count == 0:
        return 0.0

    return math.exp(log_sum) * 100


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


def cpi_transmission_bps(
    fare_change_pct: float,
    transport_weight: float = 0.0859,
) -> Dict[str, float]:
    """Compute CPI transmission basis points from fare change.

    Bps_transport = fare_change_pct * 3.85% * 100
    Bps_headline = Bps_transport * transport_weight
    """
    bps_transport = fare_change_pct * 3.85
    bps_headline = bps_transport * transport_weight
    return {
        "fare_change_pct": round(fare_change_pct, 4),
        "bps_transport": round(bps_transport, 2),
        "bps_headline": round(bps_headline, 2),
        "transport_weight": transport_weight,
    }
