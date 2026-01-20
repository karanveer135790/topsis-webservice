import os
import re
import smtplib
from email.message import EmailMessage

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

# ✅ Import your TOPSIS function (from your PyPI package)
from libname.topsis import topsis

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ✅ Your Email Setup (Gmail App Password)
SENDER_EMAIL = "karanveer467822@gmail.com"
SENDER_PASS = "tmfh mabc lrvx dkjf"   # 16-digit app password


# ✅ Email format validation
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)


# ✅ Send email with result file attached
def send_email(receiver_email, attachment_path):
    msg = EmailMessage()
    msg["Subject"] = "TOPSIS Result File"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email

    msg.set_content("Hello,\n\nYour TOPSIS result file is attached.\n\nThank you!")

    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="octet-stream",
        filename=file_name
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    file = request.files.get("file")
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")
    email = request.form.get("email")

    # ✅ Validations
    if not file or file.filename == "":
        return "❌ Error: Please upload a CSV file."

    if not weights or not impacts or not email:
        return "❌ Error: All fields are required."

    if not is_valid_email(email):
        return "❌ Error: Invalid Email Format."

    # ✅ Split weights and impacts using comma
    weights_list = weights.split(",")
    impacts_list = impacts.split(",")

    if len(weights_list) != len(impacts_list):
        return "❌ Error: Number of weights must be equal to number of impacts."

    if not all(x in ["+", "-"] for x in impacts_list):
        return "❌ Error: Impacts must be either + or -."

    # ✅ Save uploaded file
    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    # ✅ Output file path
    output_filename = "topsis_result_" + filename
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    # ✅ Run TOPSIS
    try:
        topsis(input_path, weights, impacts, output_path)
    except Exception as e:
        return f"❌ Error while processing TOPSIS: {str(e)}"

    # ✅ Email the output file
    try:
        send_email(email, output_path)
    except Exception as e:
        return f"✅ TOPSIS Done, but Email Failed: {str(e)}"

    return f"✅ Success! Result file sent to {email}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
