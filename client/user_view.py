from .models import UserData
from django.shortcuts import render, redirect
from .decorators import login_is_required
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
import requests, json
from django.http import JsonResponse

#helper function
def create_user(validated_data):
    global user_data 
    # hash the password 
    hashed_password = make_password(validated_data['password1'])

    # create user in the db
    user = UserData(
        first_name=validated_data['first_name'],
        last_name=validated_data['last_name'],
        email=validated_data['email'],
        confirm_email=validated_data['confirm_email'],
        password=hashed_password,
        confirm_password=hashed_password
    )
    user.save()
    user_data = user
    return user

def register_view(request):
    if request.session.get('user_email'):
        return redirect('home')
    if request.method =='GET':
        return render(request, 'register.html')
    else:
        data = request.POST
        # Check if email already exists
        
        if UserData.objects.filter(email=data['email']).exists():
            return JsonResponse({'error' : "An account exists with these details. Please go to the login page."})
        
        if data['password1'] != data['password2']:
            return JsonResponse({'error' : "Both passwords must match."})
        
        # Check if email and confirm_email match
        if data['email'] != data['confirm_email']:
            return JsonResponse({'error' : "Email addresses must match."})
        
        #validate google captcha
       
        captcha_data = data.get('recaptcha_response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        captcha_data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': captcha_data
        }
        captcha_response = requests.post(url, data=captcha_data)
        result = captcha_response.json()
        if not result.get('success'):
            return JsonResponse({'error': "Invalid reCAPTCHA. Please try again."})
        
        #calling the function to create user in db
        create_user(data)
        
        #just starting the session
        request.session['user_id'] = user_data.id
        request.session['user_email'] = user_data.email
        
        
        #send welcome email
        subject = "Welcome to FlightChkr.com!"
        message = render_to_string('registration/register_email_body.html', {
            'user': user_data,
            'url': settings.SITE_URL + '/login/',
            'logo': settings.SITE_URL + '/' + settings.STATIC_URL + 'images/dark_logo.png'
            
        })
        send_mail(subject, 'This is a plain text body in case the email client does not support HTML', settings.EMAIL_HOST_USER, [user_data.email], html_message=message)


        return JsonResponse({'message': "Thank you. Your account was created successfully! You have also been logged in."})
      


def login_view(request):
    #checking if session is already started
    if request.session.get('user_id') and request.session.get('user_email'):
        #session is already started
        return redirect('home')

    else:
        if request.method == 'GET':
            return render(request, 'login.html')
        elif request.method == 'POST':
            
            user_email = request.POST.get('user_email')
            
            #validate google captcha
            captcha_data = request.POST.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            captcha_data = {
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': captcha_data
            }
            captcha_response = requests.post(url, data=captcha_data)
            result = captcha_response.json()
            if not result.get('success'):
                return render(request, 'login.html', {'error': "Invalid reCAPTCHA. Please try again."})
            
            
            try:
                user = UserData.objects.get(email= user_email)
            except UserData.DoesNotExist:
                return render(request, 'login.html', {'error': 'Invalid Email'})

            user_pass = request.POST.get('user_password')

            if check_password(user_pass, user.password):
                request.session['user_id'] = user.id
                request.session['user_email'] = user.email
                json_data = request.POST.get('non_auth_data')
                print(json_data)
                if json_data:
                    d = json.loads(json_data)
                    #other function
                    request.session['custom_data'] = d
                    request.session['custom_data'].update({'killit' : "yesyes"})
                    return redirect('search_flight')                     
                else:
                    
                    return redirect('home')
            else:
                return render(request, 'login.html', {'error': 'Invalid Password'})
        else:
            return render(request, 'login.html')


@login_is_required
def logout_view(request):
    if 'user_id' in request.session:
        request.session.flush()
    return redirect('home')






def forgot_password_view(request):
    if request.method == 'POST':
        try:
            user = UserData.objects.get(email = request.POST.get('user_email'))
        except:
            return render(request, 'forgot_password.html', {'message': 'Account with this email does not Exist!'})
        context = {
            "user_details" : {
                'first_name' : user.first_name,
                'last_name' : user.last_name,
                'email' : user.email
            }
        }
    
        form_data = request.POST
        if check_password(form_data['old_password'], user.password):
            if form_data['old_password'] != form_data['new_password']:
                user.password = make_password(form_data['new_password'])
                user.save()
                context.update({'message': "Your Password has been changed!"})
            else:
                context.update({'message': 'You can not use Old Password as New Password!'})
                
        else:
            context.update({'message': 'Old password is Incorrect!'})
        return render(request, 'forgot_password.html', context)
    else:
        try:
            user = UserData.objects.get(email = request.session.get('user_email'))
            context = {
                "user_details" : {
                    'first_name' : user.first_name,
                    'last_name' : user.last_name,
                    'email' : user.email
                }
            }
            return render(request, 'forgot_password.html', context)
        except:
            return render(request, 'forgot_password.html')
            
   

@login_is_required
def update_profile_view(request):
    user = UserData.objects.get(email= request.session.get('user_email'))
    context = {
        "user_details" : {
            'first_name' : user.first_name,
            'last_name' : user.last_name,
            'email' : user.email
        }
    }
    if request.method == 'POST':
        if check_password(request.POST.get('old_password'), user.password):
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.password = make_password(request.POST.get('new_password'))
            user.save()
            context.update({'message': "Your Details Have Been Updated!"})
            context['user_details']['first_name'] = request.POST.get('first_name')
            context['user_details']['last_name'] = request.POST.get('last_name')
        else:
            context.update({'message': "Incorrect Old Password!"})
    return render(request, 'update_profile.html', context)
