from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"


# ----------------------
# DATABASE FUNCTIONS
# ----------------------

def search_medicine(name):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.name, m.shop, SUM(m.stock) as total_stock,
               u.latitude, u.longitude
        FROM medicines m
        JOIN users u ON m.shop = u.username
        WHERE m.name LIKE ?
        GROUP BY m.name, m.shop
    """, ('%' + name + '%',))

    results = cursor.fetchall()
    conn.close()
    return results


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
        results = search_medicine(medicine)
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