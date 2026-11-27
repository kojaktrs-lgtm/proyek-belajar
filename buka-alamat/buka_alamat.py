#!/usr/bin/env python3
"""Pembuka alamat otomatis.

Membaca daftar alamat (URL) dari sebuah file teks, lalu membuka tiap alamat
di browser secara otomatis, satu per satu, dengan jeda tertentu.

Format file daftar: satu alamat per baris. Baris kosong dan baris yang diawali
'#' diabaikan.

Contoh pemakaian:
    python3 buka_alamat.py                      # pakai urls.txt, jeda 3 detik
    python3 buka_alamat.py daftar.txt -d 5      # file lain, jeda 5 detik
    python3 buka_alamat.py --dry-run            # hanya tampilkan, tidak membuka
"""

import argparse
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse


def baca_alamat(path: Path) -> list[str]:
    """Baca daftar alamat dari file, buang baris kosong dan komentar."""
    alamat = []
    with path.open(encoding="utf-8") as f:
        for baris in f:
            teks = baris.strip()
            if not teks or teks.startswith("#"):
                continue
            alamat.append(teks)
    return alamat


def normalisasi(url: str) -> str | None:
    """Tambahkan https:// bila belum ada skema. Kembalikan None jika tidak valid."""
    if "://" not in url:
        url = "https://" + url
    hasil = urlparse(url)
    if hasil.scheme not in ("http", "https") or not hasil.netloc:
        return None
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description="Buka daftar alamat secara otomatis.")
    parser.add_argument("berkas", nargs="?", default="urls.txt",
                        help="file berisi daftar alamat (default: urls.txt)")
    parser.add_argument("-d", "--jeda", type=float, default=3.0,
                        help="jeda antar alamat dalam detik (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="tampilkan alamat saja, jangan dibuka")
    args = parser.parse_args()

    path = Path(args.berkas)
    if not path.is_file():
        print(f"File tidak ditemukan: {path}", file=sys.stderr)
        return 1

    daftar = baca_alamat(path)
    if not daftar:
        print("Tidak ada alamat di file.", file=sys.stderr)
        return 1

    print(f"Ditemukan {len(daftar)} baris alamat.")
    for i, mentah in enumerate(daftar, start=1):
        url = normalisasi(mentah)
        if url is None:
            print(f"[{i}] Lewati (tidak valid): {mentah}")
            continue

        if args.dry_run:
            print(f"[{i}] (dry-run) {url}")
            continue

        print(f"[{i}] Membuka {url}")
        webbrowser.open_new_tab(url)
        if i < len(daftar):
            time.sleep(args.jeda)

    print("Selesai.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
