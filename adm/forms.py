from django import forms
from django.shortcuts import redirect
from django.conf import settings
from . models import *
from django.contrib.auth.hashers import make_password
import pandas as pd



class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        for field in self.visible_fields():
            if field.name == 'photo':
                field.field.widget.attrs['class'] = 'photo'
            else:
                field.field.widget.attrs['class'] = 'form-control'
                field.field.widget.attrs['placeholder'] = field.label
                
class UpdateAdminForm(FormSettings):
    class Meta:
        model = Voter
        fields = ['company', 'username', 'email', 'first_name', 'middle_name', 'last_name', 'address']
        

class VoterForm(FormSettings):
    class Meta:
        model = Voter
        fields = ['college','username', 'first_name', 'middle_name', 'last_name',]
        
class CollegeForm(FormSettings):
    class Meta:
        model = College
        fields = ['name', 'initials']

class UpdateVoterForm(FormSettings):
    class Meta:
        model = Voter
        fields = ['username', 'first_name', 'middle_name',  'last_name', 'college']

class PositionForm(FormSettings):
    class Meta:
        model = Position
        fields = ['name','max_vote', 'college']
        
class CandidateForm(FormSettings):
    position = forms.ModelChoiceField(queryset=Position.objects.all(), initial=lambda: Position.objects.first())
    party_list = forms.ModelChoiceField(queryset=PartyList.objects.all(), initial=lambda: PartyList.objects.first())

    class Meta:
        model = Candidate
        fields = ['party_list', 'fullname', 'position']
        
        
class PartyListForm(FormSettings): 
    class Meta:
        model = PartyList
        fields = '__all__'


class PasswordChangeForm(forms.ModelForm):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Voter
        fields = []
        
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password != confirm_password:
            raise forms.ValidationError("New Password and Confirm Password do not match")
        return cleaned_data