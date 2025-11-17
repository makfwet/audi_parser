import os
import sys
from pprint import pprint

from typing import Union

from sqlalchemy import text, insert, select, update, delete
from sqlalchemy.ext.asyncio import async_session
from sqlalchemy.exc import ProgrammingError

from ..database import session_db, session_db_async, Base, engine_async, engine
from ..models import PartsLinksTable, AudiPartsLightTable, AudiPartsFullTable, create_tables
from ..dataclases import (
    PartsLinksObject, PartsLinksDTO,
    AudiPartsLightObject, AudiPartsLightDTO,
    AudiPartsFullObject, AudiPartsFullDTO
)


# Синхронные запросы в базу ссылок+статус парсинга
class PartsLinksQueries():
    tablename = "parts_links"

    # Вставка в базу pydentic-объектов ссылок
    @staticmethod
    def insert_value(values_to_insert: Union[list[PartsLinksObject], tuple[PartsLinksObject]]) -> None:
        if isinstance(values_to_insert, (list, tuple)):
            with session_db() as session:
                list_of_values = [PartsLinksTable(link=i.link, is_parsed=i.is_parsed) for i in values_to_insert]
                session.add_all(list_of_values)
                session.commit()

    # Получение из базы pydentic-объектов ссылок
    @staticmethod
    def get_value(id_: int | None = None, is_parsed: int | None = None) -> PartsLinksDTO | list[PartsLinksDTO] | None:
        with session_db() as session:
            if id_:
                res = session.get(PartsLinksTable, id_)
                return PartsLinksDTO.model_validate(res, from_attributes=True)

            if is_parsed is not None:
                res = session.execute(select(PartsLinksTable)
                    .filter(PartsLinksTable.is_parsed == is_parsed)).scalars().all()
                return [PartsLinksDTO.model_validate(i, from_attributes=True) for i in res]

            res = session.execute(select(PartsLinksTable)).scalars().all()
            return [PartsLinksDTO.model_validate(i, from_attributes=True) for i in res]

    # Обновление статуса парсинга для ссылки
    @staticmethod
    def is_parsed_update(id_: int, is_parsed: int = 2) -> None:
        with session_db() as session:
            link_to_update = session.get(PartsLinksTable, id_)
            link_to_update.is_parsed = is_parsed
            session.commit()


# Асинхронные запросы в базу ссылок+статус парсинга
class PartsLinksQueriesAsync():
    tablename = "parts_links"

    # Вставка в базу pydentic-объектов ссылок
    @staticmethod
    async def insert_value(values_to_insert: Union[list[PartsLinksObject], tuple[PartsLinksObject]]) -> None:
        if isinstance(values_to_insert, (list, tuple)):
            async with session_db_async() as session:
                list_of_values = [PartsLinksTable(link=i.link, is_parsed=i.is_parsed) for i in values_to_insert]
                session.add_all(list_of_values)
                await session.commit()

    # Получение из базы pydentic-объектов ссылок
    @staticmethod
    async def get_value(id_: int | None = None, is_parsed: int | None = None) -> PartsLinksDTO | list[PartsLinksDTO] | None:
        async with session_db_async() as session:
            if id_:
                res = await session.get(PartsLinksTable, id_)
                return PartsLinksDTO.model_validate(res, from_attributes=True)

            if is_parsed is not None:
                res = (await session.execute(select(PartsLinksTable)
                    .filter(PartsLinksTable.is_parsed == is_parsed))).scalars().all()
                return [PartsLinksDTO.model_validate(i, from_attributes=True) for i in res]

            res = (await session.execute(select(PartsLinksTable))).scalars().all()
            return [PartsLinksDTO.model_validate(i, from_attributes=True) for i in res]

    # Обновление статуса парсинга для ссылки
    @staticmethod
    async def is_parsed_update(id_: int, is_parsed: int = 1) -> None:
        async with session_db_async() as session:
            link_to_update = await session.get(PartsLinksTable, id_)
            link_to_update.is_parsed = is_parsed
            await session.commit()


# Синхронные запросы в облегченную базу с запчастями в виде json строки
class AudiPartsLightQueries():
    tablename = "audi_parts"

    # Вставка в базу json описания запчастей
    @staticmethod
    def insert_value(
        values_to_insert: Union[
            list[AudiPartsLightObject],
            tuple[AudiPartsLightObject],
            AudiPartsLightObject
        ]
    ) -> None:
        with session_db() as session:
            if isinstance(values_to_insert, (list, tuple)):
                list_of_values = [AudiPartsLightTable(data=i.data) for i in values_to_insert]
                session.add_all(list_of_values)
                session.commit()
            elif isinstance(values_to_insert, AudiPartsLightObject):
                session.add(AudiPartsLightTable(data=values_to_insert.data))
                session.commit()

    # Получение из базы json описания запчастей
    @staticmethod
    def get_value(id_: int | None = None) -> AudiPartsLightDTO | list[AudiPartsLightDTO] | None:
        with session_db() as session:
            if id_:
                res = session.get(AudiPartsLightTable, id_)
                return AudiPartsLightDTO.model_validate(res, from_attributes=True)

            res = session.execute(select(AudiPartsLightTable)).scalars().all()
            return [AudiPartsLightDTO.model_validate(i, from_attributes=True) for i in res]


# Асинхронные запросы в облегченную базу с запчастями в виде json строки
class AudiPartsLightQueriesAsync():
    tablename = "audi_parts"

    # Вставка в базу json описания запчастей
    @staticmethod
    async def insert_value(
        values_to_insert: Union[
            list[AudiPartsLightObject],
            tuple[AudiPartsLightObject],
            AudiPartsLightObject
        ]
    ) -> None:
        async with session_db_async() as session:
            if isinstance(values_to_insert, (list, tuple)):
                list_of_values = [AudiPartsLightTable(data=i.data) for i in values_to_insert]
                session.add_all(list_of_values)
                await session.commit()
            elif isinstance(values_to_insert, AudiPartsLightObject):
                session.add(AudiPartsLightTable(data=values_to_insert.data))
                await session.commit()

    # Получение из базы json описания запчастей
    @staticmethod
    async def get_value(id_: int | None = None) -> AudiPartsLightDTO | list[AudiPartsLightDTO] | None:
        async with session_db_async() as session:
            if id_:
                res = await session.get(AudiPartsLightTable, id_)
                return AudiPartsLightDTO.model_validate(res, from_attributes=True)

            res = (await session.execute(select(AudiPartsLightTable))).scalars().all()
            return [AudiPartsLightDTO.model_validate(i, from_attributes=True) for i in res]


# Синхронные запросы в полную базу с параметрами запчастей по столбцам
class AudiPartsFullQueries():
    tablename = "audi_parts_full"

    # Вставка в базу pydentic-объектов полного описания запчастей
    @staticmethod
    def insert_value(values_to_insert: Union[list[AudiPartsFullObject], tuple[AudiPartsFullObject]]) -> None:
        if isinstance(values_to_insert, (list, tuple)):
            with session_db() as session:
                list_of_values = [
                    AudiPartsFullTable(
                        part_code=i.part_code,
                        title=i.title,
                        quantity=i.quantity,
                        information=i.information,
                        link=i.link,
                    ) for i in values_to_insert
                ]
                session.add_all(list_of_values)
                session.commit()

    # Получение из базы pydentic-объектов полного описания запчастей
    @staticmethod
    def get_value(id_: int | None = None) -> AudiPartsFullDTO | list[AudiPartsFullDTO] | None:
        with session_db() as session:
            if id_:
                res = session.get(AudiPartsFullTable, id_)
                return AudiPartsFullDTO.model_validate(res, from_attributes=True)

            res = session.execute(select(AudiPartsFullTable)).scalars().all()
            return [AudiPartsFullDTO.model_validate(i, from_attributes=True) for i in res]


# Асинхронные запросы в полную базу с параметрами запчастей по столбцам
class AudiPartsFullQueriesAsync():
    tablename = "audi_parts_full"

    # Вставка в базу pydentic-объектов полного описания запчастей
    @staticmethod
    async def insert_value(values_to_insert: Union[list[AudiPartsFullObject], tuple[AudiPartsFullObject]]) -> None:
        async with session_db_async() as session:
            if isinstance(values_to_insert, (list, tuple)):
                list_of_values = [
                    AudiPartsFullTable(
                        part_code=i.part_code,
                        title=i.title,
                        quantity=i.quantity,
                        information=i.information,
                        link=i.link,
                    ) for i in values_to_insert
                ]
                session.add_all(list_of_values)
                try:
                    await session.commit()
                except Exception as e:
                    print(e)
    @staticmethod
    # Получение из базы pydentic-объектов полного описания запчастей
    async def get_value(id_: int | None = None) -> AudiPartsFullDTO | list[AudiPartsFullDTO] | None:
        async with session_db_async() as session:
            if id_:
                res = await session.get(AudiPartsFullTable, id_)
                return AudiPartsFullDTO.model_validate(res, from_attributes=True)

            res = (await session.execute(select(AudiPartsFullTable))).scalars().all()
            return [AudiPartsFullDTO.model_validate(i, from_attributes=True) for i in res]


# Добавить ссылки в бд из текстового файла
def add_links_from_file() -> None:
    create_tables()
    with open("app/parsed_files/parts_links.txt", "r") as f:
        list_of_links = [PartsLinksObject(link=i.strip(), is_parsed=0) for i in f.readlines()]
        PartsLinksQueries.insert_value(list_of_links)


if __name__ == '__main__':
    add_links_from_file()
    pass