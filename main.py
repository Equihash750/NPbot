import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from database import (
    init_db, update_stock, get_balance, STOCK_ITEMS, clear_stock,
    DELIVERY_TARIFFS, calculate_delivery_cost
)

# Переменные окружения
API_TOKEN = os.getenv('BOT_TOKEN')

# Настройка бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
# MemoryStorage важен для работы состояний (кнопка Стоимость МЭН)
dp = Dispatcher(storage=MemoryStorage())


class CalculatorStates(StatesGroup):
    choosing_country = State()
    entering_weight = State()


# --- КЛАВИАТУРЫ ---

def get_main_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Стоимость МЭН") # Убедитесь, что текст здесь...
    builder.button(text="+")
    builder.button(text="-")
    builder.button(text="Balance")
    builder.adjust(1, 2, 1) # Сделаем кнопку МЭН первой и большой
    return builder.as_markup(resize_keyboard=True)

def get_countries_keyboard():
    builder = InlineKeyboardBuilder()
    for code, data in DELIVERY_TARIFFS.items():
        # Текст на кнопке длинный, но callback_data короткий (например, calc:eu_central)
        builder.button(text=data["name"], callback_data=f"calc:{code}")
    builder.button(text="🔙 Отмена", callback_data="action:cancel")
    builder.adjust(1)
    return builder.as_markup()


# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()  # Сбрасываем любые состояния при старте
    await message.answer(
        "📦 *Складской учет и расчет доставки*\nВыберите действие:",
        reply_markup=get_main_reply_keyboard()
    )


# Обработчик кнопки "Стоимость МЭН"
# Добавляем state="*", чтобы кнопка работала, даже если бот что-то ждет
@dp.message(lambda message: message.text and message.text.strip().lower() == "стоимость мэн")
async def start_calculator(message: types.Message, state: FSMContext):
    print("Лог: Кнопка нажата!") # Это появится в логах Railway
    await state.clear()
    await state.set_state(CalculatorStates.choosing_country)
    await message.answer(
        "🌍 *Выберите страну доставки:*",
        reply_markup=get_countries_keyboard()
    )


@dp.callback_query(F.data.startswith("calc:"))
async def process_country_choice(callback: types.CallbackQuery, state: FSMContext):
    country_code = callback.data.split(":")[1]
    country_full_name = DELIVERY_TARIFFS[country_code]["name"]  # Получаем красивое имя

    await state.update_data(selected_country_code=country_code)  # Сохраняем КОД
    await state.set_state(CalculatorStates.entering_weight)

    await callback.message.edit_text(
        f"📍 Выбрано: *{country_full_name.replace('.', r'\.')}*\n\n"
        "Введите вес посылки в кг (например: `0.5` или `1.2`):"
    )
    await callback.answer()


@dp.message(CalculatorStates.entering_weight)
async def process_weight_input(message: types.Message, state: FSMContext):
    weight_str = message.text.replace(",", ".")
    try:
        weight = float(weight_str)
        if weight <= 0: raise ValueError
    except ValueError:
        await message.answer(r"❌ Ошибка! Введите число (например: 0.5)")
        return

    user_data = await state.get_data()
    code = user_data.get('selected_country_code')
    country_name = DELIVERY_TARIFFS[code]["name"]  # Для вывода в сообщении

    cost = calculate_delivery_cost(code, weight)

    safe_name = country_name.replace(".", r"\.").replace("-", r"\-")
    await message.answer(
        f"📊 *Результат расчета*\n\n"
        f"🏳️ Страна: *{safe_name}*\n"
        f"⚖️ Вес: *{weight} кг*\n"
        f"💰 Стоимость: *{cost} грн*",
        reply_markup=get_main_reply_keyboard()
    )
    await state.clear()


# --- СКЛАД (ОСТАЛЬНОЕ) ---

@dp.message(F.text == "Balance")
async def show_balance(message: types.Message):
    data = get_balance()
    table = "📊 *Текущий баланс*\n\n```\n"
    table += f"{'Товар':<8} | {'Кол-во':>5}\n" + "—" * 16 + "\n"
    for name, qty in data:
        table += f"{name:<8} | {qty:>5}\n"
    table += "```"
    await message.answer(table, reply_markup=get_main_reply_keyboard())


@dp.message(F.text.in_({"+", "-"}))
async def cmd_change(message: types.Message):
    mode = "add" if message.text == "+" else "subtract"

    builder = InlineKeyboardBuilder()
    sign = "+" if mode == 'add' else "−"
    for item in STOCK_ITEMS:
        builder.button(text=f"{sign} {item}", callback_data=f"item:{mode}:{item}")
    builder.button(text="🔙 Назад", callback_data="action:cancel")
    builder.adjust(4)

    await message.answer(
        f"🔹 Режим: *{'ПРИХОД' if mode == 'add' else 'РАСХОД'}*\nВыберите позицию:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("item:"))
async def process_item(callback: types.CallbackQuery):
    _, mode, item_name = callback.data.split(":")
    amount = 1 if mode == "add" else -1
    new_qty = update_stock(item_name, amount)

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Обновлено: *{item_name.replace('.', r'\.')}*\n"
        f"Остаток: *{new_qty}*",
        reply_markup=get_main_reply_keyboard()
    )


@dp.callback_query(F.data == "action:cancel")
async def process_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(r"Действие отменено\.", reply_markup=get_main_reply_keyboard())


async def main():
    init_db()
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())