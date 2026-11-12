from django.urls import path
from . import views


urlpatterns = [

    path('ballot/fetch/', views.fetch_ballot, name = 'fetch_ballot'),
    path("dashboard/", views.voter_dashboard, name = "voter_dashboard"),
    path('ballot/vote', views.show_ballot, name = 'show_ballot'),
    path('ballot/vote/preview', views.preview_vote, name = 'preview_vote'),
    path('ballot/vote/submit', views.submit_ballot, name = 'submit_ballot'),

   
    path('voter/profile/', views.user_profile, name = "user_profile"),
    
    path('voter/profile/password', views.update_user_password, name = "update_user_password"),
    path("voter/profile/photo" ,views.update_user_photo, name="update_user_photo"),
    
]
