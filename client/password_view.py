# views.py
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import generate_reset_token

def send_reset_email(user):
    # Generate token and uidb64
    token = generate_reset_token(user)
    uidb64 = urlsafe_base64_encode(str(user.pk).encode()).decode()

    # Generate reset link
    reset_link = f"{settings.SITE_URL}/reset/{uidb64}/{token}/"

    # Send email
    subject = "Password Reset Request"
    message = render_to_string('registration/password_reset_email.html', {
        'user': user,
        'reset_link': reset_link,
    })
    send_mail(
        subject,
        message,
        'no-reply@yourdomain.com',  # From email
        [user.email],  # Recipient email
        fail_silently=False,
    )

def request_reset_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = get_user_model().objects.get(email=email)
            send_reset_email(user)
            return redirect('password_reset_done')
        except get_user_model().DoesNotExist:
            return redirect('password_reset_done')  # or show error message
    return render(request, 'registration/password_reset_request.html')

def reset_password_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
        if token_generator.check_token(user, token):
            if request.method == "POST":
                new_password = request.POST.get('password')
                user.password = new_password  # Save new password (hashed if required)
                user.save()
                return redirect('password_reset_complete')
            return render(request, 'registration/password_reset_confirm.html')
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        return redirect('password_reset_invalid')
