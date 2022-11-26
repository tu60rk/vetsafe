from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from app.utils.buttons import create_main_menu
from app.utils.bd import DataBase

db = DataBase()


async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        "Привет! Я бот VetSafe. Выберите в ⬇️ меню ⬇️ любое действие",
        reply_markup=create_main_menu(message.from_user.id),
    )

    if message.chat.type == "private":
        if not await db.user_exists(message.from_user.id):
            await db.add_user(message.from_user.id)


def register_handlers_common(dp: Dispatcher) -> None:
    dp.register_message_handler(cmd_start, commands="start", state="*")
