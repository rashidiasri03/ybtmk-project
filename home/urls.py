from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('bahagian/', views.bahagian_view, name='bahagian'),
    path('tm/', views.tm_portal, name='tm_portal'),
    path('profiling/<int:pk>/modul/', views.pilih_modul, name='pilih_modul'),
    path('profiling/<int:pk>/lawatan/', views.kemaskini_status_lawatan, name='kemaskini_lawatan'),
    
    # Superadmin panel
    path('superadmin/', views.superadmin, name='superadmin'),
    
    # User management (admin only)
    path('urus-pengguna/', views.urus_pengguna, name='urus_pengguna'),
    path('urus-pengguna/tambah/', views.tambah_pengguna, name='tambah_pengguna'),
    path('urus-pengguna/<int:user_id>/edit/', views.edit_pengguna, name='edit_pengguna'),
    path('urus-pengguna/<int:user_id>/padam/', views.padam_pengguna, name='padam_pengguna'),
    
    # User self-profile
    path('profil/', views.profil_saya, name='profil_saya'),
    path('profil/edit/', views.edit_profil, name='edit_profil'),
    
    # Hospital & Klinik Profiling (Asas)
    path('profiling/', views.bahagian_fasiliti, name='bahagian_fasiliti'),
    path('profiling/senarai/', views.senarai_fasiliti, name='senarai_fasiliti'),
    path('profiling/tambah/', views.tambah_fasiliti, name='tambah_fasiliti'),
    path('profiling/<int:pk>/edit/', views.edit_fasiliti, name='edit_fasiliti'),
    path('profiling/<int:pk>/padam/', views.padam_fasiliti, name='padam_fasiliti'),
    path('profiling/dashboard/', views.dashboard_fasiliti, name='dashboard_fasiliti'),
    path('profiling/<int:pk>/detail/', views.detail_fasiliti, name='detail_fasiliti'),
    path('profiling/<int:pk>/api/', views.fasiliti_api_detail, name='fasiliti_api_detail'),
    path('profiling/<int:pk>/status/', views.tukar_status_fasiliti, name='tukar_status_fasiliti'),
    path('profiling/peta/', views.peta_fasiliti, name='peta_fasiliti'),
    path('profiling/peta-tm/', views.peta_tm, name='peta_tm'),
    
    # Borang Ringkas (soalan terpilih)
    path('profiling/ringkas/tambah/', views.tambah_fasiliti_ringkas, name='tambah_fasiliti_ringkas'),
    path('profiling/ringkas/<int:pk>/edit/', views.edit_fasiliti_ringkas, name='edit_fasiliti_ringkas'),

    # LALUAN PENGURUSAN SOALAN DINAMIK (ADMIN)
    path('urus-soalan-tambahan/', views.urus_soalan_tambahan, name='urus_soalan_tambahan'),
    path('padam-soalan-tambahan/<int:pk>/', views.padam_soalan_tambahan, name='padam_soalan_tambahan'),

    # Laluan Aset Kenderaan
    path('aset-kenderaan/', views.aset_kenderaan_list, name='aset_kenderaan_list'),
    path('aset-kenderaan/<int:pk>/detail/', views.detail_kenderaan, name='detail_kenderaan'),
    path('aset-kenderaan/tambah/', views.tambah_kenderaan, name='tambah_kenderaan'),
    path('aset-kenderaan/<int:pk>/edit/', views.edit_kenderaan, name='edit_kenderaan'),
    path('aset-kenderaan/<int:pk>/padam/', views.padam_kenderaan, name='padam_kenderaan'),

    # ══════════════════════════════════════════════════════════════════
    # 7 MODUL PROFILING BAHARU
    # ══════════════════════════════════════════════════════════════════
    path('profiling/latar-belakang/<int:pk>/edit/', views.edit_latar_belakang, name='edit_latar_belakang'),
    path('profiling/infrastruktur/<int:pk>/edit/', views.edit_infrastruktur, name='edit_infrastruktur'),
    path('profiling/aset-perubatan/<int:pk>/edit/', views.edit_aset_perubatan, name='edit_aset_perubatan'),
    path('profiling/sumber-manusia/<int:pk>/edit/', views.edit_pengurusan_sumber_manusia, name='edit_pengurusan_sumber_manusia'),
    path('profiling/perkhidmatan/<int:pk>/edit/', views.edit_penyampaian_perkhidmatan, name='edit_penyampaian_perkhidmatan'),
    path('profiling/kewangan-perancangan/<int:pk>/edit/', views.edit_kewangan_perancangan, name='edit_kewangan_perancangan'),
    path('profiling/digital/<int:pk>/edit/', views.edit_sistem_digital, name='edit_sistem_digital'),
]