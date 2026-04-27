from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('bahagian/', views.bahagian_view, name='bahagian'),
    path('tm/', views.tm_portal, name='tm_portal'),
    path('profiling/<int:pk>/modul/', views.pilih_modul, name='pilih_modul'),
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
    # Hospital & Klinik Profiling
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
    # Borang Sumber Manusia
    path('profiling/sm/tambah/', views.tambah_sumber_manusia, name='tambah_sumber_manusia'),
    path('profiling/sm/<int:pk>/edit/', views.edit_sumber_manusia, name='edit_sumber_manusia'),
    # Borang Aset, Servis, Ubat, Pesakit
    path('profiling/aset/<int:pk>/edit/', views.edit_aset, name='edit_aset'),
    path('profiling/servis/<int:pk>/edit/', views.edit_servis, name='edit_servis'),
    path('profiling/ubat/<int:pk>/edit/', views.edit_ubat, name='edit_ubat'),
    path('profiling/pesakit/<int:pk>/edit/', views.edit_pesakit, name='edit_pesakit'),
]
