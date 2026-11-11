from django.contrib import admin
from .models import (
    MaklumatAsas, KlusterInfrastruktur, KlusterAsetPerubatan,
    KlusterSumberManusia, KlusterPerkhidmatan, KlusterKewangan, KlusterDigital,
    FacilityProfile, UserProfile, StafFasiliti, SyarikatServisKenderaan,
    AsetKenderaan, SoalanTambahan, JawapanSoalanTambahan
)

class StafFasilitiInline(admin.TabularInline):
    model = StafFasiliti
    extra = 0
    fields = ('nama_staf', 'skim', 'status_lantikan', 'tarikh_tamat_perkhidmatan')

@admin.register(KlusterSumberManusia)
class KlusterSumberManusiaAdmin(admin.ModelAdmin):
    list_display = ('id', 'jumlah_perjawatan', 'jumlah_pengisian', 'jumlah_kekosongan')
    inlines = [StafFasilitiInline]

@admin.register(StafFasiliti)
class StafFasilitiAdmin(admin.ModelAdmin):
    list_display = ('nama_staf', 'skim', 'status_lantikan', 'tarikh_tamat_perkhidmatan', 'kluster_sm_id')
    list_filter = ('skim', 'status_lantikan')
    search_fields = ('nama_staf', 'no_pengenalan')

@admin.register(FacilityProfile)
class FacilityProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'tahun', 'updated_at')
    list_filter = ('status', 'tahun', 'status_lawatan')
    search_fields = ('maklumat_asas__nama_fasiliti',)

# Daftar model-model lain untuk rujukan mudah
admin.site.register(MaklumatAsas)
admin.site.register(KlusterInfrastruktur)
admin.site.register(KlusterAsetPerubatan)
admin.site.register(KlusterPerkhidmatan)
admin.site.register(KlusterKewangan)
admin.site.register(KlusterDigital)
admin.site.register(UserProfile)
admin.site.register(SyarikatServisKenderaan)
admin.site.register(AsetKenderaan)
admin.site.register(SoalanTambahan)
admin.site.register(JawapanSoalanTambahan)