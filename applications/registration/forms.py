import json
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import BusinessDetail, ContactPerson, CreditCard
from django.core.validators import RegexValidator

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
    country = forms.ChoiceField(label='Country', choices=[])
    city = forms.ChoiceField(label='City', choices=[])
    phone_code = forms.ChoiceField(label='Phone Code', choices=[])
    registration_number = forms.CharField(
        label='Registration Number',
        validators=[RegexValidator(r'^\d+$', 'Please enter only digits.')],
        widget=forms.TextInput(attrs={'placeholder': 'Enter registration number'})
    )

    kra_pin = forms.CharField(
        label='KRA PIN',
        validators=[RegexValidator(r'^\d+$', 'Please enter only digits.')],
        widget=forms.TextInput(attrs={'placeholder': 'Enter KRA PIN'})
    )
    phone_number = forms.CharField(
        label='Phone Number',
        validators=[RegexValidator(r'^\d{1,10}$', 'Please enter a valid phone number (up to 10 digits).')],
        widget=forms.TextInput(attrs={'placeholder': 'Enter phone number'})
    )

    registration_certificate = forms.FileField(
        label='Registration Certificate',
        widget=forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-input w-full text-sm text-grey-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-2 file:border-green-200 file:text-green-700 hover:file:border-green-400'})
    )

    trading_license = forms.FileField(
        label='Trading License',
        widget=forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-input w-full text-sm text-grey-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-2 file:border-green-200 file:text-green-700 hover:file:border-green-400'})
    )

    tax_compliance_certificate = forms.FileField(
        label='Tax Compliance Certificate',
        widget=forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-input w-full text-sm text-grey-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-2 file:border-green-200 file:text-green-700 hover:file:border-green-400'})
    )

    class Meta:
        model = BusinessDetail
        exclude = ('reference_number', 'status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load the JSON data for countries and cities
        with open('data.json', encoding='utf-8') as file:
            data = json.load(file)

            # Populate the country choices
            countries = [(country['country'], country['country']) for country in data]
            self.fields['country'].choices = [('', 'Select a country')] + countries

            # Load the JSON data for phone codes
            with open('phone_numbers.json') as phone_file:
                phone_data = json.load(phone_file)

                # Populate the phone code choices
                phone_codes = [(phone['code'], f"{phone['country']} (+{phone['code']})" ) for phone in phone_data]
                self.fields['phone_code'].choices = [('', 'Select a phone code')] + phone_codes

            # Style the country, city, and phone code fields with Tailwind CSS
            for field in ['country', 'city', 'phone_code']:
                self.fields[field].widget.attrs.update({
                    'class': 'form-input w-full border-2 border-green-200 focus:border-green-400 focus:ring-0 py-2 px-3 rounded-lg'
                })

            # Populate the city choices based on the selected country
            if self.data.get('country'):
                selected_country = next((country for country in data if country['country'] == self.data['country']), None)
                if selected_country:
                    cities = [(city, city) for city in selected_country['city']]
                    self.fields['city'].choices = [('', 'Select a city')] + cities
                else:
                    self.fields['city'].choices = [('', 'Select a city')]
            else:
                # Set initial empty choices for city
                self.fields['city'].choices = [('', 'Select a city')]
        
class ContactPersonForm(forms.ModelForm):
    mobile_number = forms.CharField(
        label='Mobile Number',
        validators=[RegexValidator(r'^\d{1,15}$', 'Please enter a valid mobile number (up to 15 digits).')],
        widget=forms.TextInput(attrs={'placeholder': 'Enter mobile number'})
    )

    class Meta:
        model = ContactPerson
        fields = ['first_name', 'last_name', 'mobile_number', 'email_address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['mobile_number'].required = False
        self.fields['email_address'].required = False

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        mobile_number = cleaned_data.get('mobile_number')
        email_address = cleaned_data.get('email_address')

        # Check if any field is filled
        if any([first_name, last_name, mobile_number, email_address]):
            # If any field is filled, make all fields required
            if not all([first_name, last_name, mobile_number, email_address]):
                raise forms.ValidationError("Please fill in all fields for the contact or leave them all empty.")

        return cleaned_data

class CreditCardForm(forms.ModelForm):
    last_8_digits = forms.CharField(
        label='Last 8 Digits',
        validators=[RegexValidator(r'^\d{8}$', 'Please enter a valid credit card number.')],
        widget=forms.TextInput(attrs={'placeholder': '12345678', 'maxlength': '8'})
    )

    class Meta:
        model = CreditCard
        fields = ['card_type', 'last_8_digits']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['card_type'].required = False
        self.fields['last_8_digits'].required = False

    def clean(self):
        cleaned_data = super().clean()
        card_type = cleaned_data.get('card_type')
        last_8_digits = cleaned_data.get('last_8_digits')

        if any([card_type, last_8_digits]):
            if not all([card_type, last_8_digits]):
                raise forms.ValidationError("Please fill in all fields for the credit card or leave them all empty.")

        return cleaned_data