import asyncio
import os
import sys
from datetime import datetime
from typing import Annotated

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, text
from sqlalchemy.orm import Mapped, MappedColumn
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .database import Base, engine

id_primary_key = Annotated[int, MappedColumn(primary_key=True)]
created_at = Annotated[datetime, MappedColumn(server_default=text("TIMEZONE('utc', now())"))]


class PartsLinksTable(Base):
    __tablename__ = "parts_links"

    id: Mapped[id_primary_key]
    link: Mapped[str] = MappedColumn(unique=True)
    is_parsed: Mapped[int] # 0-False, 1-Error, 2-True


class AudiPartsLightTable(Base):
    __tablename__ = "audi_parts"

    id: Mapped[id_primary_key]
    data: Mapped[str] = MappedColumn(nullable=False)


class AudiPartsFullTable(Base):
    __tablename__ = "audi_parts_full"

    id: Mapped[id_primary_key]
    part_code: Mapped[str] = MappedColumn(nullable=False)
    title: Mapped[str | None]
    quantity: Mapped[str | None]
    information: Mapped[str | None]
    link: Mapped[str | None] = MappedColumn(ForeignKey("parts_links.link"))
    created_at: Mapped[created_at]


# Удаление -> Создание всех таблиц описанных в моделях
def create_tables() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    create_tables()

















