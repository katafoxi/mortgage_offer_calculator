from rest_framework import serializers

from .models import Offer, Bank


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ["id", "name", "offer"]


class OfferSerializer(serializers.HyperlinkedModelSerializer):
    bank_name = serializers.CharField()

    class Meta:
        model = Offer
        fields = (
            'id',
            'bank_name',
            'rate_min',
            'rate_max',
            'term_min',
            'term_max',
            'payment_min',
            'payment_max'
        )

    def validate(self, attrs):
        if attrs['rate_min'] > attrs['rate_max']:
            raise serializers.ValidationError("Rate_min should be less than rate_max ")
        if attrs['term_min'] > attrs['term_max']:
            raise serializers.ValidationError("term_min should be less than term_max ")
        if attrs['payment_min'] > attrs['payment_max']:
            raise serializers.ValidationError("payment_min should be less than payment_max ")
        return attrs

    def create(self, validated_data):
        """
        Т.к. поле bank_name модели ипотечного предложения ссылается на модель Bank,
        то для корректного создания ипотечного предложения по API, переопределяется методы create и update.

        :param validated_data: нормализованные данные
        :return: Offer.object
        """
        bank_name, created = Bank.objects.get_or_create(name=validated_data.pop("bank_name"))
        new_offer = Offer.objects.create(bank_name=bank_name, **validated_data)
        new_offer.save()
        return new_offer

    def update(self, instance, validated_data):
        instance.bank_name = Bank.objects.get(name=validated_data.pop('bank_name'))
        instance.rate_min = validated_data.get("rate_min", instance.rate_min)
        instance.rate_max = validated_data.get("rate_max", instance.rate_max)
        instance.term_min = validated_data.get("term_min", instance.term_min)
        instance.term_max = validated_data.get("term_ma=", instance.term_max)
        instance.payment_min = validated_data.get("payment_min", instance.payment_min)
        instance.payment_max = validated_data.get("payment_max", instance.payment_max)
        instance.save()
        return instance

    @staticmethod
    def get_monthly_payment(params: dict, proposed_rate) -> int:
        """
        Метод для расчета размера ежемесячного платежа по предлагаемой процентной ставке.
        Формула расчета ежемесячного платежа с сайта https://mortgage-calculator.ru/

        :param proposed_rate:
        :param params: словарь с параметрами get-запроса.
        :return:
        """
        price = params['price']
        deposit = params['deposit']
        term = params['term']
        monthly_rate = proposed_rate / 12 / 100
        term_mortgage_months = term * 12
        total_rate = (1 + monthly_rate) ** term_mortgage_months
        credit_amount = price * (1 - deposit / 100)
        monthly_payment = (credit_amount * monthly_rate * total_rate) / (total_rate - 1)
        return monthly_payment

    @staticmethod
    def get_proposed_rate(params: dict, instance: Offer) -> float:
        """
        Метод для расчета предлагаемой процентной ставки ипотечного предложения банка.
        Предлагаемая ставка обратно зависит от среднего арифметического
        коэффициентов тела кредита (ratio_money) и срока займа (ratio_time).
        Принимается что:
         -чем больше необходимая клиенту сумма, тем ниже ставка,
         -чем на больший срок берется ипотека, тем ниже ставка
         Например:
          при максимальном теле кредита И максимальном сроке займа ставка минимальная.

        :param params: словарь с параметрами get-запроса.
        :param instance: сериализуемый объект ипотечного предложения.
        :return: proposed_rate предлагаемая процентная ставка.
        """

        price = params['price']
        term = params['term']
        ratio_money = (price - instance.payment_min) / (instance.payment_max - instance.payment_min)
        ratio_time = (term - instance.term_min) / (instance.term_max - instance.term_min)
        mean_ratio = (ratio_money + ratio_time) / 2  # среднее отношение по телу кредита и срока займа
        proposed_rate = instance.rate_min + (instance.rate_max - instance.rate_min) * (1 - mean_ratio)
        return proposed_rate

    def to_representation(self, instance: Offer) -> dict:
        """
        Метод добавляет с сериализованному объекту предложения  поле 'payment'. Если в запросе указан тип сортировки
        'по ставке', то добавляется еще поле 'rate', для проведения сортировки результатов по предлагаемой
        процентной ставке, ввиду отсутствия смысла сортировки по 'голым' диапазонам ставок.

        !Важное! Метод наверняка будет валить интеграционные тесты.

        :param instance: объект ипотечного предложения
        :return: сериализованный объект ипотечного предложения
        """
        params = self.context.get('request').query_params
        representation = super().to_representation(instance)
        if params:
            proposed_rate = OfferSerializer.get_proposed_rate(params, instance)
            representation['payment'] = OfferSerializer.get_monthly_payment(params, proposed_rate)
            if "order" in params.keys():
                if params["order"] in ['rate', '-rate']:
                    representation['rate'] = proposed_rate
            return representation
        else:
            return representation
