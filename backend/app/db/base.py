from collections.abc import AsyncIterator

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db.models import Base, User

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """SQLite ignores ON DELETE CASCADE unless foreign keys are switched on per connection."""
    if engine.dialect.name != "sqlite":
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await ensure_default_user()


async def ensure_default_user() -> User:
    """The app is single-user; every session is owned by this seeded row."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == settings.default_user_email)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=settings.default_user_email)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
