import asyncio
import os
import sys

from sqlalchemy import create_engine, URL, text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import settings


engine_async = create_async_engine(
    url=settings.database_url_asyncpg,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

engine = create_engine(
    url=settings.database_url_psycopg,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

session_db = sessionmaker(engine)
session_db_async = async_sessionmaker(engine_async)


class Base(DeclarativeBase):
    pass


async def main():
    async with session_db_async() as conn:
        res = await conn.execute(text("SELECT VERSION()"))
        print(f"{res.first()=}")

if __name__ == "__main__":
    asyncio.run(main())