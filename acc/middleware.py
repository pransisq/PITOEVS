from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect
import sweetify
from django.conf import settings

class AccountCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user

        if user.is_authenticated:
            if user.user_type == '1':  # Admin
                if modulename == 'main.views':
                    if request.path not in [reverse('fetch_ballot'), reverse('update_user_password'), reverse('user_profile')]:
                        sweetify.error(request, "You do not have access to this resource")
                        return redirect(reverse('admin_dashboard'))
            elif user.user_type == '2':  # Voter
                if modulename == 'adm.views':
                    if request.path not in [reverse('update_admin_password'), reverse('admin_profile')]:
                        sweetify.error(request, "You do not have access to this resource")
                        return redirect(reverse('voter_dashboard'))
            else:  # Redirect to login if user type is not recognized
                return redirect(reverse('login'))
        else:
            # If the path is login or has anything to do with authentication, pass
            if request.path in [reverse('login'), reverse('landingpage')] or modulename == 'django.contrib.auth.views':
                pass
            elif modulename in ['adm.views', 'main.views']:
                sweetify.error(request, "You need to be logged in to perform this operation")
                return redirect(reverse('login'))
            else:
                return redirect(reverse('login'))