# Pembuka Alamat Otomatis

Skrip Python sederhana yang membuka daftar alamat (URL) di browser secara
otomatis, satu per satu, dengan jeda yang bisa diatur. Hanya memakai pustaka
standar Python (butuh Python 3.10 atau lebih baru).

## Cara pakai

1. Isi file `urls.txt` dengan satu alamat per baris. Baris kosong dan baris
   yang diawali `#` diabaikan. Alamat tanpa `https://` otomatis ditambahkan.
2. Jalankan:

```bash
python3 buka_alamat.py
```

Opsi:

| Opsi | Keterangan |
| --- | --- |
| `berkas` | file daftar alamat (default `urls.txt`) |
| `-d`, `--jeda` | jeda antar alamat dalam detik (default `3`) |
| `--dry-run` | hanya tampilkan alamat, tidak membuka browser |

Contoh:

```bash
python3 buka_alamat.py daftar.txt -d 5
python3 buka_alamat.py --dry-run
```

Catatan: skrip memakai `webbrowser` sehingga alamat dibuka di browser default
di komputer tempat skrip dijalankan. Skrip ini tidak berjalan di lingkungan
tanpa layar (misalnya server cloud).
