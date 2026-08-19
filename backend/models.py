from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from backend.database import Base

class FactCheckRecord(Base):
    __tablename__ = "fact_checks"

    id = Column(Integer, primary_key=True, index=True)
    original_claim = Column(String, index=True)
    extracted_claim = Column(String)
    status = Column(String) # REJECTED, COMPLETED
    rejection_reason = Column(Text, nullable=True)
    
    # Debate Transcripts
    support_case = Column(Text, nullable=True)
    oppose_case = Column(Text, nullable=True)
    support_rebuttal = Column(Text, nullable=True)
    oppose_rebuttal = Column(Text, nullable=True)
    
    # Verdict
    verdict = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    citations_json = Column(Text, nullable=True) # Store as JSON string
    
    created_at = Column(DateTime, default=datetime.utcnow)
