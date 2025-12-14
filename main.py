import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

from database import init_db, update_stock, get_balance, STOCK_ITEMS, clear_stock

# ТОКЕН ОТ @BotFather
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
dp = Dispatcher()


# --- КЛАВИАТУРЫ ---

def get_main_reply_keyboard():
    """Нижнее меню управления: +, -, Balance."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="+")
    builder.button(text="-")
    builder.button(text="Balance")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def get_items_inline_keyboard(mode):
    """Сетка кнопок выбора товара (по 4 в ряд)."""
    builder = InlineKeyboardBuilder()
    sign = "+" if mode == 'add' else "−"
    for item in STOCK_ITEMS:
        builder.button(text=f"{sign} {item}", callback_data=f"item:{mode}:{item}")
    builder.button(text="🔙 Назад", callback_data="action:cancel")
    builder.adjust(4)
    return builder.as_markup()


def create_confirm_keyboard():
    """Подтверждение очистки базы."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Да, очистить всё!", callback_data="confirm:reset")
    builder.button(text="❌ Отмена", callback_data="action:cancel")
    builder.adjust(1)
    return builder.as_markup()


# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "📦 *Складской учет готов к работе*\nВыберите действие на кнопках ниже:",
        reply_markup=get_main_reply_keyboard()
    )


@dp.message(F.text == "Balance")
async def show_balance(message: types.Message):
    data = get_balance()
    # Экранируем спецсимволы для MarkdownV2 внутри блока кода (```)
    table = "📊 *Текущий баланс*\n\n"
    table += "```\n"
    table += f"{'Товар':<8} | {'Кол-во':>5}\n"
    table += "—" * 16 + "\n"
    for name, qty in data:
        table += f"{name:<8} | {qty:>5}\n"
    table += "```"
    await message.answer(table)


@dp.message(F.text.in_({"+", "-"}))
async def cmd_change(message: types.Message):
    mode = "add" if message.text == "+" else "subtract"
    label = "ПРИХОД" if mode == "add" else "РАСХОД"
    await message.answer(
        f"🔹 Режим: *{label}*\nВыберите позицию:",
        reply_markup=get_items_inline_keyboard(mode)
    )


@dp.callback_query(F.data.startswith("item:"))
async def process_item(callback: types.CallbackQuery):
    _, mode, item_name = callback.data.split(":")
    amount = 1 if mode == "add" else -1

    new_qty = update_stock(item_name, amount)

    # 1. Всплывающее уведомление (сверху)
    res_text = "Добавлено" if amount > 0 else "Списано"
    alert_text = f"✅ {res_text}: {item_name}"

    if mode == "subtract" and new_qty < 0:
        alert_text = "⚠️ Внимание: ушли в минус!"

    await callback.answer(alert_text, show_alert=False)  # show_alert=True сделает окно с кнопкой OK

    # 2. Удаляем инлайн-меню и отправляем новое сообщение с подтверждением
    await callback.message.delete()

    await callback.message.answer(
        f"✅ Обновлено: *{item_name}*\n"
        f"Действие: *{'+' if amount > 0 else ''}{amount} шт.*\n"
        f"Текущий остаток: *{new_qty}*",
        reply_markup=get_main_reply_keyboard()  # Теперь это сработает, так как это новое сообщение
    )


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    await message.answer(
        "🚨 *ВНИМАНИЕ\\!* Вы собираетесь обнулить весь склад\\.\nВы уверены?",
        reply_markup=create_confirm_keyboard()
    )


@dp.callback_query(F.data == "confirm:reset")
async def process_reset(callback: types.CallbackQuery):
    clear_stock()
    await callback.message.edit_text("✅ База данных успешно очищена\\.")
    await callback.answer()


@dp.callback_query(F.data == "action:cancel")
async def process_cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("Действие отменено\\.")
    await callback.answer()


# --- ЗАПУСК ---

async def main():
    init_db()
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")