from django.shortcuts import redirect
from django.urls import reverse

def form_step_required(step_name, next_step_url_name):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Check if the required data is present in the session
            if request.session.get(step_name, None) is None:
                # If the data is not present, redirect to the appropriate step
                return redirect(reverse(next_step_url_name))
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator