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
    def calc_monthly_payment(params, instance):
        price = int(params['price'])
        deposit = int(params['deposit'])
        term = int(params['term'])
        ratio_money = (price - instance.payment_min) / (instance.payment_max - instance.payment_min)
        ratio_time = (term - instance.term_min) / (instance.term_max - instance.term_min)
        mean_ratio = (ratio_money + ratio_time) / 2  # среднее отношение по телу и времени

        # так как в большинстве случаев ставка меньше чем запрашиваемая сумма больше, то используем обратное отношение
        # таким образом выбираем предлагаемую процентную ставку годовых в промежутке min-max
        corresponding_rate = instance.rate_min + (instance.rate_max - instance.rate_min) * (1 - mean_ratio)

        # Формула расчета ежемесячного платежа с сайта https://mortgage-calculator.ru/
        monthly_rate = corresponding_rate / 12 / 100
        term_mortgage_months = term * 12
        total_rate = (1 + monthly_rate) ** term_mortgage_months
        credit_amount = price * (1 - deposit / 100)
        monthly_payment = (credit_amount * monthly_rate * total_rate) / (total_rate - 1)
        # print('price=', price)
        # print('term=', term)
        # print('ratio_money=', ratio_money)
        # print('ratio_time', ratio_time)
        # print('mean_ratio', mean_ratio)
        # print('cor_rate=', corresponding_rate)
        # print('term_mort_m=', term_mortgage_months)
        # print('total_rate=', total_rate)
        # print('credit_amount', credit_amount)
        # print('payment=', monthly_payment)
        return {'monthly_payment': int(monthly_payment),  # Платеж в месяц
                'corresponding_rate': round(corresponding_rate, 2),  # соответствующая телу и сроку кредита ставка
                'total_rate': round(total_rate, 2)  # общая ставка из формулы
                }

    def to_representation(self, instance):
        params = self.context.get('request').query_params
        representation = super().to_representation(instance)
        if params:
            additional_fields = OfferSerializer.calc_monthly_payment(params, instance)
            representation['payment'] = additional_fields['monthly_payment']

            # TODO т.к. по тексту задания неясно по какой ставке фильтровать, то здесь можно выбрать:
            #  по предлагаемой ставке (corresponding_rate) (обратно эквивалентна телу и сроку кредита), или
            #  по общей ставке (total_rate) рассчитывается по общепринятой формуле

            if "order" in params.keys():
                if params["order"] in ['rate', '-rate']:
                    representation['rate'] = additional_fields['corresponding_rate']
            return representation
        else:
            return representation
