import asyncio
import os
import sys
from json import dumps, loads
from pathlib import Path

from loguru import logger
from playwright.async_api import async_playwright, Page, expect, BrowserContext, TimeoutError

from app.config import Settings
from .db.dataclases import AudiPartsFullObject, AudiPartsLightObject, PartsLinksDTO
from .db.queries.core import check_table_exists
from .db.queries.orm import AudiPartsLightQueriesAsync, AudiPartsFullQueriesAsync, PartsLinksQueriesAsync, \
    add_links_from_file

logger.add(
    "logs/parsing_logs.log",
    level="INFO",
    rotation="10 MB",
    retention="10 days",
    enqueue=True,
)


class PageWorker():
    context: BrowserContext
    page: Page
    list_of_links: list[PartsLinksDTO]
    worker_number: int
    list_of_parts_info: list
    list_of_errors: list


    def __init__(self, context, list_of_links, worker_number):
        self.context = context
        self.list_of_links = list_of_links
        self.worker_number = worker_number
        self.list_of_parts_info = []
        self.list_of_errors = []


    # Метод для создания страницы и парсинга списка ссылок на ней
    async def process_links(self):
        # Создание новой страницы
        self.page = await self.context.new_page()
        logger.debug(f"[Воркер #{self.worker_number}] - Открыл вкладку #{self.worker_number}")

        # Перебор ссылок
        for i in self.list_of_links:
            if i.is_parsed != 2:
                for z in range(5):
                    if result := await load_parts_article(i, self.page, self.worker_number):
                        self.list_of_parts_info.extend(result)

                        await AudiPartsLightQueriesAsync.insert_value([x[1] for x in result])
                        await AudiPartsFullQueriesAsync.insert_value([x[0] for x in result])
                        await PartsLinksQueriesAsync.is_parsed_update(i.id, 2)

                        logger.debug(f"[Воркер #{self.worker_number}] - Добавил {len(result)} строк")
                        break
                    else:
                        try:
                            await self.page.reload(timeout=5000)
                        except TimeoutError:
                            pass
                        except Exception as e:
                            logger.critical(f"[Воркер #{self.worker_number}] - Неизвестная ошибка перезагрузки страницы. Трейсбек: /{e}/")

                        logger.warning(f"[Воркер #{self.worker_number}] - Ошибка загрузки страницы {z + 1}/5. Жду 3 секунды")
                        await asyncio.sleep(3)

                else:
                    logger.error(f"[Воркер #{self.worker_number}] - Ошибка загрузки страницы 5/5 (id ссылки {i.id}). Устанавливаю статус ссылки на '1'")
                    self.list_of_errors.append(i)
                    await PartsLinksQueriesAsync.is_parsed_update(i.id, 1)

        await self.page.close()
        logger.debug(f"[Воркер #{self.worker_number}] - Закрыл вкладку")
        return self.worker_number, True



# Функция для разбивания массива на указанное количество частей (3 части по умолчанию)
def split_into_parts(lst, n:int = 3) -> list:
    total = len(lst)
    base_size, remainder = divmod(total, n)
    sizes = [base_size + (1 if i < remainder else 0) for i in range(n)]

    parts = []
    start = 0
    for s in sizes:
        parts.append(lst[start:start + s])
        start += s
    return parts




async def main():
    pages_amount = 5

    async with (async_playwright() as p):
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(loads(Path("cookies.json").read_text()))

        for i in range(5):
            if not check_table_exists():
                logger.warning(f"[Main] - Таблицы parts_links не существует! Запускаю скрипт для создания")
                add_links_from_file()
            else:
                logger.info(f"[Main] - Таблица parts_links найдена")
                break

        list_of_links_0 = await PartsLinksQueriesAsync.get_value(is_parsed=0)
        list_of_links_1 = await PartsLinksQueriesAsync.get_value(is_parsed=1)
        list_of_links = list_of_links_1 + list_of_links_0

        if not list_of_links:
            logger.warning(f"[Main] - Не удалось найти ссылки со статусом 0, 1. Завершаю работу")
            exit()

        divided_lists = split_into_parts(list_of_links, pages_amount)

        logger.info(
            f"[Main] - "
            f"Новых - {len(list_of_links_0)} | "
            f"Старых - {len(list_of_links_1)} | "
            f"Всего - {len(list_of_links)} | "
            f"Количество ссылок - {pages_amount} | "
            f"На воркера ~{len(divided_lists[0])} | "
        )

        workers = [PageWorker(context, divided_lists[i], i+1) for i in range(pages_amount)]
        tasks = [asyncio.create_task(i.process_links()) for i in workers]
        result = await asyncio.gather(*tasks, return_exceptions=True)

        for i in result:
            if i[1] is True:
                logger.info(f"[Воркер #{i[0]}] - Успешно завершил парсинг!")
            else:
                logger.critical(f"[Воркер #{i[0]}] - Неизвестная ошибка!")



async def load_parts_article(
        PartsLinksObj: PartsLinksDTO,
        page: Page,
        worker_num: int
) -> list | bool:
    id_ = PartsLinksObj.id
    link = PartsLinksObj.link
    is_parsed = PartsLinksObj.is_parsed

    try:
        await page.goto(link, timeout=5000)
    except TimeoutError:
        pass
    except Exception as e:
        logger.critical(f"[Воркер #{worker_num}] - Неизвестная ошибка загрузки страницы (id ссылки {id_}). Трейсбек: /{e}/")

    list_of_parts_info = []

    # Path("cookies.json").write_text(dumps(await page.context.cookies()))
    try:
        await expect(page.locator("[class='vue-toggles__dot']")).to_be_attached(timeout=3000)
    except AssertionError:
        logger.warning(f"[Воркер #{worker_num}] - Не найден контрольный элемент")
        return False

    if await page.get_by_text("Join the club of professionals").is_visible():
        logger.critical(f"[Воркер #{worker_num}] - Не авторизовано (id ссылки {id_})")

    buttons = await page.locator("[aria-label='info-circle']").all()
    unchecked_list_of_parts = await page.locator("[class='flex one-part']").and_(
        page.locator("[data-v-e406b3ae]")).all()
    checked_list_of_parts = [i for i in unchecked_list_of_parts if
                             await i.locator("[aria-label='info-circle']").is_visible()]

    log_txt = (
        f"Запчастей - {len(checked_list_of_parts)} | "
        f"Кнопок - {len(buttons)} | "
        f"Ссылка - {link}"
    )

    logger.info(f"[Воркер #{worker_num}] - {log_txt}")

    if len(buttons) != len(checked_list_of_parts):
        diff = len(checked_list_of_parts) - len(buttons)
        percent = (diff / len(checked_list_of_parts)) * 100

        log_txt = (
            f"Различие! | "
            f"Кол-во - {diff} | "
            f"В процентах - {percent}%"
        )
        checked_list_of_parts.pop(0)
        logger.warning(f"[Воркер #{worker_num}] - {log_txt}")


    for i in checked_list_of_parts:
        try:
            for z in range(5):
                if not await page.locator("[class='ant-modal-header']").is_visible():
                    logger.debug(f"[Воркер #{worker_num}] - Попытка открытия карточки запчасти {z + 1}/5")
                    try:
                        await i.get_by_role("button").first.click(timeout=2000)
                    except TimeoutError:
                        pass
                    except Exception as e:
                        logger.critical(f"[Воркер #{worker_num}] - Неизвестная ошибка открытия карточки (id ссылки {id_}). Трейсбек: /{e}/")
                    await asyncio.sleep(0.2)

                if text := await page.locator("[class='ant-modal-body']").locator("div").and_(
                        page.locator("[data-v-222557ef]")).all():
                    logger.debug(f"[Воркер #{worker_num}] - Успешно открыл карточку запчасти")
                    break
            else:
                logger.error(f"[Воркер #{worker_num}] - Ошибка открытия карточки запчасти 5/5")
                return False

            temp_list_of_part_info = [("link", page.url)]
            for z in text[2:7]:
                temp_list_of_part_info.append(
                    (
                        (await z.text_content(timeout=1000)).split(":")[0].strip(),
                        (await z.text_content(timeout=1000)).split(":")[1].strip(),
                    )
                )

            for z in range(5):
                if await page.locator("[class='ant-modal-header']").is_visible():
                    logger.debug(f"[Воркер #{worker_num}] - Попытка закрытия карточки запчасти {z + 1}/5")
                    try:
                        await page.click("[data-icon='close']", timeout=2000)
                    except TimeoutError:
                        pass
                    except Exception as e:
                        logger.critical(f"[Воркер #{worker_num}] - Неизвестная ошибка закрытия карточки (id ссылки {id_}). Трейсбек: /{e}/")
                logger.debug(f"[Воркер #{worker_num}] - Успешно закрыл карточку запчасти")
                break
            else:
                logger.error(f"[Воркер #{worker_num}] - Ошибка закрытия карточки запчасти 5/5")
                return False

            part_info_dict = {z[0]: z[1] for z in temp_list_of_part_info}
        except Exception as e:
            if not isinstance(e, AssertionError):
                logger.critical(f"[Воркер #{worker_num}] - Неизвестная ошибка при работе с со страницей (id ссылки {id_}). Трейсбек: /{e}/")
                return False

            await asyncio.sleep(0.5)

            logger.info(f"[Воркер #{worker_num}] - Не удалось открыть карточку. Работаю в упрощенном варианте")

            part_code = title = quantity = information = "Не удалось получить"
            try:
                part_code = await i.locator("[class='text-caption']").text_content(timeout=2000)
            except:
                pass
            try:
                title = await i.locator("[class='partName']").text_content(timeout=2000)
            except:
                pass
            try:
                quantity = await i.locator("[class='text-small']").text_content(timeout=2000)
            except:
                pass

            part_info_dict = {
                "link": page.url,
                "Part code": part_code,
                "Title": title,
                "Quantity": quantity,
                "Information": information
            }

        logger.info(f"[Воркер #{worker_num}] - {part_info_dict}")

        try:
            part_obj = AudiPartsFullObject(
                part_code=part_info_dict.get("Part code"),
                title=part_info_dict.get("Title"),
                quantity=part_info_dict.get("Quantity"),
                information=part_info_dict.get("Information"),
                link=part_info_dict.get("link"),
            )
            part_info_dict = AudiPartsLightObject(data=dumps(part_info_dict))
            list_of_parts_info.append((part_obj, part_info_dict))
        except Exception as e:
            logger.critical(f"[Воркер #{worker_num}] - Неизвестная ошибка валидации запчасти (id ссылки {id_}). Трейсбек: /{e}/")
            return False
    return list_of_parts_info


if __name__ == "__main__":
    asyncio.run(main())