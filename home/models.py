import datetime
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


def _current_year():
    return datetime.date.today().year


# ─────────────────────────────────────────────────────────────────
# KLUSTER 0 – Maklumat Asas  (table: home_maklumatAsas)
# ─────────────────────────────────────────────────────────────────
class MaklumatAsas(models.Model):
    FACILITY_TYPE_CHOICES = [
        ('hospital',                  'Hospital'),
        ('hospital_pakar',            'Hospital Pakar'),
        ('klinik_kesihatan',          'Klinik Kesihatan'),
        ('klinik_desa',              'Klinik Desa'),
        ('klinik_komuniti',          'Klinik Komuniti'),
        ('institusi_perubatan_khas',  'Institusi Perubatan Khas'),
        ('institusi_latihan',         'Institusi Latihan'),
        ('jabatan_kes_negeri',        'Jabatan Kesihatan Negeri'),
        ('klinik_pergigian_hosp',     'Klinik Pergigian di Hospital'),
        ('kk_ibu_anak',              'Klinik Kesihatan Ibu dan Anak'),
        ('klinik_pergigian_utc',      'Klinik Pergigian UTC'),
        ('klinik_pergigian_sekolah',  'Klinik Pergigian di Sekolah'),
        ('kp_kk_utc',                'Klinik Pergigian di Klinik Kesihatan UTC'),
        ('kp_kk_ibu_anak',           'Klinik Pergigian di Klinik Kesihatan Ibu dan Anak'),
        ('klinik_pergigian_rtc',      'Klinik Pergigian RTC'),
        ('klinik_kesihatan_utc',      'Klinik Kesihatan UTC'),
        ('klinik_pergigian',          'Klinik Pergigian'),
        ('pkp_bahagian',             'Pejabat Kesihatan Pergigian Bahagian'),
        ('pkp',                      'Pejabat Kesihatan Pergigian'),
        ('pkp_daerah',               'Pejabat Kesihatan Pergigian Daerah'),
        ('pkp_kawasan',              'Pejabat Kesihatan Pergigian Kawasan'),
        ('lain',                     'Lain-lain'),
    ]
    NEGERI_CHOICES = [
        ('johor', 'Johor'), ('kedah', 'Kedah'), ('kelantan', 'Kelantan'),
        ('melaka', 'Melaka'), ('negeri_sembilan', 'Negeri Sembilan'),
        ('pahang', 'Pahang'), ('perak', 'Perak'), ('perlis', 'Perlis'),
        ('pulau_pinang', 'Pulau Pinang'), ('sabah', 'Sabah'),
        ('sarawak', 'Sarawak'), ('selangor', 'Selangor'),
        ('terengganu', 'Terengganu'), ('wp_kl', 'W.P. Kuala Lumpur'),
        ('wp_putrajaya', 'W.P. Putrajaya'), ('wp_labuan', 'W.P. Labuan'),
    ]
    WILAYAH_CHOICES = [
        ('utara',   'Utara (Perlis, Kedah, P.Pinang, Perak)'),
        ('tengah',  'Tengah (Selangor, KL, Putrajaya, N.Sembilan, Melaka)'),
        ('selatan', 'Selatan (Johor)'),
        ('timur',   'Timur (Pahang, Kelantan, Terengganu)'),
        ('sabah',   'Sabah'),
        ('sarawak', 'Sarawak'),
        ('labuan',  'W.P. Labuan'),
    ]
    
    # --- MAKLUMAT RESPONDEN (Baru) ---
    nama_responden       = models.CharField(max_length=200, blank=True, verbose_name="Nama Penuh Responden")
    jawatan_responden    = models.CharField(max_length=150, blank=True, verbose_name="Jawatan Responden")
    no_telefon_responden = models.CharField(max_length=20, blank=True, verbose_name="No. Telefon Responden")
    emel_responden       = models.EmailField(blank=True, verbose_name="Emel Responden")

    # --- MAKLUMAT FASILITI (Sedia Ada) ---
    nama_fasiliti  = models.CharField(max_length=200, verbose_name="Nama Fasiliti")
    jenis_fasiliti = models.CharField(max_length=30, choices=FACILITY_TYPE_CHOICES, verbose_name="Jenis Fasiliti")
    negeri         = models.CharField(max_length=30, choices=NEGERI_CHOICES, blank=True, verbose_name="Negeri")
    daerah         = models.CharField(max_length=100, blank=True, verbose_name="Daerah/Bandar")
    wilayah        = models.CharField(max_length=20, choices=WILAYAH_CHOICES, blank=True, verbose_name="Wilayah")
    zon            = models.CharField(max_length=100, blank=True, verbose_name="Zon")
    parlimen       = models.CharField(max_length=150, blank=True, verbose_name="Parlimen")
    alamat         = models.TextField(blank=True, verbose_name="Alamat")
    poskod         = models.CharField(max_length=10, blank=True, verbose_name="Poskod")
    latitud        = models.FloatField(null=True, blank=True, verbose_name="Latitud")
    longitud       = models.FloatField(null=True, blank=True, verbose_name="Longitud")
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nama_fasiliti} ({self.get_jenis_fasiliti_display()})"

    class Meta:
        verbose_name = "K0 – Maklumat Asas"
        verbose_name_plural = "K0 – Maklumat Asas"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 1 – Kejuruteraan  (table: home_klusterkejuruteraan)
# ─────────────────────────────────────────────────────────────────
class KlusterKejuruteraan(models.Model):
    kod_fasiliti          = models.CharField(max_length=50, blank=True, verbose_name="Kod Fasiliti")
    parlimen              = models.CharField(max_length=150, blank=True, verbose_name="Parlimen")
    tahun_dibina          = models.IntegerField(null=True, blank=True, verbose_name="Q1 – Tahun Dibina")
    jenis_hospital_klinik = models.CharField(max_length=200, blank=True, verbose_name="Q2 – Jenis Hospital/Klinik")
    siling_okay           = models.BooleanField(null=True, blank=True, verbose_name="Q32 – Siling Okay?")
    ukuran_tanah          = models.TextField(blank=True, verbose_name="Q29 – Ukuran Tanah & Boleh Extend?")
    
    # --- MEDAN BARU (FASA 2) ---
    siling_nota           = models.CharField(max_length=255, blank=True, verbose_name="Nota Siling")
    tanah_mencukupi       = models.BooleanField(null=True, blank=True, verbose_name="Tanah Mencukupi?")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "K1 – Kejuruteraan"
        verbose_name_plural = "K1 – Kejuruteraan"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 2 – Sumber Manusia  (table: home_klustersumbermanusia)
# ─────────────────────────────────────────────────────────────────
class KlusterSumberManusia(models.Model):
    kakitangan_tetap           = models.IntegerField(null=True, blank=True, verbose_name="Q3 – Kakitangan Tetap")
    kakitangan_kontrak         = models.IntegerField(null=True, blank=True, verbose_name="Q3 – Kakitangan Kontrak")
    kakitangan_mystep          = models.IntegerField(null=True, blank=True, verbose_name="Q3 – Kakitangan MySTeP")
    ada_kakitangan_pinjaman    = models.BooleanField(null=True, blank=True, verbose_name="Q16 – Ada Staff Pinjaman?")
    bilangan_shift             = models.IntegerField(null=True, blank=True, verbose_name="Q21/Q39 – Bilangan Shift Sehari")
    ada_ot_allowance           = models.BooleanField(null=True, blank=True, verbose_name="Q38 – Ada OT/Allowance?")
    bilangan_staff_non_medical = models.IntegerField(null=True, blank=True, verbose_name="Q47 – Bil. Staff Non-Medical/Admin")
    waktu_beroperasi           = models.CharField(max_length=200, blank=True, verbose_name="Q43 – Waktu Beroperasi")
    cara_minta_cuti            = models.TextField(blank=True, verbose_name="Q42 – Cara Minta Cuti & Rotasi")
    isu_penempatan             = models.TextField(blank=True, verbose_name="Q36 – Isu Penempatan Staff")
    
    # --- MEDAN BARU (FASA 4) ---
    jumlah_perjawatan          = models.IntegerField(null=True, blank=True, verbose_name="Jumlah Perjawatan")
    jumlah_pengisian           = models.IntegerField(null=True, blank=True, verbose_name="Jumlah Pengisian")
    jumlah_kekosongan          = models.IntegerField(null=True, blank=True, verbose_name="Jumlah Kekosongan")
    nota_kakitangan_pinjaman   = models.CharField(max_length=255, blank=True, verbose_name="Nota Pinjaman Staf")
    
    ada_isu_kakitangan         = models.BooleanField(null=True, blank=True, verbose_name="Ada Isu/Krisis Kakitangan?")
    ada_fasiliti_petugas       = models.BooleanField(null=True, blank=True, verbose_name="Ada Fasiliti/Layanan Petugas?")
    
    jenis_shift                = models.TextField(blank=True, verbose_name="Bilangan Shift (Teks)")
    corak_penugasan            = models.TextField(blank=True, verbose_name="Corak Penugasan")
    pengurusan_jadual          = models.TextField(blank=True, verbose_name="Pengurusan Jadual (Roster)")
    status_pertukaran_staf     = models.CharField(max_length=255, blank=True, verbose_name="Status Pertukaran Staf")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "K2 – Sumber Manusia"
        verbose_name_plural = "K2 – Sumber Manusia"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 3 – Perkhidmatan Kesihatan  (table: home_klusterperkhidmatan)
# ─────────────────────────────────────────────────────────────────
class KlusterPerkhidmatan(models.Model):
    jenis_perkhidmatan      = models.TextField(blank=True, verbose_name="Q4 – Jenis Perkhidmatan")
    anggaran_pelawat_harian = models.IntegerField(null=True, blank=True, verbose_name="Q5 – Anggaran Pelawat Harian")
    jenis_penyakit_kerap    = models.TextField(blank=True, verbose_name="Q6 – Jenis Penyakit Kerap")
    boleh_selesaikan_kes    = models.BooleanField(null=True, blank=True, verbose_name="Q7 – Boleh Selesaikan Kes?")
    rujukan_ke              = models.CharField(max_length=200, blank=True, verbose_name="Q7 – Jika Tidak, Rujuk ke Mana?")
    ada_ruang_rehat         = models.BooleanField(null=True, blank=True, verbose_name="Q8 – Ada Ruang Rehat Pelawat?")
    ada_hemodialisis        = models.BooleanField(null=True, blank=True, verbose_name="Q9 – Ada Hemodialisis?")
    unit_hemodialisis       = models.IntegerField(null=True, blank=True, verbose_name="Q9 – Bilangan Unit Hemodialisis")
    bekalan_ubat_mencukupi  = models.BooleanField(null=True, blank=True, verbose_name="Q10/Q20 – Bekalan Ubat Mencukupi?")
    keperluan_oksigen       = models.TextField(blank=True, verbose_name="Q27 – Keperluan Oksigen")
    ada_emr                 = models.BooleanField(null=True, blank=True, verbose_name="Q30 – Ada EMR?")
    wad_diasingkan          = models.BooleanField(null=True, blank=True, verbose_name="Q34 – Wad Diasingkan (L/P)?")
    kualiti_makanan         = models.TextField(blank=True, verbose_name="Q35 – Kualiti Makanan")
    siapa_manage            = models.CharField(max_length=200, blank=True, verbose_name="Q37 – Siapa In-Charge?")
    masa_tunggu             = models.CharField(max_length=100, blank=True, verbose_name="Q46 – Masa Tunggu Rawatan")
    ada_osca                = models.BooleanField(null=True, blank=True, verbose_name="Q48 – Ada OSCA?")
    bilangan_osca           = models.IntegerField(null=True, blank=True, verbose_name="Q48a – Bilangan OSCA")
    
    # --- MEDAN BARU (FASA 5) ---
    ruang_tunggu_selesa     = models.BooleanField(null=True, blank=True, verbose_name="Ruang Menunggu Selesa?")
    ruang_tunggu_nota       = models.CharField(max_length=255, blank=True, verbose_name="Nota Ruang Menunggu")
    kekangan_rawatan        = models.TextField(blank=True, verbose_name="Kekangan Rawatan (Jika Tidak Boleh Selesai Kes)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "K3 – Perkhidmatan Kesihatan"
        verbose_name_plural = "K3 – Perkhidmatan Kesihatan"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 4 – Aset  (table: home_klusteraset)
# ─────────────────────────────────────────────────────────────────
class KlusterAset(models.Model):
    disposable_mencukupi = models.BooleanField(null=True, blank=True, verbose_name="Q11 – Disposable Assets Mencukupi?")
    keadaan_aset         = models.TextField(blank=True, verbose_name="Q12 – Keadaan Aset (Umur & Fungsi)")
    ada_ambulans         = models.BooleanField(null=True, blank=True, verbose_name="Q15 – Ada Ambulans?")
    keadaan_ambulans     = models.TextField(blank=True, verbose_name="Q15 – Keadaan Ambulans")
    aset_perlu_diganti   = models.TextField(blank=True, verbose_name="Q24 – Aset Yang Perlu Diganti")
    aset_tidak_ikut_spec = models.TextField(blank=True, verbose_name="Q25 – Aset Tidak Ikut Spec KKM")
    umur_komputer        = models.TextField(blank=True, verbose_name="Q31 – Umur Komputer")
    
    # --- MEDAN BARU (FASA 3) ---
    senarai_peralatan    = models.TextField(blank=True, verbose_name="Senarai Peralatan Perubatan")
    ambulans_nota        = models.CharField(max_length=255, blank=True, verbose_name="Nota Ambulans")
    sistem_pendigitalan  = models.CharField(max_length=500, blank=True, verbose_name="Sistem Pendigitalan")
    gajet_ict_baik       = models.BooleanField(null=True, blank=True, verbose_name="Gajet ICT Baik?")
    gajet_ict_nota       = models.CharField(max_length=255, blank=True, verbose_name="Nota Gajet ICT")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "K4 – Aset"
        verbose_name_plural = "K4 – Aset"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 5 – Fasiliti Fizikal  (table: home_klusterfasiliti)
# ─────────────────────────────────────────────────────────────────
class KlusterFasiliti(models.Model):
    keadaan_perabot       = models.TextField(blank=True, verbose_name="Q13 – Keadaan Perabot/Infrastruktur")
    ada_quarters          = models.BooleanField(null=True, blank=True, verbose_name="Q14 – Ada Quarters?")
    quarters_mencukupi    = models.BooleanField(null=True, blank=True, verbose_name="Q14 – Quarters Mencukupi?")
    ada_isu_parking       = models.BooleanField(null=True, blank=True, verbose_name="Q22/Q40 – Ada Isu Parking?")
    masalah_aircond       = models.BooleanField(null=True, blank=True, verbose_name="Q23/Q41 – Ada Masalah Aircond?")
    ruang_kerja_mencukupi = models.BooleanField(null=True, blank=True, verbose_name="Q26 – Ruang Kerja Mencukupi?")
    ada_bilik_mayat       = models.BooleanField(null=True, blank=True, verbose_name="Q33 – Ada Bilik Mayat?")
    ada_pantry            = models.BooleanField(null=True, blank=True, verbose_name="Q29b – Ada Kawasan Rehat Staff?")
    ada_kantin            = models.BooleanField(null=True, blank=True, verbose_name="Q44 – Ada Kantin/Mini Mart?")
    ada_security          = models.BooleanField(null=True, blank=True, verbose_name="Q45 – Ada Security?")
    
    # --- MEDAN BARU (FASA 2) ---
    ada_parking           = models.BooleanField(null=True, blank=True, verbose_name="Ada Parking Disediakan?")
    parking_mencukupi     = models.BooleanField(null=True, blank=True, verbose_name="Parking Mencukupi?")
    aircond_nota          = models.CharField(max_length=255, blank=True, verbose_name="Nota Aircond")
    masalah_kipas         = models.BooleanField(null=True, blank=True, verbose_name="Masalah Kipas?")
    kipas_nota            = models.CharField(max_length=255, blank=True, verbose_name="Nota Kipas")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "K5 – Fasiliti Fizikal"
        verbose_name_plural = "K5 – Fasiliti Fizikal"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 6 – Perancangan  (table: home_klusterperancangan)
# ─────────────────────────────────────────────────────────────────
class KlusterPerancangan(models.Model):
    perkhidmatan_baru   = models.TextField(blank=True, verbose_name="Q18 – Perkhidmatan Baru Yang Ingin Diwujudkan")
    fasiliti_diperlukan = models.TextField(blank=True, verbose_name="Q19 – Fasiliti Yang Sangat Diperlukan")
    
    # --- MEDAN BARU (FASA 6) ---
    belanja_mengurus    = models.CharField(max_length=255, blank=True, verbose_name="Belanja Mengurus (OE)")
    belanja_pembangunan = models.CharField(max_length=255, blank=True, verbose_name="Belanja Pembangunan (DE)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "K6 – Perancangan"
        verbose_name_plural = "K6 – Perancangan"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 7 – Konsesi & Lain-lain  (table: home_klusterkonsesi)
# ─────────────────────────────────────────────────────────────────
class KlusterKonsesi(models.Model):
    maintenance_okay = models.BooleanField(null=True, blank=True, verbose_name="Q28 – Maintenance Konsesi OK?")
    masalah_utama    = models.TextField(blank=True, verbose_name="Q17 – Masalah Utama")
    wishlist         = models.TextField(blank=True, verbose_name="Q17a – Wishlist")
    
    # --- MEDAN BARU (FASA 7) ---
    prosedur_kes_dadah     = models.TextField(blank=True, verbose_name="Prosedur Kes Dadah")
    hemodialisis_nota      = models.TextField(blank=True, verbose_name="Nota Mesin Hemodialisis")
    status_bekalan_oksigen = models.CharField(max_length=150, blank=True, verbose_name="Status Bekalan Oksigen")
    wishlist_fail          = models.FileField(upload_to='wishlist_files/', null=True, blank=True, verbose_name="Fail Wishlist")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "K7 – Konsesi & Lain-lain"
        verbose_name_plural = "K7 – Konsesi & Lain-lain"


# ─────────────────────────────────────────────────────────────────
# HUB – FacilityProfile  (table: home_facilityprofile)
# Menghubungkan semua 8 kluster dengan OneToOneField
# ─────────────────────────────────────────────────────────────────
class FacilityProfile(models.Model):
    # Backward-compat class constants
    FACILITY_TYPE_CHOICES = MaklumatAsas.FACILITY_TYPE_CHOICES
    NEGERI_CHOICES        = MaklumatAsas.NEGERI_CHOICES
    STATUS_CHOICES = [('aktif', 'Aktif'), ('tutup', 'Tutup')]

    # ── FK ke setiap kluster ──────────────────────────────────────
    maklumat_asas    = models.OneToOneField(MaklumatAsas,      on_delete=models.CASCADE,  null=True, blank=True, related_name='profil',         verbose_name="K0 – Maklumat Asas")
    k_kejuruteraan   = models.OneToOneField(KlusterKejuruteraan,  on_delete=models.SET_NULL, null=True, blank=True, related_name='profil', verbose_name="K1 – Kejuruteraan")
    k_sumber_manusia = models.OneToOneField(KlusterSumberManusia, on_delete=models.SET_NULL, null=True, blank=True, related_name='profil', verbose_name="K2 – Sumber Manusia")
    k_perkhidmatan   = models.OneToOneField(KlusterPerkhidmatan,  on_delete=models.SET_NULL, null=True, blank=True, related_name='profil', verbose_name="K3 – Perkhidmatan")
    k_aset           = models.OneToOneField(KlusterAset,          on_delete=models.SET_NULL, null=True, blank=True, related_name='profil', verbose_name="K4 – Aset")
    k_fasiliti       = models.OneToOneField(KlusterFasiliti,      on_delete=models.SET_NULL, null=True, blank=True, related_name='profil', verbose_name="K5 – Fasiliti")
    k_perancangan    = models.OneToOneField(KlusterPerancangan,    on_delete=models.SET_NULL, null=True, blank=True, related_name='profil', verbose_name="K6 – Perancangan")
    k_konsesi        = models.OneToOneField(KlusterKonsesi,        on_delete=models.SET_NULL, null=True, blank=True, related_name='profil', verbose_name="K7 – Konsesi")

    # ── Meta ──────────────────────────────────────────────────────
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='facility_profiles')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    tahun        = models.IntegerField(default=_current_year, verbose_name="Tahun")
    # TAMBAHAN BARU: Status Lawatan VIP
    STATUS_LAWATAN_CHOICES = [
        ('merah',  'Belum Dilawati'),
        ('kuning', 'Dalam Perancangan/Proses'),
        ('biru',   'Sudah Dilawati'),
        ('hijau',  'Selesai/Dilaksanakan'),
    ]
    status_lawatan       = models.CharField(max_length=10, choices=STATUS_LAWATAN_CHOICES, default='merah', verbose_name="Status Lawatan")
    tarikh_lawatan       = models.DateField(null=True, blank=True, verbose_name="Tarikh Lawatan")
    nama_program_lawatan = models.CharField(max_length=255, blank=True, verbose_name="Nama Program/VIP")
    catatan_lawatan      = models.TextField(blank=True, verbose_name="Catatan/Tindakan")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    # ── Kluster 0 shortcuts ───────────────────────────────────────
    @property
    def nama_fasiliti(self):
        return self.maklumat_asas.nama_fasiliti if self.maklumat_asas else ''
    @property
    def jenis_fasiliti(self):
        return self.maklumat_asas.jenis_fasiliti if self.maklumat_asas else ''
    @property
    def negeri(self):
        return self.maklumat_asas.negeri if self.maklumat_asas else ''
    @property
    def daerah(self):
        return self.maklumat_asas.daerah if self.maklumat_asas else ''
    @property
    def alamat(self):
        return self.maklumat_asas.alamat if self.maklumat_asas else ''
    @property
    def poskod(self):
        return self.maklumat_asas.poskod if self.maklumat_asas else ''
    @property
    def latitud(self):
        return self.maklumat_asas.latitud if self.maklumat_asas else None
    @property
    def longitud(self):
        return self.maklumat_asas.longitud if self.maklumat_asas else None
    @property
    def wilayah(self):
        return self.maklumat_asas.wilayah if self.maklumat_asas else ''
    @property
    def zon(self):
        return self.maklumat_asas.zon if self.maklumat_asas else ''
    @property
    def parlimen_asas(self):
        """Parlimen from MaklumatAsas (primary location)."""
        return self.maklumat_asas.parlimen if self.maklumat_asas else ''
    def get_jenis_fasiliti_display(self):
        return self.maklumat_asas.get_jenis_fasiliti_display() if self.maklumat_asas else ''
    def get_negeri_display(self):
        return self.maklumat_asas.get_negeri_display() if self.maklumat_asas else ''

    # ── Kluster 1 shortcuts ───────────────────────────────────────
    @property
    def kod_fasiliti(self):          return self.k_kejuruteraan.kod_fasiliti if self.k_kejuruteraan else ''
    @property
    def parlimen(self):
        if self.maklumat_asas and self.maklumat_asas.parlimen:
            return self.maklumat_asas.parlimen
        return self.k_kejuruteraan.parlimen if self.k_kejuruteraan else ''
    @property
    def tahun_dibina(self):          return self.k_kejuruteraan.tahun_dibina if self.k_kejuruteraan else None
    @property
    def jenis_hospital_klinik(self): return self.k_kejuruteraan.jenis_hospital_klinik if self.k_kejuruteraan else ''
    @property
    def siling_okay(self):           return self.k_kejuruteraan.siling_okay if self.k_kejuruteraan else None
    @property
    def ukuran_tanah(self):          return self.k_kejuruteraan.ukuran_tanah if self.k_kejuruteraan else ''

    # ── Kluster 2 shortcuts ───────────────────────────────────────
    @property
    def kakitangan_tetap(self):            return self.k_sumber_manusia.kakitangan_tetap if self.k_sumber_manusia else None
    @property
    def kakitangan_kontrak(self):          return self.k_sumber_manusia.kakitangan_kontrak if self.k_sumber_manusia else None
    @property
    def kakitangan_mystep(self):           return self.k_sumber_manusia.kakitangan_mystep if self.k_sumber_manusia else None
    @property
    def ada_kakitangan_pinjaman(self):     return self.k_sumber_manusia.ada_kakitangan_pinjaman if self.k_sumber_manusia else None
    @property
    def bilangan_shift(self):              return self.k_sumber_manusia.bilangan_shift if self.k_sumber_manusia else None
    @property
    def ada_ot_allowance(self):            return self.k_sumber_manusia.ada_ot_allowance if self.k_sumber_manusia else None
    @property
    def bilangan_staff_non_medical(self):  return self.k_sumber_manusia.bilangan_staff_non_medical if self.k_sumber_manusia else None
    @property
    def waktu_beroperasi(self):            return self.k_sumber_manusia.waktu_beroperasi if self.k_sumber_manusia else ''
    @property
    def cara_minta_cuti(self):             return self.k_sumber_manusia.cara_minta_cuti if self.k_sumber_manusia else ''
    @property
    def isu_penempatan(self):              return self.k_sumber_manusia.isu_penempatan if self.k_sumber_manusia else ''

    # ── Kluster 3 shortcuts ───────────────────────────────────────
    @property
    def jenis_perkhidmatan(self):      return self.k_perkhidmatan.jenis_perkhidmatan if self.k_perkhidmatan else ''
    @property
    def anggaran_pelawat_harian(self): return self.k_perkhidmatan.anggaran_pelawat_harian if self.k_perkhidmatan else None
    @property
    def jenis_penyakit_kerap(self):    return self.k_perkhidmatan.jenis_penyakit_kerap if self.k_perkhidmatan else ''
    @property
    def boleh_selesaikan_kes(self):    return self.k_perkhidmatan.boleh_selesaikan_kes if self.k_perkhidmatan else None
    @property
    def rujukan_ke(self):              return self.k_perkhidmatan.rujukan_ke if self.k_perkhidmatan else ''
    @property
    def ada_ruang_rehat(self):         return self.k_perkhidmatan.ada_ruang_rehat if self.k_perkhidmatan else None
    @property
    def ada_hemodialisis(self):        return self.k_perkhidmatan.ada_hemodialisis if self.k_perkhidmatan else None
    @property
    def unit_hemodialisis(self):       return self.k_perkhidmatan.unit_hemodialisis if self.k_perkhidmatan else None
    @property
    def bekalan_ubat_mencukupi(self):  return self.k_perkhidmatan.bekalan_ubat_mencukupi if self.k_perkhidmatan else None
    @property
    def keperluan_oksigen(self):       return self.k_perkhidmatan.keperluan_oksigen if self.k_perkhidmatan else ''
    @property
    def ada_emr(self):                 return self.k_perkhidmatan.ada_emr if self.k_perkhidmatan else None
    @property
    def wad_diasingkan(self):          return self.k_perkhidmatan.wad_diasingkan if self.k_perkhidmatan else None
    @property
    def kualiti_makanan(self):         return self.k_perkhidmatan.kualiti_makanan if self.k_perkhidmatan else ''
    @property
    def siapa_manage(self):            return self.k_perkhidmatan.siapa_manage if self.k_perkhidmatan else ''
    @property
    def masa_tunggu(self):             return self.k_perkhidmatan.masa_tunggu if self.k_perkhidmatan else ''
    @property
    def ada_osca(self):                return self.k_perkhidmatan.ada_osca if self.k_perkhidmatan else None

    # ── Kluster 4 shortcuts ───────────────────────────────────────
    @property
    def disposable_mencukupi(self):  return self.k_aset.disposable_mencukupi if self.k_aset else None
    @property
    def keadaan_aset(self):          return self.k_aset.keadaan_aset if self.k_aset else ''
    @property
    def ada_ambulans(self):          return self.k_aset.ada_ambulans if self.k_aset else None
    @property
    def keadaan_ambulans(self):      return self.k_aset.keadaan_ambulans if self.k_aset else ''
    @property
    def aset_perlu_diganti(self):    return self.k_aset.aset_perlu_diganti if self.k_aset else ''
    @property
    def aset_tidak_ikut_spec(self):  return self.k_aset.aset_tidak_ikut_spec if self.k_aset else ''
    @property
    def umur_komputer(self):         return self.k_aset.umur_komputer if self.k_aset else ''

    # ── Kluster 5 shortcuts ───────────────────────────────────────
    @property
    def keadaan_perabot(self):        return self.k_fasiliti.keadaan_perabot if self.k_fasiliti else ''
    @property
    def ada_quarters(self):           return self.k_fasiliti.ada_quarters if self.k_fasiliti else None
    @property
    def quarters_mencukupi(self):     return self.k_fasiliti.quarters_mencukupi if self.k_fasiliti else None
    @property
    def ada_isu_parking(self):        return self.k_fasiliti.ada_isu_parking if self.k_fasiliti else None
    @property
    def masalah_aircond(self):        return self.k_fasiliti.masalah_aircond if self.k_fasiliti else None
    @property
    def ruang_kerja_mencukupi(self):  return self.k_fasiliti.ruang_kerja_mencukupi if self.k_fasiliti else None
    @property
    def ada_bilik_mayat(self):        return self.k_fasiliti.ada_bilik_mayat if self.k_fasiliti else None
    @property
    def ada_pantry(self):             return self.k_fasiliti.ada_pantry if self.k_fasiliti else None
    @property
    def ada_kantin(self):             return self.k_fasiliti.ada_kantin if self.k_fasiliti else None
    @property
    def ada_security(self):           return self.k_fasiliti.ada_security if self.k_fasiliti else None

    # ── Kluster 6 shortcuts ───────────────────────────────────────
    @property
    def perkhidmatan_baru(self):   return self.k_perancangan.perkhidmatan_baru if self.k_perancangan else ''
    @property
    def fasiliti_diperlukan(self): return self.k_perancangan.fasiliti_diperlukan if self.k_perancangan else ''

    # ── Kluster 7 shortcuts ───────────────────────────────────────
    @property
    def maintenance_okay(self): return self.k_konsesi.maintenance_okay if self.k_konsesi else None
    @property
    def masalah_utama(self):    return self.k_konsesi.masalah_utama if self.k_konsesi else ''
    @property
    def wishlist(self):         return self.k_konsesi.wishlist if self.k_konsesi else ''

    # ── Computed properties ───────────────────────────────────────
    def __str__(self):
        return f"{self.nama_fasiliti} ({self.get_jenis_fasiliti_display()})"

    @property
    def jumlah_kakitangan(self):
        total = 0
        for f in [self.kakitangan_tetap, self.kakitangan_kontrak, self.kakitangan_mystep]:
            if f:
                total += f
        return total

    @property
    def skor_kesediaan(self):
        """Skor 0-100 berdasarkan 10 medan Ya/Tidak utama merentasi semua kluster.
        Setiap medan Ya = 1 mata. Skor = jumlah Ya / 10 * 100.
        Medan yang belum dijawab (None) dikira sebagai 0."""
        fields = [
            self.bekalan_ubat_mencukupi, self.ada_ambulans, self.ada_ruang_rehat,
            self.ruang_kerja_mencukupi, self.ada_security, self.ada_emr,
            self.disposable_mencukupi, self.wad_diasingkan, self.siling_okay,
            self.ada_ot_allowance,
        ]
        total = len(fields)  # always 10
        ya = sum(1 for f in fields if f is True)
        return round(ya / total * 100)

    @property
    def perlu_kemaskini(self):
        """True jika fasiliti aktif tapi data > 12 bulan tak dikemaskini."""
        if self.status != 'aktif':
            return False
        from django.utils import timezone
        import datetime
        threshold = timezone.now() - datetime.timedelta(days=365)
        return self.updated_at < threshold

    class Meta:
        verbose_name = "Profil Fasiliti"
        verbose_name_plural = "Profil Fasiliti"
        ordering = ['-created_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # List of bahagian slugs this user is allowed to access
    bahagian_slugs = models.JSONField(default=list, blank=True)
    # Read-only top-management access (sees all data, cannot add/edit/delete)
    is_top_management = models.BooleanField(default=False, verbose_name="Top Management")
    # JKN access: sees all data but can only add/edit/delete assigned facilities
    is_jkn = models.BooleanField(default=False, verbose_name="JKN - Hospital & Klinik")
    # Facility names (nama_fasiliti) this JKN user is allowed to edit
    assigned_facility_names = models.JSONField(default=list, blank=True, verbose_name="Fasiliti Diperuntukkan")

    def __str__(self):
        return f'Profile: {self.user.username}'

    def has_bahagian(self, slug):
        return slug in self.bahagian_slugs


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile when a new User is saved."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
