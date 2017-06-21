from django.contrib.auth.password_validation import validate_password
from django import forms

from account.models import EcommerceUser, Account
from account.connectors.idp_interface import email_exists

from django.core.exceptions import ObjectDoesNotExist


class RegisterUserForm(forms.ModelForm):

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(),
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput()
    )

    class Meta:
        fields = ('first_name', 'last_name', 'email', 'phone_number')
        model = EcommerceUser

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email_exists(email):
            raise forms.ValidationError('A Gluu account with this email already exists.')
        return email

    def clean_password1(self):

        password1 = self.cleaned_data.get('password1')
        validate_password(password1)
        return password1

    def clean(self):

        cleaned_data = super(RegisterUserForm, self).clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords don\'t match')


class RegisterInvitedUserForm(RegisterUserForm):

    email = forms.EmailField(
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )


class RegisterAccountForm(forms.ModelForm):

    class Meta:
        fields = ('country', 'business_name', 'address_1',
                  'address_2', 'city', 'state', 'zip_code')

        model = Account


class EditAccountForm(forms.ModelForm):

    class Meta:
        fields = ('business_name', 'address_1',
                  'address_2', 'city', 'state', 'zip_code')

        model = Account


class InvitationForm(forms.Form):

    email = forms.EmailField(max_length=100)


class PremiumInvitationAdminForm(forms.ModelForm):

    def clean_email(self):

        email = self.cleaned_data['email']
        try:
            EcommerceUser.objects.get(email=email)
            raise forms.ValidationError('This user is already registered in the system')

        except ObjectDoesNotExist:
            pass

        return email
