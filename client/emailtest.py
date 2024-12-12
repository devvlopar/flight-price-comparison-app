from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail


def emailtest(request):
    send_mail(
        'Test Email Subject',
        'Test email body',
        settings.EMAIL_HOST_USER,
        ['d1e2v3a4n5g@gmail.com'],
        fail_silently=False,
    )
    print('success')
    return HttpResponse("sdsdsdfds")
