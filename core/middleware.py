
import threading
from django.utils.deprecation import MiddlewareMixin

class ThreadLocalMiddleware(MiddlewareMixin):
    """Middleware для доступа к request объекту в сигналах"""
    
    def process_request(self, request):
        threading.current_thread().request = request
        return None
    
    def process_response(self, request, response):
        if hasattr(threading.current_thread(), 'request'):
            delattr(threading.current_thread(), 'request')
        return response
