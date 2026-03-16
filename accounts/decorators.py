# accounts/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'You do not have permission to access that page.')
        return redirect('accounts:dashboard_redirect')
    return wrapper


def admin_or_principal_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.user.is_admin or request.user.is_principal_or_deputy
        ):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'You do not have permission to access that page.')
        return redirect('accounts:dashboard_redirect')
    return wrapper


def storekeeper_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.user.is_storekeeper or request.user.is_admin
        ):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'You do not have permission to access that page.')
        return redirect('accounts:dashboard_redirect')
    return wrapper