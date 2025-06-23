from django.utils import translation

def force_default_language(get_response):
    def middleware(request):
        if not request.COOKIES.get('django_language'):
            translation.activate('en')
        response = get_response(request)
        return response
    return middleware
