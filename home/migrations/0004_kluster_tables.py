"""
Migration 0004: Bahagikan setiap kluster kepada table tersendiri.

Table baru:
  home_klusterkejuruteraan   (K1)
  home_klustersumbermanusia  (K2)
  home_klusterperkhidmatan   (K3)
  home_klusteraset           (K4)
  home_klusterfasiliti       (K5)
  home_klusterperancangan    (K6)
  home_klusterkonsesi        (K7)

FacilityProfile menjadi hub dengan 7 FK baru + buang semua field kluster lama.
"""

from django.db import migrations, models
import django.db.models.deletion


# ── field lists untuk copy data ke kluster baru ─────────────────
K1_FIELDS = ['tahun_dibina', 'jenis_hospital_klinik', 'siling_okay', 'ukuran_tanah']
K2_FIELDS = ['kakitangan_tetap', 'kakitangan_kontrak', 'kakitangan_mystep',
             'ada_kakitangan_pinjaman', 'bilangan_shift', 'ada_ot_allowance',
             'bilangan_staff_non_medical', 'waktu_beroperasi', 'cara_minta_cuti', 'isu_penempatan']
K3_FIELDS = ['jenis_perkhidmatan', 'anggaran_pelawat_harian', 'jenis_penyakit_kerap',
             'boleh_selesaikan_kes', 'rujukan_ke', 'ada_ruang_rehat', 'ada_hemodialisis',
             'unit_hemodialisis', 'bekalan_ubat_mencukupi', 'keperluan_oksigen', 'ada_emr',
             'wad_diasingkan', 'kualiti_makanan', 'siapa_manage', 'masa_tunggu', 'ada_osca']
K4_FIELDS = ['disposable_mencukupi', 'keadaan_aset', 'ada_ambulans', 'keadaan_ambulans',
             'aset_perlu_diganti', 'aset_tidak_ikut_spec', 'umur_komputer']
K5_FIELDS = ['keadaan_perabot', 'ada_quarters', 'quarters_mencukupi', 'ada_isu_parking',
             'masalah_aircond', 'ruang_kerja_mencukupi', 'ada_bilik_mayat', 'ada_pantry',
             'ada_kantin', 'ada_security']
K6_FIELDS = ['perkhidmatan_baru', 'fasiliti_diperlukan']
K7_FIELDS = ['maintenance_okay', 'masalah_utama', 'wishlist']


def migrate_clusters_forward(apps, schema_editor):
    FacilityProfile        = apps.get_model('home', 'FacilityProfile')
    KlusterKejuruteraan    = apps.get_model('home', 'KlusterKejuruteraan')
    KlusterSumberManusia   = apps.get_model('home', 'KlusterSumberManusia')
    KlusterPerkhidmatan    = apps.get_model('home', 'KlusterPerkhidmatan')
    KlusterAset            = apps.get_model('home', 'KlusterAset')
    KlusterFasiliti        = apps.get_model('home', 'KlusterFasiliti')
    KlusterPerancangan     = apps.get_model('home', 'KlusterPerancangan')
    KlusterKonsesi         = apps.get_model('home', 'KlusterKonsesi')

    STEP_MODEL = [
        (K1_FIELDS, KlusterKejuruteraan,  'k_kejuruteraan'),
        (K2_FIELDS, KlusterSumberManusia, 'k_sumber_manusia'),
        (K3_FIELDS, KlusterPerkhidmatan,  'k_perkhidmatan'),
        (K4_FIELDS, KlusterAset,          'k_aset'),
        (K5_FIELDS, KlusterFasiliti,      'k_fasiliti'),
        (K6_FIELDS, KlusterPerancangan,   'k_perancangan'),
        (K7_FIELDS, KlusterKonsesi,       'k_konsesi'),
    ]

    for fp in FacilityProfile.objects.all():
        for fields, Model, attr in STEP_MODEL:
            kwargs = {f: getattr(fp, f, None) for f in fields}
            obj = Model.objects.create(**kwargs)
            setattr(fp, attr, obj)
        fp.save(update_fields=[attr for _, _, attr in STEP_MODEL])


def migrate_clusters_reverse(apps, schema_editor):
    """Best-effort reverse: copy data back to FacilityProfile flat fields."""
    FacilityProfile = apps.get_model('home', 'FacilityProfile')
    STEP_ATTR_FIELDS = [
        ('k_kejuruteraan',  K1_FIELDS),
        ('k_sumber_manusia', K2_FIELDS),
        ('k_perkhidmatan',  K3_FIELDS),
        ('k_aset',          K4_FIELDS),
        ('k_fasiliti',      K5_FIELDS),
        ('k_perancangan',   K6_FIELDS),
        ('k_konsesi',       K7_FIELDS),
    ]
    for fp in FacilityProfile.objects.all():
        update_fields = []
        for attr, fields in STEP_ATTR_FIELDS:
            obj = getattr(fp, attr, None)
            if not obj:
                continue
            for f in fields:
                setattr(fp, f, getattr(obj, f, None))
                update_fields.append(f)
        if update_fields:
            fp.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_maklumatAsas'),
    ]

    operations = [

        # ── 1. Cipta 7 table kluster baru ────────────────────────

        migrations.CreateModel(
            name='KlusterKejuruteraan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tahun_dibina',          models.IntegerField(blank=True, null=True, verbose_name='Q1 – Tahun Dibina')),
                ('jenis_hospital_klinik', models.CharField(blank=True, max_length=200, verbose_name='Q2 – Jenis Hospital/Klinik')),
                ('siling_okay',           models.BooleanField(blank=True, null=True, verbose_name='Q32 – Siling Okay?')),
                ('ukuran_tanah',          models.TextField(blank=True, verbose_name='Q29 – Ukuran Tanah & Boleh Extend?')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'K1 – Kejuruteraan', 'verbose_name_plural': 'K1 – Kejuruteraan'},
        ),
        migrations.CreateModel(
            name='KlusterSumberManusia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kakitangan_tetap',            models.IntegerField(blank=True, null=True, verbose_name='Q3 – Kakitangan Tetap')),
                ('kakitangan_kontrak',          models.IntegerField(blank=True, null=True, verbose_name='Q3 – Kakitangan Kontrak')),
                ('kakitangan_mystep',           models.IntegerField(blank=True, null=True, verbose_name='Q3 – Kakitangan MySTeP')),
                ('ada_kakitangan_pinjaman',     models.BooleanField(blank=True, null=True, verbose_name='Q16 – Ada Staff Pinjaman?')),
                ('bilangan_shift',              models.IntegerField(blank=True, null=True, verbose_name='Q21/Q39 – Bilangan Shift Sehari')),
                ('ada_ot_allowance',            models.BooleanField(blank=True, null=True, verbose_name='Q38 – Ada OT/Allowance?')),
                ('bilangan_staff_non_medical',  models.IntegerField(blank=True, null=True, verbose_name='Q47 – Bil. Staff Non-Medical/Admin')),
                ('waktu_beroperasi',            models.CharField(blank=True, max_length=200, verbose_name='Q43 – Waktu Beroperasi')),
                ('cara_minta_cuti',             models.TextField(blank=True, verbose_name='Q42 – Cara Minta Cuti & Rotasi')),
                ('isu_penempatan',              models.TextField(blank=True, verbose_name='Q36 – Isu Penempatan Staff')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'K2 – Sumber Manusia', 'verbose_name_plural': 'K2 – Sumber Manusia'},
        ),
        migrations.CreateModel(
            name='KlusterPerkhidmatan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jenis_perkhidmatan',      models.TextField(blank=True, verbose_name='Q4 – Jenis Perkhidmatan')),
                ('anggaran_pelawat_harian', models.IntegerField(blank=True, null=True, verbose_name='Q5 – Anggaran Pelawat Harian')),
                ('jenis_penyakit_kerap',    models.TextField(blank=True, verbose_name='Q6 – Jenis Penyakit Kerap')),
                ('boleh_selesaikan_kes',    models.BooleanField(blank=True, null=True, verbose_name='Q7 – Boleh Selesaikan Kes?')),
                ('rujukan_ke',              models.CharField(blank=True, max_length=200, verbose_name='Q7 – Rujuk ke Mana?')),
                ('ada_ruang_rehat',         models.BooleanField(blank=True, null=True, verbose_name='Q8 – Ada Ruang Rehat?')),
                ('ada_hemodialisis',        models.BooleanField(blank=True, null=True, verbose_name='Q9 – Ada Hemodialisis?')),
                ('unit_hemodialisis',       models.IntegerField(blank=True, null=True, verbose_name='Q9 – Bil. Unit Hemodialisis')),
                ('bekalan_ubat_mencukupi',  models.BooleanField(blank=True, null=True, verbose_name='Q10/Q20 – Bekalan Ubat Mencukupi?')),
                ('keperluan_oksigen',       models.TextField(blank=True, verbose_name='Q27 – Keperluan Oksigen')),
                ('ada_emr',                 models.BooleanField(blank=True, null=True, verbose_name='Q30 – Ada EMR?')),
                ('wad_diasingkan',          models.BooleanField(blank=True, null=True, verbose_name='Q34 – Wad Diasingkan?')),
                ('kualiti_makanan',         models.TextField(blank=True, verbose_name='Q35 – Kualiti Makanan')),
                ('siapa_manage',            models.CharField(blank=True, max_length=200, verbose_name='Q37 – Siapa In-Charge?')),
                ('masa_tunggu',             models.CharField(blank=True, max_length=100, verbose_name='Q46 – Masa Tunggu')),
                ('ada_osca',                models.BooleanField(blank=True, null=True, verbose_name='Q48 – Ada OSCA?')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'K3 – Perkhidmatan Kesihatan', 'verbose_name_plural': 'K3 – Perkhidmatan Kesihatan'},
        ),
        migrations.CreateModel(
            name='KlusterAset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disposable_mencukupi', models.BooleanField(blank=True, null=True, verbose_name='Q11 – Disposable Mencukupi?')),
                ('keadaan_aset',         models.TextField(blank=True, verbose_name='Q12 – Keadaan Aset')),
                ('ada_ambulans',         models.BooleanField(blank=True, null=True, verbose_name='Q15 – Ada Ambulans?')),
                ('keadaan_ambulans',     models.TextField(blank=True, verbose_name='Q15 – Keadaan Ambulans')),
                ('aset_perlu_diganti',   models.TextField(blank=True, verbose_name='Q24 – Aset Perlu Diganti')),
                ('aset_tidak_ikut_spec', models.TextField(blank=True, verbose_name='Q25 – Aset Tidak Ikut Spec KKM')),
                ('umur_komputer',        models.TextField(blank=True, verbose_name='Q31 – Umur Komputer')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'K4 – Aset', 'verbose_name_plural': 'K4 – Aset'},
        ),
        migrations.CreateModel(
            name='KlusterFasiliti',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keadaan_perabot',       models.TextField(blank=True, verbose_name='Q13 – Keadaan Perabot/Infrastruktur')),
                ('ada_quarters',          models.BooleanField(blank=True, null=True, verbose_name='Q14 – Ada Quarters?')),
                ('quarters_mencukupi',    models.BooleanField(blank=True, null=True, verbose_name='Q14 – Quarters Mencukupi?')),
                ('ada_isu_parking',       models.BooleanField(blank=True, null=True, verbose_name='Q22/Q40 – Ada Isu Parking?')),
                ('masalah_aircond',       models.BooleanField(blank=True, null=True, verbose_name='Q23/Q41 – Masalah Aircond?')),
                ('ruang_kerja_mencukupi', models.BooleanField(blank=True, null=True, verbose_name='Q26 – Ruang Kerja Mencukupi?')),
                ('ada_bilik_mayat',       models.BooleanField(blank=True, null=True, verbose_name='Q33 – Ada Bilik Mayat?')),
                ('ada_pantry',            models.BooleanField(blank=True, null=True, verbose_name='Q29b – Ada Kawasan Rehat?')),
                ('ada_kantin',            models.BooleanField(blank=True, null=True, verbose_name='Q44 – Ada Kantin?')),
                ('ada_security',          models.BooleanField(blank=True, null=True, verbose_name='Q45 – Ada Security?')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'K5 – Fasiliti Fizikal', 'verbose_name_plural': 'K5 – Fasiliti Fizikal'},
        ),
        migrations.CreateModel(
            name='KlusterPerancangan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('perkhidmatan_baru',   models.TextField(blank=True, verbose_name='Q18 – Perkhidmatan Baru')),
                ('fasiliti_diperlukan', models.TextField(blank=True, verbose_name='Q19 – Fasiliti Diperlukan')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'K6 – Perancangan', 'verbose_name_plural': 'K6 – Perancangan'},
        ),
        migrations.CreateModel(
            name='KlusterKonsesi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_okay', models.BooleanField(blank=True, null=True, verbose_name='Q28 – Maintenance Konsesi OK?')),
                ('masalah_utama',    models.TextField(blank=True, verbose_name='Q17 – Masalah Utama')),
                ('wishlist',         models.TextField(blank=True, verbose_name='Q17a – Wishlist')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'K7 – Konsesi & Lain-lain', 'verbose_name_plural': 'K7 – Konsesi & Lain-lain'},
        ),

        # ── 2. Tambah 7 FK nullable ke FacilityProfile ───────────

        migrations.AddField(model_name='facilityprofile', name='k_kejuruteraan',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profil', to='home.klusterkejuruteraan', verbose_name='K1 – Kejuruteraan')),
        migrations.AddField(model_name='facilityprofile', name='k_sumber_manusia',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profil', to='home.klustersumbermanusia', verbose_name='K2 – Sumber Manusia')),
        migrations.AddField(model_name='facilityprofile', name='k_perkhidmatan',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profil', to='home.klusterperkhidmatan', verbose_name='K3 – Perkhidmatan')),
        migrations.AddField(model_name='facilityprofile', name='k_aset',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profil', to='home.klusteraset', verbose_name='K4 – Aset')),
        migrations.AddField(model_name='facilityprofile', name='k_fasiliti',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profil', to='home.klusterfasiliti', verbose_name='K5 – Fasiliti')),
        migrations.AddField(model_name='facilityprofile', name='k_perancangan',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profil', to='home.klusterperancangan', verbose_name='K6 – Perancangan')),
        migrations.AddField(model_name='facilityprofile', name='k_konsesi',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profil', to='home.klusterkonsesi', verbose_name='K7 – Konsesi')),

        # ── 3. Data migration ────────────────────────────────────
        migrations.RunPython(migrate_clusters_forward, migrate_clusters_reverse),

        # ── 4. Buang semua field kluster lama dari FacilityProfile ─
        migrations.RemoveField(model_name='facilityprofile', name='tahun_dibina'),
        migrations.RemoveField(model_name='facilityprofile', name='jenis_hospital_klinik'),
        migrations.RemoveField(model_name='facilityprofile', name='siling_okay'),
        migrations.RemoveField(model_name='facilityprofile', name='ukuran_tanah'),
        migrations.RemoveField(model_name='facilityprofile', name='kakitangan_tetap'),
        migrations.RemoveField(model_name='facilityprofile', name='kakitangan_kontrak'),
        migrations.RemoveField(model_name='facilityprofile', name='kakitangan_mystep'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_kakitangan_pinjaman'),
        migrations.RemoveField(model_name='facilityprofile', name='bilangan_shift'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_ot_allowance'),
        migrations.RemoveField(model_name='facilityprofile', name='bilangan_staff_non_medical'),
        migrations.RemoveField(model_name='facilityprofile', name='waktu_beroperasi'),
        migrations.RemoveField(model_name='facilityprofile', name='cara_minta_cuti'),
        migrations.RemoveField(model_name='facilityprofile', name='isu_penempatan'),
        migrations.RemoveField(model_name='facilityprofile', name='jenis_perkhidmatan'),
        migrations.RemoveField(model_name='facilityprofile', name='anggaran_pelawat_harian'),
        migrations.RemoveField(model_name='facilityprofile', name='jenis_penyakit_kerap'),
        migrations.RemoveField(model_name='facilityprofile', name='boleh_selesaikan_kes'),
        migrations.RemoveField(model_name='facilityprofile', name='rujukan_ke'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_ruang_rehat'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_hemodialisis'),
        migrations.RemoveField(model_name='facilityprofile', name='unit_hemodialisis'),
        migrations.RemoveField(model_name='facilityprofile', name='bekalan_ubat_mencukupi'),
        migrations.RemoveField(model_name='facilityprofile', name='keperluan_oksigen'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_emr'),
        migrations.RemoveField(model_name='facilityprofile', name='wad_diasingkan'),
        migrations.RemoveField(model_name='facilityprofile', name='kualiti_makanan'),
        migrations.RemoveField(model_name='facilityprofile', name='siapa_manage'),
        migrations.RemoveField(model_name='facilityprofile', name='masa_tunggu'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_osca'),
        migrations.RemoveField(model_name='facilityprofile', name='disposable_mencukupi'),
        migrations.RemoveField(model_name='facilityprofile', name='keadaan_aset'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_ambulans'),
        migrations.RemoveField(model_name='facilityprofile', name='keadaan_ambulans'),
        migrations.RemoveField(model_name='facilityprofile', name='aset_perlu_diganti'),
        migrations.RemoveField(model_name='facilityprofile', name='aset_tidak_ikut_spec'),
        migrations.RemoveField(model_name='facilityprofile', name='umur_komputer'),
        migrations.RemoveField(model_name='facilityprofile', name='keadaan_perabot'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_quarters'),
        migrations.RemoveField(model_name='facilityprofile', name='quarters_mencukupi'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_isu_parking'),
        migrations.RemoveField(model_name='facilityprofile', name='masalah_aircond'),
        migrations.RemoveField(model_name='facilityprofile', name='ruang_kerja_mencukupi'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_bilik_mayat'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_pantry'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_kantin'),
        migrations.RemoveField(model_name='facilityprofile', name='ada_security'),
        migrations.RemoveField(model_name='facilityprofile', name='perkhidmatan_baru'),
        migrations.RemoveField(model_name='facilityprofile', name='fasiliti_diperlukan'),
        migrations.RemoveField(model_name='facilityprofile', name='maintenance_okay'),
        migrations.RemoveField(model_name='facilityprofile', name='masalah_utama'),
        migrations.RemoveField(model_name='facilityprofile', name='wishlist'),
    ]
