import os
import sys
from typing import Union

from sqlalchemy import text, select, insert, delete, inspect
from ..database import session_db, session_db_async, Base, engine_async, engine
from ..models import AudiPartsLightTable



def insert_values(values_to_insert: Union[list[str], tuple[str], str]) -> None:
    with session_db() as session:
        flag = False
        if isinstance(values_to_insert, (list, tuple)):
            session.add_all([AudiPartsLightTable(data=i) for i in values_to_insert])
            flag = True
        elif isinstance(values_to_insert, str):
            session.add(AudiPartsLightTable(data=values_to_insert))
            flag = True

        if flag:
            session.commit()


async def aio_insert_values(values_to_insert: Union[list[str], tuple[str], str]) -> None:
    flag = False
    async with session_db_async() as session:
        print("here")
        if isinstance(values_to_insert, (list, tuple)):
            await session.add_all([AudiPartsLightTable(data=i) for i in values_to_insert])
            flag = True
        elif isinstance(values_to_insert, str):
            await session.add(AudiPartsLightTable(data=values_to_insert))
            flag = True

        if flag:
            await session.commit()

# Проверить существование таблицы parts_links
def check_table_exists():
    with engine.connect() as conn:
        tables = inspect(conn).get_table_names()
        return "parts_links" in tables


if __name__ == '__main__':
    #insert_values()
    pass
