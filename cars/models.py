from django.db import models

class Car(models.Model):
    CATEGORY_CHOICES = [
        ("sedan", "Седан"),
        ("suv", "Внедорожник"),
        ("hatchback", "Хэтчбек"),
        ("coupe", "Купе"),
        ("minivan", "Минивэн"),
        ("pickup", "Пикап"),
        ("wagon", "Универсал"),
        ("other", "Другое"),
    ]

    brand = models.CharField(max_length=100, verbose_name="Марка")
    model = models.CharField(max_length=100, verbose_name="Модель")
    engine_capacity = models.DecimalField(
        max_digits=3, decimal_places=1, verbose_name="Объем двигателя (л)",
        default=1.6  # 👉 дефолт, чтобы миграции не ругались
    )
    year = models.PositiveIntegerField(
        verbose_name="Год выпуска",
        default=2020  # 👉 дефолт
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, verbose_name="Категория",
        default="other"  # 👉 дефолт
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Цена", default=0)
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to="cars/", blank=True, null=True, verbose_name="Фото")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"
