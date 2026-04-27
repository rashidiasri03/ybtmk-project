"""
Management command: load_fasiliti
Usage: python manage.py load_fasiliti [--pdf PATH] [--dry-run]

Reads a PDF of facility names and bulk-inserts them as
MaklumatAsas + FacilityProfile records (status='draf').
Skips any facility whose nama_fasiliti already exists in DB.
"""
import re
from django.core.management.base import BaseCommand
from home.models import MaklumatAsas, FacilityProfile


# ── Jenis inference rules (checked in order, first match wins) ──
JENIS_RULES = [
    (r'klinik pergigian di hospital',             'klinik_pergigian_hosp'),
    (r'klinik pergigian di klinik kesihatan ibu', 'kp_kk_ibu_anak'),
    (r'klinik pergigian di klinik kesihatan utc', 'kp_kk_utc'),
    (r'klinik pergigian di klinik kesihatan',     'klinik_pergigian'),
    (r'klinik pergigian di sekolah',              'klinik_pergigian_sekolah'),
    (r'klinik pergigian utc',                     'klinik_pergigian_utc'),
    (r'klinik pergigian rtc',                     'klinik_pergigian_rtc'),
    (r'klinik pergigian',                         'klinik_pergigian'),
    (r'klinik kesihatan ibu dan anak',            'kk_ibu_anak'),
    (r'klinik kesihatan utc',                     'klinik_kesihatan_utc'),
    (r'klinik kesihatan',                         'klinik_kesihatan'),
    (r'klinik komuniti',                          'klinik_komuniti'),
    (r'klinik desa',                              'klinik_desa'),
    (r'hospital pakar',                           'hospital_pakar'),
    (r'hospital',                                 'hospital'),
    (r'institusi perubatan khas',                 'institusi_perubatan_khas'),
    (r'institusi latihan',                        'institusi_latihan'),
    (r'jabatan kesihatan negeri',                 'jabatan_kes_negeri'),
    (r'pejabat kesihatan pergigian bahagian',     'pkp_bahagian'),
    (r'pejabat kesihatan pergigian daerah',       'pkp_daerah'),
    (r'pejabat kesihatan pergigian kawasan',      'pkp_kawasan'),
    (r'pejabat kesihatan pergigian',              'pkp'),
]


def infer_jenis(nama: str) -> str:
    lower = nama.lower()
    for pattern, code in JENIS_RULES:
        if re.search(pattern, lower):
            return code
    return 'lain'


VALID_PREFIXES = (
    'Hospital', 'Klinik', 'Institusi', 'Jabatan', 'Pejabat',
    'Pusat', 'Institut', 'Bahagian',
)


def extract_names_from_pdf(pdf_path: str) -> list[str]:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Sila install pdfplumber: pip install pdfplumber")

    names = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                line = line.strip()
                # Skip header row and very short / empty strings
                if not line or line in ('Nama_Fasiliti', 'Tiada Informasi') or len(line) < 4:
                    continue
                # Only accept lines starting with known facility-type keywords
                if line.startswith(VALID_PREFIXES):
                    names.append(line)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for n in names:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    return unique


class Command(BaseCommand):
    help = "Load facility names from PDF into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf',
            default=r'c:\Users\rahma\Downloads\home_maklumatasas.pdf',
            help='Path to the PDF file (default: Downloads folder)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview without inserting',
        )

    def handle(self, *args, **options):
        pdf_path = options['pdf']
        dry_run  = options['dry_run']

        self.stdout.write(f"Reading PDF: {pdf_path}")
        names = extract_names_from_pdf(pdf_path)
        self.stdout.write(f"Found {len(names)} unique facility names in PDF.")

        # Get existing names to skip duplicates
        existing = set(
            MaklumatAsas.objects.values_list('nama_fasiliti', flat=True)
        )
        self.stdout.write(f"Existing in DB: {len(existing)}")

        to_insert = [n for n in names if n not in existing]
        self.stdout.write(f"To insert: {len(to_insert)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes made."))
            for n in to_insert[:30]:
                self.stdout.write(f"  >> [{infer_jenis(n)}] {n}")
            if len(to_insert) > 30:
                self.stdout.write(f"  ... and {len(to_insert)-30} more")
            return

        inserted = 0
        skipped  = 0

        for nama in to_insert:
            jenis = infer_jenis(nama)
            try:
                ma = MaklumatAsas.objects.create(
                    nama_fasiliti  = nama,
                    jenis_fasiliti = jenis,
                    negeri         = '',   # user will update
                    daerah         = '',   # user will update
                )
                FacilityProfile.objects.create(
                    maklumat_asas = ma,
                    status        = 'draf',
                )
                inserted += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ERROR: {nama} — {e}"))
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Inserted: {inserted}  |  Errors/Skipped: {skipped}"
        ))
