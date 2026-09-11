from sqlalchemy import Column, Integer, String, Float
from skymetric.models import Base


class SectorWeight(Base):
    __tablename__ = "sector_weights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin = Column(String(3), nullable=False)
    destination = Column(String(3), nullable=False)
    dgca_weight = Column(Float, nullable=False)
    passenger_volume = Column(Integer, nullable=False, default=0)
    classification = Column(String(20), nullable=False, default="metro_trunk")
