"""Sector weight management: load and query DGCA weights."""

from typing import Dict, List, Tuple, Optional

from skymetric.data.dgca_weights import CORRIDORS


def get_all_weights() -> List[Dict]:
    """Return all corridor weights."""
    return [
        {
            "origin": c["origin"],
            "destination": c["destination"],
            "weight": c["weight"],
            "passengers": c["passengers"],
            "classification": c["classification"],
        }
        for c in CORRIDORS
    ]


def get_weight(origin: str, destination: str) -> Optional[Dict]:
    """Get weight for a specific corridor."""
    for c in CORRIDORS:
        if c["origin"] == origin and c["destination"] == destination:
            return {
                "weight": c["weight"],
                "passengers": c["passengers"],
                "classification": c["classification"],
            }
    return None


def get_corridor_key(origin: str, destination: str) -> str:
    """Get the canonical corridor key."""
    return f"{origin}-{destination}"


def get_weight_vector(origin_destination_pairs: List[Tuple[str, str]]) -> List[float]:
    """Return weight vector for a list of origin-destination pairs."""
    weights = []
    for origin, dest in origin_destination_pairs:
        w = get_weight(origin, dest)
        weights.append(w["weight"] if w else 1.0)
    return weights


def normalize_weights(weights: List[float]) -> List[float]:
    """Normalize weights to sum to 1.0."""
    total = sum(weights)
    if total == 0:
        return [1.0 / len(weights)] * len(weights)
    return [w / total for w in weights]
