import json
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render


@csrf_exempt
def login_api(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    user = authenticate(request, username=username, password=password)

    if not user:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    login(request, user)
    
    return JsonResponse({
        "message": "Login successful",
        "role": user.role
    })
    

def login_page(request):
    return render(request, "auth/login.html")