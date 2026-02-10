import sqlite3

conn = sqlite3.connect("pharma.db")
cursor = conn.cursor()

# Medicines table
cursor.execute("""
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    shop TEXT NOT NULL,
    stock INTEGER NOT NULL
)
""")

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Sample user
cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('pharmacy1', '1234')")

# Sample medicines
cursor.execute("INSERT INTO medicines (name, shop, stock) VALUES ('Paracetamol', 'City Pharmacy', 20)")
cursor.execute("INSERT INTO medicines (name, shop, stock) VALUES ('Ibuprofen', 'HealthPlus Medical', 15)")

conn.commit()
conn.close()

print("Database created successfully!")