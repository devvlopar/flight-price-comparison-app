from amadeus import Client, ResponseError, Location
import json 
from django.shortcuts import HttpResponse, render
from django.contrib import messages
from .models import UserData, Airports
from django.db.models import Q

amadeus_client_t = Client(
    client_id='r4ihA5Hkomz2KstBmQjD3AaeLAZU0IQF',
    client_secret='T0S0QakCI3AXmeuT',
    hostname='production'  # Use 'test' for the sandbox environment
)

def get_airport(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            term = request.GET.get('term', None)
            object_list = Airports.objects.filter(Q(name__istartswith=term) | Q(iata__istartswith=term) | Q(city__istartswith=term)  ).order_by('city')
            
            data_list = [f"{i.city} ({i.iata} - {i.name})" if i.city else f"{i.name} ({i.iata} - {i.name})" for i in object_list]
            data = json.dumps(data_list)                                     
        except ResponseError as error:
            messages.add_message(request, messages.ERROR, error.response.result['errors'][0]['detail'])
    print(term,data_list)
    return HttpResponse(data, 'application/json')



def home_page(request):
    session_user = request.session.get('user_email')
    context = None
    if session_user:
        user = UserData.objects.get(email = session_user)
        context = {'user_details' : {
            "first_name" : user.first_name,
            "last_name" : user.last_name,
            "user_email" : user.email
        }
        }
    
    return render(request, 'search.html', context)

def get_city_airport_list(data):
    result = []
    for i, val in enumerate(data):
        result.append(data[i]['iataCode'] + ', ' + data[i]['name'])
    result = list(dict.fromkeys(result))
    return json.dumps(result)

def origin_airport_search_view(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = amadeus_client_t.reference_data.locations.get(keyword=request.GET.get('term', None),
                                                        subType=Location.ANY).data
        except ResponseError as error:
            messages.add_message(request, messages.ERROR, error.response.result['errors'][0]['detail'])
    return HttpResponse(get_city_airport_list(data), 'application/json')


def destination_airport_search_view(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = amadeus_client_t.reference_data.locations.get(keyword=request.GET.get('term', None),
                                                        subType=Location.ANY).data
        except ResponseError as error:
            messages.add_message(request, messages.ERROR, error.response.result['errors'][0]['detail'])
    return HttpResponse(get_city_airport_list(data), 'application/json')