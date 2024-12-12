from django.shortcuts import render, redirect
from django.conf import settings
from .models import SearchHistory, UserData

import pycountry
import json
import requests
from amadeus import Client, ResponseError, Location
from django.http import HttpResponse, JsonResponse


from .flight import Flight
from .metrics import Metrics
from dotenv import load_dotenv
import os

# Create your views here.

load_dotenv()
amadeus_client = Client(
    client_id="r4ihA5Hkomz2KstBmQjD3AaeLAZU0IQF",
    client_secret="T0S0QakCI3AXmeuT",
    hostname='production',
)

def about_view(request):
    session_user = request.session.get("user_email")
    context = None
    if session_user:
        user = UserData.objects.get(email = session_user)
        context = { 'user_details':
            {'first_name' : user.first_name,
                            'last_name' : user.last_name,
                            'email' : user.email}}
    
    return render(request, 'about.html', context)

def support_view(request):
    session_user = request.session.get("user_email")
    context = None
    if session_user:
        user = UserData.objects.get(email = session_user)
        context = { 'user_details':
            {'first_name' : user.first_name,
                            'last_name' : user.last_name,
                            'email' : user.email}}
    return render(request, 'support.html', context)


def rank_cheapest_flight(cheapest_flight_price, first_price, third_price):
    cheapest_flight_price_to_number = float(cheapest_flight_price)
    first_price_to_number = float(first_price)
    third_price_to_number = float(third_price)
    if cheapest_flight_price_to_number < first_price_to_number:
        return 'A GOOD DEAL'
    elif cheapest_flight_price_to_number > third_price_to_number:
        return 'HIGH'
    else:
        return 'AVERAGE'


def is_cheapest_flight_out_of_range(cheapest_flight_price, metrics):
    min_price = float(metrics['min'])
    max_price = float(metrics['max'])
    cheapest_flight_price_to_number = float(cheapest_flight_price)
    if cheapest_flight_price_to_number < min_price:
        metrics['min'] = cheapest_flight_price
    elif cheapest_flight_price_to_number > max_price:
        metrics['max'] = cheapest_flight_price

direct_flights_not_available = None
def get_flight_offers(**kwargs):
    global direct_flights_not_available 
    print('before API')
    search_flights = amadeus_client.shopping.flight_offers_search.get(**kwargs)
    
    #check if direct flights are not avail but via are available
    if not search_flights.data and (kwargs.get('nonStop') == "true"):
        kwargs['nonStop'] = 'false'
        # search2 = amadeus_client.shopping.flight_offers_search.get(**kwargs)
        # if len(search2.data) != 0:
        #     direct_flights_not_available = "There are no direct flights available for this route."
            
    
    
    flight_offers = []
    for flight in search_flights.data:
        offer = Flight(flight).construct_flights()
        flight_offers.append(offer)
    # print('AFTER')
    
    return flight_offers


def get_flight_price_metrics(**kwargs_metrics):

    metrics = amadeus_client.analytics.itinerary_price_metrics.get(**kwargs_metrics)
    print("METRICS DATA COMING FROM THE API CALL FROM THE SERVER", " --------------> ",metrics.data)
    # print(Metrics(metrics.data).construct_metrics())
    return Metrics(metrics.data).construct_metrics()



def search_flight_view(request):
    data_dict = request.session.pop('custom_data', {})
    print(data_dict)
    if(data_dict):
        origin = data_dict.get('origin').split(' - ')[0][-3:]
        destination = data_dict.get('destination').split(' - ')[0][-3:]
        departure_date = data_dict.get('departureDate')
        return_date = data_dict.get('returnDate')
        cabin_class = data_dict.get('cabin_class')
        direct_flight = data_dict.get('directFlight')
    else:
        origin = request.POST.get('Origin').split(' - ')[0][-3:]
        destination = request.POST.get('Destination').split(' - ')[0][-3:]
        departure_date = request.POST.get('Departuredate')
        return_date = request.POST.get('Returndate')
        cabin_class = request.POST.get('Cabinclass')
        direct_flight ="true" if request.POST.get('directFlights') == "on" else "false"
        
        
    
    
    
    
    if request.session.get('user_email'):
        
        user = UserData.objects.get(email = request.session.get('user_email'))
        context ={'first_name' : user.first_name,
                            'last_name' : user.last_name,
                            'email' : user.email}

        

        ##create search log/ create search history entry
        current_search_id = None
        try:
            existing_entry = SearchHistory.objects.get(user=user,
            origin_location=request.POST.get('Origin') if request.POST.get('Origin') else origin,
            destination_location=request.POST.get('Destination') if request.POST.get('Destination') else destination)
            existing_entry.user = user
            existing_entry.save()
            current_search_id = existing_entry.search_id
        except :
            if not return_date:
                s1 = SearchHistory(
                    user = user,
                    origin_location = request.POST.get('Origin') if  request.POST.get('Origin') else origin,
                    destination_location = request.POST.get('Destination') if request.POST.get('Destination') else destination,
                    travel_class = cabin_class,
                    from_date = departure_date,
                    is_one_way = not bool(return_date),
                    return_date = None
                )
                s1.save()
            else:
                s1 = SearchHistory(
                    user = user,
                    origin_location = request.POST.get('Origin') if  request.POST.get('Origin') else origin,
                    destination_location = request.POST.get('Destination') if request.POST.get('Destination') else destination,
                    travel_class = cabin_class,
                    from_date = departure_date,
                    is_one_way = not bool(return_date),
                    return_date = return_date
                )
                s1.save()
            current_search_id = s1.search_id

        #get latest 2 history entries
        latest_search = SearchHistory.objects.filter(user=user).order_by('-last_search_at')[1:3]
        context = {'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'isOneWay': bool(return_date),
            'adults': 1,
            'cabin_class': cabin_class,
            'latest_search' : latest_search,
            'user_details' : context,
            'search_id' : current_search_id,
            'nonStop' : direct_flight
            }
        if (data_dict.get('killit') == "yesyes" or request.POST.get('killit') == "yesyes"):
            context.update({'killit':"yesyes"})
        # return render(request, 'results_test.html', context)
        return render(request, 'search_results.html', context)
    else:
        currency= {
        "currency_code": get_user_location_info(get_client_ip(request))['currency_name'],
        "currency_symbol": get_user_location_info(get_client_ip(request))['currency_symbol']
        }
        kwargs_metrics = {'originIataCode': origin,
                      'destinationIataCode': destination,
                      'departureDate': departure_date,
                       "currencyCode" : currency['currency_code']
                      }
        if return_date:
            kwargs_metrics['oneWay'] = "false"
        print("SEARCHING METRICS FOR THESE PARAMS --------------------->   ", kwargs_metrics)
        metrics = get_flight_price_metrics(**kwargs_metrics)
        
        #price metrics not available
        if not metrics:
            return render(request, 'results_without_login.html', {'is_good_deal': 'nometrics'})
        
        kwargs = {'originLocationCode': origin,
              'destinationLocationCode': destination,
              'departureDate': departure_date,
              'adults': 1,
              "currencyCode" : currency['currency_code'],
              'nonStop': direct_flight
              }
        if return_date:
            kwargs['returnDate'] = return_date
        flight_offers = get_flight_offers(**kwargs)
        cheapest_flight=get_cheapest_flight_price(flight_offers)
        is_good_deal = rank_cheapest_flight(cheapest_flight, metrics['first'], metrics['third'])
        deals_dict = {'A GOOD DEAL' : "Immediate booking is recommended. Register to view flight and price check details.",
                      'HIGH' : "Consider waiting to book. Register to view flight and price check details.",
                      'AVERAGE' : "Consider waiting to book. Register to view flight and price check details."}
        
        if not flight_offers:
            # print(flight_offers)
            return render(request, 'results_without_login.html', {'is_good_deal': False})
        print(is_good_deal)
        context = {'origin': request.POST.get('Origin'),
            'destination': request.POST.get('Destination'),
            'departure_date': departure_date,
            'return_date': return_date,
            'isOneWay': str(not bool(return_date)).lower(),
            'adults': 1,
            'cabin_class': cabin_class,
            'is_good_deal': is_good_deal,
            'deal_message': deals_dict.get(is_good_deal),
            'nonStop' : direct_flight
            }
        # return render(request, 'results_test.html')
        return render(request, 'results_without_login.html', context)

    
    

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    if ip == '127.0.0.1':
        ip = '8.8.8.8'
    return ip


# Currency symbol mapping
countries_currencies = {
    "AF": ["AFN", "؋"],
    "AL": ["ALL", "Lek"],
    "DZ": ["DZD", "دج"],
    "AS": ["USD", "$"],
    "AD": ["EUR", "€"],
    "AO": ["AOA", "Kz"],
    "AI": ["XCD", "$"],
    "AQ": ["AUD", "$"],
    "AR": ["ARS", "$"],
    "AM": ["AMD", "դր."],
    "AW": ["AWG", "ƒ"],
    "AU": ["AUD", "$"],
    "AT": ["EUR", "€"],
    "AZ": ["AZN", "₼"],
    "BS": ["BSD", "$"],
    "BH": ["BHD", "د.ب"],
    "BD": ["BDT", "৳"],
    "BB": ["BBD", "$"],
    "BY": ["BYN", "Br"],
    "BE": ["EUR", "€"],
    "BZ": ["BZD", "$"],
    "BJ": ["XOF", "CFA"],
    "BM": ["BMD", "$"],
    "BT": ["BTN", "Nu."],
    "BO": ["BOB", "$"],
    "BA": ["BAM", "KM"],
    "BW": ["BWP", "P"],
    "BR": ["BRL", "R$"],
    "IO": ["USD", "$"],
    "VG": ["USD", "$"],
    "BN": ["BND", "$"],
    "BG": ["BGN", "лв"],
    "BF": ["CFA", "CFA"],
    "BI": ["BIF", "FBu"],
    "KH": ["KHR", "៛"],
    "CM": ["XAF", "FCFA"],
    "CA": ["CAD", "$"],
    "CV": ["CVE", "Esc"],
    "KY": ["KYD", "$"],
    "CF": ["CFA", "FCFA"],
    "TD": ["XAF", "FCFA"],
    "CL": ["CLP", "$"],
    "CN": ["CNY", "¥"],
    "CO": ["COP", "$"],
    "KM": ["KMF", "CF"],
    "CG": ["CDF", "FC"],
    "CK": ["NZD", "$"],
    "CR": ["CRC", "₡"],
    "HR": ["HRK", "kn"],
    "CU": ["CUP", "$"],
    "CY": ["CYP", "€"],
    "CZ": ["CZK", "Kč"],
    "DK": ["DKK", "kr"],
    "DJ": ["DJF", "Fdj"],
    "DM": ["XCD", "$"],
    "DO": ["DOP", "$"],
    "EC": ["USD", "$"],
    "EG": ["EGP", "£"],
    "SV": ["SVC", "$"],
    "GQ": ["GNF", "Fr"],
    "ER": ["ERN", "Nfk"],
    "EE": ["EEK", "kr"],
    "ET": ["ETB", "ብር"],
    "FK": ["FKP", "£"],
    "FO": ["DKK", "kr"],
    "FJ": ["FJD", "$"],
    "FI": ["EUR", "€"],
    "FR": ["EUR", "€"],
    "GF": ["EUR", "€"],
    "PF": ["XPF", "₣"],
    "GA": ["GNF", "Fr"],
    "GM": ["GMD", "D"],
    "GE": ["GEL", "₾"],
    "DE": ["EUR", "€"],
    "GH": ["GHS", "₵"],
    "GI": ["GIP", "£"],
    "GR": ["EUR", "€"],
    "GL": ["DKK", "kr"],
    "GD": ["XCD", "$"],
    "GU": ["USD", "$"],
    "GT": ["GTQ", "Q"],
    "GN": ["GNF", "Fr"],
    "GW": ["GNF", "Fr"],
    "GY": ["GYD", "$"],
    "HT": ["HTG", "G"],
    "HN": ["HNL", "L"],
    "HK": ["HKD", "$"],
    "HU": ["HUF", "Ft"],
    "IS": ["ISK", "kr"],
    "IN": ["INR", "₹"],
    "ID": ["IDR", "Rp"],
    "IR": ["IRR", "﷼"],
    "IQ": ["IQD", "د.ع"],
    "IE": ["EUR", "€"],
    "IL": ["ILS", "₪"],
    "IT": ["EUR", "€"],
    "JM": ["JMD", "$"],
    "JP": ["JPY", "¥"],
    "JO": ["JOD", "د.ا"],
    "KZ": ["KZT", "₸"],
    "KE": ["KES", "Sh"],
    "KI": ["AUD", "$"],
    "KR": ["KRW", "₩"],
    "KW": ["KWD", "د.ك"],
    "KG": ["KGS", "с"],
    "LA": ["LAK", "₭"],
    "LV": ["LVL", "Ls"],
    "LB": ["LBP", "ل.ل"],
    "LS": ["LSL", "M"],
    "LR": ["LRD", "$"],
    "LY": ["LYD", "د.ل"],
    "LT": ["LTL", "Lt"],
    "LU": ["LU", "€"],
    "MO": ["MOP", "MOP"],
    "MK": ["MKD", "ден"],
    "MG": ["MGA", "Ar"],
    "MW": ["MWK", "K"],
    "MY": ["MYR", "RM"],
    "MV": ["MVR", "Rf"],
    "ML": ["XOF", "CFA"],
    "MT": ["MTL", "Lm"],
    "MH": ["USD", "$"],
    "MQ": ["EUR", "€"],
    "MR": ["MRU", "UM"],
    "MU": ["MUR", "Rs"],
    "YT": ["EUR", "€"],
    "MX": ["MXN", "$"],
    "FM": ["USD", "$"],
    "MD": ["MDL", "lei"],
    "MC": ["EUR", "€"],
    "MN": ["MNT", "₮"],
    "ME": ["EUR", "€"],
    "MS": ["USD", "$"],
    "MA": ["MAD", "د.م."],
    "MZ": ["MZN", "MT"],
    "MM": ["MMK", "Ks"],
    "NA": ["NAD", "$"],
    "NR": ["AUD", "$"],
    "NP": ["NPR", "₨"],
    "NL": ["NLG", "ƒ"],
    "NC": ["XPF", "₣"],
    "NZ": ["NZD", "$"],
    "NI": ["NIO", "C$"],
    "NE": ["NGN", "₦"],
    "NG": ["NGN", "₦"],
    "NU": ["NZD", "$"],
    "NF": ["AUD", "$"],
    "MP": ["USD", "$"],
    "NO": ["NOK", "kr"],
    "NP": ["NPR", "₨"],
    "OM": ["OMR", "﷼"],
    "PK": ["PKR", "₨"],
    "PA": ["PAB", "B/."],
    "PF": ["XPF", "₣"],
    "PG": ["PGK", "K"],
    "PY": ["PYG", "Gs"],
    "PE": ["PEN", "S/."],
    "PH": ["PHP", "₱"],
    "PL": ["PLN", "zł"],
    "PN": ["NZD", "$"],
    "PR": ["USD", "$"],
    "PT": ["EUR", "€"],
    "PW": ["USD", "$"],
    "QA": ["QAR", "﷼"],
    "RE": ["EUR", "€"],
    "RO": ["RON", "lei"],
    "RU": ["RUB", "₽"],
    "RW": ["RWF", "FRw"],
    "SH": ["SHP", "£"],
    "KN": ["XCD", "$"],
    "LC": ["XCD", "$"],
    "PM": ["EUR", "€"],
    "VC": ["XCD", "$"],
    "WS": ["WST", "T"],
    "SM": ["EUR", "€"],
    "ST": ["STN", "Db"],
    "SA": ["SAR", "﷼"],
    "SN": ["XOF", "CFA"],
    "SC": ["SCR", "₨"],
    "SL": ["SLL", "Le"],
    "SG": ["SGD", "$"],
    "SK": ["SKK", "Sk"],
    "SI": ["SIT", "€"],
    "SB": ["SBD", "$"],
    "SO": ["SOS", "Sh"],
    "ZA": ["ZAR", "R"],
    "ES": ["EUR", "€"],
    "LK": ["LKR", "Rs"],
    "SD": ["SDG", "ج.س"],
    "SR": ["SRD", "$"],
    "SS": ["SSP", "£"],
    "SY": ["SYP", "ل.س"],
    "SZ": ["SZL", "L"],
    "SE": ["SEK", "kr"],
    "CH": ["CHF", "Fr"],
    "TJ": ["TJS", "SM"],
    "TH": ["THB", "฿"],
    "TM": ["TMT", "T"],
    "TL": ["USD", "$"],
    "TG": ["GHS", "₵"],
    "TO": ["TOP", "T$"],
    "TT": ["TTD", "$"],
    "TN": ["TND", "د.ت"],
    "TR": ["TRY", "₺"],
    "TM": ["TMT", "T"],
    "TC": ["USD", "$"],
    "TV": ["AUD", "$"],
    "UG": ["UGX", "Sh"],
    "UA": ["UAH", "₴"],
    "GB": ["GBP", "£"],
    "US": ["USD", "$"],
    "UY": ["UYU", "$"],
    "UZ": ["UZS", "so'm"],
    "VU": ["VUV", "Vt"],
    "VE": ["VEF", "Bs"],
    "VN": ["VND", "₫"],
    "WF": ["XPF", "₣"],
    "YE": ["YER", "﷼"],
    "ZM": ["ZMW", "K"],
    "ZW": ["ZWL", "$"]
}

def get_user_location_info(ip_address):
    access_key = settings.IP_STACK_KEY  # Replace with your ipstack API key
    url = f'https://ipinfo.io/{ip_address}'

    # Call ipstack API to get geolocation data
    try:
        response = requests.get(url)
        data = response.json()
        print(data)
        country_code = data.get('country', 'US')  # Default to US if no country found
    except Exception as e:
        country_code = 'US'
        c_list = countries_currencies.get(country_code)
        print(f"Error fetching location data: {e}")
   
    
    
    c_list = countries_currencies.get(country_code)
    print("####################",country_code, c_list)
    return {
        'country_name': country_code,
        'currency_name': c_list[0] if c_list else 'USD',
        'currency_symbol': c_list[1] if c_list else '$'
    }



def get_cheapest_flight_price(flight_offers):
    if len(flight_offers) != 0:
        for i in flight_offers:
            if i.get('price'):
                return i.get('price')
    else:
        return 0


def get_flight_data(request):
    global currency
    origin = request.GET.get('origin')
    destination = request.GET.get('destination')
    departure_date = request.GET.get('departure_date')
    return_date = request.GET.get('return_date')
    direct_flight =  request.GET.get('nonStop')
    travelClass = request.GET.get('travelClass')
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@AFTER", direct_flight)

    print(origin,
    destination,
    departure_date,
    return_date)

    currency= {
        "currency_code": get_user_location_info(get_client_ip(request))['currency_name'],
        "currency_symbol": get_user_location_info(get_client_ip(request))['currency_symbol']
    }

    kwargs = {'originLocationCode': origin,
              'destinationLocationCode': destination,
              'departureDate': departure_date,
              'adults': 1,
              "currencyCode" : currency['currency_code'],
              'nonStop' : direct_flight,
              "travelClass" : travelClass
              }

    kwargs_metrics = {'originIataCode': origin,
                      'destinationIataCode': destination,
                      'departureDate': departure_date,
                       "currencyCode" : currency['currency_code']
                      }
    if return_date:
        kwargs['returnDate'] = return_date
    else:
        kwargs_metrics['oneWay'] = 'true'

    print(kwargs)
   
    if origin and destination and departure_date:
        is_good_deal = ''
        context = {
                
                'origin'  : origin,
                'destination': destination,
                'departure_date': departure_date,
                'return_date': return_date,
                
                
                
                'currency_symbol': currency['currency_symbol'],
                
                'direct_flights_not_available': direct_flights_not_available
                }
        try:
            flight_offers = get_flight_offers(**kwargs)
            context['flight_offers'] = flight_offers
        except:
            flight_offers = []
            metrics = get_flight_price_metrics(**kwargs_metrics)
            cheapest_flight = get_cheapest_flight_price(flight_offers)
            context['cheapest_flight'] = cheapest_flight
            if metrics is not None:
                is_good_deal = rank_cheapest_flight(cheapest_flight, metrics['first'], metrics['third'])
                is_cheapest_flight_out_of_range(cheapest_flight, metrics)
                context['metrics'] = metrics
                context['is_good_deal'] = is_good_deal
            else: 
                is_good_deal = "DATA NT"
            return JsonResponse(context)
            
        
       
        metrics = get_flight_price_metrics(**kwargs_metrics)
        cheapest_flight = get_cheapest_flight_price(flight_offers)
        is_good_deal = ''
        if metrics is not None:
            is_good_deal = rank_cheapest_flight(cheapest_flight, metrics['first'], metrics['third'])
            is_cheapest_flight_out_of_range(cheapest_flight, metrics)
    
        else: 
            is_good_deal = "DATA NT"
        

        # print(flight_offers)
        print('sending this')
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",flight_offers,"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
     
        
        return JsonResponse({
                        'flight_offers': flight_offers,
                        'origin'  : origin,
                        'destination': destination,
                        'departure_date': departure_date,
                        'return_date': return_date,
                        'metrics': metrics,
                        'cheapest_flight': cheapest_flight,
                        'is_good_deal': is_good_deal,
                        'currency_symbol': currency['currency_symbol'],
                        'cheapest_flight': cheapest_flight,
                        'direct_flights_not_available' : direct_flights_not_available
                        })



def prev_search_view(request, sid):
    current_search = SearchHistory.objects.get(search_id = sid)
    user = UserData.objects.get(email = request.session.get('user_email'))
    u_details = {'first_name': user.first_name,
                 'last_name': user.last_name,
                 'email': user.email}
    
    latest_search = SearchHistory.objects.filter(last_search_at__lt=current_search.last_search_at).order_by('-last_search_at')[:3]
    new_current_id = new_current = None
    if len(latest_search) != 0:
        new_current_id = latest_search[0].search_id
        new_current = SearchHistory.objects.get(search_id = new_current_id)
        
    if new_current.return_date:
        context = {'origin': new_current.origin_location.split(' - ')[0][-3:],
                'destination': new_current.destination_location.split(' - ')[0][-3:],
                'departure_date': str(new_current.from_date),
                'return_date': str(new_current.return_date),
                'isOneWay': bool(new_current.return_date),
                'adults': 1,
                'cabin_class': new_current.travel_class,
                'latest_search' : latest_search[1:],
                'user_details' : u_details,
                'search_id' : new_current_id,
                'nonStop': new_current.direct_flight
                }
    else: 
        context = {'origin': new_current.origin_location.split(' - ')[0][-3:],
                'destination': new_current.destination_location.split(' - ')[0][-3:],
                'departure_date': str(new_current.from_date),
                'isOneWay': bool(new_current.return_date),
                'adults': 1,
                'cabin_class': new_current.travel_class,
                'latest_search' : latest_search[1:],
                'user_details' : u_details,
                'search_id' : new_current_id,
                'nonStop': new_current.direct_flight
            }
    
    
    return render(request, 'search_results.html', context)