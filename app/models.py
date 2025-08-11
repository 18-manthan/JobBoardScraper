from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    description = Column(String)
    url = Column(String)
    source = Column(String, default="Unknown")
    liked = Column(Boolean, default=False)
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)