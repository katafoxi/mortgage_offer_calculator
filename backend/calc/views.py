from django.http import HttpResponse
from django.views.generic import ListView
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import Offer
from .serializers import OfferSerializer
from .utils import DataMixin


def calculator(request):
    return HttpResponse("Страница приложения.")


class Calculator(DataMixin, ListView):
    """
    Класс для начальной красивой страницы с удобной формой генерации get-запроса с параметрами.
    http://localhost:8000/
    """
    model = Offer
    template_name = 'calc/base.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Выбор программы для редактора")
        return dict(list(context.items()) + list(c_def.items()))


class OfferViewSet(viewsets.ModelViewSet):
    """
    Согласно тех.задания
    """
    queryset = Offer.objects.all().order_by("id")
    serializer_class = OfferSerializer

    def get_queryset(self):
        if self.request.query_params:
            price = self.request.query_params.get('price')
            term = self.request.query_params.get('term')
            query_set = Offer.objects.filter(payment_min__lte=price,
                                             payment_max__gte=price,
                                             term_min__lte=term,
                                             term_max__gte=term,
                                             )
            return query_set
        else:
            return Offer.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Метод для обработки случая отсутствия ипотечных предложений
        :param request: запрос
        :param args: арги
        :param kwargs: кварги
        :return: ответ
        """
        queryset = self.filter_queryset(self.get_queryset())
        if len(queryset) == 0:
            return Response({"detail": "Предложений не найдено"}, status=status.HTTP_404_NOT_FOUND)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        sort_key = self.request.query_params.get('order', None)
        if sort_key:
            return OfferViewSet.parametric_sort(sort_key, serializer)
        else:
            return Response(serializer.data)

    @staticmethod
    def parametric_sort(sort_key: str, serializer: object) -> object:
        """
        Метод параметрической сортировки по ключу из запроса

        :param sort_key: ключ сортировки из запроса
        :param serializer: объедок сериализатора
        :return: ответ
        """
        flag = False
        if sort_key[0] == '-':
            flag = True
            sort_key = sort_key[1:]
        sorted_representation = sorted(serializer.data, key=lambda offer: offer.get(sort_key), reverse=flag)
        return Response(sorted_representation)
