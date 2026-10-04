# competitor_feeder.py

'''
competitor_feeder.py, yarışma sırasında gerçek rakip İHA'lar yokken onların yerine geçen bir telemetri üreticisidir.
Belirlenen merkez koordinatı etrafında dairesel hareket eden 8 sanal rakip oluşturur, her 0.5 saniyede bir bu rakiplerin konum
ve temel telemetri bilgilerini hesaplar ve POST /api/telemetry/competitors endpoint'i üzerinden Flask sunucusuna gönderir.
Böylece yer kontrol istasyonu, gerçek rakipler olmadan da rakip telemetri akışını test edebilir.
'''

import time
import math
import random
import requests

BASE_URL = "http://127.0.0.1:9999"
POST_URL = BASE_URL + "/api/telemetry/competitors"

# YARIŞMA AYARI
HZ = 2.0                 # 2 Hz (stabil)
DT = 1.0 / HZ

CENTER_LAT = 40.843
CENTER_LON = 31.156

N_TARGETS = 8            # 2 rakip denemiştim sonra 8 denemişim

def meters_to_lat(m):
    return m / 111111.0

def meters_to_lon(m, lat):
    return m / (111111.0 * math.cos(math.radians(lat)))

# BAŞLANGIÇ HEDEFLERİ
targets = []
for i in range(N_TARGETS):
    targets.append({
        "id": f"T{i+1}",
        "r": 150 + i * 20,        # yarıçap (metre)
        "w": 0.02 + i * 0.01,      # hız (daha stabil)
        "phase": random.random() * 2 * math.pi
    })

t0 = time.time()
print("Feeder başladı ->", POST_URL)

while True:
    t = time.time() - t0
    payload = []

    for s in targets:
        ang = s["phase"] + s["w"] * t

        north = s["r"] * math.cos(ang)
        east  = s["r"] * math.sin(ang)

        # AZ jitter (stabil)
        north += random.uniform(-1, 1)
        east  += random.uniform(-1, 1)

        lat = CENTER_LAT + meters_to_lat(north)
        lon = CENTER_LON + meters_to_lon(east, CENTER_LAT)

        payload.append({
            "id": s["id"],
            "lat": lat,
            "lon": lon,
            "iha_irtifa": str(round(100.0 + (i * 10), 3)),
            "iha_dikilme": str(round(random.uniform(-0.1, 0.1), 4)),
            "iha_yonelme": str(int(ang * (180 / math.pi) % 360)),
            "iha_yatis": str(round(random.uniform(-0.5, 0.5), 4)),
            "iha_hiz": str(round(random.uniform(12.0, 18.0), 3)),
            "gps_saati": {
                "saat": time.localtime().tm_hour,
                "dakika": time.localtime().tm_min,
                "saniye": time.localtime().tm_sec,
                "milisaniye": int((time.time() % 1) * 1000)
            }
        })

    try:
        r = requests.post(POST_URL, json=payload, timeout=1.0)
        '''
        print("POST", r.status_code, "targets:", len(payload))
        '''
    except Exception as e:
        print("POST hata:", e)

    time.sleep(DT)
