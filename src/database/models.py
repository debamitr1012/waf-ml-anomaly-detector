"""
Database models for storing analysis results, feedback, and rules.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class AnalysisResult(Base):
    """Store analysis results for historical tracking."""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String(45), index=True)
    method = Column(String(10))
    path = Column(String(2048))
    is_anomaly = Column(Boolean, index=True)
    anomaly_score = Column(Float)
    confidence = Column(Float)
    threat_level = Column(String(20))
    recommended_action = Column(String(50))
    explanation = Column(JSON)
    latency_ms = Column(Float)


class Feedback(Base):
    """Store administrator feedback for continuous learning."""
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    analysis_id = Column(Integer, index=True)
    is_false_positive = Column(Boolean)
    comments = Column(Text)
    submitted_by = Column(String(100))


class SecurityRule(Base):
    """Store generated security rules."""
    __tablename__ = 'security_rules'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    attack_type = Column(String(100), index=True)
    description = Column(Text)
    severity = Column(String(20))
    confidence = Column(Float)
    status = Column(String(20), default='pending')  # pending, approved, rejected, deployed
    modsecurity_format = Column(Text)
    nginx_format = Column(Text)
    generic_format = Column(JSON)


# Database initialization
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///waf_ml.db')

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
