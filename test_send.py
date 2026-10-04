import socket, time
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
i = 0
while True:
    s.sendto(f"merhaba {i}".encode(), ("172.29.70.176", 14550))
    print(f"gonderildi {i}")
    i += 1
    time.sleep(1)