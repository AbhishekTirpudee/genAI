import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Conversation(Base):
    """Represents a saved chat/analysis session in Onyx."""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), default="New Analysis Session")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    resumes = relationship("ResumeRecord", back_populates="conversation", cascade="all, delete-orphan")
    analyses = relationship("AnalysisReport", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Represents an individual message in a conversation thread."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(50), nullable=False)  # 'user' or 'gemini'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class ResumeRecord(Base):
    """Stores uploaded resume metadata and extracted text."""
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    extracted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="resumes")


class AnalysisReport(Base):
    """Stores the comparative fit analysis between resume and target position."""
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    target_position = Column(String(255), nullable=False)
    overall_score = Column(Float, default=0.0)
    sectors_data = Column(JSON, nullable=True)          # Sector breakdown & sample JDs
    strengths = Column(JSON, nullable=True)             # Skills matched
    missing_skills = Column(JSON, nullable=True)        # Gaps / what they should have
    what_to_remove = Column(JSON, nullable=True)        # Redundant or irrelevant items
    recommended_bullets = Column(JSON, nullable=True)   # Suggested bullet points to add
    summary_markdown = Column(Text, nullable=True)      # Complete narrative report
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="analyses")

