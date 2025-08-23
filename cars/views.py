
from rest_framework import viewsets

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Car
from .serializers import CarSerializer

@api_view(['GET'])
def car_list(request):
    cars = Car.objects.all()

    category = request.GET.get('category')  # например "sedan"
    fuel = request.GET.get('fuel')          # например "petrol"
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if category:
        cars = cars.filter(category__iexact=category)
    if fuel:
        cars = cars.filter(fuel_type__iexact=fuel)
    if price_min:
        cars = cars.filter(price__gte=price_min)
    if price_max:
        cars = cars.filter(price__lte=price_max)

    serializer = CarSerializer(cars, many=True)
    return Response(serializer.data)

class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
