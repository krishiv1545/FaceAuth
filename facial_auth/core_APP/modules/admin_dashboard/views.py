from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def admin_dashboard(request):
    username = request.user.username
    context = {}
    context.update({"username": username})
    return render(request, "admin_dashboard/dashboard.html", context)