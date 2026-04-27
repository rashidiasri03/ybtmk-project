"""
Script untuk import data dari home_maklumatasas.sql ke SQLite.
Jalankan: python import_maklumatasas.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ybtmk_project.settings')

# Tambah project root ke path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

django.setup()

from home.models import MaklumatAsas

# Path ke SQL file
SQL_FILE = r"C:\Users\rahma\Downloads\home_maklumatasas.sql"

def parse_values(line):
    """Parse satu baris values ('val1','val2','val3','val4').
    
    Strategi: field 2/3/4 (jenis, negeri, daerah) tidak mengandungi apostrof.
    Kita cari pattern ','<jenis>','<negeri>','<daerah>') dari belakang,
    lalu ambil selebihnya sebagai nama_fasiliti (field 1).
    Ini membolehkan nama dengan apostrof tidak escaped diproses dengan betul.
    """
    import re
    line = line.strip().rstrip(';').rstrip(',').rstrip(')')
    if not line.startswith('('):
        return None

    # Extract 3 fields dari belakang: daerah, negeri, jenis_fasiliti
    # Pattern: ,'<jenis>','<negeri>','<daerah>' — nilai-nilai ini tiada apostrof
    m = re.search(r",'([^']+)','([^']*)','([^']*)'$", line)
    if not m:
        return None

    jenis = m.group(1)
    negeri = m.group(2)
    daerah = m.group(3)

    # Selebihnya ialah ('nama_fasiliti
    # Ambil dari karakter ke-2 (lepas '(') hingga sebelum match
    prefix = line[:m.start()]  # contoh: ('Hospital Enche' Besar
    if not prefix.startswith("('"):
        return None
    nama = prefix[2:]  # buang ('

    return [nama, jenis, negeri, daerah]


def main():
    print(f"Membaca fail: {SQL_FILE}")

    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extractkan semua value rows dari INSERT INTO statement
    # Format: INSERT INTO home_maklumatasas (...) VALUES\n('...',...),...
    import re

    # Cari semua value tuples dalam SQL
    # Match pattern: ('...','...','...','...')
    pattern = re.compile(r"\('(?:[^'\\]|''|\\.)*','(?:[^'\\]|''|\\.)*','(?:[^'\\]|''|\\.)*','(?:[^'\\]|''|\\.)*'\)", re.DOTALL)

    # Split content line by line dan ambil semua lines yang bermula dengan ('
    lines = content.split('\n')

    records = []
    for line in lines:
        line = line.strip()
        if line.startswith("('") or line.startswith("('"):
            # Remove trailing comma
            clean = line.rstrip(',')
            fields = parse_values(clean)
            if fields and len(fields) == 4:
                records.append(fields)

    print(f"Dijumpai {len(records)} rekod untuk diimport.")

    if not records:
        print("Tiada rekod dijumpai. Sila semak format SQL file.")
        return

    # Tanya pengguna sama ada nak clear dulu atau append
    existing = MaklumatAsas.objects.count()
    print(f"\nJumlah rekod sedia ada dalam database: {existing}")

    if existing > 0:
        print("Database sudah ada data. Auto-padamkan semua rekod lama...")
        MaklumatAsas.objects.all().delete()
        print("Rekod lama telah dipadamkan.")

    # Bulk create
    batch_size = 500
    total = 0
    objs = []

    for fields in records:
        objs.append(MaklumatAsas(
            nama_fasiliti=fields[0],
            jenis_fasiliti=fields[1],
            negeri=fields[2],
            daerah=fields[3],
        ))

    # Insert dalam batch
    for i in range(0, len(objs), batch_size):
        batch = objs[i:i+batch_size]
        MaklumatAsas.objects.bulk_create(batch, ignore_conflicts=True)
        total += len(batch)
        print(f"  Telah import {total}/{len(objs)} rekod...")

    print(f"\nSelesai! Jumlah {total} rekod berjaya diimport ke table home_maklumatasas.")
    print(f"Jumlah dalam database sekarang: {MaklumatAsas.objects.count()}")


if __name__ == '__main__':
    main()
