
from .models import Airports
from .air_dict import dict1
from django.shortcuts import HttpResponse

data = []

def add_data(request):
    instances = [Airports( **(dict1.get(i)) ) for i in dict1 ]
    to_update = ["icao","iata","name","city","state","country","elevation","lat","lon","tz"]
    Airports.objects.bulk_create(instances)
    return HttpResponse("done")