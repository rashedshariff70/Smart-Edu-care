from django.shortcuts import render, redirect
from django.contrib import messages
from university_app.models import UniversityRequest


def register_view(request):
    return render(request, "university_register.html")


def university_register(request):
    if request.method == "POST":
        college_id = request.POST.get("college_id", "").strip().upper()
        name = request.POST.get("name", "").strip()
        university_email = request.POST.get("university_email", "").strip()
        address = request.POST.get("address", "")
        state = request.POST.get("state", "")
        pincode = request.POST.get("pincode", "")
        country = request.POST.get("country", "")
        contact_number = request.POST.get("contact_number", "")
        website = request.POST.get("website") or None

        # 🔴 College ID check
        if UniversityRequest.objects.filter(college_id=college_id).exists():
            messages.warning(
                request,
                f"College ID '{college_id}' already exists. Please use a different ID."
            )
            return render(request, "university_register.html")

        # 🔴 College Name check (case-insensitive)
        if UniversityRequest.objects.filter(name__iexact=name).exists():
            messages.warning(
                request,
                f"A university with the name '{name}' already exists."
            )
            return render(request, "university_register.html")

        UniversityRequest.objects.create(
            college_id=college_id,
            name=name,
            university_email=university_email,
            address=address,
            state=state,
            pincode=pincode,
            country=country,
            contact_number=contact_number,
            website=website,
        )

        messages.success(
            request,
            f"Registration request sent successfully for {name}."
        )
        return redirect("university_reg_show")

    return render(request, "university_register.html")


def university_reg_show(request):
    universities = UniversityRequest.objects.all()
    return render(request, "university_reg_show.html", {"universities": universities})

from admin_app.models import ApprovedUniversityCredential


def university_login(request):
    """
    Login using College/University ID + Password
    Validated against ApprovedUniversityCredential table
    """

    if request.method == "POST":
        college_id = request.POST.get("college_id")
        password = request.POST.get("password")

        # Basic validation
        if not college_id or not password:
            messages.error(request, "Both fields are required.")
            return redirect("university_login")

        # Check credentials
        try:
            ApprovedUniversityCredential.objects.get(
                college_id=college_id,
                password=password
            )

            # OPTIONAL: set session
            request.session["college_id"] = college_id

            messages.success(request, "Login successful.")
            return redirect("approved_show")

        except ApprovedUniversityCredential.DoesNotExist:
            messages.error(request, "Invalid College ID or Password.")
            return redirect("university_login")

    return render(request, "university_login.html")