from django import forms
from user_profile_api.models import UserProfile

class UserProfileAdminForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserProfileAdminForm, self).__init__(*args, **kwargs)

        # Excluye la opción 'Bloqueado' al agregar un nuevo usuario
        if not self.instance.pk:
            self.fields['profile_type'].choices = [choice for choice in self.fields['profile_type'].choices if choice[0] != 'blackList']

