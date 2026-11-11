import datetime
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

def _current_year():
    return datetime.date.today().year

# ─────────────────────────────────────────────────────────────────
# KLUSTER 0 – Maklumat Asas (BAHAGIAN 1: Latar Belakang)
# ─────────────────────────────────────────────────────────────────
class MaklumatAsas(models.Model):
    FACILITY_TYPE_CHOICES = [
        ('hospital', 'Hospital'), ('hospital_pakar', 'Hospital Pakar'), ('klinik_kesihatan', 'Klinik Kesihatan'),
        ('klinik_desa', 'Klinik Desa'), ('klinik_komuniti', 'Klinik Komuniti'), ('institusi_perubatan_khas', 'Institusi Perubatan Khas'),
        ('institusi_latihan', 'Institusi Latihan'), ('jabatan_kes_negeri', 'Jabatan Kesihatan Negeri'), ('klinik_pergigian_hosp', 'Klinik Pergigian di Hospital'),
        ('kk_ibu_anak', 'Klinik Kesihatan Ibu dan Anak'), ('klinik_pergigian_utc', 'Klinik Pergigian UTC'), ('klinik_pergigian_sekolah', 'Klinik Pergigian di Sekolah'),
        ('kp_kk_utc', 'Klinik Pergigian di Klinik Kesihatan UTC'), ('kp_kk_ibu_anak', 'Klinik Pergigian di Klinik Kesihatan Ibu dan Anak'),
        ('klinik_pergigian_rtc', 'Klinik Pergigian RTC'), ('klinik_kesihatan_utc', 'Klinik Kesihatan UTC'), ('klinik_pergigian', 'Klinik Pergigian'),
        ('pkp_bahagian', 'Pejabat Kesihatan Pergigian Bahagian'), ('pkp', 'Pejabat Kesihatan Pergigian'), ('pkp_daerah', 'Pejabat Kesihatan Pergigian Daerah'),
        ('pkp_kawasan', 'Pejabat Kesihatan Pergigian Kawasan'), ('lain', 'Lain-lain'),
    ]
    NEGERI_CHOICES = [
        ('johor', 'Johor'), ('kedah', 'Kedah'), ('kelantan', 'Kelantan'), ('melaka', 'Melaka'), ('negeri_sembilan', 'Negeri Sembilan'),
        ('pahang', 'Pahang'), ('perak', 'Perak'), ('perlis', 'Perlis'), ('pulau_pinang', 'Pulau Pinang'), ('sabah', 'Sabah'),
        ('sarawak', 'Sarawak'), ('selangor', 'Selangor'), ('terengganu', 'Terengganu'), ('wp_kl', 'W.P. Kuala Lumpur'),
        ('wp_putrajaya', 'W.P. Putrajaya'), ('wp_labuan', 'W.P. Labuan'),
    ]
    WILAYAH_CHOICES = [
        ('utara', 'Utara'), ('tengah', 'Tengah'), ('selatan', 'Selatan'),
        ('timur', 'Timur'), ('sabah', 'Sabah'), ('sarawak', 'Sarawak'), ('labuan', 'W.P. Labuan'),
    ]

    # 1.1 Maklumat Responden
    nama_responden = models.CharField(max_length=200, blank=True, verbose_name="Nama Penuh Responden")
    jawatan_responden = models.CharField(max_length=150, blank=True, verbose_name="Jawatan Responden")
    no_telefon_responden = models.CharField(max_length=20, blank=True, verbose_name="No. Telefon Responden")
    emel_responden = models.EmailField(blank=True, verbose_name="Emel Responden")

    # 1.2 Maklumat Fasiliti & Lokasi
    nama_fasiliti = models.CharField(max_length=200, verbose_name="Nama Fasiliti")
    kod_fasiliti = models.CharField(max_length=50, blank=True, verbose_name="Kod Fasiliti")
    kategori_fasiliti = models.CharField(max_length=150, blank=True, verbose_name="Kategori Fasiliti")
    jenis_fasiliti = models.CharField(max_length=30, choices=FACILITY_TYPE_CHOICES, verbose_name="Jenis Fasiliti")
    alamat = models.TextField(blank=True, verbose_name="Alamat")
    poskod = models.CharField(max_length=10, blank=True, verbose_name="Poskod")
    daerah = models.CharField(max_length=100, blank=True, verbose_name="Daerah/Bandar")
    negeri = models.CharField(max_length=30, choices=NEGERI_CHOICES, blank=True, verbose_name="Negeri")
    wilayah = models.CharField(max_length=20, choices=WILAYAH_CHOICES, blank=True)
    zon = models.CharField(max_length=100, blank=True)
    parlimen = models.CharField(max_length=150, blank=True)
    latitud = models.FloatField(null=True, blank=True, verbose_name="Latitud")
    longitud = models.FloatField(null=True, blank=True, verbose_name="Longitud")
    ketua_fasiliti = models.CharField(max_length=200, blank=True, verbose_name="Ketua Fasiliti")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nama_fasiliti} ({self.get_jenis_fasiliti_display()})"


# ─────────────────────────────────────────────────────────────────
# KLUSTER 1 – Infrastruktur (BAHAGIAN 2: Infrastruktur Fasiliti)
# ─────────────────────────────────────────────────────────────────
class KlusterInfrastruktur(models.Model):
    # 2.1 Bangunan & Ruang Tapak
    keluasan_tapak = models.CharField(max_length=100, blank=True)
    tanah_mencukupi = models.BooleanField(null=True, blank=True)
    struktur_baik = models.BooleanField(null=True, blank=True)
    struktur_nota = models.TextField(blank=True)
    lif_berfungsi = models.BooleanField(null=True, blank=True)
    lif_nota = models.TextField(blank=True)
    ada_ups = models.BooleanField(null=True, blank=True)

    # 2.2 Kemudahan Fasiliti
    ruang_rawatan_mencukupi = models.BooleanField(null=True, blank=True)
    ada_ruang_rehat_pelawat = models.BooleanField(null=True, blank=True)
    ada_kantin = models.BooleanField(null=True, blank=True)
    ada_pantry = models.BooleanField(null=True, blank=True)
    ada_surau = models.BooleanField(null=True, blank=True)
    tandas_baik = models.BooleanField(null=True, blank=True)

    # 2.3 Kemudahan Tambahan & Utiliti
    pengudaraan_baik = models.BooleanField(null=True, blank=True)
    ada_aircond = models.BooleanField(null=True, blank=True)
    aircond_nota = models.TextField(blank=True)
    ada_kipas = models.BooleanField(null=True, blank=True)
    kipas_nota = models.TextField(blank=True)
    ada_parking = models.BooleanField(null=True, blank=True)
    parking_mencukupi = models.BooleanField(null=True, blank=True)
    parking_nota = models.TextField(blank=True)
    ada_kuarters = models.BooleanField(null=True, blank=True)
    kuarters_baik = models.BooleanField(null=True, blank=True)
    kuarters_nota = models.TextField(blank=True)

    # 2.4 Aset & Peralatan
    fail_aset_alih = models.FileField(upload_to='infrastruktur_files/', null=True, blank=True)
    fail_aset_tak_alih = models.FileField(upload_to='infrastruktur_files/', null=True, blank=True)

    # 2.5 Aset Kenderaan (Pautan Butang Ke Modul Kenderaan - Tiada DB field di sini)

    # 2.6 Keselamatan
    ada_security = models.BooleanField(null=True, blank=True)
    ada_cctv = models.BooleanField(null=True, blank=True)
    json_pekerja_security = models.JSONField(null=True, blank=True) # Adding Row
    fail_pekerja_security = models.FileField(upload_to='infrastruktur_files/', null=True, blank=True)

    # 2.7 Tindak Balas Kecemasan
    ada_sistem_kebakaran = models.BooleanField(null=True, blank=True)
    json_kebakaran_aktif = models.JSONField(null=True, blank=True) # Adding Row
    json_kebakaran_pasif = models.JSONField(null=True, blank=True) # Adding Row
    tarikh_fire_drill = models.DateField(null=True, blank=True)
    pernah_kecemasan = models.BooleanField(null=True, blank=True)
    json_sejarah_kecemasan = models.JSONField(null=True, blank=True) # Adding Row
    
    fail_wishlist = models.FileField(upload_to='wishlist_files/', null=True, blank=True)


# ─────────────────────────────────────────────────────────────────
# KLUSTER 2 – Aset Perubatan (BAHAGIAN 3: Aset Perubatan)
# ─────────────────────────────────────────────────────────────────
class KlusterAsetPerubatan(models.Model):
    # 3.1 Peralatan Perubatan & Sokongan
    json_peralatan = models.JSONField(null=True, blank=True) # Adding Row
    fail_peralatan = models.FileField(upload_to='aset_perubatan_files/', null=True, blank=True)
    json_aset_tidak_spec = models.JSONField(null=True, blank=True) # Adding Row
    fail_aset_tidak_spec = models.FileField(upload_to='aset_perubatan_files/', null=True, blank=True)
    
    consumables_mencukupi = models.BooleanField(null=True, blank=True)
    ubat_mencukupi = models.BooleanField(null=True, blank=True)
    ada_blood_bank = models.BooleanField(null=True, blank=True)
    ada_hemodialisis = models.BooleanField(null=True, blank=True)
    ada_radiologi = models.BooleanField(null=True, blank=True)
    ada_makmal = models.BooleanField(null=True, blank=True)

    fail_wishlist = models.FileField(upload_to='wishlist_files/', null=True, blank=True)


# ─────────────────────────────────────────────────────────────────
# KLUSTER 3 – Sumber Manusia (BAHAGIAN 4: Pengurusan Sumber Manusia)
# ─────────────────────────────────────────────────────────────────
class KlusterSumberManusia(models.Model):
    # 4.1 Bilangan & Penempatan Staf
    # Dibuat tanpa Autokira - Diisi manual berserta fail
    jumlah_perjawatan = models.IntegerField(null=True, blank=True)
    fail_perjawatan = models.FileField(upload_to='sumber_manusia_files/', null=True, blank=True)
    
    jumlah_pengisian = models.IntegerField(null=True, blank=True)
    fail_pengisian = models.FileField(upload_to='sumber_manusia_files/', null=True, blank=True)
    
    jumlah_kekosongan = models.IntegerField(null=True, blank=True)
    fail_kekosongan = models.FileField(upload_to='sumber_manusia_files/', null=True, blank=True)
    
    # JSON untuk fail/senarai sokongan
    json_kakitangan = models.JSONField(null=True, blank=True) 
    fail_kakitangan = models.FileField(upload_to='sumber_manusia_files/', null=True, blank=True)
    
    ada_kakitangan_pinjaman = models.BooleanField(null=True, blank=True)
    ada_isu_petugas = models.BooleanField(null=True, blank=True)
    isu_petugas_nota = models.TextField(blank=True)
    status_pertukaran = models.CharField(max_length=255, blank=True)

    # 4.2 Penjadualan & Syif
    bilangan_shift = models.CharField(max_length=255, blank=True)
    corak_penugasan = models.CharField(max_length=255, blank=True)
    pengurusan_jadual = models.CharField(max_length=255, blank=True)
    proses_cuti = models.CharField(max_length=255, blank=True)
    isu_penjadualan = models.CharField(max_length=255, blank=True)

    fail_wishlist = models.FileField(upload_to='wishlist_files/', null=True, blank=True)

# Pengekalan model StafFasiliti untuk elak ralat jika ada rekod lama atau dashboard panggil
class StafFasiliti(models.Model):
    kluster_sm = models.ForeignKey(KlusterSumberManusia, on_delete=models.CASCADE, related_name='senarai_staf')
    nama_staf = models.CharField(max_length=200)
    skim = models.CharField(max_length=50)
    status_lantikan = models.CharField(max_length=30)
    tarikh_tamat_perkhidmatan = models.DateField(null=True, blank=True)


# ─────────────────────────────────────────────────────────────────
# KLUSTER 4 – Perkhidmatan (BAHAGIAN 5: Penyampaian Perkhidmatan)
# ─────────────────────────────────────────────────────────────────
class KlusterPerkhidmatan(models.Model):
    # 5.1 Operasi & Pesakit
    json_waktu_operasi = models.JSONField(null=True, blank=True) # Adding Row
    anggaran_pelawat = models.IntegerField(null=True, blank=True)
    json_program = models.JSONField(null=True, blank=True) # Adding Row
    fail_program = models.FileField(upload_to='perkhidmatan_files/', null=True, blank=True)
    json_penyakit = models.JSONField(null=True, blank=True) # Adding Row
    fail_penyakit = models.FileField(upload_to='perkhidmatan_files/', null=True, blank=True)

    # 5.2 Kapasiti Rawatan & Keselesaan
    ruang_menunggu_selesa = models.BooleanField(null=True, blank=True)
    ruang_menunggu_nota = models.TextField(blank=True)
    ada_wad = models.BooleanField(null=True, blank=True)
    wad_asing_jantina = models.BooleanField(null=True, blank=True)
    katil_mencukupi = models.BooleanField(null=True, blank=True)
    ada_kaunseling = models.BooleanField(null=True, blank=True)
    ada_rehabilitasi = models.BooleanField(null=True, blank=True)
    boleh_selesai_kes = models.BooleanField(null=True, blank=True)
    boleh_selesai_kes_nota = models.TextField(blank=True)
    
    json_fasiliti_terdekat = models.JSONField(null=True, blank=True) # Adding Row
    fail_fasiliti_terdekat = models.FileField(upload_to='perkhidmatan_files/', null=True, blank=True)
    anggaran_masa_tunggu = models.CharField(max_length=150, blank=True)

    # 5.3 Maklumat Tambahan
    ada_forensik = models.BooleanField(null=True, blank=True)
    sedia_makanan = models.BooleanField(null=True, blank=True)
    makanan_memuaskan = models.BooleanField(null=True, blank=True)
    makanan_nota = models.TextField(blank=True)

    fail_wishlist = models.FileField(upload_to='wishlist_files/', null=True, blank=True)


# ─────────────────────────────────────────────────────────────────
# KLUSTER 5 – Kewangan & Rancang (BAHAGIAN 6: Kewangan, Konsesi & Perancangan)
# ─────────────────────────────────────────────────────────────────
class KlusterKewangan(models.Model):
    # 6.1 Peruntukan Kewangan
    belanja_mengurus = models.CharField(max_length=255, blank=True)
    belanja_pembangunan = models.CharField(max_length=255, blank=True)
    
    # 6.2 Perkhidmatan Konsesi
    konsesi_lancar = models.BooleanField(null=True, blank=True)
    isu_utama = models.TextField(blank=True)
    
    # 6.3 Perancangan Masa Depan
    perlu_tambah_infrastruktur = models.BooleanField(null=True, blank=True)
    json_infrastruktur_baru = models.JSONField(null=True, blank=True) # Adding Row
    
    fail_wishlist = models.FileField(upload_to='wishlist_files/', null=True, blank=True)


# ─────────────────────────────────────────────────────────────────
# KLUSTER 6 – Sistem Digital (BAHAGIAN 7: Sistem Rangkaian & Peralatan Digital)
# ─────────────────────────────────────────────────────────────────
class KlusterDigital(models.Model):
    # 7.1 Peranti Digital
    peranti_mencukupi = models.BooleanField(null=True, blank=True)
    peranti_baik = models.BooleanField(null=True, blank=True)
    peranti_baik_nota = models.TextField(blank=True)
    perlu_tambah_peranti = models.BooleanField(null=True, blank=True)
    perlu_tambah_nota = models.TextField(blank=True)
    internet_pantas = models.BooleanField(null=True, blank=True)
    
    json_peranti = models.JSONField(null=True, blank=True) # Adding Row
    fail_peranti = models.FileField(upload_to='digital_files/', null=True, blank=True)
    
    # 7.2 Sistem Pendigitalan
    json_sistem = models.JSONField(null=True, blank=True) # Adding Row
    fail_wishlist = models.FileField(upload_to='wishlist_files/', null=True, blank=True)


# ─────────────────────────────────────────────────────────────────
# HUB – FacilityProfile (Menghubungkan semua 7 kluster)
# ─────────────────────────────────────────────────────────────────
class FacilityProfile(models.Model):
    STATUS_CHOICES = [('aktif', 'Aktif'), ('tutup', 'Tutup')]
    STATUS_LAWATAN_CHOICES = [('merah', 'Belum Dilawati'), ('kuning', 'Dalam Perancangan'), ('biru', 'Sudah Dilawati'), ('hijau', 'Selesai')]

    # Pautan ke Kluster Baharu
    maklumat_asas       = models.OneToOneField(MaklumatAsas, on_delete=models.CASCADE, null=True, blank=True)
    k_infrastruktur     = models.OneToOneField(KlusterInfrastruktur, on_delete=models.SET_NULL, null=True, blank=True)
    k_aset_perubatan    = models.OneToOneField(KlusterAsetPerubatan, on_delete=models.SET_NULL, null=True, blank=True)
    k_sumber_manusia    = models.OneToOneField(KlusterSumberManusia, on_delete=models.SET_NULL, null=True, blank=True)
    k_perkhidmatan      = models.OneToOneField(KlusterPerkhidmatan, on_delete=models.SET_NULL, null=True, blank=True)
    k_kewangan          = models.OneToOneField(KlusterKewangan, on_delete=models.SET_NULL, null=True, blank=True)
    k_digital           = models.OneToOneField(KlusterDigital, on_delete=models.SET_NULL, null=True, blank=True)

    # Medat Data Profil
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='facility_profiles')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    tahun        = models.IntegerField(default=_current_year)
    
    # Status Lawatan VIP
    status_lawatan       = models.CharField(max_length=10, choices=STATUS_LAWATAN_CHOICES, default='merah')
    tarikh_lawatan       = models.DateField(null=True, blank=True)
    nama_program_lawatan = models.CharField(max_length=255, blank=True)
    catatan_lawatan      = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    # ── FUNGSI PINTASAN LAMA (Dikekalkan untuk elak Dashboard Crash) ──
    @property
    def nama_fasiliti(self): return self.maklumat_asas.nama_fasiliti if self.maklumat_asas else ''
    @property
    def jenis_fasiliti(self): return self.maklumat_asas.jenis_fasiliti if self.maklumat_asas else ''
    @property
    def negeri(self): return self.maklumat_asas.negeri if self.maklumat_asas else ''
    @property
    def daerah(self): return self.maklumat_asas.daerah if self.maklumat_asas else ''
    @property
    def alamat(self): return self.maklumat_asas.alamat if self.maklumat_asas else ''
    
    def get_jenis_fasiliti_display(self):
        return self.maklumat_asas.get_jenis_fasiliti_display() if self.maklumat_asas else ''
    def get_negeri_display(self):
        return self.maklumat_asas.get_negeri_display() if self.maklumat_asas else ''

    # Pintasan dummy / terselamat untuk Dashboard
    @property
    def kod_fasiliti(self): return self.maklumat_asas.kod_fasiliti if self.maklumat_asas else ''
    @property
    def skor_kesediaan(self):
        # Diselaraskan dengan soalan baru (Contoh 5 metrik utama)
        score = 0
        if self.k_infrastruktur and self.k_infrastruktur.struktur_baik: score += 20
        if self.k_aset_perubatan and self.k_aset_perubatan.ubat_mencukupi: score += 20
        if self.k_aset_perubatan and self.k_aset_perubatan.consumables_mencukupi: score += 20
        if self.k_perkhidmatan and self.k_perkhidmatan.boleh_selesai_kes: score += 20
        if self.k_digital and self.k_digital.peranti_mencukupi: score += 20
        return score
        
    @property
    def perlu_kemaskini(self):
        if self.status != 'aktif': return False
        from django.utils import timezone
        threshold = timezone.now() - datetime.timedelta(days=365)
        return self.updated_at < threshold

    def __str__(self):
        return f"{self.nama_fasiliti} ({self.tahun})"


# ─────────────────────────────────────────────────────────────────
# PROFIL PENGGUNA (ROLE)
# ─────────────────────────────────────────────────────────────────
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bahagian_slugs = models.JSONField(default=list, blank=True)
    is_top_management = models.BooleanField(default=False, verbose_name="Top Management")
    is_jkn = models.BooleanField(default=False, verbose_name="JKN - Hospital & Klinik")
    assigned_facility_names = models.JSONField(default=list, blank=True, verbose_name="Fasiliti Diperuntukkan")

    def __str__(self): return f'Profile: {self.user.username}'
    def has_bahagian(self, slug): return slug in self.bahagian_slugs

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: UserProfile.objects.get_or_create(user=instance)


# ─────────────────────────────────────────────────────────────────
# ASET KENDERAAN
# ─────────────────────────────────────────────────────────────────
class SyarikatServisKenderaan(models.Model):
    nama_syarikat = models.CharField(max_length=200)
    tempoh_kontrak = models.CharField(max_length=100)
    tarikh_mula = models.DateField()
    tarikh_tamat = models.DateField()
    
    @property
    def status_kontrak(self):
        sekarang = datetime.date.today()
        baki_hari = (self.tarikh_tamat - sekarang).days
        if baki_hari < 0: return 'tamat'
        elif baki_hari <= 60: return 'hampir_tamat'
        return 'aktif'

class AsetKenderaan(models.Model):
    JENIS = [('kereta', 'Kereta'), ('van', 'Van'), ('ambulan', 'Ambulan'), ('bas', 'Bas'), ('lori', 'Lori')]
    STATUS = [('aktif', 'Aktif'), ('rosak', 'Rosak'), ('lupus', 'Lupus')]
    
    profil_fasiliti = models.ForeignKey(FacilityProfile, on_delete=models.CASCADE, related_name='senarai_kenderaan')
    jenis_kenderaan = models.CharField(max_length=20, choices=JENIS)
    model_kenderaan = models.CharField(max_length=150)
    no_pendaftaran = models.CharField(max_length=20)
    no_chasis = models.CharField(max_length=100, blank=True)
    tahun_diterima = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS, default='aktif')
    syarikat_servis = models.ForeignKey(SyarikatServisKenderaan, on_delete=models.SET_NULL, null=True, blank=True, related_name='kenderaan_diselenggara')
    
    @property
    def umur_kenderaan(self): return datetime.date.today().year - self.tahun_diterima


# ─────────────────────────────────────────────────────────────────
# SOALAN DINAMIK
# ─────────────────────────────────────────────────────────────────
class SoalanTambahan(models.Model):
    MODUL_CHOICES = [
        ('latar_belakang', 'Bahagian 1: Latar Belakang'),
        ('infrastruktur', 'Bahagian 2: Infrastruktur Fasiliti'),
        ('aset', 'Bahagian 3: Aset Perubatan'),
        ('sumber_manusia', 'Bahagian 4: Pengurusan Sumber Manusia'),
        ('perkhidmatan', 'Bahagian 5: Penyampaian Perkhidmatan'),
        ('kewangan', 'Bahagian 6: Kewangan & Perancangan'),
        ('digital', 'Bahagian 7: Rangkaian & Digital'), # Dikemaskini
    ]
    JENIS = [('teks', 'Teks Ringkas'), ('textarea', 'Teks Panjang'), ('nombor', 'Nombor'), ('ya_tidak', 'Ya/Tidak'), ('dropdown', 'Dropdown'), ('fail', 'Muat Naik Fail')]

    modul = models.CharField(max_length=50, choices=MODUL_CHOICES)
    teks_soalan = models.CharField(max_length=300)
    jenis_input = models.CharField(max_length=20, choices=JENIS, default='teks')
    pilihan_dropdown = models.TextField(blank=True)
    is_wajib = models.BooleanField(default=False)
    is_aktif = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class JawapanSoalanTambahan(models.Model):
    profil_fasiliti = models.ForeignKey(FacilityProfile, on_delete=models.CASCADE, related_name='jawapan_tambahan')
    soalan = models.ForeignKey(SoalanTambahan, on_delete=models.CASCADE, related_name='jawapan_set')
    jawapan_teks = models.TextField(blank=True)
    jawapan_fail = models.FileField(upload_to='jawapan_tambahan_files/', null=True, blank=True)