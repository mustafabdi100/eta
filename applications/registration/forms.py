from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import BusinessDetail, ContactPerson, CreditCard

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        # Remove help texts
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

class BusinessDetailForm(forms.ModelForm):
    class Meta:
        model = BusinessDetail
        exclude = ('reference_number', 'status')
        widgets = {
            'registration_certificate': forms.FileInput(),
            'trading_license': forms.FileInput(),
            'tax_compliance_certificate': forms.FileInput(),
        }

class ContactPersonForm(forms.ModelForm):
    class Meta:
        model = ContactPerson
        fields = ['first_name', 'last_name', 'mobile_number', 'email_address']

class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ['card_type', 'last_8_digits']
