from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Models
from core_APP.models import User, Organization, EventLog
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

    print("biometric_capture called")

    print("Checking user role...")
    if request.user.role != "ORG-ADMIN":
        print("Unauthorized user:", request.user)
        return JsonResponse({"error": "Unauthorized"}, status=403)

    print("Checking request method:", request.method)
    if request.method != "POST":
        print("Invalid method used")
        return JsonResponse({"error": "POST required"}, status=400)

    print("Reading request body...")
    try:
        data = json.loads(request.body)
        print("JSON parsed successfully")
    except Exception as e:
        print("JSON parsing failed:", e)
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    print("Extracting image data...")
    image_data = data.get("image")

    if not image_data:
        print("No image provided in payload")
        return JsonResponse({"error": "No image provided"}, status=400)

    print("Image data received, splitting header...")
    try:
        header, encoded = image_data.split(",", 1)
        print("Header:", header[:50])
    except Exception as e:
        print("Image split failed:", e)
        return JsonResponse({"error": "Invalid image format"}, status=400)

    print("Decoding base64 image...")
    try:
        image_bytes = base64.b64decode(encoded)
        print("Base64 decoded, byte length:", len(image_bytes))
    except Exception as e:
        print("Base64 decode failed:", e)
        return JsonResponse({"error": "Base64 decode failed"}, status=400)

    print("Converting bytes to numpy array...")
    nparr = np.frombuffer(image_bytes, np.uint8)
    print("Numpy array created:", nparr.shape)

    print("Decoding image with OpenCV...")
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        print("OpenCV failed to decode image")
        return JsonResponse({"error": "Invalid image data"}, status=400)

    print("Image decoded, shape:", img.shape)

    print("Converting BGR to RGB...")
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    print("Running face_recognition.face_encodings...")
    faces = face_recognition.face_encodings(rgb)

    print("Number of faces detected:", len(faces))

    if not faces:
        print("No face detected in image")
        return JsonResponse({
            "error": "No face detected"
        }, status=400)

    print("Face detected, extracting embedding...")
    embedding = faces[0].tolist()

    print("Embedding length:", len(embedding))

    print("Returning success response")
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

    enrollment_no = request.POST.get("enrollment_no")
    print(f"Enrollment No: {enrollment_no}")
    username = request.POST.get("username")
    print(f"Username: {username}")
    first_name = request.POST.get("first_name")
    print(f"First Name: {first_name}")
    last_name = request.POST.get("last_name")
    print(f"Last Name: {last_name}")
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
        password=password
    )

    student.first_name = first_name
    student.last_name = last_name
    student.enrollment_no = enrollment_no
    student.role = "STUDENT"
    student.organization = request.user.organization
    student.face_encoding = embedding

    student.save()

    return JsonResponse({
        "success": True,
        "message": "Student created",
        "student_id": student.id
    })


@csrf_exempt
@login_required
def recognize_face(request):

    if request.user.role != "ORG-ADMIN":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    image_data = data.get("image")

    if not image_data:
        return JsonResponse({"error": "No image"}, status=400)

    try:
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
    except Exception:
        return JsonResponse({"error": "Invalid image format"}, status=400)

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return JsonResponse({"error": "Image decode failed"}, status=400)

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

        if not student.face_encoding:
            continue

        known = np.array(student.face_encoding)

        match = face_recognition.compare_faces(
            [known],
            incoming_embedding,
            tolerance=0.5
        )[0]

        if match:
            # Returning log
            print(f"Matched {student.get_full_name()} ({student.username})")
            print(f"Enrollment: {student.enrollment_no}")
            return JsonResponse({
                "match": True,
                "student": {
                    "id": student.id,
                    "full_name": student.get_full_name() or student.username,
                    "enrollment": getattr(student, "enrollment_no", ""),
                    "email": student.email,
                    "organization": student.organization.name if student.organization else "",
                }
            })

    return JsonResponse({"match": False})


@csrf_exempt
@login_required
def create_event_log(request):

    if request.user.role != "ORG-ADMIN":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    student_id = data.get("student_id")
    event = data.get("event")

    if event not in ["ENTRY", "EXIT"]:
        return JsonResponse({"error": "Invalid event type"}, status=400)

    try:
        student = User.objects.get(
            id=student_id,
            role="STUDENT",
            organization=request.user.organization
        )
    except User.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    from core_APP.models import EventLog

    log = EventLog.objects.create(
        user=student,
        event=event
    )

    return JsonResponse({
        "success": True,
        "message": "Event logged",
        "log_id": log.id
    })


@login_required
def student_activity_view(request):

    if request.user.role != "ORG-ADMIN":
        return redirect("admin_dashboard")
    
    student_activity = EventLog.objects.filter(
        user__role="STUDENT",
        user__organization=request.user.organization
    ).select_related("user").order_by("-timestamp")

    context = {}
    context.update({"student_activity": student_activity})
    context.update({"user": request.user, "organization": request.user.organization})
    context.update({
        "primary": request.user.organization.primary_color or None,
        "secondary": request.user.organization.secondary_color or None,
        "tertiary": request.user.organization.tertiary_color or None
    })

    return render(request, "admin/student_activity.html", context)