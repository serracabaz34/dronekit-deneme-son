# AZAK SİHA — Yer Kontrol İstasyonu (GCS)

TEKNOFEST 2026 Savaşan İHA yarışması için geliştirilen yer kontrol istasyonu. PyQt5 tabanlı masaüstü arayüzdür. İHA'dan telemetriyi alır, harita ve HUD üzerinde gösterir, kamera görüntüsünü kaydeder ve yarışma sunucusuyla haberleşir.

> Çalışan uygulama **`YerKontrolAzakSiha/`** klasörüdür. Başlangıç dosyası `YerKontrolAzakSiha/main.py`.
> Kök dizindeki `.py` dosyaları (`arayuz_backend.py`, `kayitli_kodlar.py`, `main.py` vb.) eski denemelerdir. `rakipten_kacis/` ise kaçış algoritmasının sade, bağımsız bir sürümüdür.

## Gereksinimler

| Gereksinim | Not |
|---|---|
| **Python 3.9** | Sürüm önemli. `dronekit 2.9.2` yeni Python sürümlerinde (3.10+) çalışmaz. Proje 3.9.13 ile geliştirildi. |
| **PyQt5 + PyQtWebEngine** | Arayüz ve harita (Leaflet) gösterimi |
| **dronekit, pymavlink** | Araç bağlantısı ve MAVLink |
| **opencv-python, numpy** | Kamera görüntüsü ve kayıt |
| **requests** | Yarışma sunucusu istekleri |
| **FFmpeg** | Video kaydını MP4'e çevirmek ve sunucuya canlı yayın için (aşağıya bakın) |
| flask | Sadece yerel test sunucusu için (`test_server.py`) |
| rclpy (ROS 2) | **Sadece** `gcs_bridge_node.py` için, ana uygulama için gerekmez |

Python paketleri `requirements.txt` içinde.

## Kurulum (Windows)

```powershell
# 1) Python 3.9 ile sanal ortam
py -3.9 -m venv venv39
venv39\Scripts\activate

# 2) Paketleri kur
pip install -r requirements.txt
```

### FFmpeg

FFmpeg'i indirip kurun (https://ffmpeg.org/download.html, Windows için "full build" önerilir).

Uygulama FFmpeg yolunu koda sabit yazılmış olarak bekler. `YerKontrolAzakSiha/arayuzBackend.py` dosyasında (yaklaşık 393. satır):

```python
ffmpeg_path = r"C:\ffmpeg\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
```

İki seçenek var:
- FFmpeg'i tam olarak bu klasöre açın, **veya**
- Bu satırdaki yolu kendi `ffmpeg.exe` yolunuzla değiştirin.

FFmpeg bulunamazsa video kaydı yine alınır ama MP4'e çevrilmez (AVI olarak kalır); canlı yayın çalışmaz.

## Çalıştırma

```powershell
cd YerKontrolAzakSiha
python main.py
```

## Bağlantı ayarları

Bunlar kodda sabittir, kendi ağınıza göre değiştirin (`YerKontrolAzakSiha/arayuzBackend.py`):

| Ne | Varsayılan | Satır |
|---|---|---|
| ArduPilot (DroneKit) | `tcp:192.168.1.16:14553` | ~496 |
| Jetson MAVLink | `tcp:192.168.1.16:14550` | ~550 |
| Kamera | PC kamerası, `cam_index=0` | ~394 |

Araç veya Jetson bağlı değilse bu bağlantı denemeleri başarısız olur.

Yarışma sunucusunun adresi, kullanıcı adı ve şifresi **arayüzden** girilir. Kodda veya depoda saklanmaz.

Kamera açılınca video kaydı otomatik başlar, dosyalar `records/` klasörüne yazılır.

## Yerel test sunucusu

Yarışma sunucusu olmadan denemek için:

```powershell
cd YerKontrolAzakSiha
python test_server.py
```

Sahte sunucu `http://127.0.0.1:9999` adresinde çalışır. Arayüzde sunucu adresi olarak bunu, kullanıcı adı `test` ve şifre `1234` girin. `competitor_feeder_random.py` bu sahte sunucuya rastgele rakip verisi besler.

## Klasör yapısı (`YerKontrolAzakSiha/`)

| Dosya | Görev |
|---|---|
| `main.py` | Uygulamayı başlatır |
| `arayuzBackend.py` | Ana pencere mantığı: kamera, telemetri, harita, sunucu, buton olayları |
| `sihaArayuz.py/.ui`, `mod_ekrani.py/.ui`, `Uydu_Hud_Ekrani.py/.ui` | Qt Designer arayüzleri |
| `hud_widget.py`, `gostergeler.py` | HUD ve gösterge bileşenleri |
| `flight_controller.py` | Uçuş komutları (kalkış, iniş, mod) |
| `jetson_mavlink_bridge.py` | Jetson'dan MAVLink telemetri okuma |
| `server_service.py` | Yarışma sunucusu istemcisi (giriş, telemetri, video, HSS koordinatları) |
| `map.html`, `leaflet*` | Harita |
| `gcs_bridge_node.py` | MAVLink ↔ ROS 2 köprüsü (isteğe bağlı) |
| `icons/`, `*.png`, `icons_rc.py` | Görseller |

## Notlar

- `Jetson_icin_degisiklikler.txt`: kamerayı PC kamerası yerine Jetson'dan gelen UDP yayınına (`udp://0.0.0.0:5600`) geçirmek için yapılacak değişikliklerin notudur. FFmpeg'i bu yöntemde zorunlu olmaktan çıkarır.
- Geliştirme ortamı: Windows, Python 3.9.13.
