"""DGCA passenger-weighted sector weights for Indian domestic corridors.

Weights derived from DGCA city-pair passenger traffic statistics (2023-2024).
Total domestic passenger share across monitored corridors.
"""

CORRIDORS = [
    {"origin": "DEL", "destination": "BOM", "weight": 18.4, "passengers": 18_400_000, "classification": "metro_trunk"},
    {"origin": "DEL", "destination": "BLR", "weight": 14.2, "passengers": 14_200_000, "classification": "metro_trunk"},
    {"origin": "BOM", "destination": "BLR", "weight": 12.1, "passengers": 12_100_000, "classification": "metro_trunk"},
    {"origin": "DEL", "destination": "CCU", "weight": 10.5, "passengers": 10_500_000, "classification": "metro_trunk"},
    {"origin": "DEL", "destination": "HYD", "weight": 8.3, "passengers": 8_300_000, "classification": "metro_trunk"},
    {"origin": "BOM", "destination": "MAA", "weight": 6.7, "passengers": 6_700_000, "classification": "metro_trunk"},
    {"origin": "BLR", "destination": "HYD", "weight": 5.8, "passengers": 5_800_000, "classification": "metro_trunk"},
    {"origin": "DEL", "destination": "MAA", "weight": 5.2, "passengers": 5_200_000, "classification": "metro_trunk"},
    {"origin": "DEL", "destination": "IXS", "weight": 5.8, "passengers": 5_800_000, "classification": "regional_thin"},
    {"origin": "DEL", "destination": "DHM", "weight": 3.0, "passengers": 3_000_000, "classification": "regional_thin"},
]

CARRIERS = ["IndiGo", "Air India", "Vistara", "SpiceJet", "Akasa Air", "Air India Express"]

ADVANCE_WINDOWS = [1, 7, 15, 30, 45]

CARRIER_MARKET_SHARE = {
    "IndiGo": 63.6,
    "Air India": 15.2,
    "Vistara": 9.1,
    "SpiceJet": 5.5,
    "Akasa Air": 4.1,
    "Air India Express": 2.5,
}
