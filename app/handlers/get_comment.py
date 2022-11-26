import os
import re

from datetime import datetime
from aiogram import Bot
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.utils.buttons import (
    create_main_menu,
    create_stars,
    create_go_yes_no,
    create_start_comment,
)
from app.utils.bd import DataBase

db = DataBase()

TOKEN = os.getenv("BOT_TOKEN")
bot_ = Bot(token=TOKEN)


class Comments(StatesGroup):

    binary_answer = State()
    start_answer = State()
    get_comment = State()


async def start_push_vaccin(chat_id: int) -> None:
    txt = "*ВЕТСЕЙФ будет предлагать клинику партнер клинику с выгодной ценой*"
    await bot_.send_message(chat_id, txt)


async def start_push_chip(chat_id: int) -> None:
    txt = "Через некоторое время предложить клинику для чипирования и цену"
    await bot_.send_message(chat_id, txt)


async def start_push_comment(chat_id: int) -> None:
    txt = "Вы запрашивали скидку VETSAFE - расскажите, как прошло!"
    await bot_.send_message(chat_id, txt, reply_markup=create_start_comment())


async def get_push(message: types.Message) -> None:
    await message.answer("Вы посетили Вет Клинику?", reply_markup=create_go_yes_no())
    await Comments.binary_answer.set()

async def start_push_alan(chat_id: int, for_wait:int, for_process:int) -> None:
    txt = ''
    if for_wait:
        txt = f"Алан! У тебя заявок в ожидании на сегодня {for_wait} штук."
    if for_process:
        txt = f"Алан! У тебя заявок по которым подошел срок исполнения или истекли на сегодня {for_process} штук."
    await bot_.send_message(chat_id, txt)


async def check_binary_answer(message: types.Message, state: FSMContext) -> None:
    if not message.text in ["Да, посещал 🔥", "Нет, не посещал 😔"]:
        await message.answer(
            "Пожалуйста, выберите 'Да, посещал 🔥' или 'Нет, не посещал 😔'.",
            reply_markup=create_go_yes_no(),
        )
        return

    if message.text == "Нет, не посещал 😔":
        mxid = await db.get_df("select max(id) as mxid from comments", columns=["mxid"])
        data = [
            {
                "mxid": int(mxid.mxid.max() + 1),
                "chat_id": int(message.chat.id),
                "go_hospital": "нет",
                "quality": 0,
                "comment": "нет",
                "date": datetime.now().strftime("%Y%m%d %H%M"),
            }
        ]
        await db.insert_any_data(
            "insert into comments values(:mxid, :chat_id, :go_hospital, :quality, :comment, :date)",
            data,
        )
        await message.answer(
            "Спасибо за Ваш ответ!", reply_markup=create_main_menu(message.from_user.id)
        )
        await state.finish()

    if message.text == "Да, посещал 🔥":
        await state.update_data(go_hospital="да")
        await Comments.next()
        await message.answer("Оцените (Что?)", reply_markup=create_stars())


async def check_stars(message: types.Message, state: FSMContext) -> None:
    if not "⭐️" in message.text:
        await message.answer("Пожалуйста, введите ⭐️", reply_markup=create_stars())
        return

    await state.update_data(quality=len(re.findall("⭐️", message.text)))
    await Comments.next()
    await message.answer(
        "Оставьте отзыв, это улучшит нашу работу",
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def get_comment(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Спасибо за отзыв!", reply_markup=create_main_menu(message.from_user.id)
    )
    await state.update_data(comment=message.text)

    currect_data = await state.get_data()
    mxid = await db.get_df("select max(id) as mxid from comments", columns=["mxid"])
    data = [
        {
            "mxid": int(mxid.mxid.max() + 1),
            "chat_id": int(message.chat.id),
            "go_hospital": currect_data["go_hospital"],
            "quality": currect_data["quality"],
            "comment": currect_data["comment"],
            "date": datetime.now().strftime("%Y%m%d %H%M"),
        }
    ]
    await db.insert_any_data(
        "insert into comments values(:mxid, :chat_id, :go_hospital, :quality, :comment, :date)",
        data,
    )
    await state.finish()


async def return_main_menu(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        "Выберите действие из меню ниже",
        reply_markup=create_main_menu(message.from_user.id),
    )


def register_handlers_get_comment(dp: Dispatcher):
    dp.message_handler(start_push_comment)
    dp.register_message_handler(
        return_main_menu,
        Text(equals="Не хочу рассказывать :(", ignore_case=True),
        state="*",
    )
    dp.register_message_handler(
        get_push, Text(equals="Рассказать!", ignore_case=True), state="*"
    )
    dp.register_message_handler(check_binary_answer, state=Comments.binary_answer)
    dp.register_message_handler(check_stars, state=Comments.start_answer)
    dp.register_message_handler(get_comment, state=Comments.get_comment)
