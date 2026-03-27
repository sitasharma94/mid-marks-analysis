from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import io
import sqlite3

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.secret_key = "secret123"

# Global variables
filtered_data = None
last_threshold = None
last_condition = None

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    session.pop("user", None)
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():
    global filtered_data, last_threshold, last_condition

    file = request.files["file"]
    df = pd.read_excel(file)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Detect marks column
    possible_names = ["marks", "midmarks", "mid marks", "score"]

    marks_col = None
    for col in df.columns:
        if col in possible_names:
            marks_col = col
            break

    if marks_col is None:
        return "❌ Marks column not found in Excel file"

    # Get user input
    threshold = request.form.get("threshold")
    condition = request.form.get("condition")

    if not threshold or not condition:
        return "Please provide threshold and condition"

    threshold = int(threshold)

    # Store values for download
    last_threshold = threshold
    last_condition = condition

    # Apply filter
    if condition == "<":
        filtered_data = df[df[marks_col] < threshold]
    elif condition == ">":
        filtered_data = df[df[marks_col] > threshold]
    elif condition == "=":
        filtered_data = df[df[marks_col] == threshold]

    # Display result
    if filtered_data.empty:
        table = "<p style='color:red;'>No matching records found</p>"
    else:
        table = filtered_data.to_html(classes='table table-bordered')

    return render_template("index.html", table=table, show_download=True)

# ---------------- DOWNLOAD ----------------
@app.route("/download")
def download():
    global filtered_data, last_threshold, last_condition

    if filtered_data is None or filtered_data.empty:
        return "No data to download"

    output = io.BytesIO()
    filtered_data.to_excel(output, index=False)
    output.seek(0)

    # Dynamic filename
    if last_condition == "<":
        filename = f"students_below_{last_threshold}.xlsx"
    elif last_condition == ">":
        filename = f"students_above_{last_threshold}.xlsx"
    elif last_condition == "=":
        filename = f"students_equal_{last_threshold}.xlsx"
    else:
        filename = "students_filtered.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            conn.close()
            return "User already exists"

    return render_template("signup.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session.clear()  # 🔥 clear old session
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")
# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)