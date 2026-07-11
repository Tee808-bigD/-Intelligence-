"""Database models for DTDL Customer Intelligence Platform."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CustomerTicket(Base):
    __tablename__ = "customer_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, unique=True, index=True)
    customer_id = Column(String, index=True)
    customer_name = Column(String)
    customer_phone = Column(String)
    message = Column(Text)
    intent = Column(String)
    confidence = Column(Float)
    sentiment = Column(Float)
    assigned_agent = Column(String)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    response = Column(Text)
    resolution_time = Column(Float)  # in minutes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(JSON, default=dict)

class AgentMetrics(Base):
    __tablename__ = "agent_metrics"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True)
    tickets_handled = Column(Integer, default=0)
    tickets_resolved = Column(Integer, default=0)
    tickets_escalated = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    avg_resolution_time = Column(Float, default=0.0)
    customer_satisfaction = Column(Float, default=0.0)
    date = Column(DateTime, default=datetime.utcnow)

class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize database
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
