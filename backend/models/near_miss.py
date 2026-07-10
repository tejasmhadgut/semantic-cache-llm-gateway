from sqlalchemy import Column, Integer, String, Float, DateTime
from db.base import Base
from datetime import datetime, timezone

class NearMiss(Base):
    __tablename__ = "near_misses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(String, nullable=False)
    top_distance = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
