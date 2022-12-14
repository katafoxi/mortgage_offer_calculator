from .models import *

menu = [{'title': 'Главная', 'url_name': 'main'},
        {'title': 'API', 'url_name': 'offer-list'},
        ]


class DataMixin:
    """Класс для красивого меню. Самый важный класс в приложении"""

    def get_user_context(self, **kwargs):
        context = kwargs
        programs = Offer.objects.all()
        context['menu'] = menu
        context['programs'] = programs
        return context
