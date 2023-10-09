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

available_users = []

@dp.chat_member()
async def on_chat_member_join(message: types.ChatMemberUpdated):
    user_id = message.new_chat_member.user.id
    if user_id != bot.id:  # Игнорируем событие, если это вход бота в чат
        available_users.append(user_id)
        print(f"Добавлен новый пользователь. Список доступных пользователей: {available_users}")


# Хэндлер на событие выхода пользователя из чата
@dp.chat_member()
async def on_chat_member_leave(message: types.ChatMemberUpdated):
    user_id = message.left_chat_member.user.id
    if user_id != bot.id:  # Игнорируем событие, если это выход бота из чата
        available_users.remove(user_id)


@dp.message(Command('search'))
async def cmd_search(message: types.Message, state: FSMContext):
    chat_id = message.chat.id


    if chat_id in active_chats:
        await message.reply("Вы уже ищите!")
        return

    available_users.append(chat_id)

    if available_users:

        partner_chat_id = available_users.pop()  # Берем первого доступного пользователя
        active_chats[chat_id] = partner_chat_id
        active_chats[partner_chat_id] = chat_id
        await state.set_state(Form.MATCHED)
        await message.reply("Собеседник найден! Можете начинать общение.")
    else:
        await message.reply("Ожидайте...")

@form_router.message(Form.MATCHED)
async def handle_matched_chat(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in active_chats:
        partner_chat_id = active_chats[chat_id]
        if partner_chat_id:
            await bot.send_message(partner_chat_id, message.text)
        else:
            await message.reply("Ожидание собеседника...")
    else:
        await message.reply("Чат закончен.")
        await state.finish()


# Запуск процесса поллинга новых апдейтов
async def main():
    dp.include_router(form_router)
    await dp.start_polling(bot)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())