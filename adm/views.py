from multiprocessing import context
from django.shortcuts import render,reverse
from django.conf import settings
from acc. models import *
import secrets
from django.http import JsonResponse
from . forms import *
import sweetify
from urllib.parse import urlparse
from django.urls import resolve
from django_renderpdf.views import PDFView
from django.utils.encoding import force_str
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd


def find_n_winners(data, n):
    final_list = []
    candidate_data = data[:]
    for i in range(0, n):
        max1 = 0
        if len(candidate_data) == 0:
            continue
        this_winner = max(candidate_data, key=lambda x: x['votes'])
        this = this_winner['name'] + \
            " with " + str(this_winner['votes']) + " votes"
        final_list.append(this)
        candidate_data.remove(this_winner)
    return "<br>".join(final_list)

def admin_dashboard(request):
    positions = Position.objects.all().order_by('priority')
    chart_data = {}
    position_data = {}

    for position in positions:
        list_of_candidates = []
        votes_count = []
        candidates = Candidate.objects.filter(position=position)
        for candidate in candidates:
            list_of_candidates.append(candidate.fullname)
            votes = Election.objects.filter(candidate=candidate).count()
            votes_count.append(votes)
        chart_data[position] = {
            'candidates': list_of_candidates,
            'votes': votes_count,
            'pos_id': position.id
        }
        candidate_data = []
        winner = ""
        for candidate in Candidate.objects.filter(position=position):
            this_candidate_data = {}
            votes = Election.objects.filter(candidate=candidate).count()
            this_candidate_data['name'] = candidate.fullname
            this_candidate_data['votes'] = votes
            candidate_data.append(this_candidate_data)

        if candidate_data:
            if position.max_vote > 1:
                winner = find_n_winners(candidate_data, position.max_vote)
            else:
                max_votes = max(candidate_data, key=lambda x: x['votes'])[
                    'votes']
                winners = [
                    candidate for candidate in candidate_data if candidate['votes'] == max_votes]
                if len(winners) > 1:
                    winner = "Winners: " + \
                        "\n- " + "\n- ".join([winner['name']
                                             for winner in winners])
                else:
                    winner = "Winner: " + \
                        winners[0]['name'] if winners else "No one voted for this position yet!"

        position_data[position.name] = {
            'candidate_data': candidate_data,
            'winner': winner,
            'max_vote': position.max_vote
        }
    context = {
        'positions': positions,
        'chart_data': chart_data,
        'position_data': position_data,
        'page_title': 'DASHBOARD',
        'segment': 'admin',
    }

    return render(request, 'adm/dashboard.html', context)

def dashboard_data(request):
    positions = Position.objects.all().order_by('priority')
    candidates = Candidate.objects.all()
    voters = Voter.objects.exclude(is_superuser=True)
    voted_voters = Voter.objects.filter(voted=1)
    party = PartyList.objects.all()

    return JsonResponse({
        'position_count': positions.count(),
        'candidate_count': candidates.count(),
        'voters_count': voters.count(),
        'voted_voters_count': voted_voters.count(),
        'party_list_count': party.count(),
        'positions': list(positions.values_list('id', flat=True)),
    })

def chart_data(request):
    positions = Position.objects.all().order_by('priority')
    chart_data = {}

    for position in positions:
        list_of_candidates = []
        votes_count = []
        candidates = Candidate.objects.filter(position=position)
        for candidate in candidates:
            list_of_candidates.append(candidate.fullname)
            votes = Election.objects.filter(candidate=candidate).count()
            votes_count.append(votes)
        chart_data[position.id] = {
            'candidates': list_of_candidates,
            'votes': votes_count,
        }

    return JsonResponse(chart_data)



def adm_profile(request):
    if request.method =='POST':
        form = UpdateAdminForm(request.POST, instance = request.user)
        if form.is_valid():
            form.save()
            sweetify.success(request, "Success!")
            return redirect('admin_profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
    else:
        form = UpdateAdminForm(instance=request.user)
        
    context = {
        'page_title': "PROFILE",
        'segment' : 'profile',
        'form': form,
        }
    
    return render(request, "adm/profile.html",context)

def update_admin_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST, instance = request.user)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = form.cleaned_data['new_password']
            old_password = form.cleaned_data['old_password']
            if new_password:
                if request.user.check_password(old_password):
                    user.set_password(new_password)
                    user.save()
                    username = user.username
                    new_password = form.cleaned_data['new_password']
                    user = authenticate(username=username, password=new_password)
                    login(request,user)
                    sweetify.success(request, "Password Successfully Changed!")
                    return redirect(reverse("admin_profile"))
                    
                else:
                    sweetify.error(request, "Current Password is Incorrect!")
            else:
                user.save()
                sweetify.success(request, "Password Successfully Changed!")
        else:
            sweetify.error(request, "Invalid")
    else:
        sweetify.error(request, "Access Denied!")
    return redirect(reverse("admin_profile"))

def update_admin_photo(request):
    if request.method == 'POST' and request.FILES['photo']:
        user = request.user
        photo = request.FILES['photo']
    
        user.photo = photo  
        user.save()

        sweetify.success(request, 'Profile photo updated successfully!')
        return redirect(reverse('admin_profile'))  

    sweetify.error(request, 'Failed to update photo. Please try again.')
    return redirect(reverse('admin_profile')) 
    



class PrintView(PDFView):
    template_name = 'adm/print/results.html'
    prompt_download = True

    @property
    def download_name(self):
        return "result.pdf"

    def get_context_data(self, *args, **kwargs):
        title = ""
        try:
            file = open(settings.ELECTION_TITLE_PATH, 'r')
            title = file.read()
        except:
            pass
        context = super().get_context_data(*args, **kwargs)
        position_data = {}
        for position in Position.objects.all():
            candidate_data = []
            winner = ""
            for candidate in Candidate.objects.filter(position=position):
                this_candidate_data = {}
                votes = Election.objects.filter(candidate=candidate).count()
                this_candidate_data['name'] = candidate.fullname
                this_candidate_data['votes'] = votes
                candidate_data.append(this_candidate_data)
            if len(candidate_data) < 1:
                winner = "Position does not have candidates"
            else:
                if position.max_vote > 1:
                    winner = find_n_winners(candidate_data, position.max_vote)
                else:
                    winner = max(candidate_data, key=lambda x: x['votes'])
                    if winner['votes'] == 0:
                        winner = "No one voted for this yet position, yet."
                    else:
                        count = sum(1 for d in candidate_data if d.get(
                            'votes') == winner['votes'])
                        if count > 1:
                            winner = f"There are {count} candidates with {winner['votes']} votes"
                        else:
                            winner = "Winner : " + winner['name']
            position_data[position.name] = {
                'candidate_data': candidate_data, 'winner': winner, 'max_vote': position.max_vote}
        context['positions'] = position_data
        print(context)
        return context


class Passwords(PDFView):
    template_name = 'adm/print/passwords.html'
    prompt_download = True
    
    @property
    def download_name(self):
        return "passwords.pdf"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['voters'] = Voter.objects.exclude(is_superuser = True).all()
        return context    


def view_college(request):
    college_id = request.GET.get('college_id', None)
    college = College.objects.filter(id=college_id)
    context = {}
    if not college.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        college = college [0]
        context['name'] = college.name
        context['initials'] = college.initials
    return JsonResponse(context)


def view_voter(request):
    voter_id = request.GET.get('voter_id', None)
    voter = Voter.objects.filter(id=voter_id)
    context = {}
    if not voter.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        voter = voter[0]
        context['username'] = voter.username
        context['first_name'] = voter.first_name
        context['last_name'] = voter.last_name
        context['middle_name'] = voter.middle_name
        context['print_password'] = voter.print_password
        context['photo_url'] = voter.photo.url
        if voter.college:
            context['college'] = voter.college.id
        else:
            context['college'] = voter.college
        context['password'] = voter.password
    return JsonResponse(context)


def college(request):
    if request.method !='POST':
        sweetify.error(request, "Access Denied")
    try:
        form = CollegeForm(request.POST or None)
        if form.is_valid():
            college = form.save()
            sweetify.success(request, f"{str(college)} has been added!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
    return redirect(reverse("voters"))

def update_college(request):
    if request.method !='POST':
        sweetify.error(request, "Access Denied")
    try:
        instance = College.objects.get(id=request.POST.get("college_id"))
        form = CollegeForm(request.POST or None, instance=instance)
        if form.is_valid():
            college = form.save()
            sweetify.success(request, f"{str(college)} has been successfully updated!")
            
        else:
           for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
    except Exception as e:
        sweetify.errror(request, f"{str(e)}")
    return redirect(reverse("voters"))

def delete_college(request):
    if request.method !='POST':
        sweetify.error(request, "Access Denied!")
    try:
        college = College.objects.get(id=request.POST.get('college_id'))
        college.delete()
        sweetify.success(request, f"{str(college)} has been successfully deleted!")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
    return redirect(reverse('voters'))


def voters(request):
    voters = Voter.objects.exclude(is_superuser=True)
    form = VoterForm(request.POST or None)
    college = College.objects.all()
    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            if Voter.objects.filter(username=data['username']).exists():
                sweetify.error(
                    request, "A voter with this student_id already exists.")
            voter = Voter(**data)
            password = request.POST.get('password')
            voter.print_password = password
            voter.set_password(password)
            voter.save()
            sweetify.success(request, f"{str(voter)} has been successfully registered!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"Error in {field}:{error}")
        return redirect("voters")
    context = {
        'voters': voters,
        'form': form,
        "page_title": "VOTERS",
        'segment': 'voters',
        'college': college
    }
    return render(request, "adm/voters.html", context)

def get_colleges(request):
    colleges = College.objects.all()
    data = [{"id": college.id, "name": college.name} for college in colleges]
    return JsonResponse(data, safe=False)


def get_parties(request):
    parties = PartyList.objects.all()
    data = [{"id": party_list.id, "name":party_list.name} for party_list in parties]
    return JsonResponse(data, safe=False)

def get_positions(request):
    positions = Position.objects.all()
    data = [{"id": position.id, "name":position.name} for position in positions]
    return JsonResponse(data, safe=False)


def update_voter(request):
    if request.method != 'POST':
        sweetify.error(request, "Access Denied")
    try:
        instance = Voter.objects.get(id=request.POST.get('voter_id'))
        form = VoterForm(request.POST or None, instance=instance)
        if form.is_valid():
            password = instance.password
            voter = form.save(commit = False)
            voter.set_password(password)
            voter.save()
            sweetify.success(request, f"{str(voter)} has been successfully updated!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"Error in {field}:{error}")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
    return redirect(reverse("voters"))

def delete_voter(request):
    if request.method !='POST':
        sweetify.error(request, "Access Denied!")
    try:
        voter_id = request.POST.get("voter_id")
        voter = Voter.objects.get(id=voter_id)
        voter.delete()
        sweetify.success(request, f"{str(voter)} has been successfully deleted")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
    return redirect(reverse("voters"))

def delete_all_voters(request):
    Voter.objects.filter(is_superuser=False).delete()
    sweetify.error(request, "All Voters have been delete!")
    
    return redirect(reverse("voters"))

import pandas as pd
import secrets
from django.db import transaction, IntegrityError, DataError
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, reverse
from django.db.models import Q
from django.db.models.functions import Trim
from pandas.errors import EmptyDataError, ParserError
import sweetify

def get_colleges_map(college_inputs):
    if not college_inputs:
        return {}
    cleaned_inputs = [c.strip().lower() for c in college_inputs if c]
    if not cleaned_inputs:
        return {}

    query = Q()
    for col in cleaned_inputs:
        query |= Q(name__iexact=col) | Q(initials__iexact=col)
    
    colleges = College.objects.filter(query)
    college_map = {}
    for college in colleges:
        name_key = college.name.strip().lower()
        initials_key = college.initials.strip().lower() if college.initials else None
        college_map[name_key] = college
        if initials_key:
            college_map[initials_key] = college
    return college_map

def upload_voters(request):
    if request.method != 'POST':
        return redirect(reverse("voters"))

    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        sweetify.error(request, "No CSV file provided.")
        return redirect("voters")

    try:
        # 1. File Parsing Errors
        try:
            df = pd.read_csv(csv_file)
        except EmptyDataError:
            sweetify.error(request, "The uploaded CSV file is empty.")
            return redirect("voters")
        except ParserError as e:
            sweetify.error(request, f"Invalid CSV format: {str(e)}. Check for extra commas or quotes.")
            return redirect("voters")
        except UnicodeDecodeError:
            sweetify.error(request, "Encoding error. Please ensure the file is saved as UTF-8.")
            return redirect("voters")

        df = df.fillna('')

        if df.empty:
            sweetify.error(request, "The CSV file contains no data rows.")
            return redirect("voters")

        # 2. Column Validation
        required_columns = {'student_id', 'first_name', 'middle_name', 'last_name', 'college'}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            sweetify.error(request, f"Missing columns: {', '.join(missing_columns)}")
            return redirect("voters")

        # 3. Data Preparation
        college_inputs = df['college'].astype(str).unique()
        college_map = get_colleges_map(college_inputs)
        
        existing_voters = Voter.objects.annotate(
            clean_username=Trim('username')
        ).filter(
            clean_username__in=df['student_id'].astype(str).str.strip()
        )
        existing_voters_map = {v.clean_username: v for v in existing_voters}
        
        voters_to_create = []
        voters_to_update = []
        update_fields = ['first_name', 'middle_name', 'last_name', 'college']

        for index, row in df.iterrows():
            username = str(row['student_id']).strip()
            if not username:
                continue
                
            college_input = str(row['college']).strip()
            college = college_map.get(college_input.lower())
            
            if not college:
                sweetify.error(request, f"College '{college_input}' not found at row {index + 2}.")
                return redirect("voters")

            if username in existing_voters_map:
                voter = existing_voters_map[username]
                voter.first_name = str(row['first_name'])
                voter.middle_name = str(row['middle_name'])
                voter.last_name = str(row['last_name'])
                voter.college = college
                voters_to_update.append(voter)
            else:
                random_password = secrets.token_hex(4)
                voter = Voter(
                    username=username,
                    first_name=str(row['first_name']),
                    middle_name=str(row['middle_name']),
                    last_name=str(row['last_name']),
                    college=college,
                    print_password=random_password,
                    password=make_password(random_password),
                )
                # Catch model validation errors before bulk operation
                try:
                    voter.full_clean()
                except ValidationError as ve:
                    sweetify.error(request, f"Data error at row {index + 2}: {ve.message_dict}")
                    return redirect("voters")
                    
                voters_to_create.append(voter)

        # 4. Database Operations with Specific Error Handling
        with transaction.atomic():
            try:
                if voters_to_update:
                    Voter.objects.bulk_update(voters_to_update, update_fields)
                
                if voters_to_create:
                    Voter.objects.bulk_create(voters_to_create)
                    
                sweetify.success(request, f"Successfully processed {len(voters_to_create) + len(voters_to_update)} voters.")
                
            except IntegrityError as e:
                # Handles duplicates, unique constraint violations
                error_msg = str(e)
                if 'Duplicate entry' in error_msg:
                    # Extract the duplicate value if possible
                    sweetify.error(request, f"Duplicate entry detected. Some student IDs already exist or are duplicated in the file.")
                else:
                    sweetify.error(request, f"Database integrity error: {error_msg}")
                return redirect("voters")
                
            except DataError as e:
                # Handles wrong types, string too long, etc.
                sweetify.error(request, f"Data format error: {str(e)}. Check column data types and lengths.")
                return redirect("voters")

        return redirect("voters")

    except Exception as e:
        # Fallback for truly unexpected errors
        sweetify.error(request, f"Unexpected system error: {str(e)}")
        return redirect("voters")   
    
    
    
def view_position(request):
    pos_id = request.GET.get('position_id', None)
    pos = Position.objects.filter(id=pos_id)
    context = {}
    if not pos.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        pos = pos[0]
        context['name'] = pos.name
        context['max_vote'] = pos.max_vote
        context['priority'] = pos.priority
        if pos.college:
            context['college'] = pos.college.id
        else:
            context['college'] = pos.college
        context['id'] = pos.id
   
    return JsonResponse(context)

def add_position(request):
    if request.method !='POST':
        sweetify.error(request, "Access Denied!")
    try:
        positions = Position.objects.all()
        position = PositionForm(request.POST or None)
        if position.is_valid():
            position = position.save(commit=False)
            position.priority = positions.count() + 1
            position.save()
            sweetify.success(request, f'Position "{str(position.name)}" has been created!')
        else:
            for field, errors in position.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
    return redirect(reverse("election_settings"))



def update_position(request):
    if request.method != 'POST':
        sweetify.error(request, "Access Denied")
    try:
        instance = Position.objects.get(id=request.POST.get('position_id'))
        form = PositionForm(request.POST or None, instance=instance)
        if form.is_valid():
            position = form.save()
            sweetify.success(request, f"{str(position.name)} has been successfully updated!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")

    return redirect(reverse('election_settings'))

def delete_all_positions(request):
    Position.objects.all().delete()
    sweetify.success(request, "All positions have been deleted!")
    return redirect(reverse("election_settings"))


def delete_position(request):
    if request.method != 'POST':
        sweetify.error(request, "Access Denied")
    try:
        position = Position.objects.get(id=request.POST.get('position_id'))
        position.delete()
        sweetify.success(request, f'Position {str(position.name)} has been successfully deleted!')
    except Exception as e:
        sweetify.error(request, f"{str(e)}")

    return redirect(reverse('election_settings'))

 # CANDIDATES

def view_candidate(request):
    candidate_id = request.GET.get('candidate_id', None)
    candidate = Candidate.objects.filter(id=candidate_id)
    context = {}
    if not candidate.exists():
        context['code'] = 404
    else:
        context['code'] = 200
        candidate = candidate[0]
        context['fullname'] = candidate.fullname
        context['photo_url'] = candidate.photo.url
        context['party_list'] = candidate.party_list.id
        context['position'] = candidate.position.id
     
    return JsonResponse(context)


def add_candidate(request):
    if request.method !="POST":
        sweetify.error(request, "Access Denied")
        return redirect(reverse("election_settings"))
    try:
        form = CandidateForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            candidate=form.save(commit=False)
            if 'photo' in request.FILES:
                candidate.photo = request.FILES['photo']
            candidate.save()
            sweetify.success(request, "Success")
           
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
        return redirect(reverse('election_settings'))
    
    return redirect('election_settings')
        

def update_candidate(request):
    if request.method != 'POST':
        sweetify.error(request, "Access Denied")
        return redirect(reverse('election_settings'))
    try:
        candidate_id = request.POST.get('candidate_id')
        candidate = Candidate.objects.get(id=candidate_id)
        form = CandidateForm(request.POST or None, instance=candidate)
        if form.is_valid():
            candidate = form.save(commit=False)
            if 'photo' in request.FILES:
                candidate.photo = request.FILES['photo']
            candidate.save()
            sweetify.success(request, "Candidate has been successfully updated")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
        return redirect(reverse("election_settings"))
          
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
        return redirect(reverse('election_settings'))


def delete_candidate(request):
    if request.method !='POST':
        sweetify.error(request, "Access Denied")
    try:
        candidate = Candidate.objects.get(id=request.POST.get('id'))
        candidate.delete()
        sweetify.success(request, "Candidate Has Been Deleted")
    except:
        sweetify.error(request, "Access To This Resource Denied")

    return redirect(reverse('election_settings'))
    
    

def delete_candidate(request):
    if request.method !="POST":
        sweetify.error(request, "Access Denied")
    try:
        candidate_id = request.POST.get("candidate_id")
        candidate = Candidate.objects.get(id=candidate_id)
        candidate.delete()
        sweetify.success(request, "Candidate has been successfully deleted!")
        return redirect(reverse("election_settings"))
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
        return redirect(reverse('election_settings'))
    

def delete_all_candidates(request):
    Candidate.objects.all().delete()
    sweetify.success(request, "All Candidates have been deleted!")
    return redirect(reverse('election_settings'))

# * PARTIES




def view_party_by_id(request):
    party_id = request.GET.get('party_id', None)
    party = PartyList.objects.filter(id=party_id)
    context = {}
    if not party.exists():
        context['code'] = 404
    else:
        party = party[0]
        context['code'] = 200
        context['name'] = party.name
    return JsonResponse(context)



def add_party(request):
    if request.method != "POST":
        sweetify.error(request, "Access Denied")
        return redirect(reverse("election_settings"))

    party_list = PartyListForm(request.POST or None)

    if party_list.is_valid():
        try:
            party_list.save()
            sweetify.success(request, f"{party_list.cleaned_data['name']} has been created!")
        except Exception as e:
            sweetify.error(request, f"An error occurred while saving: {str(e)}")
    else:
        for field, errors in party_list.errors.items():
            for error in errors:
                sweetify.error(request, f"{error}")

    return redirect(reverse("election_settings"))

def update_party(request):
    if request.method != 'POST':
        sweetify.error(request, "Access Denied")
    try:
        party_id = request.POST.get('party_id')
        party = PartyList.objects.get(id=party_id)
        form = PartyListForm(request.POST or None, instance=party)
        if form.is_valid():
            form.save()
            sweetify.success(request, "Party Data Updated")
        else:
           for field, errors in form.errors.items():
                for error in errors:
                    sweetify.error(request, f"{error}")
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
    return redirect(reverse("election_settings"))

def delete_party(request):
    if request.method != 'POST':
        sweetify.error(request, "Access Denied")
    try:
        party_id = request.POST.get('party_id')
        party = PartyList.objects.get(id=party_id)
        party.delete()
        sweetify.success(request, "Party Has Been Deleted")
        return redirect(reverse("election_settings"))
    except Exception as e:
        sweetify.error(request, f"{str(e)}")
        return redirect(reverse("election_settings"))

def delete_all_parties(request):
    PartyList.objects.exclude(name="Independent").delete()
    sweetify.success(request, "All Parties have been deleted!")
    return redirect(reverse("election_settings"))

# * SETTINGS


def ballot_title(request):
    url = urlparse(request.META['HTTP_REFERER']).path
    try:
        redirect_url = resolve(url)
        title = request.POST.get('title', 'No Name')
        file = open(settings.ELECTION_TITLE_PATH, 'w')
        file.write(title)
        file.close()
        sweetify.success(
            request, "Election title has been changed to " + str(title))
        return redirect(url)
    except Exception as e:
        error_message = str(e)  # Convert the exception to a string
        sweetify.error(request, error_message)
        return redirect("ballot_position")

def ballot_position(request):
    context = {
        'page_title': "Ballot Position",
        'segment': 'ballot_position'
    }
    return render(request, "adm/ballot_position.html", context)



def update_ballot_position(request, position_id, up_or_down):
    try:
        context = {
            'error': False
        }
        position = Position.objects.get(id=position_id)
        
        if up_or_down == 'up':
            priority = position.priority - 1
            if priority == 0:
                context['error'] = True
                output = "This position is already at the top"
            else:
                Position.objects.filter(priority=priority).update(
                    priority=(priority+1))
                position.priority = priority
                position.save()
                output = "Moved Up"
        else:
            priority = position.priority + 1
            if priority > Position.objects.all().count():
                output = "This position is already at the bottom"
                context['error'] = True
            else:
                Position.objects.filter(priority=priority).update(
                    priority=(priority-1))
                position.priority = priority
                position.save()
                output = "Moved Down"
        context['message'] = output
    except Exception as e:
        context['message'] = e

    return JsonResponse(context)



def election_settings(request):
    candidates = Candidate.objects.all()
    parties = PartyList.objects.all()
    positions = Position.objects.order_by('priority').all()
    
    candidate_form = CandidateForm(request.POST or None, request.FILES or None)
    position_form = PositionForm(request.POST or None)
    party_form = PartyListForm(request.POST or None)
    
    context = {
        'candidate_form': candidate_form,
        'position_form': position_form,
        'party_form': party_form,
        'candidates': candidates,
        'parties': parties,
        'positions': positions,
        'page_title': 'Election Settings',
        'segment': 'elec_settings',
    }
    return render(request, "adm/election.html", context)

def reset_votes(request):
    Election.objects.all().delete()
    Voter.objects.all().update(voted=False)
    sweetify.success(request, "All votes  have been reset!")
    return redirect(reverse("admin_dashboard"))

def delete_all_college(request):
    College.objects.all().delete()
    sweetify.success(request, "All Colleges have been deleted!", iconColor="#242e4c")
    return redirect(reverse("voters"))