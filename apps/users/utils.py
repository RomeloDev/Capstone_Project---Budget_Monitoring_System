from functools import wraps
from django.shortcuts import redirect

def role_required(role, login_url='/login/'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(login_url)

            # Role checks
            if role == 'admin' and not request.user.is_admin:
                return redirect(login_url)
            elif role == 'officer' and not request.user.is_approving_officer:
                return redirect(login_url)
            elif role == 'end_user' and (request.user.is_admin or request.user.is_approving_officer):
                return redirect(login_url)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
