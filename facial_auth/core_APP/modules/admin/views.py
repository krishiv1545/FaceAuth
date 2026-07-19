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


def eye_aspect_ratio(eye_points):
    eye_points = np.array(eye_points)
    A = np.linalg.norm(eye_points[1] - eye_points[5])
    B = np.linalg.norm(eye_points[2] - eye_points[4])
    C = np.linalg.norm(eye_points[0] - eye_points[3])
    if C == 0:
        return None
    return (A + B) / (2.0 * C)


def get_ear_from_frame(rgb_frame):
    landmarks_list = face_recognition.face_landmarks(rgb_frame)
    if not landmarks_list:
        return None
    lm = landmarks_list[0]
    if "left_eye" not in lm or "right_eye" not in lm:
        return None
    left_ear = eye_aspect_ratio(lm["left_eye"])
    right_ear = eye_aspect_ratio(lm["right_eye"])
    if left_ear is None or right_ear is None:
        return None
    return (left_ear + right_ear) / 2.0


def has_blinked(ear_sequence, drop_ratio=0.75, recover_ratio=0.90):
    valid = [e for e in ear_sequence if e is not None]
    if len(valid) < 4:
        return False

    # Baseline = average of the "open eye" frames (first 2, likely eyes open)
    baseline = np.mean(valid[:2])
    if baseline == 0:
        return False

    closed_thresh = baseline * drop_ratio
    open_thresh = baseline * recover_ratio

    was_closed = False
    for ear in ear_sequence:
        if ear is None:
            continue
        if ear < closed_thresh:
            was_closed = True
        elif ear > open_thresh and was_closed:
            return True
    return False


def decode_frame(image_data):
    header, encoded = image_data.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


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

    images = data.get("images")

    # Backwards-compat: accept a single "image" too, but liveness needs a burst
    if not images and data.get("image"):
        images = [data.get("image")]

    if not images or not isinstance(images, list):
        return JsonResponse({"error": "No images"}, status=400)

    rgb_frames = []
    for image_data in images:
        try:
            rgb = decode_frame(image_data)
        except Exception:
            rgb = None
        if rgb is not None:
            rgb_frames.append(rgb)

    if not rgb_frames:
        return JsonResponse({"error": "Image decode failed"}, status=400)

    # --- Liveness check ---
    ear_sequence = [get_ear_from_frame(f) for f in rgb_frames]

    if not has_blinked(ear_sequence):
        return JsonResponse({"match": False, "liveness_failed": True})

    # --- Face match: use the last frame with a detectable face+encoding ---
    incoming_embedding = None
    for f in reversed(rgb_frames):
        faces = face_recognition.face_encodings(f)
        if faces:
            incoming_embedding = faces[0]
            break

    if incoming_embedding is None:
        return JsonResponse({"match": False})

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

        last_event = "ENTRY"
        last_event_type = (
            EventLog.objects
            .filter(user=student)
            .values_list("event", flat=True)
            .order_by("-timestamp")
            .first()
        )
        if last_event_type:
            last_event = last_event_type

        if match:
            return JsonResponse({
                "match": True,
                "student": {
                    "id": student.id,
                    "full_name": student.get_full_name() or student.username,
                    "enrollment": getattr(student, "enrollment_no", ""),
                    "email": student.email,
                    "organization": student.organization.name if student.organization else "",
                },
                "last_event": last_event,
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