"""Test configuration and shared fixtures."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from datetime import datetime, timedelta

from skymetric.models.database import init_db, engine, Base
from skymetric.data.seed_data import generate_fares_for_day


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_fares():
    """Generate a small set of sample fare records."""
    today = datetime.utcnow()
    return generate_fares_for_day(today, include_outliers=False)[:20]


@pytest.fixture
def base_fares():
    """Generate base period fare records."""
    base_date = datetime.utcnow() - timedelta(days=30)
    return generate_fares_for_day(base_date, include_outliers=False)[:20]


@pytest.fixture
def fares_with_outliers():
    """Generate fare records including outliers."""
    today = datetime.utcnow()
    return generate_fares_for_day(today, include_outliers=True)[:30]
