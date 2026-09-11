from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from skymetric.models import Base


class IndexValue(Base):
    __tablename__ = "indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    origin = Column(String(3), nullable=True)
    destination = Column(String(3), nullable=True)
    advance_window = Column(Integer, nullable=True)
    index_value = Column(Float, nullable=False)
    base_value = Column(Float, nullable=False, default=100.0)
    calculation_method = Column(String(20), nullable=False, default="jevons")
    created_at = Column(DateTime, server_default=func.now())
