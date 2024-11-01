TATA CARA MENJALANKAN FILE

Pertama, pastikan server dijalankan sebelum menjalankan client. Buka terminal pada perangkat yang digunakan sebagai server, lalu jalankan perintah: “python server.py”

Server akan mulai mendengarkan koneksi pada alamat IP dan port yang telah ditentukan dalam code.

Kemudian, pada perangkat yang ingin digunakan sebagai client, buka terminal dan jalankan perintah: “python client.py”

Client akan meng-input kata sandi yang benar, yaitu “mantapmainkan” untuk akses ke dalam server. Jika kata sandi salah, maka client akan diberi kesempatan sebanyak tiga kali untuk mengulang sebelum keluar secara otomatis.

Setelah kata sandi diterima, client diminta untuk memasukkan username yang unik (yang belum dipakai oleh client lain). Jika username yang di-input tidak unik, maka akan terkirim pesan agar client memasukkan username lain sampai server menerima.

Setelah username diterima, terjalin koneksi, dan client mulai dapat bertukar pesan. Pesan dikirim dalam format yang mencakup nomor urut, kemudian akan terkirim ke client lain.

Untuk mengakhiri sesi, client akan mengetik “exit” lalu menekan Enter. Server akan menerima pesan “EXIT”, mencatat bahwa client telah keluar, dan memberi pemberitahuan ke client lain.
