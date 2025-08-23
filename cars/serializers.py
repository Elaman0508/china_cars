from rest_framework import serializers
from .models import Car

class CarSerializer(serializers.ModelSerializer):
    # Полный публичный URL для изображения
    image = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = "__all__"

    def get_image(self, obj):
        if obj.image:
            # Поменяй на свой публичный домен / IP
            return f"http://217.25.93.75{obj.image.url}"
        return None
