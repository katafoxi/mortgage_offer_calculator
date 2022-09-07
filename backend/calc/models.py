from django.core.validators import MaxValueValidator
from django.db import models


class Bank(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=250, help_text="Наименование банка")

    def __str__(self):
        return self.name


class Offer(models.Model):
    id = models.AutoField(primary_key=True)
    bank_name = models.ForeignKey(Bank,
                                  # related_name="bank_name",
                                  to_field="name",
                                  on_delete=models.CASCADE,
                                  help_text="Наименование банка",
                                  verbose_name="Банк"
                                  )
    term_min = models.PositiveIntegerField(default=0, help_text="Срок ипотеки, ОТ")
    term_max = models.PositiveIntegerField(default=0, help_text="Срок ипотеки, ДО")
    rate_min = models.FloatField(default=0, help_text="Ставка, ОТ")
    rate_max = models.FloatField(default=0,
                                 help_text="Ставка, ДО",
                                 validators=[MaxValueValidator(50, "Тебе точно нужна эта ипотека?"), ])
    payment_min = models.PositiveIntegerField(default=0, help_text="Сумма кредита, ОТ")
    payment_max = models.PositiveIntegerField(default=0, help_text="Сумма кредита, ДО")

    def __str__(self):
        return str(self.bank_name)


