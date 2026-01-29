from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
)

from app.db.base import Base


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True)

    slug = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)

    description = Column(Text, nullable=False)

    # raw instructional content
    situation_text = Column(Text, nullable=False)

    # optional metadata
    category = Column(String(100), nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
