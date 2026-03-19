from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = "secret123"

# store data temporarily
filtered_data = None

USER = {
    "username": "admin",
    "password": "1234"
}

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    global filtered_data

    file = request.files["file"]
    df = pd.read_excel(file)

    filtered_data = df[df["Marks"] < 12]

    table = filtered_data.to_html(classes='table table-bordered')

    return render_template("index.html", table=table, show_download=True)


@app.route("/download")
def download():
    global filtered_data

    output = io.BytesIO()
    filtered_data.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="students_below_12.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == USER["username"] and password == USER["password"]:
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)