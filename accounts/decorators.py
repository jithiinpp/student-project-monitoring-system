from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(allowed_roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:

                return redirect('accounts:login')

            # Django superuser has full access
            if request.user.is_superuser:

                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            # Check user role
            if request.user.role in allowed_roles:

                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            messages.error(
                request,
                'You do not have permission to access this page.'
            )

            return redirect('accounts:dashboard')

        return wrapper

    return decorator