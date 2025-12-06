"""Enhanced database connection with connection pooling and health checks."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import event, text
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine with proper pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,  # Increased pool size for better concurrency
    max_overflow=10,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,
    future=True,
    connect_args={
        "server_settings": {"jit": "off"},  # Optimize for async
        "command_timeout": 60,
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


@event.listens_for(engine.sync_engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set connection parameters on new connections."""
    logger.info("New database connection established")


@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Validate connection health on checkout."""
    pass  # pool_pre_ping handles this


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session with automatic transaction management.
    
    Yields:
        AsyncSession: Database session
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Initialize database (create tables)."""
    try:
        # Test connection first
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise in development - allow app to start without DB
        if not settings.DEBUG:
            raise
        logger.warning("Continuing without database (DEBUG mode)")


async def close_db() -> None:
    """Close database connections gracefully."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


async def check_db_health() -> bool:
    """Check database connection health."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
