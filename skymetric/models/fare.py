from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from skymetric.models import Base


class Fare(Base):
    __tablename__ = "fares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    origin = Column(String(3), nullable=False, index=True)
    destination = Column(String(3), nullable=False, index=True)
    carrier = Column(String(20), nullable=False)
    flight_number = Column(String(20), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    advance_window_days = Column(Integer, nullable=False)
    fare_class = Column(String(20), nullable=False, default="economy")
    base_fare = Column(Float, nullable=False)
    taxes_and_fees = Column(Float, nullable=False, default=0.0)
    total_fare = Column(Float, nullable=False)
    source_platform = Column(String(30), nullable=False)

    __table_args__ = (
        Index(
            "ix_fare_route_window",
            "origin",
            "destination",
            "advance_window_days",
        ),
    )
