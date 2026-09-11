"""Tests for the ETL pipeline: cleaning, normalization, outlier rejection."""

from skymetric.pipeline.cleaner import (
    remove_outliers_zscore,
    deduplicate,
    validate_record,
    clean_pipeline,
)
from skymetric.pipeline.normalizer import normalize_record, normalize_records


class TestOutlierRemoval:
    def test_removes_high_outliers(self):
        records = [{"total_fare": 5000 + i * 100, "origin": "DEL", "destination": "BOM"} for i in range(10)]
        records.append({"total_fare": 50000, "origin": "DEL", "destination": "BOM"})
        cleaned = remove_outliers_zscore(records, threshold=2.0)
        assert len(cleaned) == 10
        assert all(r["total_fare"] < 10000 for r in cleaned)

    def test_removes_low_outliers(self):
        records = [{"total_fare": 5000 + i * 100, "origin": "DEL", "destination": "BOM"} for i in range(10)]
        records.append({"total_fare": 100, "origin": "DEL", "destination": "BOM"})
        cleaned = remove_outliers_zscore(records, threshold=2.0)
        assert len(cleaned) == 10
        assert all(r["total_fare"] > 500 for r in cleaned)

    def test_empty_list(self):
        assert remove_outliers_zscore([]) == []

    def test_preserves_normal_data(self):
        records = [{"total_fare": 5000 + i * 100} for i in range(20)]
        cleaned = remove_outliers_zscore(records)
        assert len(cleaned) == 20


class TestDeduplication:
    def test_removes_duplicates(self):
        records = [
            {"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "flight_number": "6E123",
             "advance_window_days": 15, "departure_time": "2026-09-15T10:00", "total_fare": 5000, "timestamp": "2026-09-01"},
            {"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "flight_number": "6E123",
             "advance_window_days": 15, "departure_time": "2026-09-15T10:00", "total_fare": 5200, "timestamp": "2026-09-02"},
        ]
        deduped = deduplicate(records)
        assert len(deduped) == 1
        assert deduped[0]["total_fare"] == 5200

    def test_keeps_different_flights(self):
        records = [
            {"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "flight_number": "6E123",
             "advance_window_days": 15, "departure_time": "2026-09-15T10:00", "total_fare": 5000, "timestamp": "2026-09-01"},
            {"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "flight_number": "6E456",
             "advance_window_days": 15, "departure_time": "2026-09-15T12:00", "total_fare": 5200, "timestamp": "2026-09-01"},
        ]
        deduped = deduplicate(records)
        assert len(deduped) == 2


class TestValidation:
    def test_valid_record(self):
        assert validate_record({"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "total_fare": 5000}) is True

    def test_missing_origin(self):
        assert validate_record({"destination": "BOM", "carrier": "IndiGo", "total_fare": 5000}) is False

    def test_zero_fare(self):
        assert validate_record({"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "total_fare": 0}) is False

    def test_negative_fare(self):
        assert validate_record({"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "total_fare": -100}) is False


class TestNormalization:
    def test_normalize_record(self):
        record = {"origin": "del", "destination": "bom", "total_fare": 5000}
        normalized = normalize_record(record)
        assert normalized["origin"] == "DEL"
        assert normalized["destination"] == "BOM"

    def test_normalize_records_batch(self):
        records = [{"origin": "del", "total_fare": 5000}, {"origin": "bom", "total_fare": 3000}]
        normalized = normalize_records(records)
        assert len(normalized) == 2
        assert all(r["origin"].isupper() for r in normalized)


class TestCleanPipeline:
    def test_full_pipeline(self):
        records = [
            {"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "total_fare": 5000, "base_fare": 4000, "taxes_and_fees": 1000},
            {"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "total_fare": 50000, "base_fare": 40000, "taxes_and_fees": 10000},
            {"origin": "DEL", "destination": "BOM", "carrier": "IndiGo", "total_fare": 5200, "base_fare": 4100, "taxes_and_fees": 1100},
        ]
        cleaned = clean_pipeline(records)
        assert len(cleaned) <= 3
        assert all(r["total_fare"] < 10000 for r in cleaned)
