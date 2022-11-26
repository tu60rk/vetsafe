import asyncio
import logging
import os
import threading
import asyncpg
import pandas as pd

from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.utils.executor import start_webhook
from aiogram import Bot, types

# Дополнительные функции
from app.handlers.find_friend import register_handlers_find_friends
from app.handlers.get_sale import register_handlers_check_sales
from app.handlers.common import register_handlers_common
from app.handlers.get_comment import (
    register_handlers_get_comment,
    start_push_comment,
    start_push_chip,
    start_push_vaccin,
    start_push_alan
)
from app.handlers.admin_commands import register_handlers_admin_commands
from app.handlers.lk import register_handlers_lk
from app.utils.bd import DataBase

db = DataBase()
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
loop = asyncio.get_event_loop()
dp = Dispatcher(bot, loop=loop, storage=MemoryStorage())

register_handlers_find_friends(dp)
register_handlers_check_sales(dp)
register_handlers_common(dp)
register_handlers_get_comment(dp)
register_handlers_admin_commands(dp)
register_handlers_lk(dp)


async def while_push() -> None:
    conn = await asyncpg.connect(DB_URL)
    while True:
        # comments
        nw = datetime.now().strftime("%Y%m%d%H%M")
        logging.error(f"Start while push {nw}")

        columns = ["chat_id", "type_push", "when_push", "activate"]
        tmp_df = await conn.fetch(
            f"select * from send_push where when_push = '{nw}' and active= 1"
        )
        df = pd.DataFrame(tmp_df, columns=columns)
        if not df[df.type_push == "comment"].empty:
            logging.error("Send comment.")
            for row in df.values:
                await start_push_comment(chat_id=row[0])

        # vaccined
        if not df[df.type_push == "vaccin"].empty:
            logging.error("Send vaccin.")
            for row in df.values:
                await start_push_vaccin(chat_id=row[0])

        # chiped
        if not df[df.type_push == "chip"].empty:
            logging.error("Send chip.")
            for row in df.values:
                await start_push_chip(chat_id=row[0])

        if not df.empty:
            await conn.execute(
                f"update send_push set active = 0 where when_push = '{nw}'"
            )
        # requests in waiting
        if datetime.now().hour == 12 and datetime.now().minute == 1:
            columns = ["req_id"]
            tmp_df = await conn.fetch(
                f"""select r1.req_id 
                    from requests_statuses r1
                    inner join (
                                    select req_id, max(req_datetime) as req_datetime 
                                    from requests_statuses 
                                    group by req_id
                                ) r2 on r1.req_id = r2.req_id and r1.req_datetime = r2.req_datetime
                    where r1.req_status = 'ожидание'
                """
            )
            df = pd.DataFrame(tmp_df, columns=columns)
            if not df.empty:
                await start_push_alan(chat_id=287300030, for_wait=df.shape[0])
        
            # requests in processes
            columns = ["req_id"]
            tmp_df = await conn.fetch(
                f"""select r1.req_id 
                    from requests_statuses r1
                    inner join (
                                    select req_id, max(req_datetime) as req_datetime 
                                    from requests_statuses 
                                    group by req_id
                                ) r2 on r1.req_id = r2.req_id and r1.req_datetime = r2.req_datetime
                    where r1.req_status = 'в процессе' and req_schedule_datetime <= now()
                """
            )
            df = pd.DataFrame(tmp_df, columns=columns)
            if not df.empty:
                await start_push_alan(chat_id=287300030, for_process=df.shape[0])
        await asyncio.sleep(60)


def between_callback() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(while_push())
    loop.close()


HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")

# webhook settings
WEBHOOK_HOST = f"https://{HEROKU_APP_NAME}.herokuapp.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = os.getenv("PORT", default=8000)


async def on_startup(dispatcher) -> None:

    if not db.database.is_connected:
        await db.database.connect()
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher) -> None:
    if db.database.is_connected:
        await db.database.disconnect()
    await bot.delete_webhook()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    thread = threading.Thread(target=between_callback)
    thread.start()
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
