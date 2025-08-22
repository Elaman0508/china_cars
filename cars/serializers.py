from rest_framework import serializers
from .models import Car

class CarSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = "__all__"

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image:
            return f"http://217.25.93.75{obj.image.url}"
        return None
