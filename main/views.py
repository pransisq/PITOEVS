from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse
from django.utils.text import slugify
from django_renderpdf.views import PDFView
from adm.models import *
import sweetify
from . forms import UpdateUserForm
from adm.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

def index(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            logout(request)
            return redirect(reverse("login"))
        else:
            logout(request)
            return redirect(reverse("login"))
    else:
        return redirect(reverse("login"))

def voter_dashboard(request):
    user = request.user
    my_votes = Election.objects.filter(voter=user)
    elections = Election.objects.filter(voter=user)
    my_votes = [election.candidate.fullname for election in elections]
    candidates = Candidate.objects.all()
    positions = Position.objects.filter()
    
    if user is not None:
        pass
        if user.voted: 
            context = {
                'page_title': "Dashboard",
                'my_votes': my_votes,
                'segment': 'voter',
                'candidates': candidates,
                'positions': positions,
            }
        else:
            return redirect(reverse('show_ballot'))
    else:
        return redirect(reverse('login'))\

    return render(request, "main/result.html", context)

def generate_ballot(user, display_controls=False):
    if user.is_superuser:
        positions = Position.objects.order_by('priority').all()
    else:
        positions = Position.objects.filter(
            Q(college__isnull=True) | Q(college=user.college)
        )
    output = ""
    candidates_data = ""
    num = 1

    for position in positions:
        name = position.name
        position_name = slugify(name)
        candidates = Candidate.objects.filter(position=position)

        if not candidates.exists():
            output += f"""
                        <div class="container">
                            <div class="row d-flex justify-content-center text-center mb3 mt5">
                                <div class="col-md-7 p-0">
                                    <div class="container">
                                        <div class="card" id="{position.id}">
                                            <div class="card-header">
                                                <h3 class="card-title text-center">
                                                        {name}
                                                </h3>
                                            </div>
                                            <div class="container pt-2 pb-2">
                                                <div class = "d-flex justify-content-center align-items-center">
                                                    <p class = "font-weight-bold pt-5" style = "font-size: 25px; ">
                                                        No candidates available for this position.
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
        else:
            for candidate in candidates:
                party_name = candidate.party_list.name
                if position.max_vote > 1:
                    instruction = "You may select up to " + \
                        str(position.max_vote) + " candidates"
                    input_box = '<input type="checkbox" value="'+str(candidate.id)+'" class=" ' + \
                        position_name+'" name="' + \
                        position_name+"[]" + '">'
                else:
                    instruction = "Select only one candidate"
                    input_box = '<input value="' + str(candidate.id) + '" type="radio" class=" ' + \
                        position_name+'" name="'+position_name+'">'

                image = candidate.photo.url
                candidates_data = candidates_data + f'<div class = "col-12 col-md-6 col-lg-4 pb-5 mb-5"><div class="card shadow text-center"><div class="profile-thumbnail m-sm mb-0 mt-n6"><img src="' + image + \
                    '" class="rounded-circle" height="200px" width="200px" style="border: solid 2px #00f2c3"></div><div class="card-body mb-3 text-center"><span class="card-subtitle text-gray fw-normal">' + \
                    '' + party_name + '</span><h3 class = "h3 card-title mb-2">' + \
                        candidate.fullname + '</h3></div>' + input_box + '</div></div>'

            up = ''
            if position.priority == 1:
                up = 'disabled'
            down = ''
            if position.priority == positions.count():
                down = 'disabled'
            output = output + f"""
                                
                                <div class="row d-flex justify-content-center">
                                    <div class="container-fluid">
                                        <div class="container">
                                            <div class="card" id="{position.id}">
                                                <div class="card-header">
                                                    <h3 class="card-title font-weight-bold text-center">
                                                            {name}
                                                    </h3>
                                                </div> 
            """

            if display_controls:
                output = output + f""" <div class="pull-right box-tools">
                                            <button type="button" class="btn btn-default btn-sm moveup" data-id="{position.id}" {up}>
                                                <i class="fa fa-arrow-up"></i> 
                                            </button>
                                            <button type="button" class="btn btn-default btn-sm movedown" data-id="{position.id}" {down}>
                                                <i class="fa fa-arrow-down"></i>
                                            </button>
                                        </div>
                                    """

            output = output + f"""
                                <div class="card p-4">
                                    <div class="d-flex justify-content-center align-items-center" style="padding-bottom: 10rem;">
                                        <p>
                                            {instruction}
                                        </p>
                                    </div>
                                    <div class="row justify-content-center">
                                        {candidates_data}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            """
            position.priority = num
            position.save()
            num = num + 1
            candidates_data = ''
    return output

def fetch_ballot(request):
    output = generate_ballot(request.user, display_controls=True)
    return JsonResponse(output, safe=False)

def show_ballot(request):
    if request.user.voted:
        sweetify.error(request, "You have voted already")
        return redirect(reverse('voter_dashboard'))
    ballot = generate_ballot(request.user, display_controls=False)
    context = {
        'ballot': ballot,
        'page_title': 'ballot',
        'segment': 'voter'
    }
    return render(request, "main/ballot.html", context)

def preview_vote(request):
    if request.method != 'POST':
        error = True
        response = "Please browse the system properly"
    else:
        output = ""
        form = dict(request.POST)

        form.pop('csrfmiddlewaretoken', None)
        error = False
        data = []
        positions = Position.objects.all()
        for position in positions:
            max_vote = position.max_vote
            pos = slugify(position.name)
            pos_id = position.id
            if position.max_vote > 1:
                this_key = pos + "[]"
                form_position = form.get(this_key)
                if form_position is None:
                    continue
                if len(form_position) > max_vote:
                    error = True
                    response = "You can only choose " + \
                        str(max_vote) + " candidates for " + position.name
                else:
                    # for key, value in form.items():
                    start_tag = f"""
                       <div class='row votelist' style='padding-bottom: 2px'>
		                      	<span class='col-sm-4'><span class='pull-right'><b>{pos} :</b></span></span>
		                      	<span class='col-sm-8'>
                                <ul style='list-style-type:none; margin-left:-40px'>
                                
                    
                    """
                    end_tag = "</ul></span></div><hr/>"
                    data = ""
                    for form_candidate_id in form_position:
                        try:
                            candidate = Candidate.objects.get(
                                id=form_candidate_id, position=position)
                            data += f"""
		                      	<li><i class="fa fa-check-square-o"></i> {candidate.fullname}</li>
                            """
                        except:
                            error = True
                            response = "Please, browse the system properly"
                    output += start_tag + data + end_tag
            else:
                this_key = pos
                form_position = form.get(this_key)
                if form_position is None:
                    continue
                try:
                    form_position = form_position[0]
                    candidate = Candidate.objects.get(
                        position=position, id=form_position)
                    output += f"""
                            <div class='row votelist' style='padding-bottom: 2px'>
		                      	<span class='col-sm-4'><span class='pull-right'><h6>{position.name} :</h6></span></span>
		                      	<span class='col-sm-8'><i class="fa fa-check-circle-o"></i> {candidate.fullname}</span>
		                    </div>
                      <hr/>
                    """
                except Exception as e:
                    error = True
                    response = "Please, browse the system properly"
    context = {
        'error': error,
        'list': output
    }
    return JsonResponse(context, safe=False)


def submit_ballot(request):
    if request.method != 'POST':
        sweetify.warning(request, "Please, browse the system properly")
        return redirect(reverse('show_ballot'))

    voter = request.user
    if voter.voted:
        sweetify.warning(request, "You have voted already")
        return redirect(reverse('voter_dashboard'))

    form = dict(request.POST)
    form.pop('csrfmiddlewaretoken', None)  # Pop CSRF Token
    form.pop('submit_vote', None)  # Pop Submit Button

    if len(form.keys()) < 1:
        sweetify.error(request, "Please select at least one candidate")
        return redirect(reverse('show_ballot'))
    
    positions = Position.objects.all()
        
    form_count = 0
    for position in positions:
        max_vote = position.max_vote
        pos = slugify(position.name)
        pos_id = position.id

        if position.max_vote > 1:
            this_key = pos + "[]"
            form_position = form.get(this_key)
            if form_position is None:
                continue
            if len(form_position) > max_vote:
                sweetify.error(request, "You can only choose " +
                               str(max_vote) + " candidates for " + position.name)
                return redirect(reverse('show_ballot'))
            else:
                for form_candidate_id in form_position:
                    form_count += 1
                    try:
                        candidate = Candidate.objects.get(
                            id=form_candidate_id, position=position)
                        Election.objects.create(
                            candidate=candidate, voter=voter, position=position)
                    except Exception as e:
                        sweetify.error(
                            request, "Please, browse the system properly " + str(e))
                        return redirect(reverse('show_ballot'))
        else:
            this_key = pos
            form_position = form.get(this_key)
            if form_position is None:
                continue
            form_count += 1
            try:
                candidate = Candidate.objects.get(
                    position=position, id=form_position[0])
                Election.objects.create(
                    candidate=candidate, voter=voter, position=position)
            except Exception as e:
                sweetify.error(
                    request, "Please, browse the system properly " + str(e))
                return redirect(reverse('show_ballot'))

    inserted_votes = Election.objects.filter(voter=voter)

    if inserted_votes.count() != form_count:
        sweetify.error(request, "Please try voting again!")
        inserted_votes.delete()
        return redirect(reverse('show_ballot'))
    else:
        voter.voted = True
        voter.save()
        sweetify.success(request, "Thanks for voting")
        return redirect(reverse('voter_dashboard'))


class Receipt(PDFView):
    template_name = 'main/receipt.html'
    prompt_download = True

    @property
    def download_name(self):
        user = self.request.user
        return f"{user.first_name, user.last_name}_receipt.pdf"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        elections = Election.objects.all()
        my_votes = [election.candidate.fullname for election in elections]
        candidates = Candidate.objects.all()
        positions = Position.objects.all()
        
        context = {
            'elections': elections,
            'my_votes': my_votes,
            'candidates': candidates,
            'positions': positions            
        }
        
        return context


def user_profile(request):
    colleges = College.objects.all()
    if request.method == "POST":
        form = UpdateUserForm(request.POST, instance = request.user)
        if form.is_valid():
            form.save()
            sweetify.success(request, "User Details Updated Successfully!")
            return redirect('user_profile')
        else:
            sweetify.error(request, "Administrator Update Failed!" f"{form.errors}")
    else:
        form = UpdateUserForm(instance=request.user)

    context = {
        'page_title': "PROFILE",
        'segment': 'profile',
        'colleges': colleges,
        }
    return render(request, "main/profile.html", context)

def update_user_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST, instance=request.user)
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
                    user = authenticate(username=username,
                                        password=new_password)
                    login(request, user)
                    if user.user_type == '2':
                        sweetify.success(
                            request, "Password Successfully Changed!")
                        return redirect(reverse("admin_profile"))
                    else:
                        sweetify.success(
                            request, "Password Successfully Changed!")
                        return redirect(reverse("user_profile"))
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



def update_user_photo(request):
    if request.method == 'POST' and request.FILES['photo']:
        user = request.user
        photo = request.FILES['photo']
        user.photo = photo  
        user.save()
        sweetify.success(request, 'Profile photo updated successfully!')
        return redirect(reverse('user_profile'))  

    sweetify.error(request, 'Failed to update photo. Please try again.')
    return redirect(reverse('user_profile')) 
    