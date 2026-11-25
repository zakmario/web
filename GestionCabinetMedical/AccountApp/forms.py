from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Patient


class BootstrapFormMixin:
    """Ajoute les classes CSS Bootstrap aux widgets du formulaire."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css_class = 'form-select'
            elif isinstance(widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            else:
                css_class = 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css_class}".strip()


class PatientRegistrationForm(BootstrapFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Patient
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'national_id', 'phone', 'birth_date',
        )
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('first_name', 'last_name', 'email'):
            self.fields[name].required = True

    def clean_username(self):
        # L'unicité du nom d'utilisateur porte sur tous les utilisateurs (médecins inclus)
        username = self.cleaned_data.get('username')
        if username and get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username
