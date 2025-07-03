
from flask import Flask, render_template, request, send_file
from watermark import add_watermark
from crypto_utils import generate_keys, encrypt_file, decrypt_file, sign_data, verify_signature
import os
import base64
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("static", "uploads")
KEYS_FOLDER = "keys"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(KEYS_FOLDER, exist_ok=True)

generate_keys()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("image")
        watermark_text = request.form.get("watermark_text", "© YourSite")
        if not file:
            return "No file uploaded", 400

        filename = file.filename
        original_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(original_path)

        watermarked_filename = f"watermarked_{filename}"
        watermarked_path = os.path.join(UPLOAD_FOLDER, watermarked_filename)
        add_watermark(original_path, watermarked_path, watermark_text)

        encrypted_path = watermarked_path + ".enc"
        key_path = encrypted_path + ".key"
        key = encrypt_file(watermarked_path, encrypted_path)
        with open(key_path, "wb") as kf:
            kf.write(base64.b64encode(key))

        signature = sign_data(watermarked_path)
        sig_path = encrypted_path + ".sig"
        with open(sig_path, "wb") as sig_file:
            sig_file.write(signature)

        zip_filename = os.path.join(UPLOAD_FOLDER, f"{filename}_package.zip")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            zipf.write(encrypted_path, arcname=os.path.basename(encrypted_path))
            zipf.write(sig_path, arcname=os.path.basename(sig_path))
            zipf.write(key_path, arcname=os.path.basename(key_path))

        return send_file(zip_filename, as_attachment=True)
    return render_template("index.html")

@app.route("/decrypt", methods=["GET", "POST"])
def decrypt():
    if request.method == "POST":
        enc_file = request.files.get("encrypted_file")
        sig_file = request.files.get("signature_file")
        key_file = request.files.get("key_file")

        if not enc_file or not sig_file or not key_file:
            return "Thiếu file mã hóa, chữ ký hoặc key.", 400

        enc_path = os.path.join(UPLOAD_FOLDER, enc_file.filename)
        sig_path = os.path.join(UPLOAD_FOLDER, sig_file.filename)
        key_path = os.path.join(UPLOAD_FOLDER, key_file.filename)

        enc_file.save(enc_path)
        sig_file.save(sig_path)
        key_file.save(key_path)

        decrypted_path = enc_path.replace(".enc", "_decrypted.jpg")
        with open(key_path, "rb") as kf:
            try:
                key = base64.b64decode(kf.read())
            except Exception:
                return "Không thể đọc key. Định dạng không hợp lệ.", 400

        if len(key) not in (16, 24, 32):
            return f"Lỗi: Độ dài khóa AES không hợp lệ ({len(key)} bytes)", 400

        try:
            decrypt_file(enc_path, decrypted_path, key)
        except Exception as e:
            return f"Lỗi khi giải mã: {str(e)}", 500

        with open(decrypted_path, "rb") as f:
            decrypted_data = f.read()
        with open(sig_path, "rb") as f:
            signature = f.read()

        is_valid = verify_signature(decrypted_data, signature)
        image_data = base64.b64encode(decrypted_data).decode("utf-8")
        return render_template("decrypted_result.html", image_data=image_data, valid=is_valid)

    return render_template("decrypt.html")

if __name__ == "__main__":
    app.run(debug=True)
