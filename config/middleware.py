from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.http import Http404
from django.shortcuts import render


class GracefulExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Http404:
            return render(request, 'errors/404.html', status=404)
        except PermissionDenied:
            return render(request, 'errors/403.html', status=403)
        except DatabaseError:
            return render(request, 'errors/500.html', status=500)
        except Exception:
            return render(request, 'errors/500.html', status=500)

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return render(request, 'errors/404.html', status=404)
        if isinstance(exception, PermissionDenied):
            return render(request, 'errors/403.html', status=403)
        if isinstance(exception, DatabaseError):
            return render(request, 'errors/500.html', status=500)
        return render(request, 'errors/500.html', status=500)
