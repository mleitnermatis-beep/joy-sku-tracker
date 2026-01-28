from flask import Flask, render_template, request, jsonify
import os, zipfile, datetime

app = Flask(__name__)
BASE_DOWNLOAD = "downloads"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run():
    data = request.json.get("rows", [])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    session_dir = os.path.join(BASE_DOWNLOAD, today)
    os.makedirs(session_dir, exist_ok=True)

    # Placeholder (aucune dépendance imghdr)
    for row in data:
        sku = row.get("sku", "unknown")
        sku_dir = os.path.join(session_dir, sku)
        os.makedirs(sku_dir, exist_ok=True)

        with open(os.path.join(sku_dir, "example.txt"), "w") as f:
            f.write("Placeholder for downloaded images")

    zip_name = f"joy_sku_{today}.zip"
    zip_path = os.path.join(BASE_DOWNLOAD, zip_name)

    with zipfile.ZipFile(zip_path, "w") as z:
        for root, _, files in os.walk(session_dir):
            for file in files:
                full = os.path.join(root, file)
                z.write(full, arcname=os.path.relpath(full, session_dir))

    return jsonify({"zip": zip_name})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
