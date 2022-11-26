# import configparser
import pandas as pd
import os
import logging

from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.utils import check_user
from app.utils.buttons import (
    back_lk,
    change_pet_information,
    create_main_menu,
    create_lk_menu,
    create_pet_names,
    create_binary_answer,
    create_pet_types,
    create_pet_gender,
    dont_visit,
)
from app.utils.bd import DataBase

INPUT_TEXT = """Умный робот, разработанный при участии профессиональных ветеринарных врачей поможет Вам с вашим питомцем в ВАЖНЫХ моментах его жизни!\nДля получения уведомлений по уходу и профилактике Вашего питомца.\nА также уведомления о выгодных предложениях на товары и услуги.\n\nVetSafe – Ваш компас в ветеринарном мире"""

db = DataBase()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger.error("Starting lk")
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)


class LK(StatesGroup):
    out = State()
    question = State()

    login_lk = State()
    choose_btn = State()
    # info pet
    return_info_pet = State()
    # add pet
    pre_add_pet = State()
    add_pet = State()  # кличка питомца
    pet_type = State()  # вид питомца : кошка/собака
    pet_breed = State()  # попрода питомца
    pet_birthday = State()  # день рождение
    pet_gender = State()  # пол
    pet_sterillized = State()  # стерилизован/кастрирован
    pet_vaccinated = State()  # вакцинирован
    pet_last_date_vaccinated = State()  # последняя дата вакцинации
    pet_chipped = State()  # чипирован
    pet_numbet_chip = State()  # номер чипа
    last_clinic_name = State()  # последняя клиника
    # update info pet
    change_info_pet = State()
    start_change_info_pet = State()
    change_gender = State()
    change_pet_name = State()
    change_pet_type = State()
    change_pet_breed = State()
    change_pet_birthday = State()
    change_pet_sterillized = State()
    change_pet_vaccinated = State()
    change_pet_last_date_vaccinated = State()
    change_pet_chipped = State()
    change_pet_numbet_chip = State()
    # delete info pet
    delete_info_pet = State()
    # temprorary data
    start_temprorary_data = State()


def get_txt(pet_df: pd.DataFrame) -> str:
    pet_age = (
        (
            datetime.now()
            - pd.to_datetime(pet_df.pet_birthday.values[0], dayfirst=True)
        ).total_seconds()
        / 60
        / 60
        / 24
        / 365
    )

    return "{delimeter:*<10}\nКличка: {pet_name}\n{delimeter:-<10}\nВид животного: {pet_type}\n{delimeter:-<10}\nПорода: {pet_breed}\n{delimeter:-<10}\nПол: {pet_gender}\n{delimeter:-<10}\nКастрирован/Стерилизована: {pet_sterillized}\n{delimeter:-<10}\nВозраст (полных лет): {pet_age}\n{delimeter:-<10}\nВакцинирован: {pet_vaccinated} {pet_last_date_vaccinated}\n{delimeter:-<10}\nЧипирован: {pet_chiped}\n{delimeter:*<10}".format(
        pet_name=pet_df.pet_name.values[0],
        pet_type=pet_df.pet_type.values[0],
        pet_breed=pet_df.pet_breed.values[0],
        pet_gender=pet_df.pet_gender.values[0],
        pet_sterillized=pet_df.pet_sterilized.values[0],
        pet_age=round(pet_age),
        pet_vaccinated=pet_df.pet_vaccinated.values[0],
        pet_last_date_vaccinated=pet_df.pet_last_date_vaccinated.values[0],
        pet_chiped=pet_df.pet_chiped.values[0],
        delimeter="",
    )


async def cmd_login(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        "Секундочку, проверяем Вашу регистрацию на vetsafe.ru",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    flag, telephone_number, chat_id, code = check_user.check_user_on_his_id(
        message.from_user.id
    )
    if flag:
        await message.answer(INPUT_TEXT, reply_markup=create_lk_menu())

        await state.update_data(
            telephone_number=check_user.get_int_phone(telephone_number)
        )
        await state.update_data(chat_id=chat_id)

        await LK.choose_btn.set()
    else:
        await message.answer(
            """
        Введите номер телефона для входа в личный кабинет в формате (79152304433)
        """,
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await LK.login_lk.set()


async def cmd_input_phone(message: types.Message, state: FSMContext) -> None:
    # Обработка ошибки
    if not message.text.isdigit() or len(message.text) != 11:
        await message.answer(
            "Вы ввели некорректно номер. Нужно ввести 11 цифр (79152304433). Введите снова."
        )
        return

    phone = check_user.get_string_phone(message.text)
    logger.error(f"get_int_phone - phone: {phone}")
    flag, txt = check_user.input_telphone_number_and_check(phone, message.chat.id)
    if flag:
        await state.update_data(telephone_number=int(message.text))
        await state.update_data(chat_id=message.from_user.id)
        await message.answer(INPUT_TEXT, reply_markup=create_lk_menu())
        await LK.next()
    else:
        await message.answer(txt, reply_markup=create_main_menu(message.from_user.id))
        await state.finish()


async def get_info_pet(message: types.Message, state: FSMContext) -> None:
    current_data = await state.get_data()
    if message.text not in current_data["pets"]:
        await message.answer(
            "К сожалению, такого питомца у Вас нет. Выберите питомца из списка ниже",
            reply_markup=create_pet_names(current_data["pet_names"]),
        )

    current_state = await state.get_state()
    if current_state == "LK:delete_info_pet":
        await db.delete_pet(
            pet_name=message.text,
            telephone_number=current_data["telephone_number"],
            chat_id=current_data["chat_id"],
        )
        await message.answer(
            f"Удалили питомца {message.text.capitalize()}",
            reply_markup=create_lk_menu(),
        )
        await LK.choose_btn.set()

    elif current_state == "LK:return_info_pet":
        pet_df = await db.get_pet_data(
            message.text, current_data["telephone_number"], current_data["chat_id"]
        )
        txt = get_txt(pet_df)
        await message.answer(txt, reply_markup=create_lk_menu())
        await LK.choose_btn.set()

    elif current_state == "LK:change_info_pet":
        pet_df = await db.get_pet_data(
            message.text, current_data["telephone_number"], current_data["chat_id"]
        )
        txt = get_txt(pet_df)
        await state.update_data(pet_name=pet_df.pet_name.values[0])
        await message.answer(txt, reply_markup=types.ReplyKeyboardRemove())
        await message.answer(
            "Какую информацию Вы бы хотели поменять о питомце? Выберите из списка ниже.",
            reply_markup=change_pet_information(),
        )
        await LK.next()


# add pet
async def pre_start_add_pet(message: types.Message) -> None:
    if message.text.lower().strip() not in ["да", "нет"]:
        await message.answer(
            'Вы ввели некорретный ответ. Пожалуйста, выберите "да" или "нет".',
            reply_markup=create_binary_answer(),
        )
        return
    elif message.text.lower().strip() == "да":
        await message.answer(
            "VetБот, задаст вам несколько простых вопросов - это позволит эффективно помогать Вам!",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await message.answer("Введите кличку Вашего питомца", reply_markup=back_lk())
        await LK.add_pet.set()
    elif message.text.lower().strip() == "нет":
        await message.answer(
            "Выберите действия из меню ниже", reply_markup=create_lk_menu()
        )
        await LK.choose_btn.set()


async def lk_out(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        "Выберите действия из меню ниже",
        reply_markup=create_main_menu(message.from_user.id),
    )


async def choose_path(message: types.Message, state: FSMContext) -> None:
    # out
    if message.text == "⬅️ Главное меню":
        await state.finish()
        await message.answer(
            "Выберите действия из меню ниже",
            reply_markup=create_main_menu(message.from_user.id),
        )
    # question
    elif message.text == "Задать вопрос":
        await bot.send_message(
            message.from_user.id,
            "Задайте вопрос нашему админу.",
            reply_markup=create_lk_menu(),
        )
        await LK.choose_btn.set()
    # pet info
    elif message.text == "Информация о Ваших питомцах":
        currect_data = await state.get_data()
        df = await db.get_pet_names(
            currect_data["telephone_number"], currect_data["chat_id"]
        )
        if df.empty:
            await message.answer(
                "К сожалению, у нас нет информации о Вашем(их) питомцах :( \n Хотите добавить?",
                reply_markup=create_binary_answer(),
            )
            await LK.pre_add_pet.set()
        elif df.shape[0] == 1:
            pet_df = await db.get_pet_data(
                df.pet_name.values[0],
                currect_data["telephone_number"],
                currect_data["chat_id"],
            )
            txt = get_txt(pet_df)
            await message.answer(txt, reply_markup=create_lk_menu())
            await LK.choose_btn.set()
        else:
            reply_markup = create_pet_names(df.values.tolist())
            await state.update_data(pets=df.pet_name.to_list())
            await state.update_data(pet_names=df.values.tolist())
            await message.answer(
                "Выберите питомца из списка ниже", reply_markup=reply_markup
            )
            await LK.next()
    # add pet
    elif message.text == "Добавить питомца":
        temprorary_data = await db.get_temprorary_data(user_id=message.from_user.id)
        temprorary_data = temprorary_data[temprorary_data.pet_name != ""]
        if temprorary_data.empty:
            await message.answer(
                "VetБот, задаст вам несколько простых вопросов - это позволит эффективно помогать Вам!\nВведите кличку Вашего питомца",
                reply_markup=back_lk(),
            )
            await LK.add_pet.set()
        else:
            await state.update_data(
                pet_name=temprorary_data.pet_name.values[0],
                pet_type=temprorary_data.pet_type.values[0],
                pet_breed=temprorary_data.pet_breed.values[0],
                pet_birthday=temprorary_data.pet_birthday.values[0],
                pet_gender=temprorary_data.pet_gender.values[0],
                pet_sterillized=temprorary_data.pet_sterillized.values[0],
                pet_vaccinated=temprorary_data.pet_vaccinated.values[0],
                pet_last_date_vaccined=temprorary_data.pet_last_date_vaccined.values[0],
                pet_chipped=temprorary_data.pet_chipped.values[0],
                pet_numbet_chip=temprorary_data.pet_number_chip.values[0],
            )
            await message.answer(
                "Ранее Вы вводили информацию о питомце, но не закончили ввод. Продолжить вводить?",
                reply_markup=create_binary_answer(),
            )
            await LK.start_temprorary_data.set()

    # change pet information
    elif message.text == "Изменить информацию о Вашем питомце":
        currect_data = await state.get_data()
        df = await db.get_pet_names(
            currect_data["telephone_number"], currect_data["chat_id"]
        )
        if df.empty:
            await message.answer(
                "К сожалению, у нас нет информации о Вашем(их) питомцах :( \n Хотите добавить?",
                reply_markup=create_binary_answer(),
            )
            await LK.pre_add_pet.set()
        elif df.shape[0] == 1:
            pet_df = await db.get_pet_data(
                df.pet_name.values[0],
                currect_data["telephone_number"],
                currect_data["chat_id"],
            )
            txt = get_txt(pet_df)

            await state.update_data(pet_name=pet_df.pet_name.values[0])
            await message.answer(txt, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(
                "Какую информацию Вы бы хотели поменять о питомце? Выберите из списка ниже.",
                reply_markup=change_pet_information(),
            )
            await LK.start_change_info_pet.set()
        else:
            reply_markup = create_pet_names(df.values.tolist())
            await state.update_data(pets=df.pet_name.to_list())
            await state.update_data(pet_names=df.values.tolist())
            await message.answer(
                "Выберите питомца из списка ниже", reply_markup=reply_markup
            )
            await LK.change_info_pet.set()
    # delete pet
    elif message.text == "Удалить питомца":
        currect_data = await state.get_data()
        df = await db.get_pet_names(
            currect_data["telephone_number"], currect_data["chat_id"]
        )
        if df.empty:
            await message.answer(
                "К сожалению, у нас нет информации о Вашем(их) питомцах :( \n Хотите добавить?",
                reply_markup=create_binary_answer(),
            )
            await LK.pre_add_pet.set()
        elif df.shape[0] == 1:
            pet_df = await db.get_pet_data(
                df.pet_name.values[0],
                currect_data["telephone_number"],
                currect_data["chat_id"],
            )
            await db.delete_pet(
                pet_name=df.pet_name.values[0],
                telephone_number=currect_data["telephone_number"],
                chat_id=currect_data["chat_id"],
            )
            await message.answer(
                f"Питомец {pet_df.pet_name.values[0].capitalize()} был удален!",
                reply_markup=create_lk_menu(),
            )
            await LK.choose_btn.set()
        else:
            reply_markup = create_pet_names(df.values.tolist())
            await state.update_data(pets=df.pet_name.to_list())
            await state.update_data(pet_names=df.values.tolist())
            await message.answer(
                "Выберите питомца из списка ниже", reply_markup=reply_markup
            )
            await LK.delete_info_pet.set()
    # not command
    else:
        await message.answer(
            "Такой команды не найдено! Попробуй еще раз выбрать команду из меню ниже",
            reply_markup=create_lk_menu(),
        )
        return


async def cmd_start_temprorary_data(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() not in ["да", "нет"]:
        await message.answer(
            "Вы неверно ответили. Пожалуйста, выберите ответ из списка ниже",
            reply_markup=create_binary_answer(),
        )
        return

    if message.text.lower().strip() == "да":
        temprorary_data = await db.get_temprorary_data(user_id=message.from_user.id)

        if not temprorary_data.pet_name.values[0]:
            await message.answer(
                "VetБот, задаст вам несколько простых вопросов - это позволит эффективно помогать Вам!\n\nВведите кличку Вашего питомца",
                reply_markup=back_lk(),
            )
            await LK.add_pet.set()

        elif not temprorary_data.pet_type.values[0]:
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\n\nВыберите вид вашего питомца",
                reply_markup=create_pet_types(for_lk="ok"),
            )
            await LK.pet_type.set()

        elif not temprorary_data.pet_breed.values[0]:
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\n\nПорода Вашего питомца?",
                reply_markup=back_lk(),
            )
            await LK.pet_breed.set()

        elif not temprorary_data.pet_birthday.values[0]:
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\nПорода - {temprorary_data.pet_breed.values[0]}\n\nВведите дату рождения питомца в формате (01.01.2020)",
                reply_markup=back_lk(),
            )
            await LK.pet_birthday.set()

        elif not temprorary_data.pet_gender.values[0]:
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\nПорода - {temprorary_data.pet_breed.values[0]}\nДата рождения - {temprorary_data.pet_gender.values[0]}\n\nВыберите пол",
                reply_markup=create_pet_gender(for_lk="ok"),
            )
            await LK.pet_gender.set()

        elif not temprorary_data.pet_sterillized.values[0]:
            current_data = await state.get_data()
            txt = (
                "Кастрирован?"
                if current_data["pet_gender"] == "мужской"
                else "Стерелизована?"
            )
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\nПорода - {temprorary_data.pet_breed.values[0]}\nДата рождения - {temprorary_data.pet_gender.values[0]}\nПол - {temprorary_data.pet_gender.values[0]}\n\n{txt}",
                reply_markup=create_binary_answer(for_lk="ok"),
            )
            await LK.pet_sterillized.set()

        elif not temprorary_data.pet_vaccinated.values[0]:
            current_data = await state.get_data()
            txt = (
                "Кастрирован"
                if current_data["pet_gender"] == "мужской"
                else "Стерелизована"
            )
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\nПорода - {temprorary_data.pet_breed.values[0]}\nДата рождения - {temprorary_data.pet_gender.values[0]}\nПол - {temprorary_data.pet_gender.values[0]}\n{txt} - {temprorary_data.pet_sterillized.values[0]}\n\nПитомец вакцинирован?",
                reply_markup=create_binary_answer(for_lk="ok"),
            )
            await LK.pet_vaccinated.set()

        elif (
            not temprorary_data.pet_last_date_vaccined.values[0]
            and temprorary_data.pet_vaccinated.values[0] == "да"
        ):
            current_data = await state.get_data()
            txt = (
                "Кастрирован"
                if current_data["pet_gender"] == "мужской"
                else "Стерелизована"
            )
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\nПорода - {temprorary_data.pet_breed.values[0]}\nДата рождения - {temprorary_data.pet_gender.values[0]}\nПол - {temprorary_data.pet_gender.values[0]}\n{txt} - {temprorary_data.pet_sterillized.values[0]}\nВакцинирован - {temprorary_data.pet_vaccinated.values[0]}\n\nВведите дату последней вакцинации в формате (01.01.2020)",
                reply_markup=back_lk(),
            )
            await LK.pet_last_date_vaccinated.set()

        elif not temprorary_data.pet_chipped.values[0]:
            current_data = await state.get_data()
            txt = (
                "Кастрирован"
                if current_data["pet_gender"] == "мужской"
                else "Стерелизована"
            )
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\nПорода - {temprorary_data.pet_breed.values[0]}\nДата рождения - {temprorary_data.pet_gender.values[0]}\nПол - {temprorary_data.pet_gender.values[0]}\n{txt} - {temprorary_data.pet_sterillized.values[0]}\nВакцинирован - {temprorary_data.pet_vaccinated.values[0]}\nДата последней вакцинации - {temprorary_data.pet_last_date_vaccined.values[0]}\n\nПитомец чипирован?",
                reply_markup=create_binary_answer(for_lk="ok"),
            )
            await LK.pet_chipped.set()

        elif (
            not temprorary_data.pet_number_chip.values[0]
            and temprorary_data.pet_chipped.values[0] == "да"
        ):
            await message.answer(
                f"Введенные ранее данные:\nКличка - {temprorary_data.pet_name.values[0]}\nВид питомца - {temprorary_data.pet_type.values[0]}\nПорода - {temprorary_data.pet_breed.values[0]}\nДата рождения - {temprorary_data.pet_gender.values[0]}\nПол - {temprorary_data.pet_gender.values[0]}\n{txt} - {temprorary_data.pet_sterillized.values[0]}\nВакцинирован - {temprorary_data.pet_vaccinated.values[0]}\nДата последней вакцинации - {temprorary_data.pet_last_date_vaccined.values[0]}\nЧипирован - {temprorary_data.pet_chipped.values[0]}\n\nВведите номер чипа.",
                reply_markup=back_lk(),
            )
            await LK.pet_numbet_chip.set()
    else:
        await db.delete_temprorary_data(user_id=message.from_user.id)
        await state.update_data(
            pet_name="",
            pet_type="",
            pet_breed="",
            pet_birthday="",
            pet_gender="",
            pet_sterillized="",
            pet_vaccinated="",
            pet_last_date_vaccined="",
            pet_chipped="",
            pet_numbet_chip="",
            last_clinic_name="",
        )
        await message.answer(
            "VetБот, задаст вам несколько простых вопросов - это позволит эффективно помогать Вам!\nВведите кличку Вашего питомца",
            reply_markup=back_lk(),
        )
        await LK.add_pet.set()


async def cmd_start_change_info_pet(message: types.Message, state: FSMContext) -> None:
    commands = [
        "пол",
        "кличка",
        "вид питомца",
        "порода питомца",
        "дата рождения",
        "стерилизована/кастрирован",
        "вакцинирован",
        "дата последней вакцинации",
        "чипирован",
        "номер чипа",
        # "отмена"
    ]
    if message.text.lower() not in commands:
        await message.answer(
            "Повторите снова. Введите информацию из списка ниже",
            reply_markup=change_pet_information(),
        )
        return

    if message.text.lower() == "пол":
        await message.answer(
            "Выберите пол", reply_markup=create_pet_gender(for_lk="ok")
        )
        await LK.change_gender.set()

    if message.text.lower() == "кличка":
        await message.answer("Введите новую кличку", reply_markup=back_lk())
        await LK.change_pet_name.set()

    if message.text.lower() == "вид питомца":
        await message.answer(
            "Выберите вид питомца из списка ниже",
            reply_markup=create_pet_types(for_lk="ok"),
        )
        await LK.change_pet_type.set()

    if message.text.lower() == "порода питомца":
        await message.answer("Введите новую породу", reply_markup=back_lk())
        await LK.change_pet_breed.set()

    if message.text.lower() == "дата рождения":
        await message.answer(
            "Введите новую дату рождения питомца в формате (01.01.2020)",
            reply_markup=back_lk(),
        )
        await LK.change_pet_birthday.set()

    current_data = await state.get_data()
    pet_df = await db.get_pet_data(
        current_data["pet_name"],
        current_data["telephone_number"],
        current_data["chat_id"],
    )

    quastion_text = (
        "Кастрирован?" if pet_df.pet_gender.values[0] == "мужской" else "Стерилизована?"
    )
    if message.text.lower() == "стерилизована/кастрирован":
        await message.answer(
            quastion_text, reply_markup=create_binary_answer(for_lk="ok")
        )
        await LK.change_pet_sterillized.set()

    if message.text.lower() == "вакцинирован":
        await message.answer(
            "Вакцинирован?", reply_markup=create_binary_answer(for_lk="ok")
        )
        await LK.change_pet_vaccinated.set()

    if message.text.lower() == "дата последней вакцинации":
        await message.answer(
            "Укажите последнюю дату вакцинации в формате (01.01.2022)",
            reply_markup=back_lk(),
        )
        await LK.change_pet_last_date_vaccinated.set()

    if message.text.lower() == "чипирован":
        await message.answer(
            "Чипирован?", reply_markup=create_binary_answer(for_lk="ok")
        )
        await LK.change_pet_chipped.set()

    if message.text.lower() == "номер чипа":
        await message.answer("Укажите новый номер чипа", reply_markup=back_lk())
        await LK.change_pet_numbet_chip.set()


async def cmd_add_pet(message: types.Message, state: FSMContext) -> None:
    if message.text == "" or message.text.isdigit():
        await message.answer(
            "Вы ничего не ввели или в кличке Вашего питомца есть цифры. Пожалуйста, введите кличку питомца без цифр.",
            reply_markup=back_lk(),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_name":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_name",
            data=message.text.lower().strip(),
        )
        await state.update_data(pet_name=message.text.lower().strip())
        await message.answer(
            f"""Мы поменяли кличку питомца {current_data['pet_name'].capitalize()}!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_name=message.text.lower().strip())
        await message.answer(
            f"Привет, {message.text.strip().capitalize()}! Теперь ты под надежной защитой, расскажи о себе!"
        )
        await message.answer(
            "Выберите вид вашего питомца", reply_markup=create_pet_types(for_lk="ok")
        )
        await LK.next()


async def cmd_pet_type(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() not in ["кошка", "собака"]:
        await message.answer(
            "Вы неверно ввели тип животного. Пожалуйста, повторите ввод",
            reply_markup=create_pet_types(for_lk=""),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_type":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_type",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Мы поменяли вид питомца {current_data['pet_name'].capitalize()}!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_type=message.text.lower().strip())
        await message.answer("Порода Вашего питомца?", reply_markup=back_lk())
        await LK.next()


async def cmd_pet_breed(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() == "" or message.text.isdigit():
        await message.answer(
            "Вы ничего не ввели или Ваша попрода состоит только из цифр. Пожалуйста, введите попроду корректно.",
            reply_markup=back_lk(),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_breed":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_breed",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Мы поменяли породу {current_data['pet_name'].capitalize()}!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_breed=message.text.lower().strip())
        await message.answer(
            "Введите дату рождения питомца в формате (01.01.2020)",
            reply_markup=back_lk(),
        )
        await LK.next()


async def cmd_pet_birthday(message: types.Message, state: FSMContext) -> None:
    if len(message.text.lower().strip()) != 10 or "." not in message.text:
        await message.answer(
            "Вы неверно ввели дату рождения питомца. Пожалуйста, введите дату рождения питомца в формате (01.01.2020)",
            reply_markup=back_lk(),
        )
        return

    dt_birthday = datetime(
        int(message.text.split(".")[2]),
        int(message.text.split(".")[1]),
        int(message.text.split(".")[0]),
    )
    if dt_birthday > datetime.now():
        await message.answer(
            "Дата рождения превышает текущую дату. Пожалуйста, введите дату, которая меньше текущей",
            reply_markup=back_lk(),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_birthday":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_birthday",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Мы поменяли дату рождения {current_data['pet_name'].capitalize()}!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_birthday=message.text.lower().strip())
        await message.answer(
            "Выберите пол", reply_markup=create_pet_gender(for_lk="ok")
        )
        await LK.next()


async def cmd_pet_gender(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() not in ["мужской", "женский"]:
        await message.answer(
            "Вы неверно ввели пол. Пожалуйста, выберите пол из списка ниже",
            reply_markup=create_pet_gender(for_lk=""),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_gender":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_gender",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Мы поменяли пол {current_data['pet_name'].capitalize()}!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_gender=message.text.lower().strip())
        txt = "Кастрирован?" if message.text.lower() == "мужской" else "Стерелизована?"
        await message.answer(txt, reply_markup=create_binary_answer(for_lk="ok"))
        await LK.next()


async def cmd_pet_sterillized(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() not in ["да", "нет"]:
        await message.answer(
            "Вы неверно ввели ответ. Пожалуйста, выберите ответ из списка ниже",
            reply_markup=create_binary_answer(for_lk="ok"),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_sterillized":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_sterilized",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Данные по стерилизации/кастрации {current_data['pet_name'].capitalize()} поменяли!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_sterillized=message.text.lower().strip())
        await message.answer(
            "Питомец вакцинирован?", reply_markup=create_binary_answer(for_lk="ok")
        )
        await LK.next()


async def cmd_pet_vaccinated(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() not in ["да", "нет"]:
        await message.answer(
            "Вы неверно ввели ответ. Пожалуйста, выберите ответ из списка ниже",
            reply_markup=create_binary_answer(for_lk="ok"),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_vaccinated":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_vaccinated",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Данные по вакцинации {current_data['pet_name'].capitalize()} поменяли!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_vaccinated=message.text.lower().strip())
        if message.text.lower() == "нет":

            time_length = await db.setting_time("вакцинирован")
            await db.insert_any_data(
                sql="insert into send_push values (:chat_id, :type_push, :when_push, :active)",
                data=[
                    {
                        "chat_id": int(message.chat.id),
                        "type_push": "vaccin",
                        "when_push": (
                            datetime.now() + timedelta(hours=time_length)
                        ).strftime("%Y%m%d%H%M"),
                        "active": 1,
                    }
                ],
            )
            await state.update_data(pet_last_date_vaccined="")
            await message.answer(
                "Питомец чипирован?", reply_markup=create_binary_answer(for_lk="ok")
            )
            await LK.pet_chipped.set()
        elif message.text.lower() == "да":
            await message.answer(
                "Введите дату последней вакцинации в формате (01.01.2020)",
                reply_markup=back_lk(),
            )
            await LK.next()


async def cmd_pet_last_date_vaccinated(
    message: types.Message, state: FSMContext
) -> None:
    if len(message.text.lower().strip()) != 10 or "." not in message.text:
        await message.answer(
            "Вы неверно ввели дату. Пожалуйста, введите дату в формате (01.01.2020)",
            reply_markup=back_lk(),
        )
        return
    dt_vaccined = datetime(
        int(message.text.split(".")[2]),
        int(message.text.split(".")[1]),
        int(message.text.split(".")[0]),
    )
    if dt_vaccined > datetime.now():
        await message.answer(
            "Дата вакцинации превышает текущую дату. Пожалуйста, введите дату, которая меньше текущей",
            reply_markup=back_lk(),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_last_date_vaccinated":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_last_date_vaccinated",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Данные по последней дате вакцинации {current_data['pet_name'].capitalize()} поменяли!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_last_date_vaccined=message.text.lower().strip())
        await message.answer(
            "Питомец чипирован?", reply_markup=create_binary_answer(for_lk="ok")
        )
        await LK.next()


async def cmd_pet_chipped(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() not in ["да", "нет"]:
        await message.answer(
            "Вы неверно ввели ответ. Пожалуйста, выберите ответ из списка ниже",
            reply_markup=create_binary_answer(for_lk="ok"),
        )
        return
    await state.update_data(pet_chipped=message.text.lower().strip())

    current_state = await state.get_state()
    if current_state == "LK:change_pet_chipped":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_chiped",
            data=message.text.lower().strip(),
        )
        await message.answer(
            f"""Данные по чипированию {current_data['pet_name'].capitalize()} поменяли!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        if message.text.lower().strip() == "нет":

            time_length = await db.setting_time("чипирован")
            await db.insert_any_data(
                "insert into send_push values (:chat_id, :type_push, :when_push, :active)",
                [
                    {
                        "chat_id": int(message.chat.id),
                        "type_push": "chip",
                        "when_push": (
                            datetime.now() + timedelta(hours=time_length)
                        ).strftime("%Y%m%d%H%M"),
                        "active": 1,
                    }
                ],
            )
            await state.update_data(pet_numbet_chip="")
            await message.answer(
                "Душещипательный рассказ о найденом и возвращенном животном собаке с чипом...\nИ последнее...\n Любимая клиника",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            # await message.answer('Введите наименование последней посещаемой клиники', reply_markup=types.ReplyKeyboardRemove())
            await LK.last_clinic_name.set()

        elif message.text.lower().strip() == "да":
            await message.answer("Введите номер чипа?", reply_markup=back_lk())
            await LK.next()


async def cmd_pet_numbet_chip(message: types.Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer(
            "Номер чипа должен состять только из цифр. Пожалуйста, повторите ввод снова",
            reply_markup=back_lk(),
        )
        return

    current_state = await state.get_state()
    if current_state == "LK:change_pet_numbet_chip":
        # update data
        current_data = await state.get_data()
        await db.update_pet(
            user_id=message.from_user.id,
            pet_name=current_data["pet_name"],
            column_name="pet_number_chip",
            data=message.text,
        )
        await message.answer(
            f"""Данные по номеру чипа {current_data['pet_name'].capitalize()} поменяли!\nКакую информацию Вы бы хотели поменять о питомце?\nВыберите действие из списка ниже.
                             """,
            reply_markup=change_pet_information(),
        )
        await LK.start_change_info_pet.set()
    else:
        await state.update_data(pet_numbet_chip=message.text)
        await message.answer(
            "И последнее... \n Любимая клиника", reply_markup=dont_visit()
        )
        # await message.answer('Введите наименование последней посещаемой клиники', reply_markup=types.ReplyKeyboardRemove())
        await LK.next()


async def cmd_last_clinic_name(message: types.Message, state: FSMContext) -> None:
    if message.text.lower().strip() == "" or message.text.isdigit():
        await message.answer(
            "Вы ничего не ввели или Ваша клиника состоит только из цифр. Пожалуйста, введите снова.",
            reply_markup=dont_visit(),
        )
        return
    await state.update_data(last_clinic_name=message.text.lower().strip())
    current_data = await state.get_data()

    max_id = await db.max_id_my_pet()
    await db.insert_any_data(
        """insert into my_pet values (:id
                                    , :phone
                                    , :chat_id
                                    , :pet_name
                                    , :pet_type
                                    , :pet_breed
                                    , :pet_birthday
                                    , :pet_gender
                                    , :pet_sterillized
                                    , :pet_vaccinated
                                    , :pet_last_date_vaccined
                                    , :pet_chipped
                                    , :pet_numbet_chip
                                    , :last_clinic_name
                                )""",
        [
            {
                "id": int(max_id) + 1,
                "phone": str(int(current_data["telephone_number"])),
                "chat_id": current_data["chat_id"],
                "pet_name": current_data["pet_name"],
                "pet_type": current_data["pet_type"],
                "pet_breed": current_data["pet_breed"],
                "pet_birthday": current_data["pet_birthday"],
                "pet_gender": current_data["pet_gender"],
                "pet_sterillized": current_data["pet_sterillized"],
                "pet_vaccinated": current_data["pet_vaccinated"],
                "pet_last_date_vaccined": current_data["pet_last_date_vaccined"],
                "pet_chipped": current_data["pet_chipped"],
                "pet_numbet_chip": current_data["pet_numbet_chip"],
                "last_clinic_name": current_data["last_clinic_name"],
            }
        ],
    )
    await message.answer("Спасибо за Вашу информацию!", reply_markup=create_lk_menu())
    await state.update_data(
        pet_name="",
        pet_type="",
        pet_breed="",
        pet_birthday="",
        pet_gender="",
        pet_sterillized="",
        pet_vaccinated="",
        pet_last_date_vaccined="",
        pet_chipped="",
        pet_numbet_chip="",
        last_clinic_name="",
    )
    await db.delete_temprorary_data(user_id=message.from_user.id)
    await LK.choose_btn.set()


async def cancel(message: types.Message, state: FSMContext) -> None:
    if message.text == "⬅️ Меню личного кабинета":
        pet_data = await state.get_data()
        await db.delete_temprorary_data(user_id=message.from_user.id)
        column_data = [
            "chat_id",
            "pet_name",
            "pet_type",
            "pet_breed",
            "pet_birthday",
            "pet_gender",
            "pet_sterillized",
            "pet_vaccinated",
            "pet_last_date_vaccined",
            "pet_chipped",
            "pet_numbet_chip",
        ]
        prepared_data = {}
        for name_column in column_data:
            if name_column not in pet_data.keys():
                prepared_data[name_column] = ""
            else:
                prepared_data[name_column] = pet_data[name_column]

        await db.add_temprorary_data(prepared_data)
    await LK.choose_btn.set()
    await message.answer(
        "Выберите действие из меню ниже.", reply_markup=create_lk_menu()
    )


# async def back(message : types.Message, state : FSMContext):
#     await state.previous()
#     await message.answer('Выберите действие из меню ниже.', reply_markup=create_lk_menu())


def register_handlers_lk(dp: Dispatcher) -> None:

    dp.register_message_handler(
        cancel,
        Text(equals=["отмена", "⬅️ Меню личного кабинета"], ignore_case=True),
        state="*",
    )
    # dp.register_message_handler(back, Text(equals='назад', ignore_case=True), state = '*')

    dp.register_message_handler(lk_out, state=LK.out)
    dp.register_message_handler(choose_path, state=LK.choose_btn)
    # check user
    dp.register_message_handler(
        cmd_login, Text(equals="Личный кабинет 🗝", ignore_case=True), state="*"
    )
    dp.register_message_handler(cmd_input_phone, state=LK.login_lk)
    # info pet
    dp.register_message_handler(get_info_pet, state=LK.return_info_pet)
    # add pet
    dp.register_message_handler(pre_start_add_pet, state=LK.pre_add_pet)
    dp.register_message_handler(cmd_add_pet, state=LK.add_pet)
    dp.register_message_handler(cmd_pet_type, state=LK.pet_type)
    dp.register_message_handler(cmd_pet_breed, state=LK.pet_breed)
    dp.register_message_handler(cmd_pet_birthday, state=LK.pet_birthday)
    dp.register_message_handler(cmd_pet_gender, state=LK.pet_gender)
    dp.register_message_handler(cmd_pet_sterillized, state=LK.pet_sterillized)
    dp.register_message_handler(cmd_pet_vaccinated, state=LK.pet_vaccinated)
    dp.register_message_handler(
        cmd_pet_last_date_vaccinated, state=LK.pet_last_date_vaccinated
    )
    dp.register_message_handler(cmd_pet_chipped, state=LK.pet_chipped)
    dp.register_message_handler(cmd_pet_numbet_chip, state=LK.pet_numbet_chip)
    dp.register_message_handler(cmd_last_clinic_name, state=LK.last_clinic_name)
    # update information pet
    dp.register_message_handler(get_info_pet, state=LK.change_info_pet)
    dp.register_message_handler(
        cmd_start_change_info_pet, state=LK.start_change_info_pet
    )
    dp.register_message_handler(cmd_pet_gender, state=LK.change_gender)
    dp.register_message_handler(cmd_add_pet, state=LK.change_pet_name)
    dp.register_message_handler(cmd_pet_type, state=LK.change_pet_type)
    dp.register_message_handler(cmd_pet_breed, state=LK.change_pet_breed)
    dp.register_message_handler(cmd_pet_birthday, state=LK.change_pet_birthday)
    dp.register_message_handler(cmd_pet_sterillized, state=LK.change_pet_sterillized)
    dp.register_message_handler(cmd_pet_vaccinated, state=LK.change_pet_vaccinated)
    dp.register_message_handler(
        cmd_pet_last_date_vaccinated, state=LK.change_pet_last_date_vaccinated
    )
    dp.register_message_handler(cmd_pet_chipped, state=LK.change_pet_chipped)
    dp.register_message_handler(cmd_pet_numbet_chip, state=LK.change_pet_numbet_chip)
    # delete information pet
    dp.register_message_handler(get_info_pet, state=LK.delete_info_pet)
    # temprorary data
    dp.register_message_handler(
        cmd_start_temprorary_data, state=LK.start_temprorary_data
    )
