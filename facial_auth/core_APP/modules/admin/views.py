from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def admin_dashboard(request):
    if request.user.role != "ORG-ADMIN":
        # return redirect("student_dashboard") # Admin -> Student (in student view, Student -> Login/Home)
        return redirect("superadmin_dashboard") # TODO TODO TODO TODO TODO TODO
    
    context = {}
    context.update({"user": request.user, "organization": request.user.organization})

    context.update({
        "primary": request.user.organization.primary_color or None,
        "secondary": request.user.organization.secondary_color or None,
        "tertiary": request.user.organization.tertiary_color or None
    })

    return render(request, "admin/dashboard.html", context)