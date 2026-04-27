"""
Migration: Pisahkan Maklumat Asas ke table berasingan.

Langkah:
1. Cipta table home_maklumatAsas
2. Tambah FK nullable (maklumat_asas_id) pada FacilityProfile
3. Data migration: salin nama_fasiliti/jenis/negeri/daerah ke baris MaklumatAsas baru
4. Buang 4 field lama dari FacilityProfile
"""

from django.db import migrations, models
import django.db.models.deletion


def migrate_asas_forward(apps, schema_editor):
    """Cipta baris MaklumatAsas dari data FacilityProfile sedia ada."""
    FacilityProfile = apps.get_model('home', 'FacilityProfile')
    MaklumatAsas    = apps.get_model('home', 'MaklumatAsas')
    for fp in FacilityProfile.objects.all():
        ma = MaklumatAsas.objects.create(
            nama_fasiliti  = fp.nama_fasiliti  or '',
            jenis_fasiliti = fp.jenis_fasiliti or '',
            negeri         = fp.negeri         or '',
            daerah         = fp.daerah         or '',
        )
        fp.maklumat_asas = ma
        fp.save(update_fields=['maklumat_asas'])


def migrate_asas_reverse(apps, schema_editor):
    """Reverse: salin data balik ke FacilityProfile (best-effort)."""
    FacilityProfile = apps.get_model('home', 'FacilityProfile')
    for fp in FacilityProfile.objects.select_related('maklumat_asas').all():
        if fp.maklumat_asas:
            fp.nama_fasiliti  = fp.maklumat_asas.nama_fasiliti
            fp.jenis_fasiliti = fp.maklumat_asas.jenis_fasiliti
            fp.negeri         = fp.maklumat_asas.negeri
            fp.daerah         = fp.maklumat_asas.daerah
            fp.save(update_fields=['nama_fasiliti', 'jenis_fasiliti', 'negeri', 'daerah'])


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_facilityprofile'),
    ]

    operations = [
        # ── 1. Cipta table MaklumatAsas ──────────────────────────
        migrations.CreateModel(
            name='MaklumatAsas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama_fasiliti',  models.CharField(max_length=200, verbose_name='Nama Fasiliti')),
                ('jenis_fasiliti', models.CharField(
                    max_length=30,
                    choices=[
                        ('hospital', 'Hospital'), ('hospital_pakar', 'Hospital Pakar'),
                        ('klinik_kesihatan', 'Klinik Kesihatan'), ('klinik_desa', 'Klinik Desa'),
                        ('klinik_komuniti', 'Klinik Komuniti'), ('lain', 'Lain-lain'),
                    ],
                    verbose_name='Jenis Fasiliti',
                )),
                ('negeri', models.CharField(
                    max_length=30,
                    choices=[
                        ('johor', 'Johor'), ('kedah', 'Kedah'), ('kelantan', 'Kelantan'),
                        ('melaka', 'Melaka'), ('negeri_sembilan', 'Negeri Sembilan'),
                        ('pahang', 'Pahang'), ('perak', 'Perak'), ('perlis', 'Perlis'),
                        ('pulau_pinang', 'Pulau Pinang'), ('sabah', 'Sabah'),
                        ('sarawak', 'Sarawak'), ('selangor', 'Selangor'),
                        ('terengganu', 'Terengganu'), ('wp_kl', 'W.P. Kuala Lumpur'),
                        ('wp_putrajaya', 'W.P. Putrajaya'), ('wp_labuan', 'W.P. Labuan'),
                    ],
                    verbose_name='Negeri',
                )),
                ('daerah',     models.CharField(max_length=100, verbose_name='Daerah/Bandar')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Maklumat Asas Fasiliti',
                'verbose_name_plural': 'Maklumat Asas Fasiliti',
            },
        ),

        # ── 2. Tambah FK nullable ke FacilityProfile ─────────────
        migrations.AddField(
            model_name='facilityprofile',
            name='maklumat_asas',
            field=models.OneToOneField(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='profil',
                to='home.maklumatAsas',
                verbose_name='Maklumat Asas',
            ),
        ),

        # ── 3. Data migration ────────────────────────────────────
        migrations.RunPython(migrate_asas_forward, migrate_asas_reverse),

        # ── 4. Buang 4 field lama ────────────────────────────────
        migrations.RemoveField(model_name='facilityprofile', name='nama_fasiliti'),
        migrations.RemoveField(model_name='facilityprofile', name='jenis_fasiliti'),
        migrations.RemoveField(model_name='facilityprofile', name='negeri'),
        migrations.RemoveField(model_name='facilityprofile', name='daerah'),
    ]
