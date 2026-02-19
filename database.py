import sqlite3

conn = sqlite3.connect("pharma.db")
cursor = conn.cursor()

# Users table (WITH PHONE)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    shop_name TEXT,
    phone TEXT,
    latitude REAL,
    longitude REAL
)
""")

# Medicines table
cursor.execute("""
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    shop TEXT NOT NULL,
    stock INTEGER NOT NULL,
    price REAL
)
""")

# Sample user
cursor.execute("""
INSERT INTO users (username, password, shop_name, phone, latitude, longitude)
VALUES (?, ?, ?, ?, ?, ?)
""", ("pharmacy1", "1234", "City Pharmacy", "9999999999", 8.5241, 76.9366))

# Sample medicine
cursor.execute("""
INSERT INTO medicines (name, shop, stock, price)
VALUES (?, ?, ?, ?)
""", ("Paracetamol", "pharmacy1", 20, 15.0))

conn.commit()
conn.close()

print("Database created with phone support ✅")