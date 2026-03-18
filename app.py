from flask import Flask, render_template, request, send_file
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    df = pd.read_excel(file)

    # Filter marks < 12
    filtered = df[df["Marks"] < 12]

    output_file = "students_below_12.xlsx"
    filtered.to_excel(output_file, index=False)

    return send_file(output_file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)