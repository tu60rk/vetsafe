import configparser

from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.utils import check_user
from app.utils.buttons import create_main_menu
from app.utils.bd import DataBase

db = DataBase()
# -----------------------------------------
# Парсинг файла конфигурации
# Подготавливаем тексты
config = configparser.ConfigParser()
config.read("text_settings.conf")

text_one = config["text_2_vet_safe"]["text_one"]
text_two = config["text_2_vet_safe"]["text_two"]

# -----------------------------------------


class CheckSales(StatesGroup):
    input_phone = State()


async def cmd_check_sales(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Секундочку, проверяем Вашу регистрацию на vetsafe.ru",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    flag, telephone_number, chat_id, code = check_user.check_user_on_his_id(
        message.from_user.id
    )
    if flag:
        await message.answer(
            "Ваш идентификационный код : " + str(code),
            reply_markup=create_main_menu(message.from_user.id),
        )
        time_length = await db.setting_time("комментарий")
        await db.insert_any_data(
            "insert into send_push values (:chat_id, :comment, :date, :activate)",
            data=[
                {
                    "chat_id": chat_id,
                    "comment": "comment",
                    "date": (datetime.now() + timedelta(minutes=time_length)).strftime(
                        "%Y%m%d%H%M"
                    ),
                    "activate": 1,
                }
            ],
        )
        await state.finish()
    else:
        await message.answer(
            text_one + "\n\n" + text_two, reply_markup=types.ReplyKeyboardRemove()
        )
        await CheckSales.input_phone.set()


async def cmd_input_phone(message: types.Message, state: FSMContext) -> None:
    # Обработка ошибки
    if not message.text.isdigit() or len(message.text) != 11:
        await message.answer(
            "Вы ввели некорректно номер. Нужно ввести 11 цифр (79152304433). Введите снова."
        )
        return

    phone = check_user.get_string_phone(message.text)
    flag, txt = check_user.input_telphone_number_and_check(phone, message.chat.id)
    if flag:

        time_length = await db.setting_time("комментарий")
        await db.insert_any_data(
            "insert into send_push values (:chat_id, :comment, :date, :activate)",
            data=[
                {
                    "chat_id": message.chat.id,
                    "comment": "comment",
                    "date": (datetime.now() + timedelta(minutes=time_length)).strftime(
                        "%Y%m%d%H%M"
                    ),
                    "activate": 1,
                }
            ],
        )

    await message.answer(txt, reply_markup=create_main_menu(message.from_user.id))
    await state.finish()


def register_handlers_check_sales(dp: Dispatcher) -> None:
    dp.register_message_handler(
        cmd_check_sales, Text(equals="Скидка VetSave 🎁", ignore_case=True), state="*"
    )
    dp.register_message_handler(cmd_input_phone, state=CheckSales.input_phone)
