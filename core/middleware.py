from django.utils.deprecation import MiddlewareMixin
import threading

_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class ThreadLocalRequestMiddleware(MiddlewareMixin):
    """
    Middleware to store the current request in thread local storage
    """
    def process_request(self, request):
        _thread_locals.request = request
        return None

    def process_response(self, request, response):
        if hasattr(_thread_locals, 'request'):
            delattr(_thread_locals, 'request')
        return response