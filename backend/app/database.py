from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

settings = get_settings()

# Build engine based on database type
if settings.IS_SQLITE:
    # SQLite mode - no pool options needed, enable WAL for better concurrency
    engine = create_engine(
        settings.DATABASE_URL_EFFECTIVE,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
    # Enable WAL mode for SQLite to improve concurrent read/write
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # MySQL mode - connection pool
    engine = create_engine(
        settings.DATABASE_URL_EFFECTIVE,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG,
    )

    # Ensure JSON type compatibility with MySQL 8.0
    @event.listens_for(engine, "connect")
    def set_sql_mode(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
