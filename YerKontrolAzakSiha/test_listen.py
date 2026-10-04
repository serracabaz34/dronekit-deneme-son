import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", 14550))
print("Dinleniyor, port 14550...")
while True:
    data, addr = s.recvfrom(1024)
    print(f"[PAKET GELDİ] {addr} -> {data}")
