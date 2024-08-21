from aiogram import Bot, Dispatcher, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder, ReplyKeyboardMarkup
from random import choice

import asyncio

import requests
import sqlite3
from config import BOT_TOKEN
import logging

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher()

button_register = [KeyboardButton(text="Регистрация")]
button_exchange = [KeyboardButton(text="Курс валют")]
button_tips = [KeyboardButton(text="Совет")]
button_finance = [KeyboardButton(text="Расходы")]

keyboard = ReplyKeyboardMarkup(keyboard=[button_register, button_exchange, button_tips, button_finance], resize_keyboard=True)

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT,
    category1 TEXT,
    category2 TEXT,
    category3 TEXT,
    expense1 REAL,
    expense2 REAL,
    expense3 REAL
    
)""")

conn.commit()

class FinanceForm(StatesGroup):
    category1 = State()
    category2 = State()
    category3 = State()
    expense1 = State()
    expense2 = State()
    expense3 = State()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Привет, {message.from_user.full_name} !Ты попал к нам, не пытайся бежать. А так это финансовый бот :)", reply_markup=keyboard)

@dp.message(F.text == "Регистрация")
async def cmd_register(message: Message):
    await message.answer(f"Регистрация", reply_markup=keyboard)
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    cursor.execute(f"SELECT * FROM users WHERE telegram_id = {telegram_id}")
    user = cursor.fetchone()
    if user is None:
        cursor.execute(f"INSERT INTO users (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
        conn.commit()
        await message.answer(f"Вы успешно зарегистрированы, и не удалите свой аккаунт :) и ваши данные отгружены в пентагон")
    else:
        await message.answer(f"Ваши данные уже в пентагоне, не переживайте :)")

@dp.message(F.text == "Курс валют")
async def cmd_exchange(message: Message):
    await message.answer(f"Курс валют", reply_markup=keyboard)
    url = "https://v6.exchangerate-api.com/v6/0f0c2a4ec1a1aa4d722c02f3/latest/USD"
    try:
        request = requests.get(url)
        result = request.json()

        if request.status_code != 200:
            await message.answer(f"Произошла ошибка при запросе курса валют")
            return
        usd_to_rub = result["conversion_rates"]["RUB"]
        usd_to_eur = result["conversion_rates"]["EUR"]
        euro_to_rub = result["conversion_rates"]["RUB"] / result["conversion_rates"]["EUR"]
        await message.answer(f"1 USD = {usd_to_rub:.2f} RUB\n 1 USD = {usd_to_eur:.2f} EUR\n 1 EUR = {euro_to_rub:.2f} RUB")
    except Exception as e:
        await message.answer(f"Произошла ошибка")
        print("Error: ", e)

@dp.message(F.text == "Совет")
async def cmd_tips(message: Message):
    tips = ["Совет 1 - Введите бюджет и следите за расходами", "Совет 2 - Откладывайте часть доходов на сбреежения", "Совет 3 - покупайте товары по скидкам и распродажам"]
    await message.answer(choice(tips), reply_markup=keyboard)

@dp.message(F.text == "Расходы")
async def cmd_finance(message: Message, state: FSMContext):
    await message.answer(f"Категория 1", reply_markup=keyboard)
    await state.set_state(FinanceForm.category1.state)

@dp.message(FinanceForm.category1)
async def process_category1(message: Message, state: FSMContext):
    await state.update_data(category1=message.text)
    await message.answer(f"Расход", reply_markup=keyboard)
    await state.set_state(FinanceForm.expense1.state)
@dp.message(FinanceForm.expense1)
async def process_expense1(message: Message, state: FSMContext):
    await state.update_data(expense1=float(message.text))
    data = await state.get_data()
    await message.answer(f"Категория 2", reply_markup=keyboard)
    await state.set_state(FinanceForm.category2.state)

@dp.message(FinanceForm.category2)
async def process_category2(message: Message, state: FSMContext):
    await state.update_data(category2=message.text)
    await message.answer(f"Расход", reply_markup=keyboard)
    await state.set_state(FinanceForm.expense2.state)

@dp.message(FinanceForm.expense2)
async def process_expense2(message: Message, state: FSMContext):
    await state.update_data(expense2=float(message.text))
    data = await state.get_data()
    await message.answer(f"Категория 3", reply_markup=keyboard)
    await state.set_state(FinanceForm.category3.state)

@dp.message(FinanceForm.category3)
async def process_category3(message: Message, state: FSMContext):
    await state.update_data(category3=message.text)
    await message.answer(f"Расход", reply_markup=keyboard)
    await state.set_state(FinanceForm.expense3.state)

@dp.message(FinanceForm.expense3)
async def process_expense3(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = message.from_user.id
    cursor.execute(f"UPDATE users SET category1 = ?, category2 = ?, category3 = ?, expense1 = ?, expense2 = ?, expense3 = ? WHERE telegram_id = {telegram_id}", (data["category1"], data["category2"], data["category3"], data["expense1"], data["expense2"], float(message.text)))
    conn.commit()
    await state.clear()

    await message.answer(f"Вы успешно добавили информацию. Налоговая система США уже исследует ваши расходы.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())