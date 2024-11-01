
import socket
import threading
import os
import time
import struct

# Define server's IP address and port
server_ip = "192.168.100.11"
server_port = 12345

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Set socket timeout for receiving messages
client_socket.settimeout(1.0)

# Global variables
client_name = ""
exit_flag = False
message_counter = 0
pending_acks = {}
ack_lock = threading.Lock()

def send_messages():
    global client_name, exit_flag, message_counter
    while not exit_flag:
        try:
            message = input()
            if message.lower() == 'exit':
                exit_flag = True
                send_message_with_retry(f"EXIT:{client_name}")
                print(f"{client_name} (You) have left the chat.")
                break
            if message:
                print(f"{client_name} (You): {message}")
                send_message_with_retry(f"{client_name}: {message}")
        except Exception as e:
            print(f"Error in send_messages: {e}")

def receive_messages():
    global exit_flag, client_name
    # Terus terima pesan selama exit_flag belum diaktifkan
    while not exit_flag:
        try:
            # Menerima data dari socket
            data, _ = client_socket.recvfrom(1024)
            if len(data) == 8:  # Cek apakah ini ACK
                seq_num = struct.unpack('!Q', data)[0]  # Ambil nomor urut dari data
                with ack_lock:  # Kunci akses untuk menghindari race condition
                    if seq_num in pending_acks:
                        pending_acks[seq_num].set()  # Tandai ACK sebagai diterima
            else:
                try:
                    # Untuk pesan biasa, 8 byte pertama adalah nomor urut
                    if len(data) > 8:
                        message = data[8:].decode()  # Ambil pesan setelah nomor urut
                    else:
                        message = data.decode()  # Dekode pesan langsung jika tidak ada nomor urut
                    print(message)  # Tampilkan pesan
                except UnicodeDecodeError:
                    print(f"Error decoding message")  # Tampilkan error jika gagal dekode pesan
        except socket.timeout:
            continue  # Lewati jika waktu habis
        except Exception as e:
            if not exit_flag:
                print(f"Error receiving message: {e}")  # Tampilkan error jika ada masalah saat menerima pesan

def send_message_with_retry(message, max_retries=5, timeout=2.0):
    global message_counter
    retries = 0  # Inisialisasi jumlah percobaan

    while retries < max_retries:  # Selama percobaan masih kurang dari maksimum
        try:
            message_counter += 1  # Naikkan penghitung pesan
            seq_num = message_counter  # Simpan nomor urut pesan
            
            # Buat event untuk menunggu ACK dari pesan ini
            ack_event = threading.Event()
            with ack_lock:  # Kunci akses untuk mencegah race condition
                pending_acks[seq_num] = ack_event  # Tambahkan event ke pending Acks
            
            # Kirim pesan
            full_message = struct.pack('!Q', seq_num) + message.encode()  # Gabungkan nomor urut dengan pesan
            client_socket.sendto(full_message, (server_ip, server_port))  # Kirim ke server
            
            # Tunggu ACK
            if ack_event.wait(timeout):  # Tunggu ACK selama timeout
                with ack_lock:
                    pending_acks.pop(seq_num, None)  # Hapus event dari pending Acks jika ACK diterima
                return True  # Pesan berhasil terkirim dan ACK diterima
            
            retries += 1  # Tambah jumlah percobaan
            if retries < max_retries:  # Cek apakah masih ada percobaan tersisa
                print(f"Retry {retries}: No ACK received, resending...")  # Pesan jika tidak ada ACK
            
            # Bersihkan pending ACK jika kita akan mencoba lagi
            with ack_lock:
                pending_acks.pop(seq_num, None)  # Hapus dari pending Acks untuk percobaan ulang
                
        except Exception as e:
            print(f"Error sending message: {e}")  # Tampilkan error jika ada masalah saat mengirim pesan
            retries += 1  # Tambah jumlah percobaan jika ada error
    
    print("Failed to send message after maximum retries")  # Tampilkan pesan gagal setelah semua percobaan
    return False  # Kembalikan False jika pengiriman gagal

def register_username(username):
    try:
        # Send username without sequence number for registration
        client_socket.sendto(username.encode(), (server_ip, server_port))
        
        # Wait for response
        try:
            data, _ = client_socket.recvfrom(1024)
            response = data.decode()
            
            if response == "USERNAME_ACCEPTED":
                return True
            elif response == "USERNAME_TAKEN":
                return False
        except socket.timeout:
            print("Server not responding. Please try again.")
            return False
    except Exception as e:
        print(f"Error registering username: {e}")
        return False

def main():
    global client_name, exit_flag
    
    # Password authentication
    correct_password = "mantapmainkan"
    attempts = 3

    while attempts > 0:
        password = input("Enter the password to join the chat: ")
        if password == correct_password:
            print("Password correct. Joining the chat...")
            break
        else:
            attempts -= 1
            if attempts > 0:
                print(f"Incorrect password. You have {attempts} {'attempts' if attempts > 1 else 'attempt'} left.")
            else:
                print("You've exceeded the maximum number of attempts. Exiting the program.")
                return

    # Username registration loop
    while True:
        client_name = input("Enter your unique username: ")
        if register_username(client_name):
            print(f"Welcome to the chat, {client_name}!")
            break
        else:
            print("Username already taken. Please choose another one.")

    # Start the receiving thread
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()

    print("Type your messages and press Enter to send. Type 'exit' to quit.")

    # Start sending messages
    send_messages()

    # Cleanup
    exit_flag = True
    client_socket.close()

if __name__ == "__main__":
    main()

