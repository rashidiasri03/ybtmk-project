from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages, auth
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    UserProfile, FacilityProfile, MaklumatAsas,
    KlusterKejuruteraan, KlusterSumberManusia, KlusterPerkhidmatan,
    KlusterAset, KlusterFasiliti, KlusterPerancangan, KlusterKonsesi,
)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def custom_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('home:superadmin')
        return redirect('home:peta_fasiliti')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth.login(request, user)
            if user.is_superuser:
                return redirect('home:superadmin')
            return redirect('home:peta_fasiliti')
    else:
        form = AuthenticationForm(request)
    return render(request, 'home/login.html', {'form': form})

# Peta langkah → (atribut pada FacilityProfile, ModelClass)
CLUSTER_ATTR_MAP = [
    (0, 'maklumat_asas',    MaklumatAsas),
    (1, 'k_kejuruteraan',  KlusterKejuruteraan),
    (2, 'k_sumber_manusia', KlusterSumberManusia),
    (3, 'k_perkhidmatan',  KlusterPerkhidmatan),
    (4, 'k_aset',          KlusterAset),
    (5, 'k_fasiliti',      KlusterFasiliti),
    (6, 'k_perancangan',   KlusterPerancangan),
    (7, 'k_konsesi',       KlusterKonsesi),
]
import json

# ── Normalisasi nilai dump (teks penuh) → choice key form ──────────
# Dump simpan display text (cth. "Hospital", "Melaka") tapi form guna keys
_JENIS_NORM = {v.lower(): k for k, v in [
    ('hospital','Hospital'),('hospital_pakar','Hospital Pakar'),
    ('klinik_kesihatan','Klinik Kesihatan'),('klinik_desa','Klinik Desa'),
    ('klinik_komuniti','Klinik Komuniti'),
    ('institusi_perubatan_khas','Institusi Perubatan Khas'),
    ('institusi_latihan','Institusi Latihan'),
    ('jabatan_kes_negeri','Jabatan Kesihatan Negeri'),
    ('klinik_pergigian_hosp','Klinik Pergigian di Hospital'),
    ('kk_ibu_anak','Klinik Kesihatan Ibu dan Anak'),
    ('klinik_pergigian_utc','Klinik Pergigian UTC'),
    ('klinik_pergigian_sekolah','Klinik Pergigian di Sekolah'),
    ('kp_kk_utc','Klinik Pergigian di Klinik Kesihatan UTC'),
    ('kp_kk_ibu_anak','Klinik Pergigian di Klinik Kesihatan Ibu dan Anak'),
    ('klinik_pergigian_rtc','Klinik Pergigian RTC'),
    ('klinik_kesihatan_utc','Klinik Kesihatan UTC'),
    ('klinik_pergigian','Klinik Pergigian'),
    ('pkp_bahagian','Pejabat Kesihatan Pergigian Bahagian'),
    ('pkp','Pejabat Kesihatan Pergigian'),
    ('pkp_daerah','Pejabat Kesihatan Pergigian Daerah'),
    ('pkp_kawasan','Pejabat Kesihatan Pergigian Kawasan'),
    ('lain','Lain-lain'),
]}
_NEGERI_NORM = {
    'johor':'johor','kedah':'kedah','kelantan':'kelantan','melaka':'melaka',
    'negeri sembilan':'negeri_sembilan','pahang':'pahang','perak':'perak',
    'perlis':'perlis','pulau pinang':'pulau_pinang','sabah':'sabah',
    'sarawak':'sarawak','selangor':'selangor','terengganu':'terengganu',
    'wp kuala lumpur':'kuala_lumpur','w.p. kuala lumpur':'kuala_lumpur',
    'wp kuala lumpur dan putrajaya':'kuala_lumpur',
    'kuala lumpur':'kuala_lumpur','wp putrajaya':'putrajaya',
    'w.p. putrajaya':'putrajaya','putrajaya':'putrajaya',
    'wp labuan':'labuan','w.p. labuan':'labuan','labuan':'labuan',
}

def _norm_jenis(val):
    return _JENIS_NORM.get(val.strip().lower(), val)

def _norm_negeri(val):
    return _NEGERI_NORM.get(val.strip().lower(), val)

# ──────────────────────────────────────────────
# Master list of all bahagian (single source of truth)
# ──────────────────────────────────────────────
ALL_SECTIONS = [
    {'name': 'JKN – Hospital & Klinik',                'slug': 'jkn',    'icon': 'fas fa-hospital',            'icon_color': '#1d4ed8', 'color': '#eff6ff', 'description': 'Jaringan Kesihatan Negeri – hospital & klinik'},
    {'name': 'Bahagian Kejuruteraan',                  'slug': 'bkej',   'icon': 'fas fa-hard-hat',            'icon_color': '#b45309', 'color': '#fffbeb', 'description': 'Infrastruktur, bangunan & penyenggaraan'},
    {'name': 'Bahagian Pembangunan',                   'slug': 'bpem',   'icon': 'fas fa-city',                'icon_color': '#0369a1', 'color': '#f0f9ff', 'description': 'Pembangunan fasiliti & infrastruktur kesihatan'},
    {'name': 'Bahagian Sumber Manusia',                'slug': 'bsm',    'icon': 'fas fa-users',               'icon_color': '#0891b2', 'color': '#ecfeff', 'description': 'Pengurusan tenaga kerja & perjawatan'},
    {'name': 'Bahagian Perkembangan Perubatan',        'slug': 'bpp',    'icon': 'fas fa-stethoscope',         'icon_color': '#7c3aed', 'color': '#f5f3ff', 'description': 'Perkembangan perkhidmatan & pengisian perubatan'},
    {'name': 'Bahagian Kejururawatan',                 'slug': 'bkjw',   'icon': 'fas fa-user-nurse',          'icon_color': '#db2777', 'color': '#fdf2f8', 'description': 'Pengurusan kakitangan jururawat'},
    {'name': 'Bahagian Sains Kesihatan Bersekutu',     'slug': 'bskb',   'icon': 'fas fa-flask',               'icon_color': '#059669', 'color': '#ecfdf5', 'description': 'Perkhidmatan sains kesihatan & makmal'},
    {'name': 'Bahagian Perancangan',                   'slug': 'bprc',   'icon': 'fas fa-chart-line',          'icon_color': '#1d4ed8', 'color': '#eff6ff', 'description': 'Perancangan strategik & pengembangan perkhidmatan'},
    {'name': 'Bahagian Kawalan Penyakit',              'slug': 'bkp',    'icon': 'fas fa-shield-virus',        'icon_color': '#dc2626', 'color': '#fef2f2', 'description': 'Pemantauan & kawalan wabak penyakit'},
    {'name': 'Bahagian Amalan Perubatan',              'slug': 'bap',    'icon': 'fas fa-heartbeat',           'icon_color': '#e11d48', 'color': '#fff1f2', 'description': 'Aset & peralatan perubatan hospital'},
    {'name': 'Bahagian Kesihatan Awam',                'slug': 'bka',    'icon': 'fas fa-hand-holding-medical','icon_color': '#16a34a', 'color': '#f0fdf4', 'description': 'Bekalan perubatan & kesihatan awam'},
    {'name': 'Bahagian Kesihatan Digital',             'slug': 'bkd',    'icon': 'fas fa-laptop-medical',      'icon_color': '#0284c7', 'color': '#f0f9ff', 'description': 'Sistem EMR & pendigitalan rekod kesihatan'},
    {'name': 'Bahagian Pengurusan Maklumat',           'slug': 'bpm',    'icon': 'fas fa-database',            'icon_color': '#4f46e5', 'color': '#eef2ff', 'description': 'Pengurusan data & maklumat kesihatan'},
    {'name': 'Bahagian Pemakanan',                     'slug': 'bpmk',   'icon': 'fas fa-utensils',            'icon_color': '#ca8a04', 'color': '#fefce8', 'description': 'Kualiti & pembekalan makanan hospital'},
    {'name': 'Bahagian Perolehan',                     'slug': 'bpro',   'icon': 'fas fa-file-contract',       'icon_color': '#475569', 'color': '#f8fafc', 'description': 'Perolehan & kontrak perkhidmatan konsesi'},
    {'name': 'Program Perkhidmatan Farmasi',           'slug': 'ppf',    'icon': 'fas fa-pills',               'icon_color': '#9333ea', 'color': '#faf5ff', 'description': 'Bekalan ubat & perkhidmatan farmasi'},
]
SLUG_TO_NAME = {s['slug']: s['name'] for s in ALL_SECTIONS}

SVC_CHOICES = [
    'OPD (Pesakit Luar)', 'Kecemasan (A&E)', 'Pembedahan', 'Obstetrik & Ginekologi',
    'Pediatrik', 'Perubatan Dalaman', 'Ortopedik', 'Mata', 'ENT (Telinga Hidung Tekak)',
    'Psikiatri', 'Hemodialisis', 'Radiologi', 'Farmasi', 'Pergigian', 'Rehabilitasi', 'ICU / NICU',
]
DIS_CHOICES = [
    'Diabetes Mellitus', 'Hipertensi', 'URTI', 'Dengue', 'Asma', 'Bronkitis',
    'Tuberkulosis (TB)', 'Gastritis', 'Anemia', 'Penyakit Jantung', 'Strok', 'Kanser',
    'Kegagalan Buah Pinggang', 'Penyakit Mental', 'Trauma / Kecederaan', 'COVID-19 / Jangkitan Pernafasan',
]

# ── Bahagian → Kluster tanggungjawab ────────────────────────────
# Step index: 0=Maklumat Asas, 1=Kejuruteraan, 2=Sumber Manusia,
#             3=Perkhidmatan, 4=Aset, 5=Fasiliti, 6=Perancangan, 7=Konsesi+Lain
BAHAGIAN_KLUSTER_MAP = {
    'jkn':  [0, 1, 2, 3, 4, 5, 6, 7],  # JKN – semua kluster
    'bkej': [0, 1, 5],   # Kejuruteraan: K1 + K5
    'bpem': [0, 5, 6],   # Pembangunan: K5 + K6
    'bsm':  [0, 2],       # Sumber Manusia: K2
    'bpp':  [0, 3],       # Perkembangan Perubatan: K3
    'bkjw': [0, 2, 3],   # Kejururawatan: K2 + K3
    'bskb': [0, 3],       # Sains Kesihatan: K3
    'bprc': [0, 6],       # Perancangan: K6
    'bkp':  [0, 3],       # Kawalan Penyakit: K3
    'bap':  [0, 4],       # Amalan Perubatan: K4
    'bka':  [0, 3, 5],   # Kesihatan Awam: K3 + K5
    'bkd':  [0, 3],       # Kesihatan Digital: K3
    'bpm':  [0, 3],       # Pengurusan Maklumat: K3
    'bpmk': [0, 3],       # Pemakanan: K3
    'bpro': [0, 7],       # Perolehan: K7
    'ppf':  [0, 3],       # Farmasi: K3
}

# Fields belonging to each step (for partial save)
KLUSTER_FIELDS = {
    0: ['nama_fasiliti', 'jenis_fasiliti', 'negeri', 'daerah', 'wilayah', 'zon', 'parlimen', 'alamat', 'poskod', 'latitud', 'longitud'],
    1: ['kod_fasiliti', 'tahun_dibina', 'jenis_hospital_klinik', 'siling_okay', 'ukuran_tanah'],
    2: ['kakitangan_tetap', 'kakitangan_kontrak', 'kakitangan_mystep', 'ada_kakitangan_pinjaman',
        'bilangan_shift', 'ada_ot_allowance', 'bilangan_staff_non_medical', 'waktu_beroperasi',
        'cara_minta_cuti', 'isu_penempatan'],
    3: ['jenis_perkhidmatan', 'anggaran_pelawat_harian', 'jenis_penyakit_kerap', 'boleh_selesaikan_kes',
        'rujukan_ke', 'ada_ruang_rehat', 'ada_hemodialisis', 'unit_hemodialisis',
        'bekalan_ubat_mencukupi', 'keperluan_oksigen', 'ada_emr', 'wad_diasingkan',
        'kualiti_makanan', 'siapa_manage', 'masa_tunggu', 'ada_osca'],
    4: ['disposable_mencukupi', 'keadaan_aset', 'ada_ambulans', 'keadaan_ambulans',
        'aset_perlu_diganti', 'aset_tidak_ikut_spec', 'umur_komputer'],
    5: ['keadaan_perabot', 'ada_quarters', 'quarters_mencukupi', 'ada_isu_parking',
        'masalah_aircond', 'ruang_kerja_mencukupi', 'ada_bilik_mayat', 'ada_pantry',
        'ada_kantin', 'ada_security'],
    6: ['perkhidmatan_baru', 'fasiliti_diperlukan'],
    7: ['maintenance_okay', 'masalah_utama', 'wishlist'],
}

KLUSTER_LABEL = {
    0: 'Maklumat Asas',
    1: 'Kejuruteraan',
    2: 'Sumber Manusia',
    3: 'Perkhidmatan Kesihatan',
    4: 'Aset',
    5: 'Fasiliti',
    6: 'Perancangan',
    7: 'Konsesi & Lain-lain',
}

# Primary owner label for locked step notice
KLUSTER_OWNER_LABEL = {
    1: 'Bahagian Kejuruteraan',
    2: 'Bahagian Sumber Manusia',
    3: 'Bahagian Perkembangan Perubatan / Perkhidmatan',
    4: 'Bahagian Amalan Perubatan',
    5: 'Bahagian Kejuruteraan / Pembangunan',
    6: 'Bahagian Perancangan',
    7: 'Bahagian Perolehan / JKN',
}


def get_allowed_steps(user):
    """Return sorted list of step indices the user may fill."""
    return list(range(8))


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def is_admin(user):
    return user.is_staff or user.is_superuser


def is_top_management_user(user):
    """Return True if the user is a Top Management (read-only) account."""
    try:
        return bool(user.profile.is_top_management)
    except Exception:
        return False


def is_jkn_user(user):
    """Return True if the user is a JKN account (sees all, edits own only)."""
    try:
        return bool(user.profile.is_jkn)
    except Exception:
        return False


# ──────────────────────────────────────────────
# Landing page (public)
# ──────────────────────────────────────────────
class LandingPageView(TemplateView):
    template_name = 'home/landing.html'


# ──────────────────────────────────────────────
# Dashboard (login required + bahagian access check)
# ──────────────────────────────────────────────
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'home/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        # Superadmin / staff / top management / JKN have access to all bahagian
        if request.user.is_superuser or request.user.is_staff or is_top_management_user(request.user) or is_jkn_user(request.user):
            return response
        # Regular users: check if they have access to the requested section
        slug = request.GET.get('section', '')
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if slug and slug not in profile.bahagian_slugs:
            messages.error(request, 'Anda tidak mempunyai akses ke bahagian ini.')
            return redirect('home:bahagian')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.request.GET.get('section', '')
        context['section_name'] = SLUG_TO_NAME.get(slug, slug)
        context['section_slug'] = slug
        section_obj = next((s for s in ALL_SECTIONS if s['slug'] == slug), None)
        context['section'] = section_obj
        # Real KPI data
        from django.db.models import Q
        import datetime
        _year = int(self.request.GET.get('tahun', datetime.date.today().year))
        user = self.request.user
        _is_tm = is_top_management_user(user)
        _is_jkn = is_jkn_user(user)
        if user.is_superuser or _is_tm or _is_jkn:
            qs_kpi = FacilityProfile.objects.filter(tahun=_year)
        else:
            qs_kpi = FacilityProfile.objects.filter(Q(submitted_by=user) | Q(submitted_by__isnull=True), tahun=_year)
        context['kpi_total']   = qs_kpi.count()
        from django.utils import timezone as _tz
        _threshold = _tz.now() - datetime.timedelta(days=365)
        context['kpi_aktif']   = qs_kpi.filter(status='aktif').count()
        context['kpi_tutup']   = qs_kpi.filter(status='tutup').count()
        context['kpi_pending'] = qs_kpi.filter(status='aktif', updated_at__lt=_threshold).count()
        context['kpi_tahun']   = _year
        context['is_tm']       = _is_tm
        context['is_jkn']      = _is_jkn
        all_tahun_main = FacilityProfile.objects.values_list('tahun', flat=True).distinct().order_by('-tahun')
        context['all_tahun_main'] = all_tahun_main
        # ── Pending update detection (for notification banner) ───
        _cy = datetime.date.today().year
        _py = _cy - 1
        if user.is_superuser or _is_tm or _is_jkn:
            base = FacilityProfile.objects.select_related('maklumat_asas')
        else:
            base = FacilityProfile.objects.filter(
                Q(submitted_by=user) | Q(submitted_by__isnull=True)
            ).select_related('maklumat_asas')
        prev_names = set(base.filter(tahun=_py).values_list('maklumat_asas__nama_fasiliti', flat=True))
        curr_names  = set(base.filter(tahun=_cy).values_list('maklumat_asas__nama_fasiliti', flat=True))
        pending_names = prev_names - curr_names
        context['pending_count'] = len(pending_names)
        context['current_year']  = _cy
        context['prev_year']     = _py
        return context


# ──────────────────────────────────────────────
# Section selection / facility list
# ──────────────────────────────────────────────
@login_required
def bahagian_view(request):
    """Halaman utama — senarai semua fasiliti. Klik Edit untuk pilih modul."""
    if is_top_management_user(request.user):
        return redirect('home:tm_portal')
    import re
    from django.core.paginator import Paginator
    qs = FacilityProfile.objects.select_related('maklumat_asas').order_by('-updated_at')
    carian = request.GET.get('carian', '').strip()
    if carian:
        qs = qs.filter(maklumat_asas__nama_fasiliti__icontains=carian)
    paginator = Paginator(qs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'home/bahagian.html', {
        'fasiliti': page_obj,
        'page_obj': page_obj,
        'carian': carian,
        'is_tm': False,
    })


@login_required
def tm_portal(request):
    """Portal khas untuk Top Management — akses baca sahaja."""
    if not is_top_management_user(request.user):
        return redirect('home:bahagian')
    import datetime
    from django.core.paginator import Paginator
    # Stats
    from django.utils import timezone as _tz_tm
    _threshold_tm = _tz_tm.now() - datetime.timedelta(days=365)
    total   = FacilityProfile.objects.count()
    aktif   = FacilityProfile.objects.filter(status='aktif').count()
    tutup   = FacilityProfile.objects.filter(status='tutup').count()
    pending = FacilityProfile.objects.filter(status='aktif', updated_at__lt=_threshold_tm).count()
    tahun   = datetime.date.today().year
    jumlah_tahun = FacilityProfile.objects.filter(tahun=tahun).count()
    # Senarai laporan (paginated)
    import re
    qs = FacilityProfile.objects.select_related('maklumat_asas').order_by('-updated_at')
    carian = request.GET.get('carian', '').strip()
    if carian:
        qs = qs.filter(maklumat_asas__nama_fasiliti__icontains=carian)
    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'home/tm_portal.html', {
        'total': total, 'aktif': aktif, 'tutup': tutup, 'pending': pending,
        'tahun': tahun, 'jumlah_tahun': jumlah_tahun,
        'fasiliti': page_obj, 'page_obj': page_obj,
        'carian': carian,
    })


@login_required
def pilih_modul(request, pk):
    """Pilih modul untuk dikemaskini bagi fasiliti tertentu."""
    if is_top_management_user(request.user):
        messages.error(request, 'Top Management hanya mempunyai akses baca sahaja.')
        return redirect('home:bahagian')
        
    fp = get_object_or_404(FacilityProfile, pk=pk)
    
    # --- PENGESAHAN AKSES JKN ---
    if not request.user.is_superuser and not request.user.is_staff:
        # Semak jika nama fasiliti tiada dalam senarai staf
        if fp.nama_fasiliti not in request.user.profile.assigned_facility_names:
            messages.error(request, 'Akses Ditolak: Anda tidak ditugaskan untuk mengedit fasiliti ini.')
            return redirect('home:bahagian')
    # -----------------------------
            
    return render(request, 'home/pilih_modul.html', {'fp': fp})


@login_required
def peta_fasiliti(request):
    """Peta Malaysia dengan pin lokasi semua fasiliti mengikut daerah. (Admin & Top Management sahaja)."""
    if not (request.user.is_superuser or request.user.is_staff):
        if is_top_management_user(request.user):
            return redirect('home:peta_tm')
        from django.contrib import messages
        messages.error(request, "Akses ditolak. Halaman ini untuk Admin sahaja.")
        return redirect('home:bahagian')
    import json
    fps = FacilityProfile.objects.select_related('maklumat_asas').all()
    data = []
    for fp in fps:
        if fp.maklumat_asas:
            ma = fp.maklumat_asas
            data.append({
                'pk':     fp.pk,
                'nama':   ma.nama_fasiliti,
                'jenis':  ma.get_jenis_fasiliti_display(),
                'negeri': ma.get_negeri_display(),
                'daerah': ma.daerah,
                'alamat': ma.alamat or '',
                'poskod': ma.poskod or '',
                'status': fp.status,
                'tahun':  fp.tahun or '',
                'lat':    ma.latitud,
                'lng':    ma.longitud,
                'status_lawatan': fp.status_lawatan,
            })
    return render(request, 'home/peta_fasiliti.html', {
        'fasiliti_json': json.dumps(data, ensure_ascii=False),
        'jumlah': len(data),
    })


@login_required
def peta_tm(request):
    """Peta baca-sahaja untuk Top Management."""
    if not is_top_management_user(request.user):
        return redirect('home:bahagian')
    import json
    fps = FacilityProfile.objects.select_related('maklumat_asas').all()
    data = []
    for fp in fps:
        if fp.maklumat_asas:
            ma = fp.maklumat_asas
            data.append({
                'pk':     fp.pk,
                'nama':   ma.nama_fasiliti,
                'jenis':  ma.get_jenis_fasiliti_display(),
                'negeri': ma.get_negeri_display(),
                'daerah': ma.daerah,
                'alamat': ma.alamat or '',
                'poskod': ma.poskod or '',
                'status': fp.status,
                'tahun':  fp.tahun or '',
                'lat':    ma.latitud,
                'lng':    ma.longitud,
                'status_lawatan': fp.status_lawatan,
            })
    return render(request, 'home/peta_tm.html', {
        'fasiliti_json': json.dumps(data, ensure_ascii=False),
        'jumlah': len(data),
    })


@login_required
def bahagian_fasiliti(request):
    """Landing page untuk sub-modul Fasiliti — pilih Tambah, Senarai atau Dashboard."""
    return render(request, 'home/bahagian_fasiliti.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def tukar_status_fasiliti(request, pk):
    """Superadmin sahaja boleh tukar status fasiliti (aktif/tutup)."""
    if request.method != 'POST':
        return redirect('home:senarai_fasiliti')
    fp = get_object_or_404(FacilityProfile, pk=pk)
    new_status = request.POST.get('status', '').strip()
    if new_status in ('aktif', 'tutup'):
        fp.status = new_status
        fp.save(update_fields=['status'])
        messages.success(request, f'Status "{fp.nama_fasiliti}" ditukar kepada {new_status.upper()}.')
    else:
        messages.error(request, 'Status tidak sah.')
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', ''))
    return redirect(next_url or 'home:senarai_fasiliti')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def superadmin(request):
    from django.utils import timezone
    from datetime import timedelta
    total_users   = User.objects.count()
    super_users   = User.objects.filter(is_superuser=True).count()
    staff_users   = User.objects.filter(is_staff=True, is_superuser=False).count()
    biasa_users   = total_users - super_users - staff_users
    recent_logins = User.objects.filter(last_login__isnull=False).order_by('-last_login')[:8]
    for u in recent_logins:
        profile, _ = UserProfile.objects.get_or_create(user=u)
        u.is_top_management = profile.is_top_management
        u.is_jkn = profile.is_jkn
    new_this_week = User.objects.filter(date_joined__gte=timezone.now()-timedelta(days=7)).count()
    return render(request, 'home/superadmin.html', {
        'total_users':   total_users,
        'staff_users':   staff_users,
        'super_users':   super_users,
        'biasa_users':   biasa_users,
        'recent_logins': recent_logins,
        'new_this_week': new_this_week,
    })

@login_required
@user_passes_test(is_admin)
def urus_pengguna(request):
    users = User.objects.all().order_by('username')
    for u in users:
        profile, _ = UserProfile.objects.get_or_create(user=u)
        u.bahagian_names = [SLUG_TO_NAME[s] for s in profile.bahagian_slugs if s in SLUG_TO_NAME]
        u.is_top_management = profile.is_top_management
        u.is_jkn = profile.is_jkn
    return render(request, 'home/urus_pengguna.html', {'users': users, 'active_page': 'urus_pengguna'})

@login_required
@user_passes_test(is_admin)
def tambah_pengguna(request):
    if request.method == 'POST':
        username       = request.POST.get('username', '').strip()
        password       = request.POST.get('password', '').strip()
        full_name      = request.POST.get('full_name', '').strip()
        email          = request.POST.get('email', '').strip()
        is_staff       = request.POST.get('is_staff') == 'on'
        selected_slugs = request.POST.getlist('bahagian')  # multi-checkbox

        if not username or not password:
            messages.error(request, 'Nama pengguna dan kata laluan wajib diisi.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'Nama pengguna "{username}" sudah wujud.')
        else:
            names = full_name.split(' ', 1)
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=names[0],
                last_name=names[1] if len(names) > 1 else '',
                is_staff=is_staff,
            )
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.bahagian_slugs = selected_slugs
            
            # --- Tiga Baris Kod Baru Untuk Pendaftaran Role ---
            profile.is_top_management = request.POST.get('is_top_management') == 'on'
            profile.is_jkn = request.POST.get('is_jkn') == 'on'
            profile.assigned_facility_names = request.POST.getlist('assigned_facilities')
            
            profile.save()
            messages.success(request, f'Pengguna "{username}" berjaya ditambah.')
            return redirect('home:urus_pengguna')
            
    # Ambil senarai semua fasiliti untuk diletakkan dalam ruangan 'Tandakan Fasiliti'
    all_facilities = list(
        MaklumatAsas.objects.filter(profil__isnull=False)
        .values_list('nama_fasiliti', flat=True)
        .distinct().order_by('nama_fasiliti')
    )
    
    return render(request, 'home/tambah_pengguna.html', {
        'all_facilities': all_facilities
    })

@login_required
@user_passes_test(is_admin)
def edit_pengguna(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        parts = full_name.split(' ', 1)
        target.first_name = parts[0]
        target.last_name  = parts[1] if len(parts) > 1 else ''
        target.email      = request.POST.get('email', '').strip()
        if not target.is_superuser:
            target.is_staff = request.POST.get('is_staff') == 'on'
        new_pass = request.POST.get('password', '').strip()
        if new_pass:
            target.set_password(new_pass)
        target.save()
        profile.bahagian_slugs = request.POST.getlist('bahagian')
        profile.is_top_management = request.POST.get('is_top_management') == 'on'
        profile.is_jkn = request.POST.get('is_jkn') == 'on'
        profile.assigned_facility_names = request.POST.getlist('assigned_facilities')
        profile.save()
        messages.success(request, f'Pengguna "{target.username}" berjaya dikemaskini.')
        return redirect('home:urus_pengguna')
    # All unique facility names for the picker
    all_facilities = list(
        MaklumatAsas.objects.filter(profil__isnull=False)
        .values_list('nama_fasiliti', flat=True)
        .distinct().order_by('nama_fasiliti')
    )
    return render(request, 'home/edit_pengguna.html', {
        'target':                  target,
        'all_sections':            ALL_SECTIONS,
        'user_slugs':              profile.bahagian_slugs,
        'is_target_tm':            profile.is_top_management,
        'is_target_jkn':           profile.is_jkn,
        'assigned_facility_names': profile.assigned_facility_names,
        'all_facilities':          all_facilities,
    })

@login_required
@user_passes_test(is_admin)
def padam_pengguna(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    # Block deleting any superuser account (protects against self-lockout)
    if target.is_superuser:
        messages.error(request, 'Akaun Superadmin tidak boleh dipadam.')
        return redirect('home:urus_pengguna')
    if request.method == 'POST':
        if target == request.user:
            messages.error(request, 'Anda tidak boleh memadam akaun anda sendiri.')
        else:
            uname = target.username
            target.delete()
            messages.success(request, f'Pengguna "{uname}" berjaya dipadam.')
        return redirect('home:urus_pengguna')
    return render(request, 'home/padam_pengguna.html', {'target': target})


# ──────────────────────────────────────────────
# User self-profile (all logged-in users)
# ──────────────────────────────────────────────
@login_required
def profil_saya(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    bahagian_names = [SLUG_TO_NAME.get(s, s) for s in profile.bahagian_slugs]
    return render(request, 'home/profil_saya.html', {
        'profile': profile,
        'bahagian_names': bahagian_names,
    })


@login_required
def edit_profil(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        parts = full_name.split(' ', 1)
        request.user.first_name = parts[0]
        request.user.last_name  = parts[1] if len(parts) > 1 else ''
        request.user.email      = request.POST.get('email', '').strip()
        new_pass = request.POST.get('password', '').strip()
        if new_pass:
            request.user.set_password(new_pass)
        request.user.save()
        messages.success(request, 'Profil anda berjaya dikemaskini.')
        if new_pass:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
        return redirect('home:profil_saya')
    return render(request, 'home/edit_profil.html')


# ══════════════════════════════════════════════
# PROFILING HOSPITAL & KLINIK
# ══════════════════════════════════════════════

@login_required
def detail_fasiliti(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if is_top_management_user(request.user):
        return render(request, 'home/tm_detail_fasiliti.html', {'fp': fp})
    return render(request, 'home/detail_fasiliti.html', {'fp': fp})


@login_required
def fasiliti_api_detail(request, pk):
    """JSON API — return all kluster data for one FacilityProfile (used by peta popup drawer)."""
    from django.http import JsonResponse
    fp = get_object_or_404(FacilityProfile.objects.select_related(
        'maklumat_asas', 'k_kejuruteraan', 'k_sumber_manusia',
        'k_perkhidmatan', 'k_aset', 'k_fasiliti', 'k_perancangan', 'k_konsesi',
    ), pk=pk)

    def yn(val):
        if val is True:  return 'Ya'
        if val is False: return 'Tidak'
        return '—'

    def txt(val):
        return val if val else '—'

    ma = fp.maklumat_asas
    k1 = fp.k_kejuruteraan
    k2 = fp.k_sumber_manusia
    k3 = fp.k_perkhidmatan
    k4 = fp.k_aset
    k5 = fp.k_fasiliti
    k6 = fp.k_perancangan
    k7 = fp.k_konsesi

    data = {
        'pk':     fp.pk,
        'status': fp.status,
        'tahun':  fp.tahun,
        'edit_url':   f'/profiling/{fp.pk}/edit/',
        'detail_url': f'/profiling/{fp.pk}/detail/',
        'k0': {
            'nama':   ma.nama_fasiliti if ma else '—',
            'jenis':  ma.get_jenis_fasiliti_display() if ma else '—',
            'negeri': ma.get_negeri_display() if ma else '—',
            'daerah': txt(ma.daerah) if ma else '—',
            'alamat': txt(ma.alamat) if ma else '—',
            'poskod': txt(ma.poskod) if ma else '—',
            'lat':    ma.latitud if ma else None,
            'lng':    ma.longitud if ma else None,
            'status_lawatan': fp.status_lawatan,
            'nama_program': fp.nama_program_lawatan or '',
            'tarikh_lawatan': str(fp.tarikh_lawatan) if fp.tarikh_lawatan else '',
            'catatan': fp.catatan_lawatan or '',
            # Tambahan Fasa 1
            'nama_responden': txt(ma.nama_responden) if ma else '—',
            'jawatan_responden': txt(ma.jawatan_responden) if ma else '—',
            'no_telefon_responden': txt(ma.no_telefon_responden) if ma else '—',
            'emel_responden': txt(ma.emel_responden) if ma else '—',
        },
        'k1': None if not k1 else {
            'tahun_dibina':          str(k1.tahun_dibina) if k1.tahun_dibina else '—',
            'jenis_hospital_klinik': txt(k1.jenis_hospital_klinik),
            'siling_okay':           yn(k1.siling_okay),
            'ukuran_tanah':          txt(k1.ukuran_tanah),
            # Tambahan Fasa 2
            'siling_nota':           txt(k1.siling_nota),
            'tanah_mencukupi':       yn(k1.tanah_mencukupi),
        },
        'k2': None if not k2 else {
            'kakitangan_tetap':           str(k2.kakitangan_tetap) if k2.kakitangan_tetap is not None else '—',
            'kakitangan_kontrak':         str(k2.kakitangan_kontrak) if k2.kakitangan_kontrak is not None else '—',
            'kakitangan_mystep':          str(k2.kakitangan_mystep) if k2.kakitangan_mystep is not None else '—',
            'ada_kakitangan_pinjaman':    yn(k2.ada_kakitangan_pinjaman),
            'bilangan_shift':             str(k2.bilangan_shift) if k2.bilangan_shift is not None else '—',
            'ada_ot_allowance':           yn(k2.ada_ot_allowance),
            'bilangan_staff_non_medical': str(k2.bilangan_staff_non_medical) if k2.bilangan_staff_non_medical is not None else '—',
            'waktu_beroperasi':           txt(k2.waktu_beroperasi),
            'cara_minta_cuti':            txt(k2.cara_minta_cuti),
            'isu_penempatan':             txt(k2.isu_penempatan),
            # Tambahan Fasa 4
            'jumlah_perjawatan':          str(k2.jumlah_perjawatan) if k2.jumlah_perjawatan is not None else '—',
            'jumlah_pengisian':           str(k2.jumlah_pengisian) if k2.jumlah_pengisian is not None else '—',
            'jumlah_kekosongan':          str(k2.jumlah_kekosongan) if k2.jumlah_kekosongan is not None else '—',
            'nota_kakitangan_pinjaman':   txt(k2.nota_kakitangan_pinjaman),
            'ada_isu_kakitangan':         yn(k2.ada_isu_kakitangan),
            'ada_fasiliti_petugas':       yn(k2.ada_fasiliti_petugas),
            'jenis_shift':                txt(k2.jenis_shift),
            'corak_penugasan':            txt(k2.corak_penugasan),
            'pengurusan_jadual':          txt(k2.pengurusan_jadual),
            'status_pertukaran_staf':     txt(k2.status_pertukaran_staf),
        },
        'k3': None if not k3 else {
            'jenis_perkhidmatan':      txt(k3.jenis_perkhidmatan),
            'anggaran_pelawat_harian': str(k3.anggaran_pelawat_harian) if k3.anggaran_pelawat_harian is not None else '—',
            'jenis_penyakit_kerap':    txt(k3.jenis_penyakit_kerap),
            'boleh_selesaikan_kes':    yn(k3.boleh_selesaikan_kes),
            'rujukan_ke':              txt(k3.rujukan_ke),
            'ada_ruang_rehat':         yn(k3.ada_ruang_rehat),
            'ada_hemodialisis':        yn(k3.ada_hemodialisis),
            'unit_hemodialisis':       str(k3.unit_hemodialisis) if k3.unit_hemodialisis is not None else '—',
            'bekalan_ubat_mencukupi':  yn(k3.bekalan_ubat_mencukupi),
            'keperluan_oksigen':       txt(k3.keperluan_oksigen),
            'ada_emr':                 yn(k3.ada_emr),
            'wad_diasingkan':          yn(k3.wad_diasingkan),
            'kualiti_makanan':         txt(k3.kualiti_makanan),
            'siapa_manage':            txt(k3.siapa_manage),
            'masa_tunggu':             txt(k3.masa_tunggu),
            'ada_osca':                yn(k3.ada_osca),
            # Tambahan Fasa 5
            'ruang_tunggu_selesa':     yn(k3.ruang_tunggu_selesa),
            'ruang_tunggu_nota':       txt(k3.ruang_tunggu_nota),
            'kekangan_rawatan':        txt(k3.kekangan_rawatan),
        },
        'k4': None if not k4 else {
            'disposable_mencukupi': yn(k4.disposable_mencukupi),
            'keadaan_aset':         txt(k4.keadaan_aset),
            'ada_ambulans':         yn(k4.ada_ambulans),
            'keadaan_ambulans':     txt(k4.keadaan_ambulans),
            'aset_perlu_diganti':   txt(k4.aset_perlu_diganti),
            'aset_tidak_ikut_spec': txt(k4.aset_tidak_ikut_spec),
            'umur_komputer':        txt(k4.umur_komputer),
            # Tambahan Fasa 3
            'senarai_peralatan':    txt(k4.senarai_peralatan),
            'ambulans_nota':        txt(k4.ambulans_nota),
            'sistem_pendigitalan':  txt(k4.sistem_pendigitalan),
            'gajet_ict_baik':       yn(k4.gajet_ict_baik),
            'gajet_ict_nota':       txt(k4.gajet_ict_nota),
        },
        'k5': None if not k5 else {
            'keadaan_perabot':       txt(k5.keadaan_perabot),
            'ada_quarters':          yn(k5.ada_quarters),
            'quarters_mencukupi':    yn(k5.quarters_mencukupi),
            'ada_isu_parking':       yn(k5.ada_isu_parking),
            'masalah_aircond':       yn(k5.masalah_aircond),
            'ruang_kerja_mencukupi': yn(k5.ruang_kerja_mencukupi),
            'ada_bilik_mayat':       yn(k5.ada_bilik_mayat),
            'ada_pantry':            yn(k5.ada_pantry),
            'ada_kantin':            yn(k5.ada_kantin),
            'ada_security':          yn(k5.ada_security),
            # Tambahan Fasa 2
            'ada_parking':           yn(k5.ada_parking),
            'parking_mencukupi':     yn(k5.parking_mencukupi),
            'aircond_nota':          txt(k5.aircond_nota),
            'masalah_kipas':         yn(k5.masalah_kipas),
            'kipas_nota':            txt(k5.kipas_nota),
        },
        'k6': None if not k6 else {
            'perkhidmatan_baru':   txt(k6.perkhidmatan_baru),
            'fasiliti_diperlukan': txt(k6.fasiliti_diperlukan),
            # Tambahan Fasa 6
            'belanja_mengurus':    txt(k6.belanja_mengurus),
            'belanja_pembangunan': txt(k6.belanja_pembangunan),
        },
        'k7': None if not k7 else {
            'maintenance_okay': yn(k7.maintenance_okay),
            'masalah_utama':    txt(k7.masalah_utama),
            'wishlist':         txt(k7.wishlist),
            # Tambahan Fasa 7
            'prosedur_kes_dadah':     txt(k7.prosedur_kes_dadah),
            'hemodialisis_nota':      txt(k7.hemodialisis_nota),
            'status_bekalan_oksigen': txt(k7.status_bekalan_oksigen),
            'wishlist_fail_url':      k7.wishlist_fail.url if k7.wishlist_fail else None,
        },
    }
    return JsonResponse(data)


@login_required
def senarai_fasiliti(request):
    import datetime
    _cy = datetime.date.today().year
    _py = _cy - 1

    base_qs = FacilityProfile.objects.select_related(
        'maklumat_asas', 'k_kejuruteraan', 'k_sumber_manusia',
        'k_perkhidmatan', 'k_aset', 'k_fasiliti', 'k_perancangan', 'k_konsesi',
    )
    _is_tm = is_top_management_user(request.user)
    _is_jkn = is_jkn_user(request.user)
    # All users see ALL facilities; edit permission is controlled separately via assigned_facility_names

    # ── Pending-update detection ─────────────────────────────────
    # Facilities from last year that do NOT have a current-year entry yet
    prev_year_fps = base_qs.filter(tahun=_py)
    prev_names = set(prev_year_fps.values_list('maklumat_asas__nama_fasiliti', flat=True))
    curr_names  = set(base_qs.filter(tahun=_cy).values_list('maklumat_asas__nama_fasiliti', flat=True))
    pending_names = prev_names - curr_names
    pending_fps = list(prev_year_fps.filter(
        maklumat_asas__nama_fasiliti__in=pending_names
    ).select_related('maklumat_asas').order_by('maklumat_asas__nama_fasiliti')) if pending_names else []

    qs = base_qs.order_by('-updated_at')

    # Carian nama fasiliti
    import re
    carian = request.GET.get('carian', '').strip()
    if carian:
        qs = qs.filter(maklumat_asas__nama_fasiliti__icontains=carian)

    # Filter negeri
    negeri_filter = request.GET.get('negeri', '').strip()
    if negeri_filter:
        qs = qs.filter(maklumat_asas__negeri__iexact=negeri_filter)

    # Filter status
    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'pending':
        from django.utils import timezone as _tz_senarai
        _thr_senarai = _tz_senarai.now() - __import__('datetime').timedelta(days=365)
        qs = qs.filter(status='aktif', updated_at__lt=_thr_senarai)
    elif status_filter:
        qs = qs.filter(status=status_filter)

    # Filter tahun
    tahun_filter = request.GET.get('tahun', '').strip()
    if tahun_filter:
        qs = qs.filter(tahun=tahun_filter)

    # Senarai negeri unik dari profil yang ada
    all_negeri = MaklumatAsas.objects.filter(
        profil__isnull=False
    ).values_list('negeri', flat=True).distinct().order_by('negeri')

    # Senarai tahun unik
    all_tahun = FacilityProfile.objects.values_list('tahun', flat=True).distinct().order_by('-tahun')

    from django.core.paginator import Paginator
    paginator = Paginator(qs, 50)
    page = request.GET.get('page', 1)
    fasiliti_page = paginator.get_page(page)

    return render(request, 'home/senarai_fasiliti.html', {
        'fasiliti': fasiliti_page,
        'jumlah_total': qs.count(),
        'carian': carian,
        'negeri_filter': negeri_filter,
        'status_filter': status_filter,
        'tahun_filter': tahun_filter,
        'all_negeri': all_negeri,
        'all_tahun': all_tahun,
        'current_year': _cy,
        'prev_year': _py,
        'pending_fps': pending_fps,
        'is_tm': _is_tm,
        'is_jkn': _is_jkn,
        'user_assigned_names': set(request.user.profile.assigned_facility_names) if not request.user.is_superuser and not request.user.is_staff else None,
    })


@login_required
def tambah_fasiliti(request):
    if is_top_management_user(request.user):
        messages.error(request, 'Top Management hanya mempunyai akses baca sahaja.')
        return redirect('home:senarai_fasiliti')
    if not request.user.is_superuser and not request.user.is_staff and not is_jkn_user(request.user):
        messages.error(request, 'Anda tidak mempunyai akses untuk menambah profil fasiliti.')
        return redirect('home:senarai_fasiliti')
        
    if request.method == 'POST':
        allowed = get_allowed_steps(request.user)
        fp = FacilityProfile(submitted_by=request.user)
        clusters = _build_clusters_new()
        
        # Hantar keseluruhan 'request' supaya fail boleh dibaca
        _save_facility_form(request, clusters, allowed)
        
        import datetime as _dt
        try: fp.tahun = int(request.POST.get('tahun', 0)) or _dt.date.today().year
        except (ValueError, TypeError): fp.tahun = _dt.date.today().year
            
        for step, attr, _ in CLUSTER_ATTR_MAP:
            if step in allowed:
                obj = clusters[step]
                obj.save()
                setattr(fp, attr, obj)
        fp.save()
        nama = clusters[0].nama_fasiliti if clusters.get(0) else ''
        messages.success(request, f'Profil "{nama}" berjaya ditambah.')
        return redirect('home:senarai_fasiliti')
        
    import datetime as _dt
    _cy = _dt.date.today().year
    return render(request, 'home/form_fasiliti.html', {
        'mode': 'tambah',
        'facility': None,
        'current_year': _cy,
    })


@login_required
def edit_fasiliti(request, pk):
    if is_top_management_user(request.user):
        messages.error(request, 'Top Management hanya mempunyai akses baca sahaja.')
        return redirect('home:senarai_fasiliti')
        
    fp = get_object_or_404(FacilityProfile, pk=pk)
    
    if request.method == 'POST':
        allowed = get_allowed_steps(request.user)
        clusters = _build_clusters_from_fp(fp)
        
        # Hantar keseluruhan 'request' supaya fail boleh dibaca
        _save_facility_form(request, clusters, allowed)
        
        try: fp.tahun = int(request.POST.get('tahun', 0)) or fp.tahun
        except (ValueError, TypeError): pass
            
        if 0 in allowed:
            ma = clusters[0]
            if ma.pk:
                MaklumatAsas.objects.filter(pk=ma.pk).update(
                    nama_responden=ma.nama_responden, jawatan_responden=ma.jawatan_responden,
                    no_telefon_responden=ma.no_telefon_responden, emel_responden=ma.emel_responden,
                    nama_fasiliti=ma.nama_fasiliti, jenis_fasiliti=ma.jenis_fasiliti,
                    negeri=ma.negeri, daerah=ma.daerah, alamat=ma.alamat, poskod=ma.poskod,
                    latitud=ma.latitud, longitud=ma.longitud
                )
            else:
                ma.save()
                fp.maklumat_asas = ma
                
        for step, attr, _ in CLUSTER_ATTR_MAP:
            if step == 0: continue
            if step in allowed:
                obj = clusters[step]
                obj.save()
                setattr(fp, attr, obj)
        fp.save()
        messages.success(request, f'Profil "{fp.nama_fasiliti}" berjaya dikemaskini.')
        return redirect('home:senarai_fasiliti')

    # Convert object to JSON for JS pre-fill
    fdata = {}
    for step, attr, _ in CLUSTER_ATTR_MAP:
        obj = getattr(fp, attr, None)
        if not obj: continue
        for field in obj._meta.get_fields():
            if not hasattr(obj, field.name): continue
            val = getattr(obj, field.name)
            if val is None: fdata[field.name] = ''
            elif isinstance(val, bool): fdata[field.name] = '1' if val else '0'
            elif hasattr(val, 'pk'): continue
            else: fdata[field.name] = str(val)
            
    if fdata.get('jenis_fasiliti'): fdata['jenis_fasiliti'] = _norm_jenis(fdata['jenis_fasiliti'])
    if fdata.get('negeri'): fdata['negeri'] = _norm_negeri(fdata['negeri'])
    fdata['tahun'] = str(fp.tahun) if fp.tahun else ''
    
    import datetime
    return render(request, 'home/form_fasiliti.html', {
        'mode': 'edit',
        'facility': fp,
        'facility_json': json.dumps(fdata),
        'current_year': datetime.date.today().year,
    })


@login_required
def padam_fasiliti(request, pk):
    # Top Management is read-only
    if is_top_management_user(request.user):
        messages.error(request, 'Top Management hanya mempunyai akses baca sahaja.')
        return redirect('home:senarai_fasiliti')
    fp = get_object_or_404(FacilityProfile, pk=pk)
    # Non-superuser and non-admin: must have the facility explicitly assigned
    if not request.user.is_superuser and not request.user.is_staff:
        _assigned = set(request.user.profile.assigned_facility_names)
        if fp.nama_fasiliti not in _assigned:
            messages.error(request, 'Anda tidak dibenarkan memadam fasiliti ini. Hubungi admin untuk mendapatkan akses.')
            return redirect('home:senarai_fasiliti')
    if request.method == 'POST':
        nama = fp.nama_fasiliti
        fp.delete()
        messages.success(request, f'Profil "{nama}" berjaya dipadam.')
    return redirect('home:senarai_fasiliti')


@login_required
def dashboard_fasiliti(request):
    from django.db.models import Q
    if request.user.is_superuser or is_top_management_user(request.user) or is_jkn_user(request.user):
        qs = FacilityProfile.objects.all().select_related(
            'maklumat_asas', 'k_kejuruteraan', 'k_aset', 'k_fasiliti',
            'k_perkhidmatan', 'k_sumber_manusia', 'k_konsesi'
        )
    else:
        qs = FacilityProfile.objects.filter(
            Q(submitted_by=request.user) | Q(submitted_by__isnull=True)
        ).select_related(
            'maklumat_asas', 'k_kejuruteraan', 'k_aset', 'k_fasiliti',
            'k_perkhidmatan', 'k_sumber_manusia', 'k_konsesi'
        )

    # ── GET filters ─────────────────────────────────────────────
    import datetime
    _this_year = datetime.date.today().year
    f_negeri = request.GET.get('f_negeri', '').strip()
    f_jenis  = request.GET.get('f_jenis',  '').strip()
    f_status = request.GET.get('f_status', '').strip()
    f_tahun  = request.GET.get('f_tahun',  str(_this_year)).strip()
    if f_negeri:
        qs = qs.filter(maklumat_asas__negeri=f_negeri)
    if f_jenis:
        qs = qs.filter(maklumat_asas__jenis_fasiliti=f_jenis)
    if f_status == 'pending':
        from django.utils import timezone as _tz_dash
        _threshold_dash = _tz_dash.now() - datetime.timedelta(days=365)
        qs = qs.filter(status='aktif', updated_at__lt=_threshold_dash)
    elif f_status:
        qs = qs.filter(status=f_status)
    if f_tahun:
        qs = qs.filter(tahun=f_tahun)
    # Available years for dropdown
    all_tahun_dashboard = FacilityProfile.objects.values_list('tahun', flat=True).distinct().order_by('-tahun')

    total   = qs.count()
    from django.utils import timezone as _tz_d
    _thr = _tz_d.now() - datetime.timedelta(days=365)
    aktif   = qs.filter(status='aktif').count()
    tutup   = qs.filter(status='tutup').count()
    pending = qs.filter(status='aktif', updated_at__lt=_thr).count()

    # Skor purata (iterate — select_related ensures no N+1)
    fp_list      = list(qs)
    all_scores   = [fp.skor_kesediaan for fp in fp_list]
    skor_purata  = round(sum(all_scores) / len(all_scores)) if all_scores else 0

    # KPI: jenis fasiliti breakdown
    jenis_labels = [c[1] for c in MaklumatAsas.FACILITY_TYPE_CHOICES]
    jenis_slugs  = [c[0] for c in MaklumatAsas.FACILITY_TYPE_CHOICES]
    jenis_counts = [sum(1 for fp in fp_list if fp.maklumat_asas and fp.maklumat_asas.jenis_fasiliti == s) for s in jenis_slugs]
    # Filter out zero-count types (same as negeri_data)
    jenis_data   = [(l, c) for l, c in zip(jenis_labels, jenis_counts) if c > 0]
    jenis_labels = [d[0] for d in jenis_data]
    jenis_counts = [d[1] for d in jenis_data]

    # Bar chart: common yes/no issues
    issue_fields = [
        ('k_fasiliti__ada_isu_parking',          'Isu Parking'),
        ('k_fasiliti__masalah_aircond',           'Masalah Aircond'),
        ('k_perkhidmatan__ada_hemodialisis',      'Ada Hemodialisis'),
        ('k_perkhidmatan__ada_emr',               'Ada EMR'),
        ('k_aset__ada_ambulans',                  'Ada Ambulans'),
        ('k_fasiliti__ada_quarters',              'Ada Quarters'),
        ('k_fasiliti__ada_security',              'Ada Security'),
        ('k_perkhidmatan__ada_ruang_rehat',       'Ada Ruang Rehat'),
        ('k_perkhidmatan__bekalan_ubat_mencukupi','Bekalan Ubat OK'),
        ('k_aset__disposable_mencukupi',          'Disposable Mencukupi'),
        ('k_fasiliti__ruang_kerja_mencukupi',     'Ruang Kerja OK'),
        ('k_perkhidmatan__wad_diasingkan',        'Wad Diasingkan'),
        ('k_konsesi__maintenance_okay',           'Maintenance OK'),
        ('k_fasiliti__ada_kantin',                'Ada Kantin'),
    ]
    issues_labels = [label for _, label in issue_fields]
    issues_ya     = [qs.filter(**{field: True}).count()  for field, _ in issue_fields]
    issues_tidak  = [qs.filter(**{field: False}).count() for field, _ in issue_fields]

    # Top 10 readiness scores — pick highest scoring
    top10 = sorted(fp_list, key=lambda fp: fp.skor_kesediaan, reverse=True)[:10]
    fasiliti_names  = [fp.nama_fasiliti or '—' for fp in top10]
    fasiliti_scores = [fp.skor_kesediaan for fp in top10]

    # Negeri breakdown
    negeri_labels = [c[1] for c in MaklumatAsas.NEGERI_CHOICES]
    negeri_slugs  = [c[0] for c in MaklumatAsas.NEGERI_CHOICES]
    negeri_counts = [sum(1 for fp in fp_list if fp.maklumat_asas and fp.maklumat_asas.negeri == s) for s in negeri_slugs]
    negeri_data   = [(l, c) for l, c in zip(negeri_labels, negeri_counts) if c > 0]
    negeri_labels = [d[0] for d in negeri_data]
    negeri_counts = [d[1] for d in negeri_data]

    # ── Perkhidmatan analytics ──────────────────────────────────
    perk_with_data  = qs.filter(k_perkhidmatan__isnull=False).count()
    perk_emr        = qs.filter(k_perkhidmatan__ada_emr=True).count()
    perk_hemodial   = qs.filter(k_perkhidmatan__ada_hemodialisis=True).count()
    perk_ubat       = qs.filter(k_perkhidmatan__bekalan_ubat_mencukupi=True).count()
    perk_selesai_kes= qs.filter(k_perkhidmatan__boleh_selesaikan_kes=True).count()
    perk_ruang_rehat= qs.filter(k_perkhidmatan__ada_ruang_rehat=True).count()
    perk_osca       = qs.filter(k_perkhidmatan__ada_osca=True).count()
    perk_wad        = qs.filter(k_perkhidmatan__wad_diasingkan=True).count()
    # Masa Tunggu breakdown
    _masa_choices  = ['Kurang 30 minit', '30 – 60 minit', '1 – 2 jam', '2 – 4 jam', 'Lebih 4 jam']
    _masa_counts   = [qs.filter(k_perkhidmatan__masa_tunggu=m).count() for m in _masa_choices]
    masa_data      = [(l, c) for l, c in zip(_masa_choices, _masa_counts) if c > 0]
    masa_labels    = [d[0] for d in masa_data]
    masa_counts    = [d[1] for d in masa_data]
    # Pelawat harian breakdown
    _pelawat_opts   = [('< 50', 25), ('50–100', 75), ('100–200', 150), ('200–400', 300), ('400–800', 600), ('800–1,200', 1000), ('> 1,200', 1500)]
    _pelawat_counts = [qs.filter(k_perkhidmatan__anggaran_pelawat_harian=v).count() for _, v in _pelawat_opts]
    pelawat_data   = [(l, c) for (l, _), c in zip(_pelawat_opts, _pelawat_counts) if c > 0]
    pelawat_labels = [d[0] for d in pelawat_data]
    pelawat_counts = [d[1] for d in pelawat_data]
    # Perk boolean comparison chart
    perk_bool_labels = ['Ada EMR', 'Ada Hemodialisis', 'Bekalan Ubat OK', 'Boleh Selesaikan Kes', 'Ada Ruang Rehat', 'Ada OSCA', 'Wad Diasingkan']
    perk_bool_ya     = [perk_emr, perk_hemodial, perk_ubat, perk_selesai_kes, perk_ruang_rehat, perk_osca, perk_wad]
    perk_bool_tidak  = [max(0, perk_with_data - v) for v in perk_bool_ya]

    context = {
        'total': total,
        'aktif': aktif,
        'tutup': tutup,
        'pending': pending,
        'skor_purata': skor_purata,
        # filters
        'f_negeri': f_negeri,
        'f_jenis':  f_jenis,
        'f_status': f_status,
        'f_tahun':  f_tahun,
        'is_filtered': bool(f_negeri or f_jenis or f_status or f_tahun != str(_this_year)),
        'negeri_choices': MaklumatAsas.NEGERI_CHOICES,
        'jenis_choices':  MaklumatAsas.FACILITY_TYPE_CHOICES,
        'all_tahun_dashboard': all_tahun_dashboard,
        'current_year': _this_year,
        # chart data
        'jenis_labels': json.dumps(jenis_labels),
        'jenis_counts': json.dumps(jenis_counts),
        'issues_labels': json.dumps(issues_labels),
        'issues_ya': json.dumps(issues_ya),
        'issues_tidak': json.dumps(issues_tidak),
        'fasiliti_names': json.dumps(fasiliti_names),
        'fasiliti_scores': json.dumps(fasiliti_scores),
        'negeri_labels': json.dumps(negeri_labels),
        'negeri_counts': json.dumps(negeri_counts),
        'fasiliti_list': fp_list[:5],
        'is_jkn': is_jkn_user(request.user),
        'is_tm': is_top_management_user(request.user),
        # Perkhidmatan analytics
        'perk_with_data':   perk_with_data,
        'perk_emr':         perk_emr,
        'perk_hemodial':    perk_hemodial,
        'perk_ubat':        perk_ubat,
        'perk_selesai_kes': perk_selesai_kes,
        'perk_ruang_rehat': perk_ruang_rehat,
        'perk_osca':        perk_osca,
        'perk_wad':         perk_wad,
        'masa_labels':       json.dumps(masa_labels),
        'masa_counts':       json.dumps(masa_counts),
        'pelawat_labels':    json.dumps(pelawat_labels),
        'pelawat_counts':    json.dumps(pelawat_counts),
        'perk_bool_labels':  json.dumps(perk_bool_labels),
        'perk_bool_ya':      json.dumps(perk_bool_ya),
        'perk_bool_tidak':   json.dumps(perk_bool_tidak),
    }
    return render(request, 'home/dashboard_fasiliti.html', context)


def _build_clusters_new():
    """Cipta instance kosong untuk semua 8 kluster."""
    return {step: Model() for step, _, Model in CLUSTER_ATTR_MAP}


def _build_clusters_from_fp(fp):
    """Ambil atau cipta cluster objects dari FacilityProfile sedia ada."""
    clusters = {}
    for step, attr, Model in CLUSTER_ATTR_MAP:
        obj = getattr(fp, attr, None)
        clusters[step] = obj if obj is not None else Model()
    return clusters


def _save_clusters_to_fp(clusters, fp):
    """Save semua cluster objects dan link ke fp."""
    update_attrs = []
    for step, attr, _ in CLUSTER_ATTR_MAP:
        obj = clusters.get(step)
        if obj is None:
            continue
        obj.save()
        if getattr(fp, attr + '_id', None) is None:
            setattr(fp, attr, obj)
            update_attrs.append(attr)
    return update_attrs


def _save_facility_form(request, clusters, allowed_steps=None):
    post = request.POST
    files = request.FILES
    
    def in_scope(step): return (allowed_steps is None or step in allowed_steps) and step in clusters
    def yesno(key):
        v = post.get(key)
        return True if v == '1' else (False if v == '0' else None)
    def intval(key):
        try: return int(post.get(key, ''))
        except: return None

    # Bahagian 1: Latar Belakang
    if in_scope(0):
        ma = clusters[0]
        ma.nama_responden = post.get('nama_responden', '').strip()
        ma.jawatan_responden = post.get('jawatan_responden', '').strip()
        ma.no_telefon_responden = post.get('no_telefon_responden', '').strip()
        ma.emel_responden = post.get('emel_responden', '').strip()
        ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
        ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
        ma.negeri         = post.get('negeri', '')
        ma.daerah         = post.get('daerah', '').strip()
        ma.alamat         = post.get('alamat', '').strip()
        ma.poskod         = post.get('poskod', '').strip()
        try: ma.latitud  = float(post.get('latitud', ''))
        except ValueError: ma.latitud = None
        try: ma.longitud = float(post.get('longitud', ''))
        except ValueError: ma.longitud = None

    if in_scope(1):
        k1 = clusters[1]
        k1.tahun_dibina = intval('tahun_dibina')
        k1.ukuran_tanah = post.get('ukuran_tanah', '').strip()
        k1.tanah_mencukupi = yesno('tanah_mencukupi')
        k1.siling_okay = yesno('siling_okay')
        k1.siling_nota = post.get('siling_nota', '').strip()

    # Bahagian 4: Sumber Manusia
    if in_scope(2):
        k2 = clusters[2]
        k2.jumlah_perjawatan = intval('jumlah_perjawatan')
        k2.jumlah_pengisian  = intval('jumlah_pengisian')
        k2.jumlah_kekosongan = intval('jumlah_kekosongan')
        k2.ada_kakitangan_pinjaman = yesno('ada_kakitangan_pinjaman')
        k2.nota_kakitangan_pinjaman = post.get('nota_kakitangan_pinjaman', '').strip()
        k2.ada_isu_kakitangan = yesno('ada_isu_kakitangan')
        k2.ada_fasiliti_petugas = yesno('ada_fasiliti_petugas')
        k2.jenis_shift = post.get('jenis_shift', '').strip()
        k2.corak_penugasan = post.get('corak_penugasan', '').strip()
        k2.pengurusan_jadual = post.get('pengurusan_jadual', '').strip()
        k2.cara_minta_cuti = post.get('cara_minta_cuti', '').strip()
        k2.isu_penempatan = post.get('isu_penempatan', '').strip()
        k2.status_pertukaran_staf = post.get('status_pertukaran_staf', '').strip()
        k2.waktu_beroperasi = post.get('waktu_beroperasi', '').strip()

    # Bahagian 5: Perkhidmatan
    if in_scope(3):
        k3 = clusters[3]
        k3.anggaran_pelawat_harian = intval('anggaran_pelawat_harian')
        k3.jenis_perkhidmatan = post.get('jenis_perkhidmatan', '').strip()
        k3.jenis_penyakit_kerap = post.get('jenis_penyakit_kerap', '').strip()
        k3.wad_diasingkan = yesno('wad_diasingkan')
        k3.ruang_tunggu_selesa = yesno('ruang_tunggu_selesa')
        k3.ruang_tunggu_nota = post.get('ruang_tunggu_nota', '').strip()
        k3.boleh_selesaikan_kes = yesno('boleh_selesaikan_kes')
        k3.kekangan_rawatan = post.get('kekangan_rawatan', '').strip()
        k3.masa_tunggu = post.get('masa_tunggu', '').strip()
        k3.siapa_manage = post.get('siapa_manage', '').strip()
        k3.ada_ruang_rehat = yesno('ada_ruang_rehat')
        k3.ada_hemodialisis = yesno('ada_hemodialisis')
        k3.bekalan_ubat_mencukupi = yesno('bekalan_ubat_mencukupi')
        k3.kualiti_makanan = post.get('kualiti_makanan', '').strip()

    # Bahagian 3: Aset
    if in_scope(4):
        k4 = clusters[4]
        k4.senarai_peralatan = post.get('senarai_peralatan', '').strip()
        k4.aset_tidak_ikut_spec = post.get('aset_tidak_ikut_spec', '').strip()
        k4.disposable_mencukupi = yesno('disposable_mencukupi')
        k4.ada_ambulans = yesno('ada_ambulans')
        k4.ambulans_nota = post.get('ambulans_nota', '').strip()
        k4.sistem_pendigitalan = post.get('sistem_pendigitalan', '').strip()
        k4.gajet_ict_baik = yesno('gajet_ict_baik')
        k4.gajet_ict_nota = post.get('gajet_ict_nota', '').strip()
        k4.umur_komputer = post.get('umur_komputer', '').strip()

    # Bahagian 2: Fasiliti
    if in_scope(5):
        k5 = clusters[5]
        k5.keadaan_perabot = post.get('keadaan_perabot', '').strip()
        k5.ada_quarters = yesno('ada_quarters')
        k5.quarters_mencukupi = yesno('quarters_mencukupi')
        k5.ada_parking = yesno('ada_parking')
        k5.parking_mencukupi = yesno('parking_mencukupi')
        k5.masalah_aircond = yesno('masalah_aircond')
        k5.aircond_nota = post.get('aircond_nota', '').strip()
        k5.masalah_kipas = yesno('masalah_kipas')
        k5.kipas_nota = post.get('kipas_nota', '').strip()
        k5.ruang_kerja_mencukupi = yesno('ruang_kerja_mencukupi')
        k5.ada_pantry = yesno('ada_pantry')
        k5.ada_kantin = yesno('ada_kantin')
        k5.ada_security = yesno('ada_security')
        k5.ada_bilik_mayat = yesno('ada_bilik_mayat')

    # Bahagian 6: Perancangan
    if in_scope(6):
        k6 = clusters[6]
        k6.belanja_mengurus = post.get('belanja_mengurus', '').strip()
        k6.belanja_pembangunan = post.get('belanja_pembangunan', '').strip()
        k6.perkhidmatan_baru = post.get('perkhidmatan_baru', '').strip()
        k6.fasiliti_diperlukan = post.get('fasiliti_diperlukan', '').strip()

    # Bahagian 7: Konsesi & Lain-lain
    if in_scope(7):
        k7 = clusters[7]
        k7.maintenance_okay = yesno('maintenance_okay')
        k7.masalah_utama = post.get('masalah_utama', '').strip()
        k7.prosedur_kes_dadah = post.get('prosedur_kes_dadah', '').strip()
        k7.hemodialisis_nota = post.get('hemodialisis_nota', '').strip()
        k7.status_bekalan_oksigen = post.get('status_bekalan_oksigen', '').strip()
        k7.wishlist = post.get('wishlist_lama', '').strip()
        
        # Proses Muat Naik / Padam Fail Wishlist
        if post.get('delete_wishlist_fail') == '1':
            if k7.wishlist_fail:
                k7.wishlist_fail.delete(save=False)
                
        if 'wishlist_fail' in files:
            if k7.wishlist_fail:
                k7.wishlist_fail.delete(save=False)
            k7.wishlist_fail = files['wishlist_fail']


# ─────────────────────────────────────────────────────────────────
# FORM RINGKAS – Soalan terpilih Q1,2,8,13,14,19,22,23,24,25,26,27,29,29a,32,34,40,44,45
# ─────────────────────────────────────────────────────────────────
@login_required
def tambah_fasiliti_ringkas(request):
    """Borang ringkas: hanya soalan terpilih dari profiling KKM."""
    if is_top_management_user(request.user):
        from django.contrib import messages
        messages.error(request, 'Top Management hanya mempunyai akses baca sahaja.')
        return redirect('home:bahagian')
    if request.method == 'POST':
        return _save_fasiliti_ringkas(request, fp=None)
    return render(request, 'home/form_fasiliti_ringkas.html', {'mode': 'tambah'})


@login_required
def edit_fasiliti_ringkas(request, pk):
    """Edit borang ringkas untuk FacilityProfile sedia ada."""
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_fasiliti_ringkas(request, fp=fp)

    # Pre-populate context
    ctx = {'mode': 'edit', 'fp': fp}
    # Cluster 0
    if fp.maklumat_asas:
        ctx.update({
            'nama_fasiliti': fp.maklumat_asas.nama_fasiliti,
            'jenis_fasiliti': fp.maklumat_asas.jenis_fasiliti,
            'negeri': fp.maklumat_asas.negeri,
            'daerah': fp.maklumat_asas.daerah,
            'wilayah': fp.maklumat_asas.wilayah,
            'zon': fp.maklumat_asas.zon,
            'parlimen': fp.maklumat_asas.parlimen,
            'alamat': fp.maklumat_asas.alamat,
            'poskod': fp.maklumat_asas.poskod,
            'koordinat': '{}, {}'.format(fp.maklumat_asas.latitud, fp.maklumat_asas.longitud)
                         if fp.maklumat_asas.latitud is not None else '',
        })
    # Cluster 1
    if fp.k_kejuruteraan:
        ctx.update({
            'kod_fasiliti': fp.k_kejuruteraan.kod_fasiliti,
            'parlimen': fp.k_kejuruteraan.parlimen,
            'tahun_dibina': fp.k_kejuruteraan.tahun_dibina,
            'jenis_hospital_klinik': fp.k_kejuruteraan.jenis_hospital_klinik,
            'ukuran_tanah': fp.k_kejuruteraan.ukuran_tanah,
            'siling_okay': fp.k_kejuruteraan.siling_okay,
        })
    # Cluster 3
    if fp.k_perkhidmatan:
        ctx.update({
            'ada_ruang_rehat': fp.k_perkhidmatan.ada_ruang_rehat,
            'keperluan_oksigen': fp.k_perkhidmatan.keperluan_oksigen,
            'wad_diasingkan': fp.k_perkhidmatan.wad_diasingkan,
        })
    # Cluster 4
    if fp.k_aset:
        ctx.update({
            'aset_perlu_diganti': fp.k_aset.aset_perlu_diganti,
            'aset_tidak_ikut_spec': fp.k_aset.aset_tidak_ikut_spec,
        })
    # Cluster 5
    if fp.k_fasiliti:
        ctx.update({
            'keadaan_perabot': fp.k_fasiliti.keadaan_perabot,
            'ada_quarters': fp.k_fasiliti.ada_quarters,
            'quarters_mencukupi': fp.k_fasiliti.quarters_mencukupi,
            'ada_isu_parking': fp.k_fasiliti.ada_isu_parking,
            'masalah_aircond': fp.k_fasiliti.masalah_aircond,
            'ruang_kerja_mencukupi': fp.k_fasiliti.ruang_kerja_mencukupi,
            'ada_pantry': fp.k_fasiliti.ada_pantry,
            'ada_kantin': fp.k_fasiliti.ada_kantin,
            'ada_security': fp.k_fasiliti.ada_security,
        })
    # Cluster 6
    if fp.k_perancangan:
        ctx['fasiliti_diperlukan'] = fp.k_perancangan.fasiliti_diperlukan
    return render(request, 'home/form_fasiliti_ringkas.html', ctx)


def _save_fasiliti_ringkas(request, fp):
    """Internal: save borang ringkas POST data."""
    post = request.POST

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None

    def intval(key):
        try: return int(post.get(key, ''))
        except (ValueError, TypeError): return None

    # ── Cluster 0: Maklumat Asas ──
    if fp and fp.maklumat_asas:
        ma = fp.maklumat_asas
    else:
        ma = MaklumatAsas()
    ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
    ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
    ma.negeri         = post.get('negeri', '')
    ma.daerah         = post.get('daerah', '').strip()
    ma.wilayah        = post.get('wilayah', '')
    ma.zon            = post.get('zon', '').strip()
    ma.parlimen       = post.get('parlimen', '').strip()
    ma.alamat         = post.get('alamat', '').strip()
    ma.poskod         = post.get('poskod', '').strip()
    _koord = post.get('koordinat', '').strip()
    if _koord and ',' in _koord:
        _parts = _koord.split(',', 1)
        try: ma.latitud  = float(_parts[0].strip())
        except ValueError: pass
        try: ma.longitud = float(_parts[1].strip())
        except ValueError: pass
    elif not _koord:
        ma.latitud  = None
        ma.longitud = None
    if not ma.nama_fasiliti:
        messages.error(request, 'Nama fasiliti tidak boleh kosong.')
        return redirect(request.path)
    ma.save()

    # ── Cluster 1: Kejuruteraan ──
    k1 = (fp.k_kejuruteraan if fp and fp.k_kejuruteraan else None) or KlusterKejuruteraan()
    k1.kod_fasiliti          = post.get('kod_fasiliti', '').strip()
    k1.parlimen              = post.get('parlimen', '').strip()
    k1.tahun_dibina          = intval('tahun_dibina')
    k1.jenis_hospital_klinik = post.get('jenis_hospital_klinik', '').strip()
    k1.ukuran_tanah          = post.get('ukuran_tanah', '').strip()
    k1.siling_okay           = yesno('siling_okay')
    k1.save()

    # ── Cluster 3: Perkhidmatan ──
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.ada_ruang_rehat  = yesno('ada_ruang_rehat')
    k3.keperluan_oksigen = post.get('keperluan_oksigen', '').strip()
    k3.wad_diasingkan   = yesno('wad_diasingkan')
    k3.save()

    # ── Cluster 4: Aset ──
    k4 = (fp.k_aset if fp and fp.k_aset else None) or KlusterAset()
    k4.aset_perlu_diganti   = post.get('aset_perlu_diganti', '').strip()
    k4.aset_tidak_ikut_spec = post.get('aset_tidak_ikut_spec', '').strip()
    k4.save()

    # ── Cluster 5: Fasiliti ──
    k5 = (fp.k_fasiliti if fp and fp.k_fasiliti else None) or KlusterFasiliti()
    k5.keadaan_perabot       = post.get('keadaan_perabot', '').strip()
    k5.ada_quarters          = yesno('ada_quarters')
    k5.quarters_mencukupi    = yesno('quarters_mencukupi')
    k5.ada_isu_parking       = yesno('ada_isu_parking')
    k5.masalah_aircond       = yesno('masalah_aircond')
    k5.ruang_kerja_mencukupi = yesno('ruang_kerja_mencukupi')
    k5.ada_pantry            = yesno('ada_pantry')
    k5.ada_kantin            = yesno('ada_kantin')
    k5.ada_security          = yesno('ada_security')
    k5.save()

    # ── Cluster 6: Perancangan ──
    k6 = (fp.k_perancangan if fp and fp.k_perancangan else None) or KlusterPerancangan()
    k6.fasiliti_diperlukan = post.get('fasiliti_diperlukan', '').strip()
    k6.save()

    # ── Save / update FacilityProfile ──
    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.maklumat_asas    = ma
    fp.k_kejuruteraan   = k1
    fp.k_perkhidmatan   = k3
    fp.k_aset           = k4
    fp.k_fasiliti       = k5
    fp.k_perancangan    = k6
    fp.save()

    messages.success(request, f'Profil "{ma.nama_fasiliti}" berjaya disimpan.')
    return redirect('home:senarai_fasiliti')


# ══════════════════════════════════════════════════════════════════
# SUMBER MANUSIA (borang ringkas SM)
# ══════════════════════════════════════════════════════════════════

@login_required
def tambah_sumber_manusia(request):
    """Borang Sumber Manusia: soalan 3,16,21,36,37,38,39,42,47."""
    if request.method == 'POST':
        return _save_sumber_manusia(request, fp=None)
    return render(request, 'home/form_sumber_manusia.html', {'mode': 'tambah'})


@login_required
def edit_sumber_manusia(request, pk):
    """Edit borang Sumber Manusia untuk FacilityProfile sedia ada."""
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_sumber_manusia(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    if fp.maklumat_asas:
        ctx.update({
            'nama_fasiliti':  fp.maklumat_asas.nama_fasiliti,
            'jenis_fasiliti': fp.maklumat_asas.jenis_fasiliti,
            'negeri':         fp.maklumat_asas.negeri,
            'daerah':         fp.maklumat_asas.daerah,
        })
    if fp.k_sumber_manusia:
        sm = fp.k_sumber_manusia
        ctx.update({
            'kakitangan_tetap':           sm.kakitangan_tetap,
            'kakitangan_kontrak':         sm.kakitangan_kontrak,
            'kakitangan_mystep':          sm.kakitangan_mystep,
            'ada_kakitangan_pinjaman':    sm.ada_kakitangan_pinjaman,
            'bilangan_shift':             sm.bilangan_shift,
            'ada_ot_allowance':           sm.ada_ot_allowance,
            'cara_minta_cuti':            sm.cara_minta_cuti,
            'isu_penempatan':             sm.isu_penempatan,
            'bilangan_staff_non_medical': sm.bilangan_staff_non_medical,
        })
    if fp.k_perkhidmatan:
        ctx['siapa_manage'] = fp.k_perkhidmatan.siapa_manage
    return render(request, 'home/form_sumber_manusia.html', ctx)


def _save_sumber_manusia(request, fp):
    """Internal: save borang Sumber Manusia POST data."""
    post = request.POST

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None

    def intval(key):
        try: return int(post.get(key, ''))
        except (ValueError, TypeError): return None

    # ── Cluster 0: Maklumat Asas ──
    if fp and fp.maklumat_asas:
        ma = fp.maklumat_asas
    else:
        ma = MaklumatAsas()
    ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
    ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
    ma.negeri         = post.get('negeri', '')
    ma.daerah         = post.get('daerah', '').strip()
    if not ma.nama_fasiliti:
        messages.error(request, 'Nama fasiliti tidak boleh kosong.')
        return redirect(request.path)
    ma.save()

    # ── Cluster 2: Sumber Manusia ──
    sm = (fp.k_sumber_manusia if fp and fp.k_sumber_manusia else None) or KlusterSumberManusia()
    sm.kakitangan_tetap           = intval('kakitangan_tetap')
    sm.kakitangan_kontrak         = intval('kakitangan_kontrak')
    sm.kakitangan_mystep          = intval('kakitangan_mystep')
    sm.ada_kakitangan_pinjaman    = yesno('ada_kakitangan_pinjaman')
    sm.bilangan_shift             = intval('bilangan_shift')
    sm.ada_ot_allowance           = yesno('ada_ot_allowance')
    sm.cara_minta_cuti            = post.get('cara_minta_cuti', '').strip()
    sm.isu_penempatan             = post.get('isu_penempatan', '').strip()
    sm.bilangan_staff_non_medical = intval('bilangan_staff_non_medical')
    sm.save()

    # ── Cluster 3: Perkhidmatan (Q37 – siapa_manage) ──
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.siapa_manage = post.get('siapa_manage', '').strip()
    k3.save()

    # ── Save / update FacilityProfile ──
    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.maklumat_asas   = ma
    fp.k_sumber_manusia = sm
    fp.k_perkhidmatan  = k3
    fp.save()

    messages.success(request, f'Data Sumber Manusia "{ma.nama_fasiliti}" berjaya disimpan.')
    return redirect('home:senarai_fasiliti')


# ══════════════════════════════════════════════════════════════════
#  BORANG ASET  (KlusterAset – Q11, Q12, Q15, Q24, Q25, Q31)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_aset(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_aset(request, fp=fp)
    ctx = {'mode': 'edit', 'fp': fp}
    if fp.maklumat_asas:
        ctx.update({'nama_fasiliti': fp.maklumat_asas.nama_fasiliti,
                    'jenis_fasiliti': fp.maklumat_asas.jenis_fasiliti,
                    'negeri': fp.maklumat_asas.negeri,
                    'daerah': fp.maklumat_asas.daerah})
    if fp.k_aset:
        a = fp.k_aset
        ctx.update({'disposable_mencukupi': a.disposable_mencukupi,
                    'keadaan_aset': a.keadaan_aset,
                    'ada_ambulans': a.ada_ambulans,
                    'keadaan_ambulans': a.keadaan_ambulans,
                    'aset_perlu_diganti': a.aset_perlu_diganti,
                    'aset_tidak_ikut_spec': a.aset_tidak_ikut_spec,
                    'umur_komputer': a.umur_komputer})
    if fp.k_perkhidmatan:
        ctx.update({'ada_hemodialisis': fp.k_perkhidmatan.ada_hemodialisis,
                    'unit_hemodialisis': fp.k_perkhidmatan.unit_hemodialisis,
                    'ada_emr': fp.k_perkhidmatan.ada_emr})
    return render(request, 'home/form_aset.html', ctx)


def _save_aset(request, fp):
    post = request.POST
    def yesno(k):
        v = post.get(k)
        return True if v == '1' else (False if v == '0' else None)
    def intval(k):
        try: return int(post.get(k, ''))
        except: return None

    # Maklumat Asas
    ma = (fp.maklumat_asas if fp and fp.maklumat_asas else None) or MaklumatAsas()
    ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
    ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
    ma.negeri         = post.get('negeri', '')
    ma.daerah         = post.get('daerah', '').strip()
    if not ma.nama_fasiliti:
        messages.error(request, 'Nama fasiliti tidak boleh kosong.')
        return redirect(request.path)
    ma.save()

    # KlusterAset
    a = (fp.k_aset if fp and fp.k_aset else None) or KlusterAset()
    a.disposable_mencukupi = yesno('disposable_mencukupi')
    a.keadaan_aset         = post.get('keadaan_aset', '').strip()
    a.ada_ambulans         = yesno('ada_ambulans')
    a.keadaan_ambulans     = post.get('keadaan_ambulans', '').strip()
    a.aset_perlu_diganti   = post.get('aset_perlu_diganti', '').strip()
    a.aset_tidak_ikut_spec = post.get('aset_tidak_ikut_spec', '').strip()
    a.umur_komputer        = post.get('umur_komputer', '').strip()
    a.save()

    # KlusterPerkhidmatan (hemodialisis + EMR)
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.ada_hemodialisis  = yesno('ada_hemodialisis')
    k3.unit_hemodialisis = intval('unit_hemodialisis')
    k3.ada_emr           = yesno('ada_emr')
    k3.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.maklumat_asas = ma
    fp.k_aset        = a
    fp.k_perkhidmatan = k3
    fp.save()
    messages.success(request, f'Data Aset "{ma.nama_fasiliti}" berjaya disimpan.')
    return redirect('home:senarai_fasiliti')


# ══════════════════════════════════════════════════════════════════
#  BORANG SERVIS  (KlusterPerkhidmatan Servis – Q4,6,7,15,18,33,35,43,46)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_servis(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_servis(request, fp=fp)
    ctx = {'mode': 'edit', 'fp': fp, 'svc_choices': SVC_CHOICES, 'dis_choices': DIS_CHOICES}
    if fp.maklumat_asas:
        ctx.update({'nama_fasiliti': fp.maklumat_asas.nama_fasiliti,
                    'jenis_fasiliti': fp.maklumat_asas.jenis_fasiliti,
                    'negeri': fp.maklumat_asas.negeri,
                    'daerah': fp.maklumat_asas.daerah})
    if fp.k_perkhidmatan:
        p = fp.k_perkhidmatan
        ctx.update({'jenis_perkhidmatan': p.jenis_perkhidmatan,
                    'jenis_penyakit_kerap': p.jenis_penyakit_kerap,
                    'boleh_selesaikan_kes': p.boleh_selesaikan_kes,
                    'rujukan_ke': p.rujukan_ke,
                    'kualiti_makanan': p.kualiti_makanan,
                    'masa_tunggu': p.masa_tunggu})
    if fp.k_aset:
        ctx.update({'ada_ambulans': fp.k_aset.ada_ambulans,
                    'keadaan_ambulans': fp.k_aset.keadaan_ambulans})
    if fp.k_fasiliti:
        ctx['ada_bilik_mayat'] = fp.k_fasiliti.ada_bilik_mayat
    if fp.k_perancangan:
        ctx['perkhidmatan_baru'] = fp.k_perancangan.perkhidmatan_baru
    if fp.k_sumber_manusia:
        ctx['waktu_beroperasi'] = fp.k_sumber_manusia.waktu_beroperasi
    return render(request, 'home/form_servis.html', ctx)


def _save_servis(request, fp):
    post = request.POST
    def yesno(k):
        v = post.get(k)
        return True if v == '1' else (False if v == '0' else None)

    ma = (fp.maklumat_asas if fp and fp.maklumat_asas else None) or MaklumatAsas()
    ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
    ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
    ma.negeri         = post.get('negeri', '')
    ma.daerah         = post.get('daerah', '').strip()
    if not ma.nama_fasiliti:
        messages.error(request, 'Nama fasiliti tidak boleh kosong.')
        return redirect(request.path)
    ma.save()

    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.jenis_perkhidmatan   = post.get('jenis_perkhidmatan', '').strip()
    k3.jenis_penyakit_kerap = post.get('jenis_penyakit_kerap', '').strip()
    k3.boleh_selesaikan_kes = yesno('boleh_selesaikan_kes')
    k3.rujukan_ke           = post.get('rujukan_ke', '').strip()
    k3.kualiti_makanan      = post.get('kualiti_makanan', '').strip()
    k3.masa_tunggu          = post.get('masa_tunggu', '').strip()
    k3.save()

    a = (fp.k_aset if fp and fp.k_aset else None) or KlusterAset()
    a.ada_ambulans     = yesno('ada_ambulans')
    a.keadaan_ambulans = post.get('keadaan_ambulans', '').strip()
    a.save()

    kf = (fp.k_fasiliti if fp and fp.k_fasiliti else None) or KlusterFasiliti()
    kf.ada_bilik_mayat = yesno('ada_bilik_mayat')
    kf.save()

    kp = (fp.k_perancangan if fp and fp.k_perancangan else None) or KlusterPerancangan()
    kp.perkhidmatan_baru = post.get('perkhidmatan_baru', '').strip()
    kp.save()

    sm = (fp.k_sumber_manusia if fp and fp.k_sumber_manusia else None) or KlusterSumberManusia()
    sm.waktu_beroperasi = post.get('waktu_beroperasi', '').strip()
    sm.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.maklumat_asas  = ma
    fp.k_perkhidmatan = k3
    fp.k_aset         = a
    fp.k_fasiliti     = kf
    fp.k_perancangan  = kp
    fp.k_sumber_manusia = sm
    fp.save()
    messages.success(request, f'Data Servis "{ma.nama_fasiliti}" berjaya disimpan.')
    return redirect('home:senarai_fasiliti')


# ══════════════════════════════════════════════════════════════════
#  BORANG UBAT  (Q10, Q11, Q20)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_ubat(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_ubat(request, fp=fp)
    ctx = {'mode': 'edit', 'fp': fp}
    if fp.maklumat_asas:
        ctx.update({'nama_fasiliti': fp.maklumat_asas.nama_fasiliti,
                    'jenis_fasiliti': fp.maklumat_asas.jenis_fasiliti,
                    'negeri': fp.maklumat_asas.negeri,
                    'daerah': fp.maklumat_asas.daerah})
    if fp.k_perkhidmatan:
        ctx['bekalan_ubat_mencukupi'] = fp.k_perkhidmatan.bekalan_ubat_mencukupi
    if fp.k_aset:
        ctx['disposable_mencukupi'] = fp.k_aset.disposable_mencukupi
    return render(request, 'home/form_ubat.html', ctx)


def _save_ubat(request, fp):
    post = request.POST
    def yesno(k):
        v = post.get(k)
        return True if v == '1' else (False if v == '0' else None)

    ma = (fp.maklumat_asas if fp and fp.maklumat_asas else None) or MaklumatAsas()
    ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
    ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
    ma.negeri         = post.get('negeri', '')
    ma.daerah         = post.get('daerah', '').strip()
    if not ma.nama_fasiliti:
        messages.error(request, 'Nama fasiliti tidak boleh kosong.')
        return redirect(request.path)
    ma.save()

    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.bekalan_ubat_mencukupi = yesno('bekalan_ubat_mencukupi')
    k3.save()

    a = (fp.k_aset if fp and fp.k_aset else None) or KlusterAset()
    a.disposable_mencukupi = yesno('disposable_mencukupi')
    a.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.maklumat_asas  = ma
    fp.k_perkhidmatan = k3
    fp.k_aset         = a
    fp.save()
    messages.success(request, f'Data Ubat "{ma.nama_fasiliti}" berjaya disimpan.')
    return redirect('home:senarai_fasiliti')


# ══════════════════════════════════════════════════════════════════
#  BORANG PESAKIT  (Q48, Q48a)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_pesakit(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_pesakit(request, fp=fp)
    ctx = {'mode': 'edit', 'fp': fp}
    if fp.maklumat_asas:
        ctx.update({'nama_fasiliti': fp.maklumat_asas.nama_fasiliti,
                    'jenis_fasiliti': fp.maklumat_asas.jenis_fasiliti,
                    'negeri': fp.maklumat_asas.negeri,
                    'daerah': fp.maklumat_asas.daerah})
    if fp.k_perkhidmatan:
        ctx.update({'ada_osca': fp.k_perkhidmatan.ada_osca,
                    'bilangan_osca': fp.k_perkhidmatan.bilangan_osca})
    return render(request, 'home/form_pesakit.html', ctx)


def _save_pesakit(request, fp):
    post = request.POST
    def yesno(k):
        v = post.get(k)
        return True if v == '1' else (False if v == '0' else None)
    def intval(k):
        try: return int(post.get(k, ''))
        except: return None

    ma = (fp.maklumat_asas if fp and fp.maklumat_asas else None) or MaklumatAsas()
    ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
    ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
    ma.negeri         = post.get('negeri', '')
    ma.daerah         = post.get('daerah', '').strip()
    if not ma.nama_fasiliti:
        messages.error(request, 'Nama fasiliti tidak boleh kosong.')
        return redirect(request.path)
    ma.save()

    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.ada_osca      = yesno('ada_osca')
    k3.bilangan_osca = intval('bilangan_osca')
    k3.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.maklumat_asas  = ma
    fp.k_perkhidmatan = k3
    fp.save()
    messages.success(request, f'Data Pesakit "{ma.nama_fasiliti}" berjaya disimpan.')
    return redirect('home:senarai_fasiliti')

@login_required
@csrf_exempt
def kemaskini_status_lawatan(request, pk):
    """API khas untuk Admin menyimpan status lawatan dari pop-up peta"""
    if not is_admin(request.user):
        return JsonResponse({'status': 'error', 'message': 'Tiada kebenaran'}, status=403)
        
    if request.method == 'POST':
        fp = get_object_or_404(FacilityProfile, pk=pk)
        
        fp.status_lawatan = request.POST.get('status_lawatan', 'merah')
        fp.nama_program_lawatan = request.POST.get('nama_program', '').strip()
        fp.catatan_lawatan = request.POST.get('catatan', '').strip()
        
        tarikh_raw = request.POST.get('tarikh_lawatan', '').strip()
        fp.tarikh_lawatan = tarikh_raw if tarikh_raw else None
        
        fp.save(update_fields=['status_lawatan', 'nama_program_lawatan', 'tarikh_lawatan', 'catatan_lawatan'])
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# ══════════════════════════════════════════════════════════════════
# MODUL 1: LATAR BELAKANG (Google Forms)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_latar_belakang(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_latar_belakang(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    
    if fp.maklumat_asas:
        ctx.update({
            'nama_responden': fp.maklumat_asas.nama_responden,
            'jawatan_responden': fp.maklumat_asas.jawatan_responden,
            'no_telefon_responden': fp.maklumat_asas.no_telefon_responden,
            'emel_responden': fp.maklumat_asas.emel_responden,
            'nama_fasiliti': fp.maklumat_asas.nama_fasiliti,
            'jenis_fasiliti': fp.maklumat_asas.jenis_fasiliti,
        })
    if fp.k_kejuruteraan:
        ctx['tahun_dibina'] = fp.k_kejuruteraan.tahun_dibina
    if fp.k_perkhidmatan:
        ctx['siapa_manage'] = fp.k_perkhidmatan.siapa_manage

    return render(request, 'home/form_latar_belakang.html', ctx)

def _save_latar_belakang(request, fp):
    post = request.POST

    ma = (fp.maklumat_asas if fp and fp.maklumat_asas else None) or MaklumatAsas()
    ma.nama_responden = post.get('nama_responden', '').strip()
    ma.jawatan_responden = post.get('jawatan_responden', '').strip()
    ma.no_telefon_responden = post.get('no_telefon_responden', '').strip()
    ma.emel_responden = post.get('emel_responden', '').strip()
    
    ma.nama_fasiliti  = post.get('nama_fasiliti', '').strip()
    ma.jenis_fasiliti = post.get('jenis_fasiliti', '')
    
    # --- TAMBAHAN DATA LOKASI ---
    ma.negeri = post.get('negeri', '')
    ma.daerah = post.get('daerah', '').strip()
    ma.alamat = post.get('alamat', '').strip()
    ma.poskod = post.get('poskod', '').strip()
    
    _lat = post.get('latitud', '').strip()
    _lon = post.get('longitud', '').strip()
    try:
        ma.latitud = float(_lat) if _lat else None
    except ValueError:
        pass
    try:
        ma.longitud = float(_lon) if _lon else None
    except ValueError:
        pass
    # -----------------------------
    
    if not ma.nama_fasiliti:
        messages.error(request, 'Nama fasiliti tidak boleh kosong.')
        return redirect(request.path)
    ma.save()

    # Kluster 1 (Tahun Dibina)
    k1 = (fp.k_kejuruteraan if fp and fp.k_kejuruteraan else None) or KlusterKejuruteraan()
    try:
        k1.tahun_dibina = int(post.get('tahun_dibina', ''))
    except (ValueError, TypeError):
        pass
    k1.save()

    # Kluster 3 (Person in Charge / Ketua Fasiliti)
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.siapa_manage = post.get('siapa_manage', '').strip()
    k3.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.maklumat_asas = ma
    fp.k_kejuruteraan = k1
    fp.k_perkhidmatan = k3
    fp.save()
    
    messages.success(request, f'Bahagian Latar Belakang "{ma.nama_fasiliti}" berjaya dikemaskini.')
    return redirect('home:pilih_modul', pk=fp.pk)

# ══════════════════════════════════════════════════════════════════
# MODUL 2: INFRASTRUKTUR FASILITI (Google Forms)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_infrastruktur(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_infrastruktur(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    
    if fp.k_kejuruteraan:
        ctx.update({
            'siling_okay': fp.k_kejuruteraan.siling_okay,
            'siling_nota': fp.k_kejuruteraan.siling_nota,
            'ukuran_tanah': fp.k_kejuruteraan.ukuran_tanah,
            'tanah_mencukupi': fp.k_kejuruteraan.tanah_mencukupi,
        })
    if fp.k_fasiliti:
        ctx.update({
            'ruang_kerja_mencukupi': fp.k_fasiliti.ruang_kerja_mencukupi,
            'ada_pantry': fp.k_fasiliti.ada_pantry,
            'ada_kantin': fp.k_fasiliti.ada_kantin,
            'ada_parking': fp.k_fasiliti.ada_parking,
            'parking_mencukupi': fp.k_fasiliti.parking_mencukupi,
            'ada_quarters': fp.k_fasiliti.ada_quarters,
            'quarters_mencukupi': fp.k_fasiliti.quarters_mencukupi,
            'masalah_aircond': fp.k_fasiliti.masalah_aircond,
            'aircond_nota': fp.k_fasiliti.aircond_nota,
            'masalah_kipas': fp.k_fasiliti.masalah_kipas,
            'kipas_nota': fp.k_fasiliti.kipas_nota,
        })
    if fp.k_perkhidmatan:
        ctx.update({
            'ada_ruang_rehat': fp.k_perkhidmatan.ada_ruang_rehat,
        })

    return render(request, 'home/form_infrastruktur.html', ctx)

def _save_infrastruktur(request, fp):
    post = request.POST

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None

    # Kluster 1 (Kejuruteraan)
    k1 = (fp.k_kejuruteraan if fp and fp.k_kejuruteraan else None) or KlusterKejuruteraan()
    k1.siling_okay = yesno('siling_okay')
    k1.siling_nota = post.get('siling_nota', '').strip()
    k1.ukuran_tanah = post.get('ukuran_tanah', '').strip()
    k1.tanah_mencukupi = yesno('tanah_mencukupi')
    k1.save()

    # Kluster 5 (Fasiliti)
    k5 = (fp.k_fasiliti if fp and fp.k_fasiliti else None) or KlusterFasiliti()
    k5.ruang_kerja_mencukupi = yesno('ruang_kerja_mencukupi')
    k5.ada_pantry = yesno('ada_pantry')
    k5.ada_kantin = yesno('ada_kantin')
    k5.ada_parking = yesno('ada_parking')
    k5.parking_mencukupi = yesno('parking_mencukupi')
    k5.ada_quarters = yesno('ada_quarters')
    k5.quarters_mencukupi = yesno('quarters_mencukupi')
    k5.masalah_aircond = yesno('masalah_aircond')
    k5.aircond_nota = post.get('aircond_nota', '').strip()
    k5.masalah_kipas = yesno('masalah_kipas')
    k5.kipas_nota = post.get('kipas_nota', '').strip()
    k5.save()

    # Kluster 3 (Perkhidmatan - untuk ruang rehat pelawat)
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.ada_ruang_rehat = yesno('ada_ruang_rehat')
    k3.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.k_kejuruteraan = k1
    fp.k_fasiliti = k5
    fp.k_perkhidmatan = k3
    fp.save()
    
    messages.success(request, f'Bahagian Infrastruktur Fasiliti berjaya dikemaskini.')
    return redirect('home:pilih_modul', pk=fp.pk)

# ══════════════════════════════════════════════════════════════════
# MODUL 3: ASET PERUBATAN (Google Forms)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_aset_perubatan(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_aset_perubatan(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    
    # Data dari Kluster Aset
    if fp.k_aset:
        ctx.update({
            'senarai_peralatan': fp.k_aset.senarai_peralatan,
            'aset_tidak_ikut_spec': fp.k_aset.aset_tidak_ikut_spec,
            'disposable_mencukupi': fp.k_aset.disposable_mencukupi,
            'ada_ambulans': fp.k_aset.ada_ambulans,
            'ambulans_nota': fp.k_aset.ambulans_nota,
            'sistem_pendigitalan': fp.k_aset.sistem_pendigitalan,
            'gajet_ict_baik': fp.k_aset.gajet_ict_baik,
            'gajet_ict_nota': fp.k_aset.gajet_ict_nota,
        })
    
    # Data dari Kluster Perkhidmatan (Ubat & Hemodialisis)
    if fp.k_perkhidmatan:
        ctx.update({
            'bekalan_ubat_mencukupi': fp.k_perkhidmatan.bekalan_ubat_mencukupi,
            'ada_hemodialisis': fp.k_perkhidmatan.ada_hemodialisis,
        })
        
    # Data dari Kluster Fasiliti (Perabot & Security)
    if fp.k_fasiliti:
        ctx.update({
            'keadaan_perabot': fp.k_fasiliti.keadaan_perabot,
            'ada_security': fp.k_fasiliti.ada_security,
        })

    # Pilihan sistem pendigitalan untuk template
    ctx['digital_choices'] = ['EMR', 'CMS', 'HIS', 'LIS', 'HRMIS', 'PhIS', 'MyVAS', 'Tidak berkenaan']

    return render(request, 'home/form_aset_perubatan.html', ctx)

def _save_aset_perubatan(request, fp):
    post = request.POST

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None

    # Simpan Kluster Aset
    a = (fp.k_aset if fp and fp.k_aset else None) or KlusterAset()
    a.senarai_peralatan = post.get('senarai_peralatan', '').strip()
    a.aset_tidak_ikut_spec = post.get('aset_tidak_ikut_spec', '').strip()
    a.disposable_mencukupi = yesno('disposable_mencukupi')
    a.ada_ambulans = yesno('ada_ambulans')
    a.ambulans_nota = post.get('ambulans_nota', '').strip()
    a.sistem_pendigitalan = post.get('sistem_pendigitalan', '').strip()
    a.gajet_ict_baik = yesno('gajet_ict_baik')
    a.gajet_ict_nota = post.get('gajet_ict_nota', '').strip()
    a.save()

    # Simpan Kluster Fasiliti (Perabot & Security)
    kf = (fp.k_fasiliti if fp and fp.k_fasiliti else None) or KlusterFasiliti()
    kf.keadaan_perabot = post.get('keadaan_perabot', '').strip()
    kf.ada_security = yesno('ada_security')
    kf.save()

    # Simpan Kluster Perkhidmatan (Ubat & Hemodialisis)
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.bekalan_ubat_mencukupi = yesno('bekalan_ubat_mencukupi')
    k3.ada_hemodialisis = yesno('ada_hemodialisis')
    k3.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.k_aset = a
    fp.k_fasiliti = kf
    fp.k_perkhidmatan = k3
    fp.save()
    
    messages.success(request, 'Bahagian Aset Perubatan berjaya dikemaskini.')
    return redirect('home:pilih_modul', pk=fp.pk)

# ══════════════════════════════════════════════════════════════════
# MODUL 4: PENGURUSAN SUMBER MANUSIA (Google Forms)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_pengurusan_sumber_manusia(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_pengurusan_sumber_manusia(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    
    if fp.k_sumber_manusia:
        k2 = fp.k_sumber_manusia
        ctx.update({
            'jumlah_perjawatan': k2.jumlah_perjawatan,
            'jumlah_pengisian': k2.jumlah_pengisian,
            'jumlah_kekosongan': k2.jumlah_kekosongan,
            'ada_kakitangan_pinjaman': k2.ada_kakitangan_pinjaman,
            'nota_kakitangan_pinjaman': k2.nota_kakitangan_pinjaman,
            'ada_isu_kakitangan': k2.ada_isu_kakitangan,
            'ada_fasiliti_petugas': k2.ada_fasiliti_petugas,
            
            # Text list untuk checkboxes
            'jenis_shift': k2.jenis_shift,
            'corak_penugasan': k2.corak_penugasan,
            'pengurusan_jadual': k2.pengurusan_jadual,
            'cara_minta_cuti': k2.cara_minta_cuti,
            'isu_penempatan': k2.isu_penempatan,
            'status_pertukaran_staf': k2.status_pertukaran_staf,
        })

    # Data Checkboxes
    ctx['opt_shift'] = [
        '1 Shift (Waktu Pejabat: 8 pagi - 5 petang)', '2 Shift (Pagi & Petang)', 
        '3 Shift (Pagi, Petang & Malam / Operasi 24 jam)', 'Sistem Panggilan Tugas (On Call / Standby)', 'Tidak Berkenaan'
    ]
    ctx['opt_corak'] = [
        'Mengikut standard / Norma ditetapkan (Kapasiti / Tenaga kerja mencukupi)',
        'Kekurangan staf tinggi / Penugasan double shift kerap diamalkan akibat kekurangan staf',
        'Tugas on-call / kerja lebih masa (OT) kerap diamalkan sehingga ada staf burnout',
        'Kerja lebih masa (OT) jarang diamalkan', 'Tidak Berkenaan'
    ]
    ctx['opt_roster'] = [
        'Disediakan oleh Ketua Unit / Penyelia secara manual (Borang / Microsoft Excel/Word)',
        'Sistem Penjadualan Digital / Automasi',
        'Dibuat secara tetap - tiada rotasi / pertukaran tempoh',
        'Sistem dalam Percubaan / Skim Syif yang fleksibel antara rakan sekerja (bergilir atas persetujuan)',
        'Tidak Berkenaan'
    ]
    ctx['opt_cuti'] = [
        'Sistem Dalam Talian (HRMIS / Sistem Pengurusan Cuti Dalaman)',
        'Manual / Borang / Kertas (Borang Cuti Fizikal Sokongan / Lulus & Disimpan)',
        'Hybrid (Borang secara fizikal, tetapi data direkod juga di pangkalan data secara manual)'
    ]
    ctx['opt_isu'] = [
        'Kekurangan Staf Utama Menyebabkan Penugasan Syif Yang Tidak Seimbang / Beban Kerja Berlebihan',
        'Pertindihan Jadual Waktu Bekerja / Kekurangan Pengganti Cuti',
        'Jadual Syif Kerap Ditukar (Perubahan Minit Akhir / Kurang Notice)',
        'Kesukaran Memantau Penugasan/Cuti (Sistem Manual Tiada Ciri Integrasi Automatik)',
        'Tiada Sokongan ICT / Penggunaan Perisian Jadual Yang Ketinggalan Zaman/Teruk',
        'Tidak Berkenaan'
    ]

    return render(request, 'home/form_pengurusan_sumber_manusia.html', ctx)

def _save_pengurusan_sumber_manusia(request, fp):
    post = request.POST

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None
        
    def intval(key):
        try: return int(post.get(key, ''))
        except (ValueError, TypeError): return None

    k2 = (fp.k_sumber_manusia if fp and fp.k_sumber_manusia else None) or KlusterSumberManusia()
    
    k2.jumlah_perjawatan = intval('jumlah_perjawatan')
    k2.jumlah_pengisian  = intval('jumlah_pengisian')
    k2.jumlah_kekosongan = intval('jumlah_kekosongan')
    k2.ada_kakitangan_pinjaman = yesno('ada_kakitangan_pinjaman')
    k2.nota_kakitangan_pinjaman = post.get('nota_kakitangan_pinjaman', '').strip()
    
    k2.ada_isu_kakitangan = yesno('ada_isu_kakitangan')
    k2.ada_fasiliti_petugas = yesno('ada_fasiliti_petugas')
    
    k2.jenis_shift = post.get('jenis_shift', '').strip()
    k2.corak_penugasan = post.get('corak_penugasan', '').strip()
    k2.pengurusan_jadual = post.get('pengurusan_jadual', '').strip()
    k2.cara_minta_cuti = post.get('cara_minta_cuti', '').strip()
    k2.isu_penempatan = post.get('isu_penempatan', '').strip()
    k2.status_pertukaran_staf = post.get('status_pertukaran_staf', '').strip()

    k2.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.k_sumber_manusia = k2
    fp.save()
    
    messages.success(request, 'Bahagian Pengurusan Sumber Manusia berjaya dikemaskini.')
    return redirect('home:pilih_modul', pk=fp.pk)

# ══════════════════════════════════════════════════════════════════
# MODUL 5: PENYAMPAIAN PERKHIDMATAN (Google Forms)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_penyampaian_perkhidmatan(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_penyampaian_perkhidmatan(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    
    # K2: Waktu Operasi (disimpan dalam Sumber Manusia pada asalnya)
    if fp.k_sumber_manusia:
        ctx['waktu_beroperasi'] = fp.k_sumber_manusia.waktu_beroperasi

    # K3: Data Perkhidmatan Kesihatan
    if fp.k_perkhidmatan:
        k3 = fp.k_perkhidmatan
        ctx.update({
            'anggaran_pelawat_harian': k3.anggaran_pelawat_harian,
            'jenis_perkhidmatan': k3.jenis_perkhidmatan,
            'jenis_penyakit_kerap': k3.jenis_penyakit_kerap,
            'wad_diasingkan': k3.wad_diasingkan,
            'ruang_tunggu_selesa': k3.ruang_tunggu_selesa,
            'ruang_tunggu_nota': k3.ruang_tunggu_nota,
            'boleh_selesaikan_kes': k3.boleh_selesaikan_kes,
            'kekangan_rawatan': k3.kekangan_rawatan,
            'masa_tunggu': k3.masa_tunggu,
        })

    return render(request, 'home/form_penyampaian_perkhidmatan.html', ctx)

def _save_penyampaian_perkhidmatan(request, fp):
    post = request.POST

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None

    def intval(key):
        try: return int(post.get(key, ''))
        except (ValueError, TypeError): return None

    # Simpan Waktu Operasi ke Kluster 2
    k2 = (fp.k_sumber_manusia if fp and fp.k_sumber_manusia else None) or KlusterSumberManusia()
    k2.waktu_beroperasi = post.get('waktu_beroperasi', '').strip()
    k2.save()

    # Simpan Kluster 3
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.anggaran_pelawat_harian = intval('anggaran_pelawat_harian')
    k3.jenis_perkhidmatan = post.get('jenis_perkhidmatan', '').strip()
    k3.jenis_penyakit_kerap = post.get('jenis_penyakit_kerap', '').strip()
    k3.wad_diasingkan = yesno('wad_diasingkan')
    k3.ruang_tunggu_selesa = yesno('ruang_tunggu_selesa')
    k3.ruang_tunggu_nota = post.get('ruang_tunggu_nota', '').strip()
    k3.boleh_selesaikan_kes = yesno('boleh_selesaikan_kes')
    k3.kekangan_rawatan = post.get('kekangan_rawatan', '').strip()
    k3.masa_tunggu = post.get('masa_tunggu', '').strip()
    k3.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.k_sumber_manusia = k2
    fp.k_perkhidmatan = k3
    fp.save()
    
    messages.success(request, 'Bahagian Penyampaian Perkhidmatan berjaya dikemaskini.')
    return redirect('home:pilih_modul', pk=fp.pk)

# ══════════════════════════════════════════════════════════════════
# MODUL 6: KEWANGAN, KONSESI & PERANCANGAN (Google Forms)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_kewangan_perancangan(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_kewangan_perancangan(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    
    # K6: Kewangan & Perancangan Masa Depan
    if fp.k_perancangan:
        ctx.update({
            'belanja_mengurus': fp.k_perancangan.belanja_mengurus,
            'belanja_pembangunan': fp.k_perancangan.belanja_pembangunan,
            'fasiliti_diperlukan': fp.k_perancangan.fasiliti_diperlukan,
        })

    # K7: Konsesi & Isu Utama
    if fp.k_konsesi:
        ctx.update({
            'maintenance_okay': fp.k_konsesi.maintenance_okay,
            'masalah_utama': fp.k_konsesi.masalah_utama,
        })

    return render(request, 'home/form_kewangan_perancangan.html', ctx)

def _save_kewangan_perancangan(request, fp):
    post = request.POST

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None

    # Simpan Kewangan & Perancangan (K6)
    k6 = (fp.k_perancangan if fp and fp.k_perancangan else None) or KlusterPerancangan()
    k6.belanja_mengurus = post.get('belanja_mengurus', '').strip()
    k6.belanja_pembangunan = post.get('belanja_pembangunan', '').strip()
    k6.fasiliti_diperlukan = post.get('fasiliti_diperlukan', '').strip()
    k6.save()

    # Simpan Konsesi & Isu Utama (K7)
    k7 = (fp.k_konsesi if fp and fp.k_konsesi else None) or KlusterKonsesi()
    k7.maintenance_okay = yesno('maintenance_okay')
    k7.masalah_utama = post.get('masalah_utama', '').strip()
    k7.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.k_perancangan = k6
    fp.k_konsesi = k7
    fp.save()
    
    messages.success(request, 'Bahagian Kewangan & Perancangan berjaya dikemaskini.')
    return redirect('home:pilih_modul', pk=fp.pk)

# ══════════════════════════════════════════════════════════════════
# MODUL 7: LAIN-LAIN (Google Forms)
# ══════════════════════════════════════════════════════════════════

@login_required
def edit_lain_lain(request, pk):
    fp = get_object_or_404(FacilityProfile, pk=pk)
    if request.method == 'POST':
        return _save_lain_lain(request, fp=fp)

    ctx = {'mode': 'edit', 'fp': fp}
    
    # K7: Konsesi (Google Form)
    if fp.k_konsesi:
        k7 = fp.k_konsesi
        ctx.update({
            'prosedur_kes_dadah': k7.prosedur_kes_dadah,
            'hemodialisis_nota': k7.hemodialisis_nota,
            'status_bekalan_oksigen': k7.status_bekalan_oksigen,
            'wishlist_fail': k7.wishlist_fail,
            'wishlist_lama': k7.wishlist,  # Teks lama wishlist
        })
        
    # --- Data Arkib (Maklumat Tambahan Lama) ---
    if fp.k_fasiliti:
        ctx['ada_bilik_mayat'] = fp.k_fasiliti.ada_bilik_mayat
    if fp.k_perkhidmatan:
        ctx['kualiti_makanan'] = fp.k_perkhidmatan.kualiti_makanan
    if fp.k_aset:
        ctx['umur_komputer'] = fp.k_aset.umur_komputer

    return render(request, 'home/form_lain_lain.html', ctx)

def _save_lain_lain(request, fp):
    post = request.POST
    files = request.FILES

    def yesno(key):
        val = post.get(key)
        if val == '1': return True
        if val == '0': return False
        return None

    # Simpan Google Form (K7)
    k7 = (fp.k_konsesi if fp and fp.k_konsesi else None) or KlusterKonsesi()
    k7.prosedur_kes_dadah = post.get('prosedur_kes_dadah', '').strip()
    k7.hemodialisis_nota = post.get('hemodialisis_nota', '').strip()
    k7.status_bekalan_oksigen = post.get('status_bekalan_oksigen', '').strip()
    k7.wishlist = post.get('wishlist_lama', '').strip()
    
    # 1. Proses Buang Fail (Jika pengguna menekan butang Padam Fail Semasa)
    if post.get('delete_wishlist_fail') == '1':
        if k7.wishlist_fail:
            k7.wishlist_fail.delete(save=False)  # Padam fail dari server
            
    # 2. Proses Muat Naik Fail Baru
    if 'wishlist_fail' in files:
        if k7.wishlist_fail:
            k7.wishlist_fail.delete(save=False)  # Buang fail lama jika di-override
        k7.wishlist_fail = files['wishlist_fail']
        
    k7.save()

    # Simpan Data Arkib
    k5 = (fp.k_fasiliti if fp and fp.k_fasiliti else None) or KlusterFasiliti()
    k5.ada_bilik_mayat = yesno('ada_bilik_mayat')
    k5.save()
    
    k3 = (fp.k_perkhidmatan if fp and fp.k_perkhidmatan else None) or KlusterPerkhidmatan()
    k3.kualiti_makanan = post.get('kualiti_makanan', '').strip()
    k3.save()
    
    k4 = (fp.k_aset if fp and fp.k_aset else None) or KlusterAset()
    k4.umur_komputer = post.get('umur_komputer', '').strip()
    k4.save()

    if fp is None:
        fp = FacilityProfile(submitted_by=request.user, status='draf')
    fp.k_konsesi = k7
    fp.k_fasiliti = k5
    fp.k_perkhidmatan = k3
    fp.k_aset = k4
    fp.save()
    
    messages.success(request, 'Bahagian Lain-lain dan Lampiran berjaya dikemaskini.')
    return redirect('home:pilih_modul', pk=fp.pk)