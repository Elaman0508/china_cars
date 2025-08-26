from rest_framework import serializers
from .models import Car
from django.conf import settings

class CarSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            "id",
            "brand",
            "model",
            "description",
            "price",
            "category",
            "created_at",
            "year",
            "engine_capacity",
            "fuel_type",
            "color",
            "condition",
            "image",
        ]

    def get_image(self, obj):
        if obj.image:
            return f"{settings.SITE_URL}{obj.image.url}"
        return None
