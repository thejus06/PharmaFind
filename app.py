from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"

def search_medicine(name):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, shop, stock FROM medicines WHERE name LIKE ?", ('%' + name + '%',))
    results = cursor.fetchall()
    conn.close()
    return results

def check_login(username, password):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

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

    if request.method == "POST":
        name = request.form["name"]
        stock = request.form["stock"]
        shop = session["user"]
        add_medicine(name, stock, shop)

    return render_template("dashboard.html", user=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")
def add_medicine(name, stock, shop):
    conn = sqlite3.connect("pharma.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO medicines (name, shop, stock) VALUES (?, ?, ?)",
        (name, shop, stock)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True)