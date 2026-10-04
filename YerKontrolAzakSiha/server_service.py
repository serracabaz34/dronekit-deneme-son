# server_service.py

# client dosyasıdır, yki ile server ı bağlar
# ServerClient: HTTP isteklerini göndermek
# PyQt ile ServerClient arasındaki köprüdür.

'''
Bu dosya sunucu değildir; yer kontrol istasyonunun istemci (client) katmanıdır.
ServerClient sınıfı HTTP üzerinden Flask sunucusuna GET ve POST isteklerini gönderir.
ServerWorker ise bu işlemleri PyQt'nin sinyal-slot yapısıyla arayüzü dondurmadan yürütür.
Böylece arayüz doğrudan requests çağrıları yapmak yerine ServerWorker üzerinden sunucuyla haberleşir ve alınan veriler sinyaller aracılığıyla kullanıcı arayüzüne aktarılır.
Bu nedenle server_service.py, arayüz ile sunucu arasında çalışan bir haberleşme ve köprü (communication layer) görevi görür.
'''

import os
import requests
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from typing import Optional

# servera istek atan sınıf
class ServerClient:
    ENDPOINT_LOGIN = "/api/giris"
    ENDPOINT_LOGOUT = "/api/logout"
    ENDPOINT_CONNECT = "/api/connect"
    ENDPOINT_TELEMETRY = "/api/telemetri_gonder"
    ENDPOINT_UPLOAD_VIDEO = "/api/upload_video"  # HTTP upload (opsiyonel)
    ENDPOINT_HSS = "/api/hss_koordinatlari"

    def __init__(self, base_url: str, timeout_sec: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_sec
        self.session = requests.Session()  # requests.Session kullanmamızın nedeni aynı sunucuya sürekli istek attığımız için bağlantıyı tekrar kullanarak performansı ve stabiliteyi artırmaktır.
        self.token = None

    def _url(self, path: str):
        return f"{self.base_url}{path}"

    def _headers(self):
        h = {}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def login(self, username: str, password: str):
        payload = {"kadi": username, "sifre": password}
        r = self.session.post(
            self._url(self.ENDPOINT_LOGIN),
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout
        )
        r.raise_for_status()
        data = r.json() if r.content else {}
        self.token = data.get("token") or data.get("access_token") or self.token
        return data

    def logout(self):
        r = self.session.post(
            self._url(self.ENDPOINT_LOGOUT),
            headers=self._headers(),
            timeout=self.timeout
        )
        r.raise_for_status()
        self.token = None
        return r.json() if r.content else {}

    def connect_server(self):
        r = self.session.post(
            self._url(self.ENDPOINT_CONNECT),
            headers=self._headers(),
            timeout=self.timeout
        )
        r.raise_for_status()
        return r.json() if r.content else {}

    def send_telemetry(self, telemetry: dict):
        headers = self._headers()
        headers["Content-Type"] = "application/json"

        r = self.session.post(
            self._url(self.ENDPOINT_TELEMETRY),
            headers=headers,
            json=telemetry,
            timeout=self.timeout
        )
        r.raise_for_status()
        return r.json() if r.content else {}

    # server_service.py -> ServerClient sınıfı içindeki metod:

    def upload_video_file_http(self, video_path: str, field_name: str = "video"):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video dosyası bulunamadı: {video_path}")

        # Sunucu URL'sini ve token başlıklarını doğru yapıdan alıyoruz
        url = self._url(self.ENDPOINT_UPLOAD_VIDEO)
        headers = self._headers()  # Authorization token eklenir

        with open(video_path, 'rb') as f:
            # Sunucunun beklediği dosya parametresi 'video' veya 'file' olabilir
            files = {field_name: (os.path.basename(video_path), f, "video/mp4")}

            # Session üzerinden istek atılarak yetkilendirme korunur
            response = self.session.post(
                url,
                headers=headers,
                files=files,
                timeout=max(self.timeout, 120)
            )

        response.raise_for_status()
        return response.json() if response.content else {}

    def get_server_time(self):
        r = self.session.get(
            self._url("/api/sunucusaati"),
            headers=self._headers(),
            timeout=self.timeout
        )
        r.raise_for_status()
        return r.json()

    def get_hss_koordinatlari(self):
        r = self.session.get(
            self._url(self.ENDPOINT_HSS),
            headers=self._headers(),
            timeout=self.timeout
        )
        r.raise_for_status()
        return r.json() if r.content else {}

# sunucu işlemlerini arayüzü dondurmadan yapan ve ui ile sunucu arasında köprü oluşturan sınıf
class ServerWorker(QObject):
    ok = pyqtSignal(str)
    err = pyqtSignal(str)
    connected_state = pyqtSignal(bool)
    competitors = pyqtSignal(list)   #yeni eklendi bu da
    hss_received = pyqtSignal(list)  # HSS sinyali[cite: 15]
    # bunların hepsi sinyal ve emit ile kullanım yapıldı

    def __init__(self):
        super().__init__()
        # self.client: Optional[ServerClient] = None
        self.client = None
        self.is_connected = False

    @pyqtSlot(str)
    def init_client(self, base_url: str):
        try:
            if not base_url or not base_url.strip():
                raise ValueError("Sunucu adresi boş olamaz.")
            self.client = ServerClient(base_url.strip())
            self.ok.emit("Sunucu client hazır.")
        except Exception as e:
            self.client = None
            self.err.emit(f"Client init hata: {e}")

    @pyqtSlot(str, str)
    def login(self, username: str, password: str):
        try:
            if not self.client:
                raise RuntimeError("Önce sunucu adresi gir (client yok).")
            if not username or not password:
                raise ValueError("Kullanıcı adı/şifre boş olamaz.")
            self.client.login(username, password)
            self.ok.emit("Sunucuya giriş başarılı.")
        except Exception as e:
            self.err.emit(f"Giriş hatası: {e}")

    @pyqtSlot()
    def logout(self):
        try:
            if not self.client:
                raise RuntimeError("Client yok.")
            self.client.logout()
            self.is_connected = False
            self.connected_state.emit(False)
            self.ok.emit("Sunucudan çıkış yapıldı.")
        except Exception as e:
            self.err.emit(f"Çıkış hatası: {e}")

    @pyqtSlot()
    def connect_server(self):
        try:
            if not self.client:
                raise RuntimeError("Client yok.")
            self.client.connect_server()
            self.is_connected = True
            self.connected_state.emit(True)
            # self.ok.emit("Sunucuya bağlanıldı.")
        except Exception as e:
            self.is_connected = False
            self.connected_state.emit(False)
            self.err.emit(f"Bağlanma hatası: {e}")

    @pyqtSlot(dict)
    def send_telemetry(self, payload: dict):
        if not self.client:
            self.err.emit("Client ilklendirilmedi.")
            return
        try:
            # POST isteği gönderiliyor
            res_data = self.client.send_telemetry(payload)

            # Sunucudan dönen yanıt içerisinden rakip konum bilgilerini ayıkla
            konum_bilgileri = res_data.get("konumBilgileri", [])
            # Rakip verilerini direkt sinyalle backend'e gönder
            self.competitors.emit(konum_bilgileri)

        except Exception as e:
            self.err.emit(f"Telemetri gönderilirken hata oluştu: {str(e)}")

    @pyqtSlot(str)
    def upload_video_http(self, file_path: str):
        try:
            if not self.client:
                raise RuntimeError("Client yok.")
            if not self.is_connected:
                raise RuntimeError("Önce Sunucuya Bağlan.")
            self.client.upload_video_file_http(file_path)
            self.ok.emit("Video dosyası (HTTP) sunucuya gönderildi.")
        except Exception as e:
            self.err.emit(f"Video upload hatası: {e}")

    @pyqtSlot()
    def fetch_hss_coordinates(self):
        if not self.client:
            self.err.emit("Client ilklendirilmedi.")
            return
        try:
            res_data = self.client.get_hss_koordinatlari()
            hss_list = res_data.get("hss_koordinat_bilgileri", [])
            self.hss_received.emit(hss_list)
        except Exception as e:
            self.err.emit(f"HSS koordinatları alınırken hata: {str(e)}")
