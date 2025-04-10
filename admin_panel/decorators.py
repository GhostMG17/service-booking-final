from django.http import HttpResponseForbidden

def owner_required(view_func):
    """ Декоратор для ограничения доступа только владельцам """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_owner:
            return HttpResponseForbidden("Access denied")
        return view_func(request, *args, **kwargs)
    return wrapper
