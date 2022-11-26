import os
import pandas as pd

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import List

ADMINS = os.getenv("ADMINS")
admins = [int(i) for i in ADMINS.split(",")]


def create_main_menu(user_id: int) -> ReplyKeyboardMarkup:

    lst_buttons = []
    lst_buttons.append(
        [KeyboardButton("Личный кабинет 🗝"), KeyboardButton("Скидка VetSave 🎁")]
    )

    lst_buttons.append([KeyboardButton("Сотрудничество 🤝"), KeyboardButton("Хочу завести друга 🐱🐶")])
    if user_id in admins:
        lst_buttons.append([KeyboardButton("Админка")])

    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_admin_menu() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("Выгрузить данные")])
    lst_buttons.append(
        [
            KeyboardButton("Настроить уведомление"),
            KeyboardButton("Посмотреть текущие настройки уведомлений"),
        ]
    )
    lst_buttons.append([KeyboardButton("Отправить сообщение пользователям")])
    lst_buttons.append([KeyboardButton("Просмотреть активные заявки")])
    lst_buttons.append([KeyboardButton("⬅️ Главное меню")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def type_data() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append(
        [KeyboardButton("Данные по отзывам"), KeyboardButton("Данные по питомцам")]
    )
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def type_setting() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append(
        [
            KeyboardButton("Вакцинирование"),
            KeyboardButton("Чипирование"),
            KeyboardButton("Комментарий"),
        ]
    )
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_lk_menu() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append(
        [KeyboardButton("Добавить питомца"), KeyboardButton("Удалить питомца")]
    )
    lst_buttons.append(
        [
            KeyboardButton("Информация о Ваших питомцах"),
            KeyboardButton("Изменить информацию о Вашем питомце"),
        ]
    )
    lst_buttons.append(
        [KeyboardButton("Задать вопрос"), KeyboardButton("⬅️ Главное меню")]
    )
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_binary_answer(for_lk: str = "") -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("Да"), KeyboardButton("Нет")])
    if for_lk:
        lst_buttons.append([KeyboardButton("⬅️ Меню личного кабинета")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_stars() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append(
        [
            KeyboardButton("⭐️"),
            KeyboardButton("⭐️⭐️"),
            KeyboardButton("⭐️⭐️⭐️"),
            KeyboardButton("⭐️⭐️⭐️⭐️"),
            KeyboardButton("⭐️⭐️⭐️⭐️⭐️"),
        ]
    )
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_go_yes_no() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append(
        [KeyboardButton("Да, посещал 🔥"), KeyboardButton("Нет, не посещал 😔")]
    )
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_pet_names(
    info_pet: List[List[int]], for_lk: str = ""
) -> ReplyKeyboardMarkup:
    lst_buttons = []
    for pet in info_pet:
        pet_id, pet_name = pet[0], pet[1]
        lst_buttons.append([KeyboardButton(pet_name)])
    if for_lk:
        lst_buttons.append([KeyboardButton("⬅️ Меню личного кабинета")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_pet_types(for_lk: str = "", for_find_friend: str = "") -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("Кошка"), KeyboardButton("Собака")])
    if for_lk:
        lst_buttons.append([KeyboardButton("⬅️ Меню личного кабинета")])
    if for_find_friend:
        lst_buttons.append([KeyboardButton("Вернуться в меню")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_pet_gender(for_lk: str = "", for_find_friend: str = "") -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("Мужской"), KeyboardButton("Женский")])
    if for_lk:
        lst_buttons.append([KeyboardButton("⬅️ Меню личного кабинета")])
    if for_find_friend:
        lst_buttons.append([KeyboardButton("Не имеет значения")])
        lst_buttons.append([KeyboardButton("Вернуться в меню")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def create_start_comment() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append(
        [KeyboardButton("Рассказать!"), KeyboardButton("Не хочу рассказывать :(")]
    )
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def dont_visit(for_lk: str = "") -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("Еще не посещали")])
    if for_lk:
        lst_buttons.append([KeyboardButton("⬅️ Меню личного кабинета")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def change_pet_information() -> ReplyKeyboardMarkup:

    lst_buttons = []
    lst_buttons.append([KeyboardButton("отмена")])
    lst_buttons.append([KeyboardButton("пол"), KeyboardButton("кличка")])
    lst_buttons.append(
        [KeyboardButton("вид питомца"), KeyboardButton("порода питомца")]
    )
    lst_buttons.append(
        [KeyboardButton("дата рождения"), KeyboardButton("стерилизована/кастрирован")]
    )
    lst_buttons.append(
        [KeyboardButton("вакцинирован"), KeyboardButton("дата последней вакцинации")]
    )
    lst_buttons.append([KeyboardButton("чипирован"), KeyboardButton("номер чипа")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)


def back_lk() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("⬅️ Меню личного кабинета")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)

def start_find_animal() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("Заказать услугу")])
    lst_buttons.append([KeyboardButton("Задать вопрос")])
    lst_buttons.append([KeyboardButton("Вернуться в меню")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)

def animal_age() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("До года")])
    lst_buttons.append([KeyboardButton("От года")])
    lst_buttons.append([KeyboardButton("Не имеет значения")])
    lst_buttons.append([KeyboardButton("Вернуться в меню")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)

def req_list(df:pd.DataFrame) -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("⬅️ Главное меню")])
    for row in df.values:
        lst_buttons.append([KeyboardButton(f"Номер заявки - {row[0]}, Статус - {row[2]}, Ник - {row[1]}")])
    
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)

def doing_with_requests() -> ReplyKeyboardMarkup:

    lst_buttons = []
    lst_buttons.append([KeyboardButton("Изменить статус")])
    lst_buttons.append([KeyboardButton("Полная информация о заявке")])
    lst_buttons.append([KeyboardButton("Связаться с клиентом")])
    lst_buttons.append([KeyboardButton("Вернуться к заявкам")])
    lst_buttons.append([KeyboardButton("⬅️ Главное меню")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)

def request_status() -> ReplyKeyboardMarkup:
    lst_buttons = []
    lst_buttons.append([KeyboardButton("Изменить статус заявки на 'закрыто'")])
    lst_buttons.append([KeyboardButton("Изменить статус заявки на 'в процессе'")])
    lst_buttons.append([KeyboardButton("Назад")])
    lst_buttons.append([KeyboardButton("⬅️ Главное меню")])
    return ReplyKeyboardMarkup(keyboard=lst_buttons, resize_keyboard=True)