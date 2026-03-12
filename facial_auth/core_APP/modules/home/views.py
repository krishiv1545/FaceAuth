from django.shortcuts import redirect


def home(request):
    return redirect("login_page")