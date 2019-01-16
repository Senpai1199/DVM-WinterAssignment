from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
import openpyxl
from .models import Profile

def register(request):
	if request.method == "POST":
		form = UserRegisterForm(request.POST) #Creates the form with the data contained in request.POST
		if form.is_valid():
			form.save()
			messages.success(request, 'Your account has been created. You can now login!')
			return redirect('login') 
	else:
		form = UserRegisterForm()
	return render(request, 'users/register.html', {'form': form, 'title': 'Register'})

@login_required #Decorator to make sure this view is blocked for those not logged in
def profile(request):
	if request.method == "POST":
		u_form = UserUpdateForm(request.POST, instance=request.user)
		p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

		if u_form.is_valid() and p_form.is_valid():
			u_form.save()
			p_form.save()
			messages.success(request, 'Profile updated successfully')
			return redirect('profile')
	else:
		u_form = UserUpdateForm(instance=request.user)
		p_form = ProfileUpdateForm(instance=request.user.profile)

	context = {
		'u_form': u_form,
		'p_form': p_form
	}
	return render(request, 'users/profile.html', context)

@permission_required('admin.can_add_log_entry')
def export_profile_data(request):
	response = HttpResponse(content_type='application/ms-excel')
	response['Content-Disposition'] = 'attachment; filename="profile_data.xlsx"'

	wb = openpyxl.Workbook()
	ws = wb.active
	ws.title = 'Profile Data'

	profiles = Profile.objects.all()
	row_data = [
		['PROFILE ID', 'USERNAME', 'EMAIL', 'USER(S) FOLLOWED', 'PROFILE-PICTURE PATH']
	]
	for profile in profiles:
		following_profiles = profile.follows.all()
		followed_usernames = []
		for following_profile in following_profiles:
			followed_usernames.append(following_profile.user.username)
		followed_usernames_str = ','.join(followed_usernames)

		row = [profile.id, profile.user.username, profile.user.email, followed_usernames_str, str(profile.image)]
		row_data.append(row)

	for line in row_data:
		ws.append(line)

	wb.save(response)
	return response
