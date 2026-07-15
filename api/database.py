from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from api.config import DATABASE_URL, auto_logger

# create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# create async session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# dependency to get db session in fastapi endpoints
@auto_logger()
async def get_db():
    async with async_session() as session:
        yield session
