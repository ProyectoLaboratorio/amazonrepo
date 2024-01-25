import requests
from django.core.signals import Signal
from django.utils.deprecation import MiddlewareMixin

specific_page_loaded = Signal()

class SpecificPageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path == '/admin/user_profile_api/userprofile/add/':  # Change this to the specific path you want to trigger the signal for
            specific_page_loaded.send(sender=self.__class__)
        return None

class Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

