from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.utils.config import settings

engine = create_async_engine(
    url=settings.get_db_url
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with async_session_maker() as session:
        yield session

class Base(DeclarativeBase):
    pass

async def reset_tables():
    async with engine.begin() as eng:
        await eng.run_sync(Base.metadata.drop_all)
        await eng.run_sync(Base.metadata.create_all)
