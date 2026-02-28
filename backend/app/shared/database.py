from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session


@contextmanager
def managed_session(db: Session | None = None) -> Generator[Session, None, None]:
    if db is not None:
        yield db
        return

    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    from app.db.session import get_db as _get_db

    yield from _get_db()
