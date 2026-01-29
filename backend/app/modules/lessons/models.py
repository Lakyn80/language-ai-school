from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.db.base import Base


class LessonGeneration(Base):
    __tablename__ = "lesson_generations"

    id = Column(Integer, primary_key=True)

    level = Column(String(10), nullable=False)

    input_context = Column(Text, nullable=False)

    result_json = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
