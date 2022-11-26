from datetime import datetime
import logging
import os
import io

from aiogram import Dispatcher, types, Bot
from aiogram.types.input_file import InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from app.utils.buttons import (
    create_main_menu,
    create_admin_menu,
    type_data,
    type_setting,
    req_list,
    doing_with_requests,
    request_status
)
from app.utils.bd import DataBase
from app.utils.check_user import get_string_phone


db = DataBase()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
admins = [int(i) for i in os.getenv("ADMINS").split(",")]


class SendAll(StatesGroup):
    insert_text = State()


class Adminka(StatesGroup):
    choose_path = State()
    load_data = State()

    set_settings = State()
    set_time_settings = State()
    set_comment_settings = State()

    insert_text = State()

    manage_requests = State()
    choose_doing_requests = State()
    choose_request_status = State()
    request_comment = State()
    request_date = State()

async def admin(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    if message.from_user.id in admins:
        await Adminka.choose_path.set()
        await message.answer(
            "выберите действие из меню ниже", reply_markup=create_admin_menu()
        )
    else:
        await message.answer(
            "Для Вас недоступна такая команда.",
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
    # data
    elif message.text == "Выгрузить данные":
        await message.answer(
            "Выберите, какие данные из меню ниже вы хотите выгрузить",
            reply_markup=type_data(),
        )
        await Adminka.load_data.set()
    # set settings
    elif message.text == "Настроить уведомление":
        await message.answer(
            "Выберите, какое уведомление из меню ниже вы хотите настроить",
            reply_markup=type_setting(),
        )
        await Adminka.set_settings.set()
    # look settings
    elif message.text == "Посмотреть текущие настройки уведомлений":
        df = await db.get_push_comment("вакцинирован")
        await message.answer(
            f"""----- Оповещение о вакцинации ------
        оповещение через {df.after_minute.max()} минут.
        -----------------------------------------
        """,
            reply_markup=types.ReplyKeyboardRemove(),
        )

        df = await db.get_push_comment("комментарий")
        await message.answer(
            f"""----- Оповещение о комментарии ------
        оповещение через {df.after_minute.max()} минут.
        комментарий оповещения '{df.comment_text.values[0]}'
        -----------------------------------------
        """,
            reply_markup=types.ReplyKeyboardRemove(),
        )

        df = await db.get_push_comment("чипирован")
        await message.answer(
            f"""----- Оповещение о чипировании ------
        оповещение через {df.after_minute.max()} минут.
        комментарий оповещения '{df.comment_text.values[0]}'
        -----------------------------------------
        """,
            reply_markup=create_admin_menu(),
        )
    # send message
    elif message.text == "Отправить сообщение пользователям'":
        await message.answer(
            "Введи текст, который ты хочешь отправить пользователям.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await Adminka.insert_text.set()
    # manage requests
    elif message.text == 'Просмотреть активные заявки':

        columns = ["req_id", "user_nik", "req_status"]
        df = await db.get_df("""
                                select req.req_id, req.user_nik, req_s.req_status 
                                from requests req
                                    inner join 
                                        (select r1.* 
                                            from requests_statuses r1
                                                inner join (select req_id, max(req_datetime) as req_datetime 
                                                            from requests_statuses
                                                            group by req_id
                                                        ) r2 on r1.req_id = r2.req_id and r1.req_datetime = r2.req_datetime
                                        ) req_s on req.req_id = req_s.req_id
                                where 1=1
                                      and req.req_id not in (select distinct req_id from requests_statuses where req_status = 'закрыто')
                                order by req_schedule_datetime
                             """, columns=columns)

        await message.answer(
            "Выберите одну из заявок",
            reply_markup=req_list(df=df),
        )
        await Adminka.manage_requests.set()
    # not command
    else:
        await message.answer(
            "Такой команды не найдено! Попробуй еще раз выбрать команду из меню ниже",
            reply_markup=create_admin_menu(),
        )
        return

async def cmd_manage_requests(message: types.Message, state: FSMContext):

    req_id = message.text.split('Номер заявки - ')[1].split(',')[0]
    req_status = message.text.split('Статус - ')[1].split(',')[0]
    user_nik = message.text.split('Ник - ')[1]

    await state.update_data(req_id=req_id, req_status=req_status, user_nik=user_nik)
    await message.answer("Что хотите сделать с заявкой?", reply_markup=doing_with_requests())
    await Adminka.choose_doing_requests.set()

async def get_requests():
    columns = ["req_id", "user_nik", "req_status"]
    df = await db.get_df("""
                            select req.req_id, req.user_nik, req_s.req_status 
                                from requests req
                                    inner join 
                                        (select r1.* 
                                            from requests_statuses r1
                                                inner join (select req_id, max(req_datetime) as req_datetime 
                                                            from requests_statuses
                                                            group by req_id
                                                        ) r2 on r1.req_id = r2.req_id and r1.req_datetime = r2.req_datetime
                                        ) req_s on req.req_id = req_s.req_id
                                where 1=1
                                      and req.req_id not in (select distinct req_id from requests_statuses where req_status = 'закрыто')
                                order by req_schedule_datetime
                            """, columns=columns)
    return df

async def cmd_choose_doing_requests(message: types.Message, state: FSMContext):
    if message.text == 'Вернуться к заявкам':
        df = await get_requests()

        await message.answer(
            "Выберите одну из заявок",
            reply_markup=req_list(df=df),
        )
        await Adminka.manage_requests.set()
    
    if message.text == 'Изменить статус':
        await message.answer(
            "Выберите из списка ниже нужный статус",
            reply_markup=request_status(),
        )
        await Adminka.choose_request_status.set()

    if message.text == 'Полная информация о заявке':
        data = await state.get_data()
        columns = ['req_id', 'create_datetime', 'user_nik', 
                    'animal_type', 'animal_gender', 'animal_age', 
                    'animal_breed', 'user_telephone', 'req_status',
                    'req_comment', 'req_schedule_datetime'
                    ]
        #logging.error(f'DATA {data}')
        df = await db.get_df(f"""
            select  req.req_id,
                    req.create_datetime,
                    req.user_nik, 
                    req.animal_type,
                    req.animal_gender,
                    req.animal_age,
                    req.animal_breed,
                    req.user_telephone,
                    req_s.req_status,
                    req_s.req_comment,
                    req_s.req_schedule_datetime 
            from requests req
                inner join 
                    (select r1.* 
                     from requests_statuses r1
                        inner join (
                                        select req_id, max(req_datetime) as req_datetime 
                                        from requests_statuses 
                                        group by req_id
                                    ) r2 on r1.req_id = r2.req_id and r1.req_datetime = r2.req_datetime
                    ) req_s on req.req_id = req_s.req_id
            where 1=1
                  and req.req_id = {int(data['req_id'])}
                  and req_s.req_status = '{data['req_status']}'
        """, columns=columns)
        await message.answer(f"""Информация о заявке:
Номер заявки - {df.req_id.values[0]}
Дата создания заявки - {df.create_datetime.values[0]} 
Ник пользователя, создавшего заявку - {df.user_nik.values[0]} 
Тип животного - {df.animal_type.values[0]}
Пол - {df.animal_gender.values[0]}
Возраст - {df.animal_age.values[0]} 
Порода - {df.animal_breed.values[0]}
Телефон пользователя - {df.user_telephone.values[0]} 
Статус заявки - {df.req_status.values[0]}
Комментарий Алана - {df.req_comment.values[0]} 
Дата оповещения, поставленная Аланом - {df.req_schedule_datetime.values[0]} 
""")

        await message.answer("Что хотите сделать с заявкой?", reply_markup=doing_with_requests())
        return

    if message.text == 'Связаться с клиентом':
        data = await state.get_data()
        columns = ['user_nik', 'user_telephone']
        df = await db.get_df(f"""
            select  distinct
                    req.user_nik, 
                    req.user_telephone
            from requests req
                inner join 
                    (select r1.* 
                        from requests_statuses r1
                            inner join (select req_id, max(req_datetime) as req_datetime
                                        from requests_statuses
                                        group by req_id
                            ) r2 on r1.req_id = r2.req_id and r1.req_datetime = r2.req_datetime
                    ) req_s on req.req_id = req_s.req_id
            where 1=1
                  and req.req_id = {data['req_id']}
                  and req_s.req_status = '{data['req_status']}'
        """, columns=columns)
        await message.answer(f"Для связи с пользователем:\n Ник в телеграмме - @{df.user_nik.values[0]} \n Телефон - {get_string_phone(str(df.user_telephone.values[0]))}")
        await message.answer("Что хотите сделать с заявкой?", reply_markup=doing_with_requests())
        return

async def cmd_choose_request_status(message: types.Message, state: FSMContext) -> None:
    d = await state.get_data()
    now = datetime.now()
    if message.text == "Изменить статус заявки на 'закрыто'":
        data = {
            'req_id' : int(d['req_id']),
            'req_status': 'закрыто',
            "req_datetime" :  now,
            "req_comment" : None,
            "req_schedule_datetime" : now
        }

        logging.error(f'DATA : {data}')
        await db.insert_requests_statuses(data = data)
        df = await get_requests()
        await message.answer('Статус обновлен! \n Выберите одну из заявок',
            reply_markup=req_list(df=df))
        await Adminka.manage_requests.set()

    elif message.text == "Изменить статус заявки на 'в процессе'":
        await message.answer("Введите комментарий, почему вы меняете статус на 'в процесссе'", reply_markup=types.ReplyKeyboardRemove())
        await Adminka.request_comment.set()
    elif message.text == "Назад":
        await message.answer("Что хотите сделать с заявкой?", reply_markup=doing_with_requests())
        await Adminka.choose_doing_requests.set()
    else:
        await message.answer(
            "Повторите снова. Выберите из списка ниже нужный статус",
            reply_markup=request_status(),
        )
        return

async def cmd_request_comment(message: types.Message, state: FSMContext) -> None:
    await state.update_data(comment = message.text)
    await message.answer("Введите дату, когда нужно оповестить в формате (20210101)", reply_markup=types.ReplyKeyboardRemove())
    await Adminka.request_date.set()

async def cmd_request_date(message: types.Message, state: FSMContext) -> None:
    date = datetime(int(message.text[0:4]), int(message.text[4:6]), int(message.text[6:]), 12, 0, 0)
    if message.text.isdigit() and len(message.text) == 8 and date > datetime.now():
        d = await state.get_data()

        await db.insert_requests_statuses(data = {
            'req_id' : int(d['req_id']),
            'req_status': 'в процессе',
            "req_datetime" :  datetime.now(),
            "req_comment" : d['comment'],
            "req_schedule_datetime" : date
        })

        df = await get_requests()
        await message.answer('Статус обновлен! \n Выберите одну из заявок',
            reply_markup=req_list(df=df))
        await Adminka.manage_requests.set()
        return
    await message.answer("Повторите ввод даты! Она должна содержать 8 цифр в формате (20210101) и быть больше чем текущее время.", reply_markup=types.ReplyKeyboardRemove())
    return 

async def load_data(message: types.Message, state: FSMContext) -> None:
    if message.text not in ["Данные по отзывам", "Данные по питомцам"]:
        await message.answer(
            "Пожалуйста, выберите действие из меню ниже", reply_markup=type_data()
        )
        return
    if message.text == "Данные по отзывам":
        columns = ["id", "chat_id", "go_hospital", "quality", "comment", "date"]
        df = await db.get_df("select * from comments", columns=columns)

        towrite = io.BytesIO()
        towrite.seek(0)
        text_file = InputFile(towrite, filename="comments.xlsx")

    if message.text == "Данные по питомцам":
        columns = [
            "id",
            "telephone_number",
            "chat_id",
            "pet_name",
            "pet_type",
            "pet_breed",
            "pet_birthday",
            "pet_gender",
            "pet_sterilized",
            "pet_vaccinated",
            "pet_last_date_vaccinated",
            "pet_chiped",
            "pet_number_chip",
            "last_clinic_name",
        ]
        df = await db.get_df("select * from my_pet", columns=columns)
        towrite = io.BytesIO()
        towrite.seek(0)
        text_file = InputFile(towrite, filename="my_pet.xlsx")
    await message.answer_document(text_file, reply_markup=create_admin_menu())
    await Adminka.choose_path.set()


async def set_time_settings(message: types.Message, state: FSMContext) -> None:
    if message.text not in ["Вакцинирование", "Чипирование", "Комментарий"]:
        await message.answer(
            "Пожалуйста, выберите действие из меню ниже", reply_markup=type_setting()
        )
        return

    currect_type = {
        "Вакцинирование": "вакцинирован",
        "Чипирование": "чипирован",
        "Комментарий": "комментарий",
    }
    await state.update_data(type_setting=currect_type.get(message.text))
    await message.answer(
        "Через какое время уведомлять? Укажите время в минутах",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await Adminka.next()


async def set_comment_settings(message: types.Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer(
            "Пожалуйста, введите цифры", reply_markup=types.ReplyKeyboardRemove()
        )
        return

    await state.update_data(time=int(message.text))
    data = await state.get_data()
    if data["type_setting"] == "комментарий":
        max_id_push_comment = await db.max_id_push_comment()
        await db.insert_any_data(
            """insert into push_setting values (:id, :after_minute, :comment_text, :type_comment)""",
            [
                {
                    "id": int(max_id_push_comment) + 1,
                    "after_minute": data["time"],
                    "comment_text": "",
                    "type_comment": data["type_setting"],
                }
            ],
        )
        await message.answer("Данные обновлены!", reply_markup=create_admin_menu())
        await Adminka.choose_path.set()
    else:
        await message.answer(
            "Напишите текст, который будет отправляться",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await Adminka.next()


async def set_finish_settings(message: types.Message, state: FSMContext) -> None:

    current_data = await state.get_data()
    max_id_push_comment = await db.max_id_push_comment()
    await db.insert_any_data(
        """insert into push_setting values (:id, :after_minute, :comment_text, :type_comment)""",
        [
            {
                "id": int(max_id_push_comment) + 1,
                "after_minute": current_data["time"],
                "comment_text": message.text,
                "type_comment": current_data["type_setting"],
            }
        ],
    )
    await message.answer("Данные обновлены!", reply_markup=create_admin_menu())
    await Adminka.choose_path.set()


async def send_message(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer(
            "Ты ничего не ввел! Давай попробуем снова.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return

    users = await db.get_users()
    for row in users:
        user_id = row[0]
        active = int(row[1])
        try:
            await bot.send_message(user_id, message.text)
            if active != 1:
                await db.set_active(user_id, 1)
        except:
            await db.set_active(user_id, 0)
    await bot.send_message(
        message.from_user.id,
        "Успешно отправлено!",
        reply_markup=create_main_menu(message.from_user.id),
    )
    await state.finish()

async def admin_out(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer(
        "Выберите действия из меню ниже",
        reply_markup=create_main_menu(message.from_user.id),
    )

def register_handlers_admin_commands(dp: Dispatcher) -> None:
    
    dp.register_message_handler(
        admin_out, Text(equals="⬅️ Главное меню", ignore_case=True), state="*"
    )
    dp.register_message_handler(
        admin, Text(equals="Админка", ignore_case=True), state="*"
    )
    dp.register_message_handler(choose_path, state=Adminka.choose_path)
    dp.register_message_handler(set_time_settings, state=Adminka.set_settings)
    dp.register_message_handler(set_comment_settings, state=Adminka.set_time_settings)
    dp.register_message_handler(set_finish_settings, state=Adminka.set_comment_settings)
    dp.register_message_handler(send_message, state=Adminka.insert_text)
    dp.register_message_handler(load_data, state=Adminka.load_data)
    dp.register_message_handler(cmd_manage_requests, state=Adminka.manage_requests)
    dp.register_message_handler(cmd_choose_doing_requests, state=Adminka.choose_doing_requests)
    dp.register_message_handler(cmd_choose_request_status, state=Adminka.choose_request_status)
    dp.register_message_handler(cmd_request_comment, state=Adminka.request_comment)
    dp.register_message_handler(cmd_request_date, state=Adminka.request_date)