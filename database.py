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
