from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula
    R = 6371  # Earth radius in km

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
# DATABASE FUNCTIONS
# ----------------------

def search_medicine(name):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.name,
               u.shop_name,
               SUM(m.stock),
               u.latitude,
               u.longitude
        FROM medicines m
        JOIN users u ON m.shop = u.username
        WHERE m.name LIKE ?
        GROUP BY m.name, u.shop_name
    """, ('%' + name + '%',))

    results = cursor.fetchall()
    conn.close()
    return results

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        shop_name = request.form["shop_name"]
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        conn = sqlite3.connect("pharma.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password, shop_name, latitude, longitude) VALUES (?, ?, ?, ?, ?)",
            (username, password, shop_name, latitude, longitude)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

def check_login(username, password):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def add_medicine(name, stock, shop):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()

    # Check if medicine already exists for this pharmacy
    cursor.execute(
        "SELECT id, stock FROM medicines WHERE name=? AND shop=?",
        (name, shop)
    )
    existing = cursor.fetchone()

    if existing:
        # Update stock
        new_stock = existing[1] + int(stock)
        cursor.execute(
            "UPDATE medicines SET stock=? WHERE id=?",
            (new_stock, existing[0])
        )
    else:
        # Insert new medicine
        cursor.execute(
            "INSERT INTO medicines (name, shop, stock) VALUES (?, ?, ?)",
            (name, shop, stock)
        )

    conn.commit()
    conn.close()

def get_pharmacy_medicines(shop):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, stock FROM medicines WHERE shop = ?",
        (shop,)
    )
    medicines = cursor.fetchall()
    conn.close()
    return medicines
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

        raw_results = search_medicine(medicine)

        for r in raw_results:
            name, shop, stock, plat, plon = r

            distance = None

            try:
                if user_lat and user_lon and plat and plon:
                    distance = calculate_distance(
                        float(user_lat),
                        float(user_lon),
                        float(plat),
                        float(plon)
                    )
            except:
                distance = None

            results.append((name, shop, stock, plat, plon, distance))

    return render_template("index.html", results=results)


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

    return render_template("dashboard.html", user=shop, medicines=medicines)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/edit/<int:medicine_id>", methods=["GET", "POST"])
def edit_medicine(medicine_id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("pharma.db")
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

@app.route("/delete/<int:medicine_id>")
def delete_medicine(medicine_id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM medicines WHERE id=? AND shop=?",
        (medicine_id, session["user"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/update_location", methods=["POST"])
def update_location():
    if "user" not in session:
        return redirect("/login")

    latitude = request.form["latitude"]
    longitude = request.form["longitude"]

    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET latitude=?, longitude=? WHERE username=?",
        (latitude, longitude, session["user"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

if __name__ == "__main__":
    app.run(debug=True)