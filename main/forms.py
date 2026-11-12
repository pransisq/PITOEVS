
from adm.forms import FormSettings
from django import forms
from django.conf import settings
from adm.models import Voter



class UpdateUserForm(FormSettings):
    class Meta:
        model = Voter
        fields = ['username', 'first_name', 'last_name', 'middle_name', 'address',]
        
        