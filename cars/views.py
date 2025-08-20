from rest_framework import generics
from .models import Car
from .serializers import CarSerializer
from rest_framework import viewsets

class CarList(generics.ListAPIView):
    serializer_class = CarSerializer

    def get_queryset(self):
        queryset = Car.objects.all()
        brand = self.request.query_params.get("brand")
        max_price = self.request.query_params.get("max_price")

        if brand:
            queryset = queryset.filter(brand__icontains=brand)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
