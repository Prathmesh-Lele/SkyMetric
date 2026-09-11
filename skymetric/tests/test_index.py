"""Tests for index calculation engine."""

from skymetric.index_engine.formulas import jevons_index, laspeyres_index, chain_laspeyres_index
from skymetric.index_engine.calculator import compute_sector_index, compute_national_index, compute_daily_index
from skymetric.index_engine.weights import get_all_weights, get_weight, normalize_weights


class TestJevonsIndex:
    def test_no_change(self):
        assert jevons_index([100, 200], [100, 200]) == 100.0

    def test_price_increase(self):
        result = jevons_index([120, 240], [100, 200])
        assert result == 120.0

    def test_price_decrease(self):
        result = jevons_index([80, 160], [100, 200])
        assert result == 80.0

    def test_empty_input(self):
        assert jevons_index([], []) == 0.0

    def test_mismatched_lengths(self):
        assert jevons_index([100], [100, 200]) == 0.0


class TestLaspeyresIndex:
    def test_no_change(self):
        assert laspeyres_index([100, 200], [100, 200], [1, 1]) == 100.0

    def test_with_weights(self):
        result = laspeyres_index([120, 180], [100, 200], [2, 1])
        expected = ((2 * 1.2 + 1 * 0.9) / 3) * 100
        assert abs(result - expected) < 0.01

    def test_empty_input(self):
        assert laspeyres_index([], [], []) == 0.0


class TestChainLaspeyres:
    def test_single_period(self):
        assert chain_laspeyres_index([105]) == 105.0

    def test_multiple_periods(self):
        result = chain_laspeyres_index([105, 102, 98])
        expected = 100 * 1.05 * 1.02 * 0.98
        assert abs(result - expected) < 0.01

    def test_empty(self):
        assert chain_laspeyres_index([]) == 100.0


class TestSectorIndex:
    def test_identical_records(self, sample_fares, base_fares):
        result = compute_sector_index(sample_fares, sample_fares)
        assert abs(result - 100.0) < 0.01

    def test_empty_records(self):
        result = compute_sector_index([], [])
        assert result == 100.0


class TestNationalIndex:
    def test_uniform_indices(self):
        sectors = {"DEL-BOM": 100.0, "DEL-BLR": 100.0, "BOM-BLR": 100.0}
        result = compute_national_index(sectors)
        assert abs(result - 100.0) < 0.1

    def test_empty_sectors(self):
        assert compute_national_index({}) == 100.0


class TestWeights:
    def test_get_all_weights(self):
        weights = get_all_weights()
        assert len(weights) == 10

    def test_get_weight(self):
        w = get_weight("DEL", "BOM")
        assert w is not None
        assert w["weight"] == 18.4

    def test_get_weight_unknown(self):
        assert get_weight("XYZ", "ABC") is None

    def test_normalize_weights(self):
        normalized = normalize_weights([18.4, 14.2, 12.1])
        assert abs(sum(normalized) - 1.0) < 0.001
