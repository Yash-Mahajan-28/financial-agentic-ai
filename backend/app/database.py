import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# Determine active database URL
db_url = settings.DATABASE_URL

def create_db_engine():
    global db_url
    # If SQLite fallback is active and no remote PostgreSQL is provided (or running on Vercel without remote DB), use SQLite directly
    is_localhost_postgres = "localhost" in db_url or "127.0.0.1" in db_url
    if settings.USE_SQLITE_FALLBACK and (is_localhost_postgres or not db_url.startswith("postgresql")):
        logger.info(f"Using SQLite database at {settings.SQLITE_DB_PATH}.")
        os.makedirs(os.path.dirname(os.path.abspath(settings.SQLITE_DB_PATH)), exist_ok=True)
        db_url = f"sqlite:///{os.path.abspath(settings.SQLITE_DB_PATH)}"
        return create_engine(db_url, connect_args={"check_same_thread": False})

    if "postgresql" in db_url:
        try:
            # Test postgres connection quickly
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                connect_args={"connect_timeout": 3}
            )
            # Try a quick connection test
            with engine.connect() as conn:
                pass
            logger.info("Connected to PostgreSQL database successfully.")
            return engine
        except Exception as e:
            if settings.USE_SQLITE_FALLBACK:
                logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite at {settings.SQLITE_DB_PATH}.")
                os.makedirs(os.path.dirname(os.path.abspath(settings.SQLITE_DB_PATH)), exist_ok=True)
                db_url = f"sqlite:///{os.path.abspath(settings.SQLITE_DB_PATH)}"
                return create_engine(db_url, connect_args={"check_same_thread": False})
            else:
                raise e
    else:
        # SQLite
        os.makedirs(os.path.dirname(os.path.abspath(settings.SQLITE_DB_PATH)), exist_ok=True)
        return create_engine(db_url, connect_args={"check_same_thread": False})

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
