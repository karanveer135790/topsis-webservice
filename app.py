from flask import Flask, render_template, request
import os
import pandas as pd
from werkzeug.utils import secure_filename

import smtplib
from email.message import EmailMessage

# ✅ Import TOPSIS function from your deployed package
# Make sure your package has a function named `topsis(input_file, weights, impacts, output_file)`
from Topsis_Karanveer_102303670.topsis import topsis

app = Flask(__name__)

# ✅ Folders
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


# ✅ Email Function
def send_email(receiver_email, filepath):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_pass = os.getenv("SENDER_PASS")

    if not sender_email or not sender_pass:
        raise Exception("Email environment variables not set (SENDER_EMAIL / SENDER_PASS missing)")

    msg = EmailMessage()
    msg["Subject"] = "TOPSIS Result File"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content("Your TOPSIS result file is attached.")

    with open(filepath, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(filepath)

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="octet-stream",
        filename=file_name
    )

    # ✅ Gmail SMTP SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_pass)
        server.send_message(msg)


@app.route("/", methods=["GET", "POST"])
def index():
    message = ""

    if request.method == "POST":
        try:
            # ✅ Get form values
            weights = request.form.get("weights", "").strip()
            impacts = request.form.get("impacts", "").strip()
            email = request.form.get("email", "").strip()

            # ✅ File handling
            if "file" not in request.files:
                return render_template("index.html", message="❌ No file part found!")

            file = request.files["file"]

            if file.filename == "":
                return render_template("index.html", message="❌ No file selected!")

            filename = secure_filename(file.filename)

            # ✅ Save uploaded file
            input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(input_path)

            # ✅ Validate CSV format
            if not filename.lower().endswith(".csv"):
                return render_template("index.html", message="❌ Upload only CSV file!")

            # ✅ Basic validation for weights/impacts
            if not weights or not impacts:
                return render_template("index.html", message="❌ Please enter weights and impacts!")

            w_list = weights.split(",")
            i_list = impacts.split(",")

            if len(w_list) != len(i_list):
                return render_template("index.html", message="❌ Weights count must equal impacts count!")

            if not all(x in ["+", "-"] for x in i_list):
                return render_template("index.html", message="❌ Impacts must contain only + or -")

            # ✅ Output file name
            output_filename = "topsis_result.csv"
            output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

            # ✅ Run TOPSIS
            topsis(input_path, weights, impacts, output_path)

            # ✅ Send email
            try:
                send_email(email, output_path)
                message = "✅ TOPSIS Done! Result file sent to your email."
            except Exception as e:
                message = f"✅ TOPSIS Done, but Email Failed: {str(e)}"

        except Exception as e:
            message = f"❌ Error while processing TOPSIS: {str(e)}"

    return render_template("index.html", message=message)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
