from django.db import models
import uuid
# Create your models here.

class UserData(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    confirm_email = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=200)
    confirm_password = models.CharField(max_length=200)

    def __str__(self):
        return self.email

class SearchHistory(models.Model):
    travel_classes = (
        ( 'ECONOMY', 'ECONOMY'), 
        ( 'PREMIUM_ECONOMY' , 'PREMIUM_ECONOMY'), 
        ( 'BUSINESS', 'BUSINESS'),
        ( 'FIRST' , 'FIRST')
    )

    search_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    origin_location = models.CharField(max_length=50)
    destination_location = models.CharField(max_length=50)
    travel_class = models.CharField(choices=travel_classes, max_length=50, default='ECONOMY')
    searched_at = models.DateTimeField(auto_now_add=True)
    last_search_at = models.DateTimeField(auto_now=True)
    from_date = models.DateField()
    is_one_way = models.BooleanField(default=False)
    return_date = models.DateField(null=True, blank=True)
    direct_flight = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return "from " + self.origin_location + " to " + self.destination_location + "by" + self.user.email
        
        
class Airports(models.Model):
    icao = models.CharField(max_length=10)
    iata = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=5)
    elevation = models.IntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    tz = models.CharField(max_length=255)

    def __str__(self):
        return self.name