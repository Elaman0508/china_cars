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

    FUEL_CHOICES = [
        ("petrol", "Бензин"),
        ("diesel", "Дизель"),
        ("gas", "Газ"),
        ("electric", "Электро"),
        ("hybrid", "Гибрид"),
    ]

    CONDITION_CHOICES = [
        ("new", "Новый"),
        ("used", "Б/у"),
    ]

    brand = models.CharField(max_length=100, verbose_name="Марка")
    model = models.CharField(max_length=100, verbose_name="Модель")
    engine_capacity = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name="Объем двигателя (л)",
        default=1.6
    )
    year = models.PositiveIntegerField(verbose_name="Год выпуска", default=2020)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория",
        default="other"
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_CHOICES,
        verbose_name="Топливо",
        default="petrol"
    )
    condition = models.CharField(   # ✅ Новое поле
        max_length=10,
        choices=CONDITION_CHOICES,
        verbose_name="Состояние",
        default="used"
    )
    color = models.CharField(       # ✅ Новое поле
        max_length=50,
        verbose_name="Цвет",
        blank=True,
        null=True
    )
    # city = models.CharField(        # ✅ Новое поле
    #     max_length=100,
    #     verbose_name="Город",
    #     default="Бишкек"
    # )
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Цена", default=0)
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to="cars/", blank=True, null=True, verbose_name="Фото")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"
