from django import forms
from adm.forms import FormSettings
from adm. models import Voter
from django.contrib.auth import authenticate


class RegistrationForm(FormSettings):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Voter
        fields = ['username', 'first_name', 'middle_name', 'last_name', 'college']
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password1')
        confirm_password = cleaned_data.get('password2')
        if password != confirm_password and confirm_password != password:
            raise forms.ValidationError("Password do not match")
        return cleaned_data
        
class LoginForm(forms.Form):
    username = forms.CharField(max_length = 255)
    password = forms.CharField(max_length =255, widget=forms.PasswordInput)
    
    def clean(self):

        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        
        if not username or not password:
            raise forms.ValidationError('Both username and password are required')

        try:
            user = Voter.objects.get(username=username) or Voter.objects.get(email=username)
        except Voter.DoesNotExist:
            raise forms.ValidationError('Invalid username or email')

        if not user.check_password(password):
            raise forms.ValidationError('Invalid password')

        return self.cleaned_data
        