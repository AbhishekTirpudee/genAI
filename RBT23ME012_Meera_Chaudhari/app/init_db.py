"""
Database Initialization Script for Onyx.
Creates all required tables in Neon PostgreSQL.
"""

from .database import engine, Base
from .models import Conversation, Message, ResumeRecord, AnalysisReport


def init_db():
    print("Connecting to Neon PostgreSQL and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()

