
import socket
import os
import struct

# Server IP address and port
server_ip = "127.0.0.1"
server_port = 12345

# Dictionaries untuk tracking client and menghubungi counters
clients = {}  # {client_address: client_name}
active_usernames = set()  # Untuk tracking username yang aktif
message_counters = {}  # {client_address: sequence_number}

# Create UDP socket for server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # socket khusus UDP
server_socket.bind((server_ip, server_port))

def handle_client_message(data, client_address):
    try:
        # Registrasi klien kalau alamatnya belum ada di dictionary clients
        if client_address not in clients:
            # Dekode data yang masuk untuk mendapatkan username klien
            client_name = data.decode().strip()
            # Cek apakah username sudah digunakan
            if client_name in active_usernames:
                # Beritahu klien bahwa username sudah diambil
                server_socket.sendto("USERNAME_TAKEN".encode(), client_address)
            else:
                # Tambahkan username baru ke daftar user aktif dan registrasi klien
                active_usernames.add(client_name)
                clients[client_address] = client_name
                # Inisialisasi penghitung pesan untuk klien
                message_counters[client_address] = 0
                # Kirim konfirmasi penerimaan username ke klien
                server_socket.sendto("USERNAME_ACCEPTED".encode(), client_address)
                print(f"Klien baru terhubung: {client_name} ({client_address})")
                # Siarkan pesan ke semua klien bahwa klien ini sudah bergabung
                broadcast_message(f"{client_name} telah bergabung ke chat.", None)
            return  # Keluar dari fungsi karena registrasi selesai

        # Tangani pesan biasa dari klien (dengan nomor urut)
        try:
            # Ambil nomor urut dari 8 byte pertama data
            seq_num = struct.unpack('!Q', data[:8])[0]
            # Dekode isi pesan dari data
            message = data[8:].decode()

            # Kirim ACK untuk pesan yang diterima
            send_ack(client_address, seq_num)

            # Cek apakah pesan menunjukkan bahwa pengguna ingin keluar
            if message.startswith("EXIT:"):
                # Ambil username dari pesan
                username = message.split(":")[1]
                print(f"{username} telah meninggalkan chat.")
                # Hapus username dari pengguna aktif
                active_usernames.remove(username)
                # Hapus klien dari dictionary clients
                del clients[client_address]
                # Hapus penghitung pesan untuk klien ini
                del message_counters[client_address]
                # Siarkan pesan ke semua klien bahwa pengguna ini telah keluar
                broadcast_message(f"{username} telah keluar dari chat.", None)
                # Cek apakah tidak ada klien tersisa, lalu matikan server
                if not clients:
                    print("Semua klien sudah keluar. Mematikan server.")
                    server_socket.close()  # Tutup socket server
                    os._exit(0)  # Hentikan program

            else:
                # Cetak pesan yang diterima beserta username klien
                print(f"Pesan dari {clients[client_address]}: {message}")
                # Siarkan pesan ke semua klien kecuali pengirim
                broadcast_message(message, client_address)

        except struct.error:
            # Tangani kesalahan terkait unpacking pesan
            print(f"Kesalahan saat unpacking pesan dari {client_address}")

    except Exception as e:
        # Tangkap dan cetak kesalahan lain yang terjadi saat menangani pesan
        print(f"Kesalahan saat menangani pesan: {e}")

def send_ack(client_address, seq_num):
    # Siapkan pesan ACK dengan mengemas nomor urut (seq_num) ke dalam format biner
    ack = struct.pack('!Q', seq_num)
    # Kirim pesan ACK ke alamat klien yang sesuai
    server_socket.sendto(ack, client_address)

def broadcast_message(message, sender_address):
    # Kirim pesan ke semua klien kecuali pengirim
    for client_address, client_name in clients.items():
        if client_address != sender_address:  # Jangan kirim pesan balik ke pengirim
            try:
                # Dapatkan nomor urut terbaru dan tambah 1
                seq_num = message_counters.get(client_address, 0) + 1
                message_counters[client_address] = seq_num  # Simpan nomor urut terbaru
                
                # Siapkan pesan lengkap dengan nomor urut yang terpaket
                full_message = struct.pack('!Q', seq_num) + message.encode()
                
                # Kirim pesan ke alamat klien yang sesuai
                server_socket.sendto(full_message, client_address)
            except Exception as e:
                # Tampilkan error jika gagal mengirim pesan
                print(f"Error broadcasting to {client_name}: {e}")
                
def start_server():
    print(f"Server listening on {server_ip}:{server_port}")
    while True:
        try:
            data, client_address = server_socket.recvfrom(1024)
            handle_client_message(data, client_address)
        except Exception as e:
            print(f"Error in start_server: {e}")

if __name__ == "__main__":
    start_server()
