import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router, html
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ChatMemberUpdated
from aiogram.handlers import ChatMemberHandler
import random


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    name = State()
    age = State()
    MATCHED = State()

# Объект бота
bot = Bot("6687747350:AAEsqbGCXZO-U43JsbS0Rk8GZNmAW4sR8zw")

storage=MemoryStorage()
form_router = Router()

# Диспетчер
dp = Dispatcher(storage=storage)

# Словарь для хранения текущих состояний чатов
active_chats = {}

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Привет!!!"), ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(Form.name)
    await message.reply('Привет, я анонимный чат-знакомств. Как тебя зовут?', reply_markup=reply_markup)

@form_router.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Продолжить!"), ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(Form.age)  # Переходим к следующему состоянию
    await message.reply(f"Приятно познакомиться, {name}! Укажи свой возраст", reply_markup=reply_markup)

@form_router.message(Form.age)
async def get_age(message: types.Message, state: FSMContext):
    age=message.text
    await state.update_data(age=age)

    await message.reply(f"Готовься к поиску путник!!!")

available_users = {}

# @dp.chat_member()
# async def on_chat_member_join(message: types.ChatMemberUpdated):
#     user_id = message.new_chat_member.user.id
#     if user_id != bot.id:  # Игнорируем событие, если это вход бота в чат
#         available_users.append(user_id)
#         print(f"Добавлен новый пользователь. Список доступных пользователей: {available_users}")
#
#
# # Хэндлер на событие выхода пользователя из чата
# @dp.chat_member()
# async def on_chat_member_leave(message: types.ChatMemberUpdated):
#     user_id = message.left_chat_member.user.id
#     if user_id != bot.id:  # Игнорируем событие, если это выход бота из чата
#         available_users.remove(user_id)
#

# @form_router.message(Form.MATCHED)
# async def handle_matched_chat(message: types.Message, state: FSMContext):
#     chat_id = message.chat.id
#     if chat_id in active_chats:
#         partner_chat_id = active_chats[chat_id]
#         if partner_chat_id:
#             await bot.send_message(partner_chat_id, message.text)
#         else:
#             await message.reply("Ожидание собеседника...")
#     else:
#         await message.reply("Чат закончен.")
#         await state.finish()


# @dp.message(Command('search'))
# async def cmd_search(message: types.Message, state: FSMContext):
#     chat_id = message.chat.id
#
#     if chat_id in active_chats:
#         await message.reply("Вы уже ищите!")
#         return
#
#
#
#     user_data = await state.get_data()
#     age = user_data.get("age")
#
#     available_users[f"{message.chat.id}"] = age
#
#     if age is None:
#         await message.reply("Сначала укажите свой возраст с помощью команды /start")
#         return
#
#     suitable_users = get_suitable_users(age)
#     if suitable_users:
#         if str(chat_id) in suitable_users:
#             suitable_users.remove(str(chat_id))  # Удаляем текущего пользователя из списка suitable_users
#
#         if suitable_users:
#             partner_chat_id = random.choice(suitable_users)  # Выбираем случайного подходящего пользователя
#             suitable_users.remove(partner_chat_id)  # Удаляем выбранного пользователя из списка suitable_users
#
#             active_chats[chat_id] = partner_chat_id
#             active_chats[partner_chat_id] = chat_id
#             await state.set_state(Form.MATCHED)
#             await message.reply("Собеседник найден! Можете начинать общение.")
#         else:
#             await message.reply("Нет доступных собеседников. Ожидайте...")
#     else:
#         await message.reply("Нет доступных собеседников. Ожидайте...")


async def check_available_partners(chat_id, state):
    while True:
        suitable_users = get_suitable_users(available_users[chat_id][1])
        if suitable_users:
            if chat_id in suitable_users:
                suitable_users.remove(chat_id)  # Удаляем текущего пользователя из списка suitable_users

            if suitable_users:
                partner_chat_id = random.choice(suitable_users)  # Выбираем случайного подходящего пользователя
                suitable_users.remove(partner_chat_id)  # Удаляем выбранного пользователя из списка suitable_users

                active_chats[chat_id] = partner_chat_id
                active_chats[partner_chat_id] = chat_id
                await state.set_state(Form.MATCHED)

                await bot.send_message(chat_id, "Собеседник найден! Можете начинать общение.")
                await bot.send_message(chat_id, f"Ваш собеседник: {available_users[partner_chat_id][0]}\nУровень жизни: {available_users[partner_chat_id][1]}")
                break  # Выходим из цикла, так как нашелся партнер
        await asyncio.sleep(3)  # Ждем 3 секунды перед следующей проверкой

@dp.message(Command('search'))
async def cmd_search(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    if chat_id in active_chats:
        await message.reply("Вы уже ищете!")
        return

    user_data = await state.get_data()
    name = user_data.get("name")
    age = user_data.get("age")

    available_users[chat_id] = [name, age]

    if age is None:
        await message.reply("Сначала укажите свой возраст с помощью команды /start")
        return

    await message.reply("Ожидайте...")
    asyncio.create_task(check_available_partners(chat_id, state))



def get_suitable_users(age):
    suitable_users = []
    for user_id, user_data in available_users.items():
        user_age = user_data[1]
        if user_age is not None and abs(int(user_age[1]) - int(age)) <= 5:
            suitable_users.append(user_id)
    return suitable_users

# @form_router.message(Form.MATCHED)
# async def handle_matched_chat(message: types.Message, state: FSMContext):
#     chat_id = message.chat.id
#     partner_chat_id = active_chats.get(chat_id)
#
#     if partner_chat_id is None:
#         await message.reply("Вы не в активном чате.")
#         return
#
#     partner_age = available_users.get(partner_chat_id)
#     if partner_age is None:
#         await message.reply("Возраст партнера неизвестен.")
#     else:
#         await message.reply(f"Возраст вашего партнера: {partner_age} лет.")
#


@form_router.message(Form.MATCHED)
async def handle_matched_chat(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    if chat_id in active_chats:
        partner_chat_id = active_chats[chat_id]

        if partner_chat_id:
            if message.text:
                await bot.send_message(partner_chat_id, message.text)
            elif message.voice:
                await bot.send_voice(partner_chat_id, message.voice.file_id)
            elif message.video:
                await bot.send_video(partner_chat_id, message.video.file_id)
            elif message.photo:
                # Если сообщение содержит фотографию, отправляем самую большую доступную фотографию
                photo = message.photo[-1]  # Получаем самую большую фотографию из списка
                await bot.send_photo(partner_chat_id, photo.file_id)
            elif message.video_note:
                await bot.send_video_note(partner_chat_id, message.video_note.file_id)
            else:
                await message.reply(f"Неподдерживаемый тип сообщения.{message.content_type}")
        else:
            await message.reply("Ожидание собеседника...")
    else:
        await message.reply("Чат закончен.")
        await state.finish()

@dp.message(Command('remove'))
async def handle_remove_command(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    if chat_id in active_chats:
        partner_chat_id = active_chats.pop(chat_id, None)

        if partner_chat_id:
            await bot.send_message(partner_chat_id, "Соединение было оборвано.")
            active_chats.pop(partner_chat_id, None)  # Удаляем информацию о партнере из списка активных чатов
        else:
            await message.reply("Ожидание собеседника...")
    else:
        await message.reply("Вы не в активном чате.")

    await state.finish()



# Запуск процесса поллинга новых апдейтов
async def main():
    dp.include_router(form_router)
    await dp.start_polling(bot)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())