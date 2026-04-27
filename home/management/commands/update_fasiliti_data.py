"""
Management command: update_fasiliti_data

Extracts all columns from home_maklumatasas.pdf and updates existing
MaklumatAsas records with negeri, daerah, alamat, poskod, latitud, longitud.

PDF section layout (confirmed via bounding-box analysis):
  Section 1  â€“ Nama Fasiliti   â€“ pages   1-82   x=  0-300  header="Nama_Fasiliti"
  Section 2  â€“ Kod KKM         â€“ pages  83-164  (skip â€“ codes only)
  Section 3  â€“ Negeri          â€“ pages 165-246  x=300-600  header="PTJ Negeriâ€¦"
  Section 4  â€“ Zon/Daerah/Parlimen/Kawasan
                                â€“ pages 247-328
                                  Zon (row ref)  x=  0-100
                                  Daerah value   x=100-240  header="Wilayah/Zonâ€¦"
  Section 5  â€“ Alamat          â€“ pages 329-410  x=  0-600  header="Alamat"
  Section 6  â€“ GPS / Poskod    â€“ pages 411-492
                                  Poskod   x=  0-120
                                  Latitud  x=120-170   (labelled "Longitude" in PDF â€“ values ~1-7)
                                  Longitud x=170-230   (labelled "Latitude"  in PDF â€“ values ~100-119)
                                  header row on page 411
"""

import re
import pdfplumber
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from home.models import MaklumatAsas

# â”€â”€ NEGERI STRING â†’ CHOICE CODE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
NEGERI_MAP = {
    'johor':                                      'johor',
    'kedah':                                      'kedah',
    'kelantan':                                   'kelantan',
    'melaka':                                     'melaka',
    'negeri sembilan':                            'negeri_sembilan',
    'pahang':                                     'pahang',
    'perak':                                      'perak',
    'perlis':                                     'perlis',
    'pulau pinang':                               'pulau_pinang',
    'sabah':                                      'sabah',
    'sarawak':                                    'sarawak',
    'selangor':                                   'selangor',
    'terengganu':                                 'terengganu',
    'wp kuala lumpur dan putrajaya':              'wp_kl',
    'wilayah persekutuan kuala lumpur':           'wp_kl',
    'w.p. kuala lumpur':                          'wp_kl',
    'wp kuala lumpur':                            'wp_kl',
    'wilayah persekutuan putrajaya':              'wp_putrajaya',
    'w.p. putrajaya':                             'wp_putrajaya',
    'wp putrajaya':                               'wp_putrajaya',
    'wilayah persekutuan labuan':                 'wp_labuan',
    'w.p. labuan':                                'wp_labuan',
    'wp labuan':                                  'wp_labuan',
}

PDF_PATH = r'c:\Users\rahma\Downloads\home_maklumatasas.pdf'


# â”€â”€ LOW-LEVEL EXTRACTION HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _words_on_page(pdf, page_index):
    """Return pdfplumber words list for the given 0-based page index."""
    return pdf.pages[page_index].extract_words()


def _rows_from_words(words, x_min, x_max, top_tolerance=3):
    """
    Group words whose x0 is in [x_min, x_max] by their `top` value
    (within Â±top_tolerance).  Returns sorted list of (top, text) tuples.
    """
    col_words = [w for w in words if x_min <= w['x0'] <= x_max]
    buckets = {}
    for w in col_words:
        t = round(w['top'])
        buckets.setdefault(t, []).append(w)
    result = []
    for top in sorted(buckets.keys()):
        row_words = sorted(buckets[top], key=lambda w: w['x0'])
        text = ' '.join(w['text'] for w in row_words).strip()
        if text:
            result.append((top, text))
    return result


def extract_column(pdf, page_start, page_end, x_min, x_max, skip_first_row=False):
    """
    Extract a sequential list of text values from one column across pages.
    page_start / page_end are 1-based, inclusive.
    skip_first_row  : drop the very first row of page_start (column header).
    """
    entries = []
    for pi in range(page_start - 1, page_end):
        rows = _rows_from_words(_words_on_page(pdf, pi), x_min, x_max)
        if skip_first_row and pi == page_start - 1 and rows:
            rows = rows[1:]
        entries.extend(text for _, text in rows)
    return entries


def extract_column_with_blanks(pdf, page_start, page_end,
                                ref_x_min, ref_x_max,
                                val_x_min, val_x_max,
                                skip_first_row=False):
    """
    Extract a column that may have BLANK entries (not every row has a value).

    Uses the *reference* column (ref_x) to enumerate all row top-positions,
    then extracts the *value* column (val_x) at the same top-position.
    Missing value rows become empty strings.
    """
    entries = []
    for pi in range(page_start - 1, page_end):
        words = _words_on_page(pdf, pi)

        # Reference top positions
        ref_rows = _rows_from_words(words, ref_x_min, ref_x_max)
        if skip_first_row and pi == page_start - 1 and ref_rows:
            ref_rows = ref_rows[1:]

        # Value words per top
        val_words = [w for w in words if val_x_min <= w['x0'] <= val_x_max]
        val_by_top = {}
        for w in val_words:
            t = round(w['top'])
            val_by_top.setdefault(t, []).append(w)

        for top, _ in ref_rows:
            # Accept value words within Â±4 pts of reference top
            candidates = []
            for t, wds in val_by_top.items():
                if abs(t - top) <= 4:
                    candidates.extend(wds)
            text = ' '.join(w['text'] for w in sorted(candidates, key=lambda w: w['x0'])).strip()
            entries.append(text)

    return entries


def extract_gps_section(pdf, page_start, page_end, skip_first_row=False):
    """
    Extracts (poskod, latitud, longitud) triples from the GPS section.
    Column layout confirmed:
      Poskod   x =  0 â€“ 120
      Lat      x = 120 â€“ 170  (small value ~1-7)
      Lon      x = 170 â€“ 230  (large value ~100-119)
    """
    result = []
    for pi in range(page_start - 1, page_end):
        words = _words_on_page(pdf, pi)

        # All rows by top (use poskod column as reference)
        poskod_rows = _rows_from_words(words, 0, 120)
        if skip_first_row and pi == page_start - 1 and poskod_rows:
            poskod_rows = poskod_rows[1:]

        lat_words  = [w for w in words if 120 <= w['x0'] <= 170]
        lon_words  = [w for w in words if 170 <= w['x0'] <= 230]

        def _nearest(word_list, top):
            candidates = [w for w in word_list if abs(round(w['top']) - top) <= 4]
            return ' '.join(w['text'] for w in sorted(candidates, key=lambda w: w['x0'])).strip()

        for top, poskod_text in poskod_rows:
            lat_text = _nearest(lat_words,  top)
            lon_text = _nearest(lon_words,  top)
            # Keep only numeric poskod (5-digit)
            poskod = poskod_text.strip() if re.match(r'^\d{3,6}$', poskod_text.strip()) else ''
            try:
                lat = float(lat_text) if lat_text else None
            except ValueError:
                lat = None
            try:
                lon = float(lon_text) if lon_text else None
            except ValueError:
                lon = None
            result.append((poskod, lat, lon))
    return result


# â”€â”€ MAIN COMMAND â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class Command(BaseCommand):
    help = (
        'Update MaklumatAsas records with negeri, daerah, alamat, poskod, '
        'latitud, longitud extracted from the PDF.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf',
            default=PDF_PATH,
            help='Path to the PDF file (default: %s)' % PDF_PATH,
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually saving.',
        )

    def handle(self, *args, **options):
        pdf_path = options['pdf']
        dry_run  = options['dry_run']

        self.stdout.write(self.style.NOTICE('Opening PDF: %s' % pdf_path))
        try:
            pdf = pdfplumber.open(pdf_path)
        except Exception as e:
            raise CommandError('Cannot open PDF: %s' % e)

        with pdf:
            # â”€â”€ Section 1: Facility names â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            self.stdout.write('Extracting Section 1 (names)â€¦')
            sec1_names = extract_column(pdf, 1, 82, 0, 300, skip_first_row=True)
            self.stdout.write('  â†’ %d rows' % len(sec1_names))

            # â”€â”€ Section 3: Negeri â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            self.stdout.write('Extracting Section 3 (negeri)â€¦')
            sec3_negeri_raw = extract_column(pdf, 165, 246, 300, 600, skip_first_row=True)
            self.stdout.write('  â†’ %d rows' % len(sec3_negeri_raw))

            # â”€â”€ Section 4: Daerah (with blank rows) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            self.stdout.write('Extracting Section 4 (daerah)â€¦')
            sec4_daerah = extract_column_with_blanks(
                pdf,
                page_start=247, page_end=328,
                ref_x_min=0,   ref_x_max=100,   # Zon column (always present)
                val_x_min=100, val_x_max=240,    # Daerah column
                skip_first_row=True,
            )
            self.stdout.write('  â†’ %d rows (blanks included)' % len(sec4_daerah))

            # â”€â”€ Section 5: Alamat â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            self.stdout.write('Extracting Section 5 (alamat)â€¦')
            sec5_alamat = extract_column(pdf, 329, 410, 0, 600, skip_first_row=True)
            self.stdout.write('  â†’ %d rows' % len(sec5_alamat))

            # â”€â”€ Section 6: GPS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            self.stdout.write('Extracting Section 6 (GPS)â€¦')
            sec6_gps = extract_gps_section(pdf, 411, 492, skip_first_row=True)
            self.stdout.write('  â†’ %d rows' % len(sec6_gps))

        # â”€â”€ Build lookup: name (lower) â†’ data dict â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Use the minimum length across sections to avoid index errors
        n = len(sec1_names)
        self.stdout.write('Building lookup from %d entriesâ€¦' % n)

        lookup = {}   # lower_name â†’ {negeri, daerah, alamat, poskod, lat, lon}
        for i, raw_name in enumerate(sec1_names):
            name_lower = raw_name.strip().lower()
            if not name_lower:
                continue

            # Negeri
            negeri_raw = sec3_negeri_raw[i] if i < len(sec3_negeri_raw) else ''
            negeri_code = NEGERI_MAP.get(negeri_raw.strip().lower(), '')
            if not negeri_code and negeri_raw:
                # Fuzzy partial match
                for k, v in NEGERI_MAP.items():
                    if k in negeri_raw.lower():
                        negeri_code = v
                        break

            # Daerah
            daerah = sec4_daerah[i].strip() if i < len(sec4_daerah) else ''

            # Alamat
            alamat = sec5_alamat[i].strip() if i < len(sec5_alamat) else ''

            # GPS
            if i < len(sec6_gps):
                poskod, lat, lon = sec6_gps[i]
            else:
                poskod, lat, lon = '', None, None

            entry = dict(negeri=negeri_code, daerah=daerah, alamat=alamat,
                         poskod=poskod, lat=lat, lon=lon)

            # If the same name appears multiple times, keep first (they should
            # be the same; subsequent repeats are the same physical facility)
            if name_lower not in lookup:
                lookup[name_lower] = entry

        self.stdout.write('  â†’ %d unique names in lookup' % len(lookup))

        # â”€â”€ Update DB records â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        updated  = 0
        skipped  = 0
        notfound = 0

        qs = MaklumatAsas.objects.all()
        bulk_updates = []

        # Pre-compute trimmed lookup keys: strip after comma, strip trailing
        # state/address suffixes that some older records have appended
        _NEGERI_SUFFIXES = [
            ' sabah', ' sarawak', ' selangor', ' johor', ' perak',
            ' pahang', ' kedah', ' kelantan', ' melaka', ' terengganu',
            ' perlis', ' negeri sembilan', ' pulau pinang',
        ]

        def _resolve_key(raw_name):
            k = raw_name.strip().lower()
            # Exact match
            if k in lookup:
                return lookup[k]
            # Strip after comma
            k2 = k.split(',')[0].strip()
            if k2 in lookup:
                return lookup[k2]
            # Strip trailing state suffix
            for suf in _NEGERI_SUFFIXES:
                if k2.endswith(suf):
                    k3 = k2[: -len(suf)].strip()
                    if k3 in lookup:
                        return lookup[k3]
            # Try up to 6-word prefix
            words_k = k.split()
            for n in range(min(6, len(words_k) - 1), 2, -1):
                prefix = ' '.join(words_k[:n])
                if prefix in lookup:
                    return lookup[prefix]
            return None

        for obj in qs.iterator():
            data = _resolve_key(obj.nama_fasiliti)
            if data is None:
                notfound += 1
                continue

            changed = False

            if not obj.negeri and data['negeri']:
                obj.negeri = data['negeri']
                changed = True
            if not obj.daerah and data['daerah']:
                obj.daerah = data['daerah']
                changed = True
            if not obj.alamat and data['alamat']:
                obj.alamat = data['alamat']
                changed = True
            if not obj.poskod and data['poskod']:
                obj.poskod = data['poskod']
                changed = True
            if obj.latitud is None and data['lat'] is not None:
                obj.latitud = data['lat']
                changed = True
            if obj.longitud is None and data['lon'] is not None:
                obj.longitud = data['lon']
                changed = True

            if changed:
                bulk_updates.append(obj)
                updated += 1
            else:
                skipped += 1

        if not dry_run and bulk_updates:
            fields = ['negeri', 'daerah', 'alamat', 'poskod', 'latitud', 'longitud', 'updated_at']
            with transaction.atomic():
                # Process in batches of 500
                batch_size = 500
                for start in range(0, len(bulk_updates), batch_size):
                    batch = bulk_updates[start:start + batch_size]
                    MaklumatAsas.objects.bulk_update(batch, fields)
                    self.stdout.write('  Saved batch %dâ€“%d' % (start + 1, start + len(batch)))

        self.stdout.write(self.style.SUCCESS(
            '\nDone. Updated=%d  Skipped(already filled)=%d  Not-in-PDF=%d  dry_run=%s'
            % (updated, skipped, notfound, dry_run)
        ))

