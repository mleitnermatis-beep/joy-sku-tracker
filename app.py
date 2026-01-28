from flask import Flask, render_template, request, jsonify, send_from_directory
import os, zipfile, datetime, requests

app = Flask(__name__)
BASE_DOWNLOAD = "downloads"
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

# ------------------------
# 🔍 Téléchargement images
# ------------------------
def download_images(query, target_folder, limit=5):
    os.makedirs(target_folder, exist_ok=True)

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_images",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 20,                 # on récupère plus pour filtrer
        "tbs": "isz:l"             # grandes images uniquement
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    results = response.json().get("images_results", [])

    downloaded = 0

    for img in results:
        if downloaded >= limit:
            break

        try:
            img_url = img.get("original")
            if not img_url:
                continue

            img_data = requests.get(img_url, timeout=15).content

            # 🧪 Filtrage simple par taille (évite miniatures)
            if len(img_data) < 150_000:   # ~150 KB minimum
                continue

            filename = f"image_{downloaded+1}.jpg"
            with open(os.path.join(target_folder, filename), "wb") as f:
                f.write(img_data)

            downloaded += 1

        except Exception as e:
            print("Download error:", e)

    return downloaded


# ------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run():
    data = request.json.get("rows", [])
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    session_dir = os.path.join(BASE_DOWNLOAD, today)
    os.makedirs(session_dir, exist_ok=True)

    for row in data:
        sku = row.get("sku", "unknown")
        brand = row.get("brand", "")
        name = row.get("name", "")
        size = row.get("size", "")

        query = f"{brand} {name} {size}"
        sku_dir = os.path.join(session_dir, sku)

        print("Searching:", query)
        download_images(query, sku_dir, limit=5)

    zip_name = f"joy_sku_{today}.zip"
    zip_path = os.path.join(BASE_DOWNLOAD, zip_name)

    with zipfile.ZipFile(zip_path, "w") as z:
        for root, _, files in os.walk(session_dir):
            for file in files:
                full = os.path.join(root, file)
                z.write(full, arcname=os.path.relpath(full, session_dir))

    return jsonify({
        "zip": zip_name,
        "download_url": f"/download/{zip_name}"
    })

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(BASE_DOWNLOAD, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
