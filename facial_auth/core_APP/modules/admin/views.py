from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Models
from core_APP.models import User
# Dependencies
import base64
import json
import numpy as np
import face_recognition_models
import face_recognition
import cv2


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


@login_required
def add_student(request):
    if request.user.role != "ORG-ADMIN":
        return redirect("admin_dashboard")
    
    context = {}
    context.update({"user": request.user, "organization": request.user.organization})

    context.update({
        "primary": request.user.organization.primary_color or None,
        "secondary": request.user.organization.secondary_color or None,
        "tertiary": request.user.organization.tertiary_color or None
    })

    return render(request, "admin/add_student.html", context)


@csrf_exempt
def biometric_capture(request):

    if request.user.role != "ORG-ADMIN":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)

    image_data = data.get("image")

    if not image_data:
        return JsonResponse({"error": "No image provided"}, status=400)

    header, encoded = image_data.split(",", 1)

    image_bytes = base64.b64decode(encoded)

    nparr = np.frombuffer(image_bytes, np.uint8)

    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_encodings(rgb)

    if not faces:
        return JsonResponse({
            "error": "No face detected"
        }, status=400)

    embedding = faces[0].tolist()

    return JsonResponse({
        "success": True,
        "message": "Biometric captured",
        "embedding": embedding
    })


@csrf_exempt
@login_required
def add_student_api(request):

    if request.user.role != "ORG-ADMIN":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")
    embedding_raw = request.POST.get("embedding")

    if not username or not email or not password:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    if not embedding_raw:
        return JsonResponse({"error": "Biometric embedding missing"}, status=400)

    try:
        embedding = json.loads(embedding_raw)
    except Exception:
        return JsonResponse({"error": "Invalid embedding format"}, status=400)

    # prevent duplicate usernames
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)

    student = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role="STUDENT",
        organization=request.user.organization,
        face_encoding=embedding
    )

    return JsonResponse({
        "success": True,
        "message": "Student created",
        "student_id": student.id
    })


@csrf_exempt
@login_required
def recognize_face(request):

    if request.user.role != "ORG-ADMIN":
        return JsonResponse({"error":"Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error":"POST required"}, status=400)

    data = json.loads(request.body)
    image_data = data.get("image")

    if not image_data:
        return JsonResponse({"error":"No image"}, status=400)

    header, encoded = image_data.split(",",1)
    image_bytes = base64.b64decode(encoded)

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_encodings(rgb)

    if not faces:
        return JsonResponse({"match": False})

    incoming_embedding = faces[0]

    students = User.objects.filter(
        role="STUDENT",
        organization=request.user.organization,
        is_active=True
    )

    for student in students:
        # print(f"Student Username: {student.username}")
        known = np.array(student.face_encoding)

        match = face_recognition.compare_faces(
            [known],
            incoming_embedding,
            tolerance=0.5
        )[0]

        if match:
            return JsonResponse({
                "match": True,
                "username": student.username
            })

    return JsonResponse({"match": False})