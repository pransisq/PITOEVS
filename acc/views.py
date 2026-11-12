from django.shortcuts import render, redirect, reverse
from adm.models import *
from django.contrib.auth import authenticate, login, logout
import sweetify
from adm.models import *
from .forms import RegistrationForm, LoginForm
from django.utils.encoding import force_str


def landingpage(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            login(request, user)
            if request.user.user_type == '1':
                sweetify.success(request, "Login Successfully!")
                return redirect(reverse("admin_dashboard"))
            else:
                sweetify.success(request, "LoginSuccessfully!")
                return redirect(reverse("voters_dashboard"))
        else:
            sweetify.error(request, "Invalid username or password!")
    return render(request, "landingpage.html")

def account_login(request):
    context = {
        "page_title": "LOGIN"
    }
    if request.method == 'POST':
        user = authenticate(request, 
                            username=request.POST['username'], 
                            password=request.POST['password']
                            )
        if user is not None:
            login(request, user)
            if request.user.user_type == '1':
                if user.first_time_login == True:
                    set_default_party()
                    user.save()
                sweetify.success(request, "Login Successfully!")
                return redirect(reverse("admin_dashboard"))
            else:
                sweetify.success(request, 'Login Successfully!')
                return redirect(reverse("voter_dashboard"))
        else:
            sweetify.error(request, "Invalid Credentials!")
    return render(request, "acc/login.html", context)

def account_logout(request):
    user = request.user
    if user.is_authenticated:
        logout(request)
        sweetify.success(request, 'Success!')
    else:
        sweetify.error(
            request, "You need to be logged in to perform this action")
    return redirect(reverse("landingpage"))


