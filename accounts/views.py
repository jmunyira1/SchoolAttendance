from django.shortcuts import render

# Create your views here.
# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import LoginForm, UserForm
from .decorators import admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(request, user)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_admin:
        return redirect('attendance:dashboard')
    elif user.is_principal_or_deputy:
        return redirect('attendance:dashboard')
    elif user.is_storekeeper:
        return redirect('attendance:storekeeper')
    return redirect('accounts:login')


@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by('role', 'full_name')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@admin_required
def user_create(request):
    form = UserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        messages.success(request, f'User {user.full_name} created successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Add User'})


@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data['password'])
        user.save()
        messages.success(request, f'User {user.full_name} updated.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Edit User'})


@login_required
@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted.')
        return redirect('accounts:user_list')
    return render(request, 'confirm_delete.html', {'object': user, 'title': 'Delete User'})