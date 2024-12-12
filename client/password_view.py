# views.py
from .models import UserData
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import generate_reset_token, token_generator, is_token_expired
from django.conf import settings
from django.contrib.auth.hashers import make_password


def send_reset_email(user):
    # Generate token and timestamp
    token, timestamp = generate_reset_token(user)
    uidb64 = urlsafe_base64_encode(str(user.id).encode())

    # Generate the reset link
    reset_link = f"{settings.SITE_URL}/reset/{uidb64}/{token}/{timestamp}/"

    # Send the email
    subject = "Password Reset Request"
    message = render_to_string('registration/password_reset_email.html', {
        'user': user,
        'reset_link': reset_link,
        'logo' : "http://flightchkr.com/static/images/dark_logo.png"
    })
    send_mail(subject, 'This is a plain text body in case the email client does not support HTML', settings.EMAIL_HOST_USER, [user.email], html_message=message)

def request_reset_password(request):
    if request.method == "POST":
        email = request.POST.get('user_email')
        try:
            user = UserData.objects.get(email=email)
            send_reset_email(user)
            return JsonResponse({'message': "Thank you. An email has sent with password reset instructions. Please check your email inbox."})
        except UserData.DoesNotExist:
            return JsonResponse({'error': 'The email address is not registered in our system. Please check the email address you entered or click “Register” in the top menu to continue.”'})  # or show error message
    return render(request, 'forgot_password.html')

def reset_password_confirm(request, uidb64, token, timestamp):
    # try:
    # Decode user ID from URL
    uid = urlsafe_base64_decode(uidb64).decode()
    user = UserData.objects.get(id=uid)

    # Validate token and expiration
    if token_generator.check_token(user, token):
        if not is_token_expired(int(timestamp)):
            if request.method == "POST":
                # Allow user to reset the password
                new_password = request.POST.get('password')
                user.password = make_password(new_password)  
                user.save()
                return JsonResponse({'updated': True})
            print(uidb64, token, timestamp)
            return render(request, 'registration/password_reset_confirm.html', {'valid': True, 'uidb64':str(uidb64), 'token':token, 'timestamp':timestamp})
        else:
            return render(request, 'registration/password_reset_confirm.html', {'expired': True})
    # except (TypeError, ValueError, OverflowError, UserData.DoesNotExist):
    #     return render(request, 'registration/password_reset_confirm.html', {'invalid': True})


# views.py

def password_reset_done(request):
    return render(request, 'registration/password_reset_done.html')

def password_reset_complete(request):
    return render(request, 'registration/password_reset_complete.html')

def password_reset_invalid(request):
    return render(request, 'registration/password_reset_invalid.html')
