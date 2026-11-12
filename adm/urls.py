from django.urls import path
from . import views

urlpatterns = [
    # * PROFILE

    path("administrator/profile/", views.adm_profile, name="admin_profile"),
    path("administrator/password/", views.update_admin_password, name="update_admin_password"),
    path("administrator/profile_photo/", views.update_admin_photo, name="update_admin_photo"),

    # * DASHBOARD DATA
    path("dashboard", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard_data", views.dashboard_data, name="dashboard_data"),
    path("chart_data", views.chart_data, name="chart_data"),
    path("reset_votes", views.reset_votes, name="reset_votes"),
    
    
    # * VOTERS
    path("voters", views.voters, name="voters"),
    path("voter/view", views.view_voter, name="view_voter"),
    path("voter/update", views.update_voter, name="update_voter"),
    path("voter/delete", views.delete_voter, name="delete_voter"),
    path("voters/upload", views.upload_voters, name="upload_voters"),
    path("voters/passwords", views.Passwords.as_view(), name="print_passwords"),
    path("voters/delete_all_voters", views.delete_all_voters, name="delete_all_voters"),
    path("get_colleges", views.get_colleges, name="get_colleges"),
    
    # * COLLEGE
    path("college/", views.college, name ="college"),
    path("college/view", views.view_college, name = "view_college"),
    path("update_collge/", views.update_college, name = "update_college"),
    path("delete_college/", views.delete_college, name ="delete_college"),
    path("delete_all_college/", views.delete_all_college, name="delete_all_college"),
    
    
    # *BALLOT CREATION
    path("election_settings/", views.election_settings, name = "election_settings"),

    # POSITIONS
    path("add_position", views.add_position, name = "add_position"),
    path("positions/view", views.view_position, name="view_position"),
    path("position/update", views.update_position, name="update_position"),
    path("position/delete", views.delete_position, name="delete_position"),
    path("positions/delete_all_pos", views.delete_all_positions, name="delete_all_positions"),
    path("get_positions", views.get_positions, name="get_positions"),
    
    
    # PARTIES

    path("add_party", views.add_party, name = "add_party"),
    path("party/update/", views.update_party, name="update_party"),
    path("party/delete/", views.delete_party, name="delete_party"),
    path("party/view", views.view_party_by_id, name="view_party"),
    path("party/delete_all_parties?/", views.delete_all_parties, name = "delete_all_parties"),
    path("get_parties", views.get_parties, name="get_parties"),

    
    # CANDIDATES
    path("add_candidate", views.add_candidate, name="add_candidate"),
    path("candidates/view", views.view_candidate, name="view_candidate"),
    path("candidate/update", views.update_candidate, name="update_candidate"),
    path("candidate/delete", views.delete_candidate, name="delete_candidate"),
    path("candidate/delete_all_candidates", views.delete_all_candidates, name="delete_all_candidates"),

    path("votes/print", views.PrintView.as_view(), name="print_results"),

    # * BALLOT POSITION
    path("ballot_position/", views.ballot_position, name="ballot_position"),
    path("ballot/title", views.ballot_title, name="ballot_title"),
    path("settings/ballot/position/update/<int:position_id>/<str:up_or_down>/", views.update_ballot_position, name='update_ballot_position'),
    path("reset_election/", views.reset_votes, name="reset_votes"),
    
]
