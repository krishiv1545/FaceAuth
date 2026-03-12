from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
# Import models
from core_APP.models import Organization, User


@login_required
def superadmin_dashboard(request):
    if request.user.role != "SUPERADMIN":
        return redirect("admin_dashboard") # Superadmin -> Admin (in admin route, Admin -> Student)
    
    username = request.user.username
    context = {}
    context.update({"username": username})
    
    return render(request, "superadmin/dashboard.html", context)


@login_required
def organizations_view(request):
    if request.user.role != "SUPERADMIN":
        return redirect("superadmin_dashboard")
    
    username = request.user.username
    context = {}
    context.update({"username": username})
    
    # Fetch Organizations
    organizations = Organization.objects.all()
    context.update({"organizations": organizations})

    return render(request, "superadmin/organizations.html", context)


@csrf_exempt
@login_required
def create_organization(request):

    if request.user.role != "SUPERADMIN":
        return JsonResponse({"error":"Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error":"POST required"}, status=400)

    org_name = request.POST.get("org_name")
    primary = request.POST.get("primary_color")
    secondary = request.POST.get("secondary_color")
    tertiary = request.POST.get("tertiary_color")

    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")

    logo = request.FILES.get("logo")

    org = Organization.objects.create(
        name=org_name,
        primary_color=primary,
        secondary_color=secondary,
        tertiary_color=tertiary,
        logo=logo
    )

    admin = User.objects.create(
        username=username,
        email=email,
        password=make_password(password),
        role="ORG-ADMIN",
        organization=org
    )

    return JsonResponse({
        "message":"Organization and admin created",
        "org_id": org.id
    })