# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser,ShippingAddress


GHANA_REGIONS = [
    ('', 'Select Region'),
    ('Ahafo', 'Ahafo'),
    ('Ashanti', 'Ashanti'),
    ('Bono', 'Bono'),
    ('Bono East', 'Bono East'),
    ('Central', 'Central'),
    ('Eastern', 'Eastern'),
    ('Greater Accra', 'Greater Accra'),
    ('North East', 'North East'),
    ('Northern', 'Northern'),
    ('Oti', 'Oti'),
    ('Savannah', 'Savannah'),
    ('Upper East', 'Upper East'),
    ('Upper West', 'Upper West'),
    ('Volta', 'Volta'),
    ('Western', 'Western'),
    ('Western North', 'Western North'),
]



class CustomUserCreationForm(UserCreationForm):
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        required=True,
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2', 'confirm_password']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        confirm_password = cleaned_data.get('confirm_password')

        if password1 and confirm_password and password1 != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
    


# forms.py
from django import forms
from .models import ShippingAddress
class ShippingAddressForm(forms.ModelForm):
    region = forms.ChoiceField(choices=GHANA_REGIONS, widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'phone', 'address_line_1', 'address_line_2', 'city', 'region', 'is_default']
        widgets = {
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }