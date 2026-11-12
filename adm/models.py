from django.db import models
from acc.models import VoterManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image as PILImage
from io import BytesIO
import os



class College(models.Model):
    name = models.CharField(max_length=100, unique=True)
    initials = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name

class Voter(AbstractUser):
    USER_TYPE = ((1, _("Admin")), (2, _("Voter")))
    
    username = models.CharField(_("username"), max_length=12, unique=True)
    user_type = models.CharField(
        _("User Type"), choices=USER_TYPE, max_length=1, default=2)
    
    first_name = models.CharField(_("First Name"), max_length=30)
    last_name = models.CharField(_("Last Name"), max_length=30)
    middle_name = models.CharField(_("Middle Name"), max_length=30, null=True,  blank=True)
    
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    voted = models.BooleanField(_("Voted"), default=False)
    first_time_login = models.BooleanField(_("First Time Login"), default=True)
    print_password = models.CharField(_("Print Password"), max_length=20)
    photo = models.ImageField(upload_to="voter_photos/", default="voter_photos/default_photo.jpg")
    
    company = models.CharField(_("Company"), max_length = 200)
    address = models.CharField(_("Address"), max_length = 200)

    objects = VoterManager()

    def get_middle_initial(self):  
        middle_name = self.middle_name
        if middle_name:
            return f"{middle_name[0].upper()}."
        else:
            middle_name = self.middle_name

    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.get_middle_initial()}"
    
class Position(models.Model):
    name = models.CharField(max_length=100, unique=True)
    max_vote = models.IntegerField()
    priority = models.IntegerField()
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            self.priority = Position.objects.count() + 1
        super(Position, self).save(*args, **kwargs)
        
    
    def __str__(self):
        return self.name

class PartyList(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

def set_default_party():
    name = "Independent"
    party, created = PartyList.objects.get_or_create(name = name)

class Candidate(models.Model):
    fullname = models.CharField(max_length=100, unique=True)
    party_list = models.ForeignKey(PartyList, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to="candidates_photos/", default="defaults/default_photo.jpg") 
    
    def __str__(self):
        return self.fullname
    
    

class Election(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null = True) 
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null = True)

