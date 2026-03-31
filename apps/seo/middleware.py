from django.http import HttpResponsePermanentRedirect


class LegacyRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .models import Redirect

        path = request.path
        try:
            redirect = Redirect.objects.get(old_path=path)
            return HttpResponsePermanentRedirect(redirect.new_path)
        except Redirect.DoesNotExist:
            pass

        return self.get_response(request)
