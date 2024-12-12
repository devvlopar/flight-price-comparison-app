from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail


# def emailtest(request):
#     send_mail(
#         'Test Email Subject',
#         'Test email body',
#         settings.EMAIL_HOST_USER,
#         ['d1e2v3a4n5g@gmail.com'],
#         fail_silently=False,
#     )
#     print('success')
#     return HttpResponse("sdsdsdfds")
from amadeus.client.errors import ServerError
from .views import amadeus_client

def emailtest(request):
    # try:
        # Example API call
    response = amadeus_client.shopping.flight_offers_search.get(
        originLocationCode='NYC',
        destinationLocationCode='LON',
        departureDate='2024-12-15',
        adults=1
    )
    return HttpResponse(str(response))
    # except ServerError as e:
        # print(f"ServerError: {e}")
        # Log the error and notify the administrator