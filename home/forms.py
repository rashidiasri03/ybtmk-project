from django import forms
from .models import AsetKenderaan, FacilityProfile

class AsetKenderaanForm(forms.ModelForm):
    class Meta:
        model = AsetKenderaan
        fields = ['profil_fasiliti', 'jenis_kenderaan', 'model_kenderaan', 'no_pendaftaran', 'no_chasis', 'tahun_diterima', 'status', 'syarikat_servis']
        widgets = {
            'profil_fasiliti': forms.Select(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none'}),
            'jenis_kenderaan': forms.Select(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none'}),
            'model_kenderaan': forms.TextInput(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none', 'placeholder': 'Cth: Toyota Hiace'}),
            'no_pendaftaran': forms.TextInput(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none', 'placeholder': 'Cth: WAA 1234'}),
            'no_chasis': forms.TextInput(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none'}),
            'tahun_diterima': forms.NumberInput(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none', 'placeholder': 'Cth: 2018'}),
            'status': forms.Select(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none'}),
            'syarikat_servis': forms.Select(attrs={'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-400 outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AsetKenderaanForm, self).__init__(*args, **kwargs)
        
        # Tapisan dropdown Fasiliti mengikut peranan pengguna
        if user:
            if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_top_management):
                self.fields['profil_fasiliti'].queryset = FacilityProfile.objects.all()
            elif hasattr(user, 'profile') and user.profile.is_jkn:
                self.fields['profil_fasiliti'].queryset = FacilityProfile.objects.filter(
                    maklumat_asas__nama_fasiliti__in=user.profile.assigned_facility_names
                )
            else:
                self.fields['profil_fasiliti'].queryset = FacilityProfile.objects.filter(submitted_by=user)
                
        self.fields['profil_fasiliti'].label_from_instance = lambda obj: obj.maklumat_asas.nama_fasiliti if obj.maklumat_asas else f"Fasiliti ID {obj.id}"