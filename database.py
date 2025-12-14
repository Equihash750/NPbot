import sqlite3

STOCK_ITEMS = ['05', '055', '1', '11', '2', '22', '3', '33', '4', '5', '10', '15', '20', '30', '301', '30кв']

def init_db():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            name TEXT PRIMARY KEY,
            quantity INTEGER DEFAULT 0
        )
    ''')
    data_to_insert = [(item, 0) for item in STOCK_ITEMS]
    cursor.executemany('INSERT OR IGNORE INTO inventory (name, quantity) VALUES (?, ?)', data_to_insert)
    conn.commit()
    conn.close()

def update_stock(name, amount):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE name = ?', (amount, name))
    cursor.execute('SELECT quantity FROM inventory WHERE name = ?', (name,))
    new_qty = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_qty  # Исправлено: убрано "git"

def get_balance():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, quantity FROM inventory')
    data = dict(cursor.fetchall())
    conn.close()
    return [(item, data.get(item, 0)) for item in STOCK_ITEMS]

def clear_stock():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE inventory SET quantity = 0')
    conn.commit()
    conn.close()

# Данные тарифов из таблицы
DELIVERY_TARIFFS = {
    "Польща 🇵🇱": {"up_to_01": 330, "up_to_025": 350, "up_to_05": 370, "up_to_1": 400, "next_kg": 20},
    "Канада 🇨🇦": {"up_to_01": 450, "up_to_025": 500, "up_to_05": 700, "up_to_1": 1000, "next_kg": 280},
    "Чехія/Литва/Німеччина/Словаччина 🇪🇺": {"up_to_01": 480, "up_to_025": 500, "up_to_05": 520, "up_to_1": 550, "next_kg": 45},
    "Італія/Латвія/Франція/Велика Британія 🌍": {"up_to_01": 880, "up_to_025": 900, "up_to_05": 920, "up_to_1": 950, "next_kg": 55},
    "Іспанія 🇪🇸": {"up_to_01": 1050, "up_to_025": 1070, "up_to_05": 1100, "up_to_1": 1150, "next_kg": 45},
}

def calculate_delivery_cost(country_name, weight):
    """Расчет стоимости на основе веса и тарифов таблицы."""
    rates = DELIVERY_TARIFFS.get(country_name)
    if not rates:
        return None

    if weight <= 0.1:
        return rates["up_to_01"]
    elif weight <= 0.25:
        return rates["up_to_025"]
    elif weight <= 0.5:
        return rates["up_to_05"]
    elif weight <= 1.0:
        return rates["up_to_1"]
    else:
        # Стоимость за 1 кг + (остаток веса * тариф за каждый след. кг)
        # В таблице указано "+ цена за следующий 1 кг"
        extra_weight = weight - 1.0
        return rates["up_to_1"] + (extra_weight * rates["next_kg"])
