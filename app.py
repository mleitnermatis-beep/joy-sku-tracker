from flask import Flask, render_template, request, send_file, jsonify
import os
import datetime
from bing_image_downloader import downloader
import zipfile
import threading
import time

app = Flask(__name__)

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

progress_state = {
    "total": 0,
    "current": 0,
    "running": False
}

def process_skus(skus):
    global progress_state

    progress_state["total"] = len(skus)
    progress_state["current"] = 0
    progress_state["running"] = True

    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    main_folder = os.path.join(DOWNLOAD_DIR, f'Joy_SKU_Tracker_{date_str}')
    os.makedirs(main_folder, exist_ok=True)

    for item in skus:
        folder_sku = os.path.join(main_folder, item['sku'])
        os.makedirs(folder_sku, exist_ok=True)

        query = f"{item['marque']} {item['nom']} {item['contenance']}" if item['marque'] or item['contenance'] else item['nom']
        try:
            downloader.download(query, limit=3, output_dir=main_folder, adult_filter_off=True, force_replace=False, timeout=60)
            temp_folder = os.path.join(main_folder, query)
            if os.path.exists(temp_folder):
                for f in os.listdir(temp_folder):
                    os.rename(os.path.join(temp_folder, f), os.path.join(folder_sku, f))
                os.rmdir(temp_folder)
        except Exception as e:
            print(f"Erreur pour {item['sku']}: {e}")

        progress_state["current"] += 1
        time.sleep(0.2)

    zip_name = f"Joy_SKU_Tracker_{date_str}.zip"
    zip_path = os.path.join(DOWNLOAD_DIR, zip_name)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(main_folder):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, main_folder)
                zipf.write(full_path, arcname)

    progress_state["running"] = False
    progress_state["zip_path"] = zip_path

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        skus = []
        for i in range(50):
            sku = request.form.get(f'sku_{i}', '').strip()
            marque = request.form.get(f'marque_{i}', '').strip()
            nom = request.form.get(f'nom_{i}', '').strip()
            contenance = request.form.get(f'contenance_{i}', '').strip()
            if sku and nom:
                skus.append({'sku': sku, 'marque': marque, 'nom': nom, 'contenance': contenance})

        thread = threading.Thread(target=process_skus, args=(skus,))
        thread.start()

        return jsonify({"status": "started"})

    return render_template('index.html')

@app.route('/progress')
def progress():
    if progress_state["total"] == 0:
        percent = 0
    else:
        percent = int((progress_state["current"] / progress_state["total"]) * 100)

    return jsonify({
        "current": progress_state["current"],
        "total": progress_state["total"],
        "percent": percent,
        "running": progress_state["running"],
        "zip_path": progress_state.get("zip_path")
    })

@app.route('/download')
def download():
    zip_path = progress_state.get("zip_path")
    if zip_path and os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return "Fichier non prêt", 404

if __name__ == '__main__':
    app.run(debug=True)
