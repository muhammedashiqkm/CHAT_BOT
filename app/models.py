import uuid 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

db = SQLAlchemy()

class Document(db.Model):
    """(RAG Table) The parent record for a processed PDF."""
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(255), unique=True, nullable=False)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String(20), default='PENDING', nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    processing_error = Column(Text, nullable=True)
    chunks = db.relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    def __str__(self):
        return f"{self.display_name} ({self.id})"


class DocumentChunk(db.Model):
    """(RAG Table) Stores the actual text chunk and its queryable vector."""
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    document = db.relationship("Document", back_populates="chunks")