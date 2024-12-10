from django.urls import path
from .views import support_view, about_view, search_flight_view, get_flight_data, prev_search_view
from .user_view import *
from .client_object import origin_airport_search_view, home_page, destination_airport_search_view, get_airport
from .on import add_data

urlpatterns = [
    path("", home_page, name='home'),
    path("login/", login_view, name='login'),
    path("register/", register_view, name='register'),
    path("logout/", logout_view, name='logout'),
    path("forgot_password/", forgot_password_view, name="forgot_password"),
    path("update_profile/", update_profile_view, name="update_profile"),
    path("origin_airport_search/", origin_airport_search_view, name="origin_airport_search"),
    path("destination_airport_search/", destination_airport_search_view, name="destination_airport_search"),
    path("about/", about_view, name='about'),
    path("support/", support_view, name='support'),
    path("search_flight/", search_flight_view, name="search_flight"),
    path("get_flight_data/", get_flight_data, name="get_flight_data"),
   
    path("get_airport/", get_airport, name= 'get_airport'),
    

    path("prev_search/<str:sid>", prev_search_view, name="prev_search")
    
]
