from django.shortcuts import redirect

def login_is_required(fun1):
    def logic_fun1(request, *args):
        if not request.session.get('user_id'):
            return redirect('login')
        return fun1(request, *args)
    return logic_fun1