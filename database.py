import sqlite3

# Строгий список позиций в нужном порядке
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
    # Предзаполняем базу, если позиций еще нет
    data_to_insert = [(item, 0) for item in STOCK_ITEMS]
    cursor.executemany('INSERT OR IGNORE INTO inventory (name, quantity) VALUES (?, ?)', data_to_insert)
    conn.commit()
    conn.close()


def update_stock(name, amount):
    """Обновляет количество товара и возвращает новый остаток."""
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()

    # 1. Обновляем количество
    cursor.execute('''
        UPDATE inventory SET quantity = quantity + ? WHERE name = ?
    ''', (amount, name))

    # 2. Получаем новое количество этого товара
    cursor.execute('''
        SELECT quantity FROM inventory WHERE name = ?
    ''', (name,))
    new_qty = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return new_qtygit

def get_balance():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, quantity FROM inventory')
    data = dict(cursor.fetchall())
    conn.close()
    # Возвращаем данные строго по списку STOCK_ITEMS
    return [(item, data.get(item, 0)) for item in STOCK_ITEMS]

def clear_stock():
    """Сброс всех остатков на 0."""
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE inventory SET quantity = 0')
    conn.commit()
    conn.close()

