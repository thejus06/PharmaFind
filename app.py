from flask import Flask, render_template, request, redirect, session
import sqlite3
import math

app = Flask(__name__)
app.secret_key = "secretkey"

# ----------------------
# DB HELPER
# ----------------------
def get_db():
    return sqlite3.connect("pharma.db")

# ----------------------
# DISTANCE
# ----------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return round(R * c, 2)

# ----------------------
# SEARCH
# ----------------------
def search_medicine(name):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.name,
               u.shop_name,
               SUM(m.stock),
               u.latitude,
               u.longitude,
               u.phone
        FROM medicines m
        JOIN users u ON m.shop = u.username
        WHERE m.name LIKE ?
        GROUP BY m.name, u.shop_name
    """, ('%' + name + '%',))

    results = cursor.fetchall()
    conn.close()
    return results

# ----------------------
# AUTH
# ----------------------
def check_login(username, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()
    return user

# ----------------------
# MEDICINES
# ----------------------
def add_medicine(name, stock, shop):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, stock FROM medicines WHERE name=? AND shop=?",
        (name, shop)
    )
    existing = cursor.fetchone()

    if existing:
        new_stock = existing[1] + int(stock)
        cursor.execute(
            "UPDATE medicines SET stock=? WHERE id=?",
            (new_stock, existing[0])
        )
    else:
        cursor.execute(
            "INSERT INTO medicines (name, shop, stock) VALUES (?, ?, ?)",
            (name, shop, stock)
        )

    conn.commit()
    conn.close()

def get_pharmacy_medicines(shop):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, stock FROM medicines WHERE shop=?",
        (shop,)
    )
    meds = cursor.fetchall()
    conn.close()
    return meds

# ----------------------
# ROUTES
# ----------------------
@app.route("/", methods=["GET", "POST"])
def home():
    results = []

    if request.method == "POST":
        medicine = request.form["medicine"]
        user_lat = request.form.get("user_lat")
        user_lon = request.form.get("user_lon")

        raw = search_medicine(medicine)

        for r in raw:
            name, shop, stock, plat, plon, phone = r
            distance = None

            try:
                if user_lat and user_lon and plat and plon:
                    distance = calculate_distance(user_lat, user_lon, plat, plon)
            except:
                distance = None

            results.append((name, shop, stock, plat, plon, distance, phone))

        # SORT BY DISTANCE
        results.sort(key=lambda x: x[5] if x[5] is not None else 9999)

    return render_template("index.html", results=results)

# ----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        shop_name = request.form["shop_name"]
        phone = request.form["phone"]
        lat = request.form.get("latitude")
        lon = request.form.get("longitude")

        conn = get_db()
        cursor = conn.cursor()

        # duplicate username check
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            conn.close()
            return "Username already exists"

        cursor.execute("""
            INSERT INTO users (username, password, shop_name, phone, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password, shop_name, phone, lat, lon))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = check_login(username, password)
        if user:
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html")

# ----------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    shop = session["user"]

    if request.method == "POST":
        name = request.form["name"]
        stock = request.form["stock"]
        add_medicine(name, stock, shop)

    medicines = get_pharmacy_medicines(shop)
    return render_template("dashboard.html", medicines=medicines)

# ----------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ----------------------
@app.route("/edit/<int:medicine_id>", methods=["GET", "POST"])
def edit_medicine(medicine_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        new_stock = request.form["stock"]
        cursor.execute(
            "UPDATE medicines SET stock=? WHERE id=? AND shop=?",
            (new_stock, medicine_id, session["user"])
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    cursor.execute(
        "SELECT id, name, stock FROM medicines WHERE id=? AND shop=?",
        (medicine_id, session["user"])
    )
    medicine = cursor.fetchone()
    conn.close()

    return render_template("edit.html", medicine=medicine)

# ----------------------
@app.route("/delete/<int:medicine_id>")
def delete_medicine(medicine_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM medicines WHERE id=? AND shop=?",
        (medicine_id, session["user"])
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ----------------------
@app.route("/update_location", methods=["POST"])
def update_location():
    if "user" not in session:
        return redirect("/login")

    lat = request.form["latitude"]
    lon = request.form["longitude"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET latitude=?, longitude=? WHERE username=?",
        (lat, lon, session["user"])
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ----------------------
if __name__ == "__main__":
    app.run(debug=True)