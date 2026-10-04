from flask import Flask, request, jsonify
import datetime
import time
import json
import os  #  BU SATIRI EKLEYİN (Kırmızı çizgiyi düzelten kısım)

app = Flask(__name__)

# Videoların kaydedileceği klasör (os modülü import edildiği için artık hata vermeyecek)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "server_records")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# RAM'de son rakip telemetri snapshot'ı
LATEST_COMPETITORS = {
    "ts": 0.0,
    "targets": []
}


@app.post("/api/giris")
def login():
    data = request.get_json(silent=True) or {}
    # Resmi dokümana uygun olarak kadi ve sifre kontrol ediliyor
    if data.get("kadi") == "test" and data.get("sifre") == "1234":
        return jsonify({"token": "demo-token"})
    return jsonify({"error": "bad credentials"}), 401


@app.post("/api/connect")
def connect():
    return jsonify({"status": "ok"})


@app.post("/api/telemetri_gonder")
def telemetry():
    data = request.get_json(silent=True) or {}

    print("\n" + "=" * 50)
    print("[KENDİ İHA TELEMETRİMİZ ALINDI]:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("=" * 50 + "\n")

    return jsonify({
        "sunucusaati": get_server_time().json,
        "konumBilgileri": LATEST_COMPETITORS["targets"]
    })

@app.get("/api/sunucusaati")
def get_server_time():
    now = datetime.datetime.now()

    return jsonify({
        "gun": now.day,
        "saat": now.hour,
        "dakika": now.minute,
        "saniye": now.second,
        "milisaniye": int(now.microsecond / 1000)
    })


@app.post("/api/telemetry/competitors")
def competitors_post():
    data = request.get_json(silent=True)

    if isinstance(data, list):
        targets = data
    elif isinstance(data, dict):
        targets = data.get("targets") or data.get("competitors") or []
    else:
        return jsonify({"error": "invalid json"}), 400

    if not isinstance(targets, list):
        return jsonify({"error": "targets must be a list"}), 400

    LATEST_COMPETITORS["ts"] = time.time()
    LATEST_COMPETITORS["targets"] = targets

    print("\n" + "=" * 50)
    print("[RAKİP TELEMETRİLERİ ALINDI]:")
    print(json.dumps(targets, indent=2, ensure_ascii=False))
    print("=" * 50 + "\n")

    return jsonify({"received": True, "count": len(targets)})


@app.get("/api/telemetry/competitors")
def competitors_get():
    return jsonify(LATEST_COMPETITORS)


# VİDEO YÜKLEME ENDPOINT'İ (404 hatasını çözen endpoint)
@app.post("/api/upload_video")
def upload_video():
    file = request.files.get("video") or request.files.get("file")

    if not file:
        print("[VİDEO YÜKLEME HATA]: Dosya bulunamadı!")
        return jsonify({"error": "No file uploaded"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    print("\n" + "=" * 50)
    print(f"[DEĞERLENDİRME VİDEOSU SUNUCUYA YÜKLENDİ]:")
    print(f"Kayıt Yolu: {save_path}")
    print(f"Dosya Boyutu: {os.path.getsize(save_path) / (1024 * 1024):.2f} MB")
    print("=" * 50 + "\n")

    return jsonify({"status": "ok", "message": "Video yüklendi", "path": save_path}), 200


@app.post("/api/logout")
def logout():
    return jsonify({"bye": True})

@app.get("/api/hss_koordinatlari")
def get_hss_koordinatlari():
    now = datetime.datetime.now()
    return jsonify({
        "sunucusaati": {
            "gun": now.day,
            "saat": now.hour,
            "dakika": now.minute,
            "saniye": now.second,
            "milisaniye": int(now.microsecond / 1000)
        },
        "hss_koordinat_bilgileri": [
            {"id": 0, "hssEnlem": 40.23260922, "hssBoylam": 29.00573015, "hssYaricap": 50},
            {"id": 1, "hssEnlem": 40.23351019, "hssBoylam": 28.99976492, "hssYaricap": 50},
            {"id": 2, "hssEnlem": 40.23105297, "hssBoylam": 29.00744677, "hssYaricap": 75},
            {"id": 3, "hssEnlem": 40.23090554, "hssBoylam": 29.00221109, "hssYaricap": 150}
        ]
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9999, debug=True)