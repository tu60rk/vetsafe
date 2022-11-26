
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.utils.buttons import start_find_animal, create_main_menu, create_pet_types, create_pet_gender, animal_age
from app.utils import check_user
from app.utils.bd import DataBase

db = DataBase()

class FindFriend(StatesGroup):
    choose_path = State()
    choose_animal_type = State()
    choose_animal_gender = State()
    choose_animal_breed = State()
    choose_animal_age = State()
    input_user_telephone = State()

async def start_find_friend(message: types.Message, state: FSMContext):
    await message.answer("""Найдем и подберем достойный приют или добросовестного заводчика!
Осмотр животного ветеринарным врачом у заводчика или в приюте перед вашей встречей с новым другом!
После подачи заявки и заполнения основных полей мы свяжемся с вами!

Выберите любое действие ниже:""", reply_markup=start_find_animal())

    await FindFriend.choose_path.set()


async def choose_path(message: types.Message, state: FSMContext):
    if message.text == 'Заказать услугу':
        await message.answer('Какое животное вы хотите?', reply_markup=create_pet_types(for_find_friend=True))
        await FindFriend.next()
    elif message.text == 'Задать вопрос':
        await message.answer("Напишите, пожалуйста, Ваш вопрос @alanasanov", reply_markup=start_find_animal())
    else:
        await message.answer("Пожалуйста, выберите действие из списка ниже.", reply_markup=start_find_animal())
        return


async def choose_animal_type(message: types.Message, state: FSMContext):
    if message.text in ['Кошка', "Собака"]:
        await state.update_data(animal_type = message.text)
        await message.answer('Выберите желаемый пол животного', reply_markup=create_pet_gender(for_find_friend=True))
        await FindFriend.next()
    else:
        await message.answer('Пожалуйста, выберите животное из списка ниже.', reply_markup=create_pet_types(for_find_friend=True))
        return

async def choose_animal_gender(message: types.Message, state: FSMContext):
    gender_format = {
        'Мужской' : 'муж',
        'Женский' : 'жен',
        'Не имеет значения' : 'нз',
    }

    if message.text in ['Мужской', "Женский", "Не имеет значения"]:
        await state.update_data(animal_gender = gender_format.get(message.text))
        await message.answer('Пожалуйста, введите желаемую породу животного', reply_markup=types.ReplyKeyboardRemove())
        await FindFriend.next()
    else:
        await message.answer('Пожалуйста, Выберите желаемый пол животного из списка ниже.', reply_markup=create_pet_gender(for_find_friend=True))
        return

async def choose_animal_breed(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await state.update_data(animal_breed = message.text)
        await message.answer('Пожалуйста, выберите возраст животного', reply_markup=animal_age())
        await FindFriend.next()
    else:
        await message.answer('Пожалуйста, повторите ввод. Порода не должна содержать цифры!', reply_markup=types.ReplyKeyboardRemove())
        return

async def choose_animal_age(message: types.Message, state: FSMContext):
    return_ans = {
        "Не имеет значения" : "нз"
    }

    if message.text in ['До года', "От года", "Не имеет значения"]:
        req_id = await db.get_max_req_id() + 1
        create_datetime = datetime.now()

        await state.update_data(animal_age = return_ans.get(message.text, message.text))
        await state.update_data(create_datetime = create_datetime)
        await state.update_data(req_id = req_id)
        await state.update_data(user_id = message.from_user.id)
        await state.update_data(user_nik = message.from_user.username)
        data_for_statuses = {
                'req_id' : req_id , 
                'req_status': 'ожидание',
                'req_datetime': create_datetime, 
                'req_comment': None, 
                'req_schedule_datetime': None
            }

        await state.update_data(data_for_statuses = data_for_statuses)

        flag, telephone_number, chat_id, code = check_user.check_user_on_his_id(
            message.from_user.id
        )
        if flag:
            await state.update_data(user_telephone = check_user.get_int_phone(telephone_number))
            await db.insert_requests_statuses(data = data_for_statuses)
            await db.insert_requests(data = await state.get_data())
            await message.answer('Специалист скоро свяжется с Вами!', reply_markup=create_main_menu(message.from_user.id))
            await state.finish()
        else:
            await message.answer('Пожалуйста, введите номер телефона в формате (79152304433)', reply_markup=types.ReplyKeyboardRemove())
            await FindFriend.next()
    else:
        await message.answer('Пожалуйста, повторите ввод из списка ниже', reply_markup=animal_age())
        return

async def input_user_telephone(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or len(message.text) != 11:
        await message.answer(
            "Вы ввели некорректно номер. Нужно ввести 11 цифр (79152304433). Введите снова."
        )
        return
    
    await state.update_data(user_telephone = message.text)
    await db.insert_requests_statuses(data = await state.get_data().get('data_for_statuses'))
    await db.insert_requests(data = await state.get_data())
    await message.answer('Специалист скоро свяжется с Вами!', reply_markup=create_main_menu(message.from_user.id))
    await state.finish()

    
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Выберите из списка ниже любое действие:", reply_markup=create_main_menu(message.from_user.id))

def register_handlers_find_friends(dp: Dispatcher) -> None:

    dp.register_message_handler(
        cancel,
        Text(equals=["отмена", "Вернуться в меню"], ignore_case=True),
        state="*",
    )
    dp.register_message_handler(
            start_find_friend, Text(equals="Хочу завести друга 🐱🐶", ignore_case=True), state="*"
        )

    dp.register_message_handler(choose_path, state=FindFriend.choose_path)
    dp.register_message_handler(choose_animal_type, state=FindFriend.choose_animal_type)
    dp.register_message_handler(choose_animal_gender, state=FindFriend.choose_animal_gender)
    dp.register_message_handler(choose_animal_breed, state=FindFriend.choose_animal_breed)
    dp.register_message_handler(choose_animal_age, state=FindFriend.choose_animal_age)
    dp.register_message_handler(input_user_telephone, state=FindFriend.input_user_telephone)