from django.shortcuts import render,HttpResponse,redirect
import pandas as pd 
from django.contrib import messages
from django.conf import settings  
import os
import csv
from io import TextIOWrapper
from django.http import HttpResponseRedirect
import os
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

# ── same path as the big views.py ──────────────────────────────────────────
PASSWORD_FILES_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "student_and_parent_logins"
)


import os
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

# SAME PATH
PASSWORD_FILES_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "student_and_parent_logins"
)


def parent_login(request):
    """
    Parent login (uses SAME Excel as student login)
    Columns required:
    StudentID, AISHE_Code, student_password
    """

    college_files = []

    # ✅ LOAD FILES
    if os.path.exists(PASSWORD_FILES_DIR):
        for file in os.listdir(PASSWORD_FILES_DIR):
            if file.endswith(".xlsx") or file.endswith(".xls"):
                college_files.append({
                    "name": file.replace(".xlsx", "").replace(".xls", ""),
                    "file": file,
                })

    if request.method == "POST":
        selected_file = request.POST.get("college_file", "").strip()
        student_id    = request.POST.get("student_id", "").strip()   # ✅ FIXED
        aishe_code    = request.POST.get("aishe_code", "").strip()
        password      = request.POST.get("password", "").strip()

        file_path = os.path.join(PASSWORD_FILES_DIR, selected_file)

        try:
            df = pd.read_excel(file_path)

            # ✅ CLEAN COLUMN NAMES
            df.columns = df.columns.str.strip()

            # ✅ SAME AS STUDENT LOGIN
            required_columns = ["StudentID", "AISHE_Code", "student_password"]

            if not all(col in df.columns for col in required_columns):
                messages.error(request, "Excel format is incorrect ❌")
                return render(request, "parent_login.html", {"college_files": college_files})

            # ✅ MATCH ROW (SAME LOGIC)
            match = df[
                (df["StudentID"].astype(str).str.strip()        == student_id) &
                (df["AISHE_Code"].astype(str).str.strip()       == aishe_code) &
                (df["student_password"].astype(str).str.strip() == password)
            ]

            if not match.empty:
                row = match.iloc[0]

                # ✅ IMPORT CONTEXT BUILDERS
                from .views import build_parent_context, get_student_full_data

                full_data = get_student_full_data(student_id, aishe_code)
                relation  = "Parent"

                if full_data:
                    build_parent_context(student_id, aishe_code, full_data, relation)

                # ✅ SESSION KEYS (FOR CHAT)
                request.session["parent_student_id"]   = student_id
                request.session["parent_aishe_code"]   = aishe_code
                request.session["parent_relation"]     = relation
                request.session["parent_student_name"] = str(
                    row.get("Name", student_id)
                ).strip() or student_id

                messages.success(request, "Login Successful ✅")
                return redirect("parent_chat_room")

            else:
                messages.error(request, "Invalid credentials ❌")

        except Exception as e:
            messages.error(request, f"Error reading file: {str(e)}")

    return render(request, "parent_login.html", {"college_files": college_files})

def student_ml_home(request):
    return render(request,'student_ml_home.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrationForm, LoginForm
from .models import StudentRegistration, StudentLogin


def student_register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Save registration data
            student = form.save(commit=False)
            student.set_password(form.cleaned_data['password'])
            student.save()

            # Create separate login record
            StudentLogin.objects.create(
                registration=student,
                college_id=student.college_id,
                college_name=student.college_name,
            ).set_password(form.cleaned_data['password'])

            messages.success(request, "Registration successful! You can now login.")
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'student_register.html', {'form': form})


import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import pandas as pd
from pathlib import Path


def student_ml_upload_data(request):
    """
    View for students to upload datasets (CSV, Excel, JSON)
    Shows preview of uploaded data in the template
    """
    context = {
        'title': 'Upload Dataset - ML Student Zone',
        'uploaded': False,
        'filename': None,
        'preview_data': None,
        'columns': None,
        'row_count': 0,
        'col_count': 0,
        'file_size_mb': 0,
        'error': None
    }

    # Directory where uploaded files will be temporarily/permanently saved
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'student_datasets')
    os.makedirs(upload_dir, exist_ok=True)

    if request.method == 'POST' and request.FILES.get('dataset'):
        uploaded_file = request.FILES['dataset']
        
        # Basic validation
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.json']
        file_ext = Path(uploaded_file.name).suffix.lower()
        
        if file_ext not in allowed_extensions:
            messages.error(request, f'Unsupported file format. Please upload one of: {", ".join(allowed_extensions)}')
            return render(request, 'student_ml_upload_data.html', context)

        try:
            # Option 1: Save file permanently (recommended for student projects)
            fs = FileSystemStorage(location=upload_dir)
            saved_filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(saved_filename)

            # Option 2: Temporary processing without saving (uncomment if preferred)
            # file_path = None
            # content = uploaded_file.read()
            # But then you'll need different handling for each format

            # Read preview data
            preview_rows = 100  # How many rows to show in preview

            if file_ext == '.csv':
                df = pd.read_csv(file_path, nrows=preview_rows)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=preview_rows)
            elif file_ext == '.json':
                df = pd.read_json(file_path, nrows=preview_rows, orient='records')
            else:
                raise ValueError("Unsupported file type")

            # Prepare data for template
            context.update({
                'uploaded': True,
                'filename': uploaded_file.name,
                'preview_data': df.to_dict('records'),  # list of dictionaries
                'columns': df.columns.tolist(),
                'row_count': len(df),  # preview rows count
                'col_count': len(df.columns),
                'file_size_mb': round(uploaded_file.size / (1024 * 1024), 2),
                'saved_path': saved_filename,  # relative path for later use
            })

            messages.success(request, f'Dataset "{uploaded_file.name}" uploaded successfully!')

        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            context['error'] = str(e)

    return render(request, 'student_ml_upload_data.html', context)

# views.py (Django function)
from django.shortcuts import render

def student_ml_view_models(request):
    # This view renders the HTML template for viewing models.
    # No dynamic data fetching is needed as all results are hardcoded in JS for demo.
    # In a real app, you could fetch user-specific models from DB and pass as JSON.
    context = {
        "page_title": "My Trained Models",
        "domains": [
            {"value": "exam_performance", "label": "Student Exam Performance"},
            {"value": "alcohol_use", "label": "Student Alcohol Consumption"},
            {"value": "mental_health", "label": "Student Mental Health"},
            {"value": "performance_factors", "label": "Student Performance Factors"},
            {"value": "stress_factors", "label": "Student Stress Factors"},
        ]
    }
    return render(request, 'student_ml_view_models.html', context)

from django.shortcuts import render
from django.conf import settings
import os
import joblib
import pandas as pd


# Helper: Encode categorical inputs for alcohol domain
def encode_alcohol_inputs(input_data):
    mapping = {
        'school': {'GP': 0, 'MS': 1},
        'sex': {'F': 0, 'M': 1},
        'address': {'U': 0, 'R': 1},
        'schoolsup': {'yes': 1, 'no': 0},
        'famsup': {'yes': 1, 'no': 0},
        'nursery': {'yes': 1, 'no': 0},
        'higher': {'yes': 1, 'no': 0},
        'romantic': {'yes': 1, 'no': 0}
    }
    for key, map_dict in mapping.items():
        if key in input_data:
            input_data[key] = map_dict.get(input_data[key], input_data[key])  # fallback to original if not found
    return input_data


def student_ml_prediction(request):
    context = {}
    BASE_ML_PATH = os.path.join(settings.BASE_DIR, 'static', 'data', 'ML')

    if request.method == 'POST':
        domain = request.POST.get('domain')
        try:
            # 1. Exam Performance
            if domain == 'exam_performance':
                model_path = os.path.join(BASE_ML_PATH, 'Perfomance_Exam', 'neural_network_model.pkl')
                prep_path = os.path.join(BASE_ML_PATH, 'Perfomance_Exam', 'preprocessor.pkl')
                model = joblib.load(model_path)
                preprocessor = joblib.load(prep_path)

                input_data = {
                    'gender': request.POST.get('gender', ''),
                    'race/ethnicity': request.POST.get('race_ethnicity', ''),
                    'parental level of education': request.POST.get('parental_education', ''),
                    'lunch': request.POST.get('lunch', ''),
                    'test preparation course': request.POST.get('test_preparation_course', ''),
                    'reading score': float(request.POST.get('reading_score') or 0),
                    'writing score': float(request.POST.get('writing_score') or 0)
                }

                df = pd.DataFrame([input_data])
                processed = preprocessor.transform(df)
                prediction = model.predict(processed)[0]

                if prediction >= 85:
                    suggestion = "Excellent! Encourage advanced problem-solving."
                elif prediction >= 70:
                    suggestion = "Good! Focus on consistency."
                elif prediction >= 50:
                    suggestion = "Average. Needs more practice."
                else:
                    suggestion = "At Risk. Immediate remedial support needed."

                context['result'] = {'prediction': f"{prediction:.2f}", 'suggestion': suggestion}

            # 2. Alcohol Use
            elif domain == 'alcohol_use':
                model_path = os.path.join(BASE_ML_PATH, 'Student_alcohol_idea', 'xgboost_model.pkl')
                model = joblib.load(model_path)

                input_data = {
                    'school': request.POST.get('school', ''),
                    'sex': request.POST.get('sex', ''),
                    'address': request.POST.get('address', ''),
                    'studytime': float(request.POST.get('studytime') or 0),
                    'schoolsup': request.POST.get('schoolsup', ''),
                    'famsup': request.POST.get('famsup', ''),
                    'nursery': request.POST.get('nursery', ''),
                    'higher': request.POST.get('higher', ''),
                    'romantic': request.POST.get('romantic', ''),
                    'famrel': float(request.POST.get('famrel') or 0),
                    'goout': float(request.POST.get('goout') or 0),
                    'absences': float(request.POST.get('absences') or 0)
                }

                input_data = encode_alcohol_inputs(input_data)
                df = pd.DataFrame([input_data])
                prediction = model.predict(df)[0]

                suggestion = (
                    "Alcohol user detected → Recommend counseling..." 
                    if prediction == 1 else 
                    "No alcohol usage detected → Keep it up!"
                )
                context['result'] = {'prediction': 'Alcohol User' if prediction == 1 else 'Non-User', 'suggestion': suggestion}

            # 3. Mental Health
            elif domain == 'mental_health':
                model_path = os.path.join(BASE_ML_PATH, 'Student_mental_health', 'DT.joblib')
                model = joblib.load(model_path)

                input_data = {
                    'Choose your gender': request.POST.get('gender', ''),
                    'Age': float(request.POST.get('age') or 0),
                    'Course': request.POST.get('course', ''),
                    'Year of Study': request.POST.get('year_of_study', ''),
                    'CGPA': float(request.POST.get('cgpa') or 0),
                    'Marital Status': request.POST.get('marital_status', ''),
                    'Do you have Anxiety?': request.POST.get('anxiety', ''),
                    'Do you have Panic attack?': request.POST.get('panic_attack', ''),
                    'Did you seek any specialist for a treatment?': request.POST.get('specialist_treatment', '')
                }

                # Very important: match exact order & names
                df = pd.DataFrame([input_data], columns=model.feature_names_in_)
                prediction = model.predict(df)[0]

                suggestion = (
                    "Depression detected → Seek counseling..." 
                    if prediction == 1 else 
                    "No depression detected → Stay balanced."
                )
                context['result'] = {
                    'prediction': 'Depression Detected' if prediction == 1 else 'No Depression',
                    'suggestion': suggestion
                }

            # 4. Performance Factors – FIXED VERSION
            elif domain == 'performance_factors':
                model_path = os.path.join(BASE_ML_PATH, 'Student_perforamnce_factors', 'random_forest_regression_model.pkl')
                model = joblib.load(model_path)

                # Define ALL features in the EXACT ORDER the model expects
                feature_order = [
                    "Hours_Studied",
                    "Attendance",
                    "Parental_Involvement",
                    "Access_to_Resources",
                    "Extracurricular_Activities",
                    "Previous_Scores",
                    "Internet_Access",
                    "Tutoring_Sessions",
                    "Teacher_Quality",
                    "Peer_Influence",
                    "Learning_Disabilities",
                    "Distance_from_Home"
                ]

                # Read values in correct order
                input_values = [
                    float(request.POST.get("Hours_Studied") or 0),
                    float(request.POST.get("Attendance") or 0),
                    request.POST.get("Parental_Involvement", ""),
                    request.POST.get("Access_to_Resources", ""),
                    request.POST.get("Extracurricular_Activities", ""),
                    float(request.POST.get("Previous_Scores") or 0),
                    request.POST.get("Internet_Access", ""),
                    float(request.POST.get("Tutoring_Sessions") or 0),
                    request.POST.get("Teacher_Quality", ""),
                    request.POST.get("Peer_Influence", ""),
                    request.POST.get("Learning_Disabilities", ""),
                    request.POST.get("Distance_from_Home", "")
                ]

                # Create DataFrame with EXACT column names and order
                df = pd.DataFrame([input_values], columns=feature_order)

                prediction = model.predict(df)[0]

                if prediction >= 70:
                    suggestion = "Great! Keep maintaining your study habits."
                elif 50 <= prediction < 70:
                    suggestion = "Average performance. Consider reviewing weak topics and practice more."
                else:
                    suggestion = "Low performance. Seek extra help or tutoring sessions to improve."

                context['result'] = {'prediction': f"{prediction:.2f}", 'suggestion': suggestion}

            # 5. Stress Factors
            elif domain == 'stress_factors':
                model_path = os.path.join(BASE_ML_PATH, 'Student_stress_factors', 'gradient_boosting_model.pkl')
                model = joblib.load(model_path)

                input_data = {
                    key: float(request.POST.get(key) or 0)
                    for key in [
                        'anxiety_level', 'self_esteem', 'depression', 'headache', 'blood_pressure',
                        'sleep_quality', 'academic_performance', 'teacher_student_relationship',
                        'future_career_concerns', 'social_support', 'extracurricular_activities', 'bullying'
                    ]
                }

                df = pd.DataFrame([input_data])
                prediction = model.predict(df)[0]

                if prediction == 0:
                    suggestion = "Low stress: Maintain current lifestyle..."
                elif prediction == 1:
                    suggestion = "Moderate stress: Consider short breaks..."
                elif prediction == 2:
                    suggestion = "High stress: Seek professional counseling..."
                else:
                    suggestion = "Unknown stress level."

                context['result'] = {'prediction': int(prediction), 'suggestion': suggestion}

        except FileNotFoundError as e:
            context['error'] = f"Model file not found: {str(e)}"
        except ValueError as ve:
            context['error'] = f"Invalid numeric input: {str(ve)}"
        except Exception as e:
            context['error'] = f"Error during prediction: {str(e)}"

    return render(request, 'student_ml_prediction.html', context)

import os
import json
import requests
import pandas as pd
import base64
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────────
# LOAD .env FIRST
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# API KEYS from .env
# ─────────────────────────────────────────────────────────────────────────────
GROQ_KEY_LLAMA   = os.getenv("GROQ_API_KEY2")
GROQ_KEY_GPT     = os.getenv("GROQ_API_KEY")
GROQ_KEY_WHISPER = os.getenv("GROQ_API_KEY3")

if not GROQ_KEY_LLAMA:
    raise ValueError("❌ GROQ_API_KEY2 not found in .env  (LLaMA 70B)")
if not GROQ_KEY_GPT:
    raise ValueError("❌ GROQ_API_KEY not found in .env   (GPT-OSS 120B)")
if not GROQ_KEY_WHISPER:
    raise ValueError("❌ GROQ_API_KEY3 not found in .env  (Whisper Large v3)")

# ─────────────────────────────────────────────────────────────────────────────
# MODEL DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
MODELS = {
    "llama": {
        "model_id": "meta-llama/llama-4-scout-17b-16e-instruct",
        "api_key":  GROQ_KEY_LLAMA,
        "label":    "LLaMA 4 Scout – 17B",
        "icon":     "🦙",
    },
    "gpt": {
        "model_id": "openai/gpt-oss-120b",
        "api_key":  GROQ_KEY_GPT,
        "label":    "GPT-OSS – 120B",
        "icon":     "✨",
    },
}
DEFAULT_MODEL = "llama"

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
PASSWORD_FILES_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "student_and_parent_logins"
)

STUDENT_CONTEXT_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "student_chat_contexts"
)

def get_rules_dir(aishe_code):
    return os.path.join(
        settings.BASE_DIR,
        "static", "data", "uploads", "AISHE_CODE",
        aishe_code.strip(), "rules"
    )


# ═════════════════════════════════════════════════════════════════════════════
# PDF / WORD READERS
# ═════════════════════════════════════════════════════════════════════════════

def read_pdf_text(filepath):
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print(f"⚠️  PDF read error ({filepath}): {e}")
        return ""


def read_word_text(filepath):
    try:
        from docx import Document
        doc  = Document(filepath)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text.strip()
    except Exception as e:
        print(f"⚠️  Word read error ({filepath}): {e}")
        return ""


def read_college_rules(aishe_code):
    rules_dir = get_rules_dir(aishe_code)
    if not os.path.exists(rules_dir):
        return ""
    combined = ""
    for filename in os.listdir(rules_dir):
        filepath = os.path.join(rules_dir, filename)
        ext      = os.path.splitext(filename.lower())[1]
        if ext == ".pdf":
            text = read_pdf_text(filepath)
        elif ext in [".doc", ".docx"]:
            text = read_word_text(filepath)
        else:
            continue
        if text:
            combined += f"\n--- Rules from: {filename} ---\n{text}\n"
            print(f"✅  Rules loaded: {filepath}")
    return combined.strip()


# ═════════════════════════════════════════════════════════════════════════════
# ── CORE FIX: _load_student_row_from_excel ──────────────────────────────────
#
#  Mirrors exactly what parent_login does:
#    1. Scan every file in PASSWORD_FILES_DIR
#    2. Normalise column names (strip whitespace)
#    3. Match StudentID + AISHE_Code + student_password in one pass
#    4. Return the matched row as a plain dict  ← primary data source
#    5. NEVER depend on get_student_full_data as primary; use it only to enrich
#
#  Why parent works and student didn't:
#    parent_login reads the row directly and falls back to the row dict if
#    get_student_full_data returns None.
#    student_login_view called get_student_full_data as PRIMARY and had NO
#    fallback, so any column-name mismatch silently killed the whole login.
# ═════════════════════════════════════════════════════════════════════════════

def _load_student_row_from_excel(student_id, aishe_code, password, selected_file=None):
    """
    Scan PASSWORD_FILES_DIR for a matching row.
    Returns (matched_dict, filename) or (None, None).

    Logic is identical to parent_login's DataFrame matching block.
    """
    if not os.path.exists(PASSWORD_FILES_DIR):
        print(f"⚠️  Directory not found: {PASSWORD_FILES_DIR}")
        return None, None

    for filename in sorted(os.listdir(PASSWORD_FILES_DIR)):
        if not filename.lower().endswith((".xlsx", ".xls", ".csv")):
            continue
        filepath = os.path.join(PASSWORD_FILES_DIR, filename)
        try:
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(filepath, dtype=str).fillna("")
            else:
                df = pd.read_excel(filepath, dtype=str).fillna("")

            # Normalise column names exactly like parent_login
            df.columns = df.columns.str.strip()

            # Need at least these three columns
            if not {"StudentID", "AISHE_Code", "student_password"}.issubset(df.columns):
                print(f"⚠️  Skipping {filename}: missing required columns "
                      f"(have: {list(df.columns)})")
                continue

            # Normalise values  ← same as parent_login
            df["StudentID"]        = df["StudentID"].astype(str).str.strip()
            df["AISHE_Code"]       = df["AISHE_Code"].astype(str).str.strip()
            df["student_password"] = df["student_password"].astype(str).str.strip()

            match = df[
                (df["StudentID"]        == student_id.strip()) &
                (df["AISHE_Code"]       == aishe_code.strip()) &
                (df["student_password"] == password.strip())
            ]

            if not match.empty:
                print(f"✅  Student found in {filename}")
                row_dict = match.iloc[0].to_dict()
                return row_dict, filename

        except Exception as e:
            print(f"⚠️  Error reading {filename}: {e}")

    print(f"❌  No match for StudentID={student_id!r} AISHE={aishe_code!r}")
    return None, None


# ═════════════════════════════════════════════════════════════════════════════
# get_student_full_data  (kept for compatibility, used as ENRICHMENT only)
# ═════════════════════════════════════════════════════════════════════════════

def get_student_full_data(student_id, aishe_code):
    """
    Fetch complete student data. Used as an enrichment step AFTER primary login
    succeeds.  Returns dict or None — callers must handle None gracefully.
    """
    if not os.path.exists(PASSWORD_FILES_DIR):
        return None

    for filename in os.listdir(PASSWORD_FILES_DIR):
        if not filename.lower().endswith((".xlsx", ".xls", ".csv")):
            continue
        filepath = os.path.join(PASSWORD_FILES_DIR, filename)
        try:
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(filepath, dtype=str).fillna("")
            else:
                df = pd.read_excel(filepath, dtype=str).fillna("")

            df.columns = [c.strip() for c in df.columns]

            if "StudentID" not in df.columns or "AISHE_Code" not in df.columns:
                continue

            df["StudentID"]  = df["StudentID"].astype(str).str.strip()
            df["AISHE_Code"] = df["AISHE_Code"].astype(str).str.strip()

            match = df[
                (df["StudentID"]  == student_id.strip()) &
                (df["AISHE_Code"] == aishe_code.strip())
            ]
            if not match.empty:
                print(f"✅  Enrichment data found in {filename}")
                return match.iloc[0].to_dict()

        except Exception as e:
            print(f"⚠️  Error reading {filename}: {e}")

    return None


# ═════════════════════════════════════════════════════════════════════════════
# CONTEXT BUILDING  (unchanged in logic, added robust name extraction)
# ═════════════════════════════════════════════════════════════════════════════

def build_student_context(student_id, aishe_code, student_data):
    os.makedirs(STUDENT_CONTEXT_DIR, exist_ok=True)
    context_path = os.path.join(STUDENT_CONTEXT_DIR, f"{aishe_code}_{student_id}.txt")

    student_section = "=== STUDENT INFORMATION ===\n"
    for key, value in student_data.items():
        student_section += f"{key}: {value}\n"

    rules_text = read_college_rules(aishe_code)
    rules_section = (
        f"\n=== COLLEGE RULES ===\n{rules_text}\n"
        if rules_text else
        "\n=== COLLEGE RULES ===\n(No rules file uploaded yet)\n"
    )

    with open(context_path, "w", encoding="utf-8") as f:
        f.write(student_section)
        f.write(rules_section)

    print(f"✅  Context written → {context_path}")
    return context_path


def read_student_context(student_id, aishe_code):
    context_path = os.path.join(
        STUDENT_CONTEXT_DIR, f"{aishe_code}_{student_id}.txt"
    )
    print(f"📂 Looking for context: {context_path}")
    if os.path.exists(context_path):
        with open(context_path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
        print(f"✅  Context loaded ({len(data)} chars)")
        return data
    print("❌  Context file NOT found")
    return ""


def build_parent_context(student_id, aishe_code, student_data, relation):
    os.makedirs(STUDENT_CONTEXT_DIR, exist_ok=True)
    context_path = os.path.join(
        STUDENT_CONTEXT_DIR, f"{aishe_code}_parent_{student_id}.txt"
    )
    content = f"=== STUDENT INFORMATION (Viewed by: {relation}) ===\n"
    for k, v in student_data.items():
        content += f"{k}: {v}\n"
    rules = read_college_rules(aishe_code)
    content += (
        f"\n=== COLLEGE RULES ===\n{rules}\n"
        if rules else
        "\n=== COLLEGE RULES ===\n(No rules file uploaded yet)\n"
    )
    with open(context_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅  Parent context built → {context_path}")
    return context_path


def read_parent_context(student_id, aishe_code):
    context_path = os.path.join(
        STUDENT_CONTEXT_DIR, f"{aishe_code}_parent_{student_id}.txt"
    )
    if os.path.exists(context_path):
        with open(context_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


# ═════════════════════════════════════════════════════════════════════════════
# LLM CALLS
# ═════════════════════════════════════════════════════════════════════════════

def call_llm(question, context, model_key=DEFAULT_MODEL):
    if model_key not in MODELS:
        model_key = DEFAULT_MODEL

    cfg      = MODELS[model_key]
    api_key  = cfg["api_key"]
    model_id = cfg["model_id"]

    prompt = f"""You are a helpful college academic assistant.
Answer in the SAME language the student uses.
Be concise, friendly, and accurate.
Use the student data to answer personal academic questions.
Use the college rules to answer policy/regulation questions.

=== STUDENT DATA + COLLEGE RULES ===
{context}

=== STUDENT QUESTION ===
{question}

Answer clearly based on the data above.
IMPORTANT: Answer ONLY using above data. Do NOT say you don't have access.
"""
    try:
        url     = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You are a helpful academic assistant."},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens":  500,
            "temperature": 0.4,
        }
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code != 200:
            return f"❌ Groq Error {res.status_code}: {res.text}"
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error: {str(e)}"


def _configure_gemini():
    key = os.getenv("Gemini_API_Key") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini_API_Key not found in .env")
    genai.configure(api_key=key)


def call_gemini_parent(question, context, relation):
    _configure_gemini()
    prompt = f"""You are a helpful and respectful college academic assistant speaking to a student's {relation}.
Answer in the SAME language the parent uses.
Be polite, professional, and give COMPLETE answers. Never truncate.

=== STUDENT DATA + COLLEGE RULES ===
{context}

=== PARENT/GUARDIAN QUESTION ===
{question}
"""
    try:
        model    = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(max_output_tokens=1500, temperature=0.4)
        )
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"


# ═════════════════════════════════════════════════════════════════════════════
# AUDIO TRANSCRIPTION
# ═════════════════════════════════════════════════════════════════════════════

def transcribe_audio(audio_path):
    try:
        url     = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {GROQ_KEY_WHISPER}"}
        with open(audio_path, "rb") as f:
            files = {
                "file":  (os.path.basename(audio_path), f, "audio/webm"),
                "model": (None, "whisper-large-v3"),
            }
            res = requests.post(url, headers=headers, files=files, timeout=60)
        if res.status_code == 200:
            transcript = res.json().get("text", "").strip()
            print(f"✅  Transcription: {transcript[:80]}")
            return transcript
        print(f"⚠️  Whisper error {res.status_code}: {res.text}")
        return ""
    except Exception as e:
        print(f"⚠️  Transcription error: {e}")
        return ""


def transcribe_parent_audio(audio_path):
    return transcribe_audio(audio_path)


# ═════════════════════════════════════════════════════════════════════════════
# ── STUDENT LOGIN VIEW  (mirrors parent_login exactly) ──────────────────────
# ═════════════════════════════════════════════════════════════════════════════

def student_login_view(request):
    """
    Student login — architecture mirrors parent_login:

      1. Collect college files for the dropdown (same as parent_login)
      2. On POST: call _load_student_row_from_excel (same match logic as parent)
      3. Use matched row as primary student_data (parent does the same)
      4. Try get_student_full_data as enrichment; fall back to row dict if None
      5. Build context from whichever dict we have
      6. Store session keys identical to parent pattern
      7. Redirect to student_chat_room
    """
    # ── Collect college files for dropdown ──────────────────────────────────
    college_files = []
    if os.path.exists(PASSWORD_FILES_DIR):
        for fname in sorted(os.listdir(PASSWORD_FILES_DIR)):
            if fname.lower().endswith((".xlsx", ".xls", ".csv")):
                college_files.append({
                    "name": os.path.splitext(fname)[0].replace("_", " "),
                    "file": fname,
                })

    if request.method != "POST":
        return render(request, "student_login_valid.html", {"college_files": college_files})

    # ── Collect POST fields ─────────────────────────────────────────────────
    selected_file = request.POST.get("college_file", "").strip()
    student_id    = request.POST.get("student_id",   "").strip()
    aishe_code    = request.POST.get("aishe_code",   "").strip()
    password      = request.POST.get("password",     "").strip()

    if not all([selected_file, student_id, aishe_code, password]):
        messages.error(request, "All fields are required.")
        return render(request, "student_login_valid.html", {"college_files": college_files})

    # ── Step 1: Primary match — identical to parent_login ───────────────────
    #   _load_student_row_from_excel scans PASSWORD_FILES_DIR, normalises
    #   columns, matches StudentID + AISHE_Code + student_password.
    #   The matched row dict becomes our primary student_data.
    row_dict, matched_file = _load_student_row_from_excel(student_id, aishe_code, password, selected_file)

    if row_dict is None:
        print(f"❌  Login failed for StudentID={student_id!r}")
        messages.error(request, "Invalid Student ID, AISHE Code, or Password.")
        return render(request, "student_login_valid.html", {"college_files": college_files})

    # ── Step 2: Enrichment (optional, same pattern as parent_login) ─────────
    #   parent_login calls get_student_full_data and falls back to row_dict.
    #   We do exactly the same.
    student_data = get_student_full_data(student_id, aishe_code)
    if student_data is None:
        print("⚠️  Enrichment returned None → falling back to matched row dict")
        # Convert row_dict values to plain strings (handles numpy types)
        student_data = {
            str(k): (v.item() if hasattr(v, "item") else
                     ("" if (hasattr(pd, "isna") and pd.isna(v)) else str(v)))
            for k, v in row_dict.items()
        }

    print(f"✅  Student data ready ({len(student_data)} fields): "
          f"{list(student_data.keys())[:6]}…")

    # ── Step 3: Build LLM context file ─────────────────────────────────────
    try:
        build_student_context(student_id, aishe_code, student_data)
        print("✅  Context successfully created")
    except Exception as e:
        print(f"❌  Context build failed: {e}")
        messages.error(request, "Error preparing student data. Please try again.")
        return render(request, "student_login_valid.html", {"college_files": college_files})

    # ── Step 4: Derive student name (same priority order as parent_login) ───
    student_name = (
        student_data.get("Name")         or
        student_data.get("name")         or
        student_data.get("StudentName")  or
        student_data.get("student_name") or
        student_id
    )

    # ── Step 5: Store session keys ──────────────────────────────────────────
    request.session["chat_student_id"]   = student_id
    request.session["chat_aishe_code"]   = aishe_code
    request.session["chat_student_name"] = str(student_name).strip() or student_id

    print(f"✅  Session stored → student_id={student_id}  name={student_name}")

    messages.success(request, "Login Successful ✅")
    return redirect("student_chat_room")


# ═════════════════════════════════════════════════════════════════════════════
# STUDENT DATA CHAT (verify-only flow, kept for backward compat)
# ═════════════════════════════════════════════════════════════════════════════

def student_data_chat(request):
    error = None
    excel_files = []
    display_files = []

    if os.path.exists(PASSWORD_FILES_DIR):
        excel_files = [
            f for f in os.listdir(PASSWORD_FILES_DIR)
            if f.endswith((".xlsx", ".xls", ".csv"))
        ]
        for f in excel_files:
            clean_name = os.path.splitext(f)[0].replace("_", " ")
            display_files.append({"file": f, "name": clean_name})

    if request.method == "POST":
        selected_file = request.POST.get("excel_file", "").strip()
        aishe_code    = request.POST.get("aishe_code", "").strip()
        student_id    = request.POST.get("student_id", "").strip()

        if not selected_file or not aishe_code or not student_id:
            error = "Please fill all required fields."
            return render(request, "student_data_chat.html", {"error": error, "excel_files": display_files})

        file_path = os.path.join(PASSWORD_FILES_DIR, selected_file)
        if not os.path.exists(file_path):
            error = "Selected file not found."
            return render(request, "student_data_chat.html", {"error": error, "excel_files": display_files})

        try:
            if selected_file.endswith(".csv"):
                df = pd.read_csv(file_path, dtype=str).fillna("")
            else:
                df = pd.read_excel(file_path, dtype=str).fillna("")
        except Exception as e:
            error = f"Error reading file: {str(e)}"
            return render(request, "student_data_chat.html", {"error": error, "excel_files": display_files})

        df.columns = df.columns.str.strip()
        search_col = "StudentID" if "StudentID" in df.columns else df.columns[0]
        df[search_col]   = df[search_col].astype(str).str.strip()
        df["AISHE_Code"] = df["AISHE_Code"].astype(str).str.strip() if "AISHE_Code" in df.columns else ""

        match = df[
            (df[search_col]  == student_id) &
            (df["AISHE_Code"] == aishe_code)
        ]
        if match.empty:
            error = "Invalid AISHE Code or Student ID."
            return render(request, "student_data_chat.html", {"error": error, "excel_files": display_files})

        row_dict     = match.iloc[0].to_dict()
        student_data = get_student_full_data(student_id, aishe_code) or {
            str(k): ("" if (hasattr(pd, "isna") and pd.isna(v)) else str(v))
            for k, v in row_dict.items()
        }

        build_student_context(student_id, aishe_code, student_data)
        request.session["chat_student_id"]   = student_id
        request.session["chat_aishe_code"]   = aishe_code
        request.session["chat_student_name"] = str(
            student_data.get("Name") or student_data.get("name") or student_id
        ).strip()
        return redirect("student_chat_room")

    return render(request, "student_data_chat.html", {"excel_files": display_files})


# ═════════════════════════════════════════════════════════════════════════════
# STUDENT CHAT ROOM
# ═════════════════════════════════════════════════════════════════════════════

def student_chat_room(request):
    if "chat_student_id" not in request.session:
        return redirect("student_data_chat")
    return render(request, "student_chat_room.html", {
        "student_name":  request.session.get("chat_student_name", "Student"),
        "student_id":    request.session.get("chat_student_id",   ""),
        "aishe_code":    request.session.get("chat_aishe_code",   ""),
        "default_model": DEFAULT_MODEL,
    })


# ═════════════════════════════════════════════════════════════════════════════
# STUDENT CHAT ASK
# ═════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def student_chat_ask(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Invalid method"}, status=405)

    if "chat_student_id" not in request.session:
        return JsonResponse({"answer": "Session expired. Please login again."})

    try:
        data       = json.loads(request.body)
        question   = data.get("question", "").strip()
        model_key  = data.get("model_key", DEFAULT_MODEL).strip()
        student_id = request.session["chat_student_id"]
        aishe_code = request.session["chat_aishe_code"]

        if not question:
            return JsonResponse({"answer": "Please type a question."})

        # ── Read context ────────────────────────────────────────────────────
        context = read_student_context(student_id, aishe_code)

        # ── Rebuild if missing (mirrors parent_chat_ask rebuild pattern) ────
        if not context:
            print("⚠️  Context missing → rebuilding…")
            student_data = get_student_full_data(student_id, aishe_code)
            if student_data:
                build_student_context(student_id, aishe_code, student_data)
                context = read_student_context(student_id, aishe_code)
                print("✅  Context rebuilt")
            else:
                print("❌  Cannot rebuild: student not found in any file")

        print(f"====== CONTEXT SENT TO LLM ({len(context)} chars) ======")
        print(context[:500])

        if not context:
            context = "No student data available."

        # ── Call LLM ────────────────────────────────────────────────────────
        answer = call_llm(question, context, model_key)
        cfg    = MODELS.get(model_key, MODELS[DEFAULT_MODEL])

        return JsonResponse({
            "answer":      answer,
            "model_key":   model_key,
            "model_label": cfg["label"],
            "model_icon":  cfg["icon"],
        })

    except Exception as e:
        print(f"❌  student_chat_ask error: {e}")
        return JsonResponse({"answer": f"Error: {str(e)}"})


# ═════════════════════════════════════════════════════════════════════════════
# STUDENT CHAT VOICE
# ═════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def student_chat_voice(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Invalid method"}, status=405)

    if "chat_student_id" not in request.session:
        return JsonResponse({"answer": "Session expired. Please login again."})

    try:
        audio_file = request.FILES.get("audio")
        model_key  = request.POST.get("model_key", DEFAULT_MODEL).strip()

        if not audio_file:
            return JsonResponse({"answer": "No audio received."})

        student_id = request.session["chat_student_id"]
        aishe_code = request.session["chat_aishe_code"]

        temp_path = os.path.join(settings.BASE_DIR, "temp_voice.webm")
        with open(temp_path, "wb") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        transcript = transcribe_audio(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not transcript:
            return JsonResponse({"answer": "Could not understand audio.", "transcript": ""})

        context = read_student_context(student_id, aishe_code)
        if not context:
            student_data = get_student_full_data(student_id, aishe_code)
            if student_data:
                build_student_context(student_id, aishe_code, student_data)
                context = read_student_context(student_id, aishe_code)

        answer = call_llm(transcript, context, model_key)
        cfg    = MODELS.get(model_key, MODELS[DEFAULT_MODEL])

        return JsonResponse({
            "answer":      answer,
            "transcript":  transcript,
            "model_label": cfg["label"],
            "model_icon":  cfg["icon"],
        })

    except Exception as e:
        return JsonResponse({"answer": f"Error: {str(e)}", "transcript": ""})


# ═════════════════════════════════════════════════════════════════════════════
# STUDENT LOGOUT
# ═════════════════════════════════════════════════════════════════════════════

def student_chat_logout(request):
    for key in ["chat_student_id", "chat_aishe_code", "chat_student_name"]:
        request.session.pop(key, None)
    return redirect("student_data_chat")

# ═════════════════════════════════════════════════════════════════════════════
# PARENT LOGIN & CHAT VIEWS TAKE REFFERENCE FROM BELOW
# ═════════════════════════════════════════════════════════════════════════════


import os
import json
import base64
import requests
import pandas as pd
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from datetime import datetime

from .utils import (
    get_student_full_data,
    build_parent_context,
    read_parent_context,
    call_gemini_parent,
    transcribe_parent_audio,
    _configure_gemini,
)
import google.generativeai as genai

GROQ_KEY_WHISPER = os.getenv("GROQ_API_KEY3", "")
GROQ_KEY_QWEN    = os.getenv("GROQ_API_KEY4", "")

PASSWORD_FILES_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "student_and_parent_logins"
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. /parent_login/
#    Excel password login → same pipeline as parent_data_chat
# ─────────────────────────────────────────────────────────────────────────────
def parent_login(request):
    files = []
    if os.path.exists(PASSWORD_FILES_DIR):
        for f in os.listdir(PASSWORD_FILES_DIR):
            if f.endswith(".xlsx"):
                files.append({"name": f, "file": f})

    error = None

    if request.method == "POST":
        file     = request.POST.get("college_file", "").strip()
        sid      = request.POST.get("student_id",   "").strip()
        aishe    = request.POST.get("aishe_code",   "").strip()
        pwd      = request.POST.get("password",     "").strip()
        relation = request.POST.get("relation",     "Parent").strip()

        if not all([file, sid, aishe, pwd]):
            error = "All fields are required."
        else:
            file_path = os.path.join(PASSWORD_FILES_DIR, file)
            if not os.path.exists(file_path):
                error = "College file not found."
            else:
                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()

                match = df[
                    (df["StudentID"].astype(str).str.strip()        == sid)  &
                    (df["AISHE_Code"].astype(str).str.strip()       == aishe) &
                    (df["student_password"].astype(str).str.strip() == pwd)
                ]

                if not match.empty:
                    # ── Step 1: get the matched student dict ──
                    student_row  = match.iloc[0]
                    student_dict = student_row.to_dict()

                    # ── Step 2: pull full enriched data (same as parent_data_chat) ──
                    # get_student_full_data returns the rich dict used by build_parent_context
                    student_data = get_student_full_data(sid, aishe)

                    if student_data is None:
                        # fallback: use the Excel row itself
                        student_data = {
                            str(k): (v.item() if hasattr(v, "item") else
                                     ("" if pd.isna(v) else str(v)))
                            for k, v in student_dict.items()
                        }

                    # ── Step 3: build LLM context file  ← THE KEY STEP ──
                    # This writes the context that read_parent_context() will read
                    build_parent_context(sid, aishe, student_data, relation)

                    # ── Step 4: derive student name ──
                    student_name = (
                        student_data.get("Name")         or
                        student_data.get("name")         or
                        student_data.get("StudentName")  or
                        student_data.get("student_name") or
                        sid
                    )

                    # ── Step 5: store session keys  ← identical to parent_data_chat ──
                    request.session["parent_student_id"]   = sid
                    request.session["parent_aishe_code"]   = aishe
                    request.session["parent_relation"]     = relation
                    request.session["parent_student_name"] = str(student_name)

                    return redirect("parent_chat_room")

                error = "Invalid Student ID, AISHE Code, or Password."

    return render(request, "parent_login.html", {
        "college_files": files,
        "error":         error,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 2. /parent_data_chat/
#    ID-only login (no password) — the original working flow, untouched
# ─────────────────────────────────────────────────────────────────────────────
def parent_data_chat(request):
    error = None

    if request.method == "POST":
        aishe_code = request.POST.get("aishe_code", "").strip()
        student_id = request.POST.get("student_id", "").strip()
        relation   = request.POST.get("relation",   "Parent").strip()

        if not aishe_code or not student_id:
            error = "Both AISHE Code and Student ID are required."
        else:
            student_data = get_student_full_data(student_id, aishe_code)

            if student_data is None:
                error = "Student not found. Please check AISHE Code and Student ID."
            else:
                build_parent_context(student_id, aishe_code, student_data, relation)

                request.session["parent_student_id"]   = student_id
                request.session["parent_aishe_code"]   = aishe_code
                request.session["parent_relation"]     = relation
                request.session["parent_student_name"] = student_data.get(
                    "Name", student_data.get("name", student_id)
                )

                return redirect("parent_chat_room")

    return render(request, "parent_data_chat.html", {"error": error})


# ─────────────────────────────────────────────────────────────────────────────
# 3. /parent_chat_room/
# ─────────────────────────────────────────────────────────────────────────────
def parent_chat_room(request):
    if "parent_student_id" not in request.session:
        return redirect("parent_login")

    return render(request, "parent_chat_room.html", {
        "student_name": request.session.get("parent_student_name", "Student"),
        "student_id":   request.session.get("parent_student_id",   ""),
        "aishe_code":   request.session.get("parent_aishe_code",   ""),
        "relation":     request.session.get("parent_relation",     "Parent"),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 4. /parent_chat_ask/
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def parent_chat_ask(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Invalid method"}, status=405)

    if "parent_student_id" not in request.session:
        return JsonResponse({"answer": "Session expired. Please login again."})

    try:
        data       = json.loads(request.body)
        question   = data.get("question", "").strip()
        model      = data.get("model", "gemini").strip()   # ← NEW: "gemini" or "gpt"
        student_id = request.session["parent_student_id"]
        aishe_code = request.session["parent_aishe_code"]
        relation   = request.session.get("parent_relation", "Parent")

        if not question:
            return JsonResponse({"answer": "Please type a question."})

        context = read_parent_context(student_id, aishe_code)

        # ── Model routing ──────────────────────────────────────────────────
        if model == "gpt":
            # GPT-OSS-120B via Groq
            groq_key = os.getenv("GROQ_API_KEY", "")
            if not groq_key:
                return JsonResponse({"answer": "❌ GROQ_API_KEY missing in .env"})

            system_prompt = f"""You are a helpful academic assistant for parents.
The parent's relation to the student is: {relation}.
Use the following student data to answer questions accurately.
Always be respectful, clear and concise.

STUDENT DATA:
{context}"""

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key.strip()}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": question},
                    ],
                    "temperature": 0.3,
                    "max_tokens":  1024,
                },
                timeout=40,
            )

            if res.status_code != 200:
                return JsonResponse({"answer": f"❌ GPT API error: {res.text}"})

            answer = res.json()["choices"][0]["message"]["content"]

        else:
            # Default: Gemini 2.5 (existing flow — untouched)
            answer = call_gemini_parent(question, context, relation)

        return JsonResponse({"answer": answer})

    except Exception as e:
        return JsonResponse({"answer": f"Error: {str(e)}"})

# ─────────────────────────────────────────────────────────────────────────────
# 5. /parent_chat/voice/
# ─────────────────────────────────────────────────────────────────────────────
@csrf_exempt
def parent_chat_voice(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Invalid method"}, status=405)

    if "parent_student_id" not in request.session:
        return JsonResponse({"answer": "Session expired. Please login again."})

    try:
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return JsonResponse({"answer": "No audio received."})

        student_id = request.session["parent_student_id"]
        aishe_code = request.session["parent_aishe_code"]
        relation   = request.session.get("parent_relation", "Parent")

        temp_path = os.path.join(settings.BASE_DIR, "temp_parent_voice.webm")
        with open(temp_path, "wb") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        transcript = transcribe_parent_audio(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not transcript:
            return JsonResponse({
                "answer":     "Could not understand audio. Please try again.",
                "transcript": ""
            })

        context = read_parent_context(student_id, aishe_code)
        answer  = call_gemini_parent(transcript, context, relation)

        return JsonResponse({"answer": answer, "transcript": transcript})
    except Exception as e:
        return JsonResponse({"answer": f"Error: {str(e)}", "transcript": ""})


# ─────────────────────────────────────────────────────────────────────────────
# 6. /parent_chat_logout/
# ─────────────────────────────────────────────────────────────────────────────
def parent_chat_logout(request):
    for key in [
        "parent_student_id",
        "parent_aishe_code",
        "parent_relation",
        "parent_student_name",
    ]:
        request.session.pop(key, None)
    return redirect("parent_login")


# ─────────────────────────────────────────────────────────────────────────────
# 7. /parent-chat/tts/
# ─────────────────────────────────────────────────────────────────────────────
@csrf_exempt
def parent_chat_tts(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data       = json.loads(request.body)
        text       = data.get("text", "").strip()[:500]
        voice_name = data.get("voice", "Kore")

        if not text:
            return JsonResponse({"error": "No text provided"})

        # PRIMARY: Gemini 2.5 Flash TTS
        try:
            _configure_gemini()
            tts_model = genai.GenerativeModel("gemini-2.5-flash-preview-tts")
            response  = tts_model.generate_content(
                text,
                generation_config=genai.GenerationConfig(
                    response_modalities=["AUDIO"],
                    speech_config=genai.SpeechConfig(
                        voice_config=genai.VoiceConfig(
                            prebuilt_voice_config=genai.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        )
                    )
                )
            )
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            return JsonResponse({
                "audio": base64.b64encode(audio_data).decode("utf-8"),
                "type":  "audio/pcm"
            })
        except Exception as gemini_err:
            print(f"⚠️  Gemini TTS failed: {gemini_err}")

        # FALLBACK: Groq TTS
        groq_key = os.getenv("GROQ_API_KEY3", GROQ_KEY_WHISPER)
        GROQ_VOICE_MAP = {
            "Kore":   "nova",
            "Aoede":  "shimmer",
            "Charon": "onyx",
            "Fenrir": "echo",
            "Puck":   "fable",
        }
        groq_voice = GROQ_VOICE_MAP.get(voice_name, "nova")

        if groq_key:
            res = requests.post(
                "https://api.groq.com/openai/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":           "playai-tts",
                    "input":           text,
                    "voice":           groq_voice,
                    "response_format": "mp3",
                },
                timeout=30,
            )
            if res.status_code == 200:
                return JsonResponse({
                    "audio": base64.b64encode(res.content).decode("utf-8"),
                    "type":  "audio/mp3"
                })
            print(f"⚠️  Groq TTS error {res.status_code}: {res.text}")

        return JsonResponse({"error": "All TTS engines failed."})
    except Exception as e:
        return JsonResponse({"error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────..............>>>>
# 8.  /parent_report_generate/
# ─────────────────────────────────────────────────────────────────────────────
def parent_report_generate(request):
    """
    Generates AI-analysed PDF report from session data and emails it.
    Reads student data from session — no global dict dependency.
    """
    if "parent_student_id" not in request.session:
        return redirect("parent_login")

    if request.method == "POST":
        try:
            email        = request.POST.get("parent_email", "").strip()
            student_data = request.session.get("parent_student_data")

            if not student_data:
                return HttpResponse("❌ Session data missing. Please login again.")

            if not email:
                return HttpResponse("❌ Please provide an email address.")

            student_row = pd.Series(student_data)

            # ── Build prompt ──
            prompt = f"""
Analyze this student data and return STRICT JSON only:

{student_data}

Return exactly:
{{
  "strengths":        "...",
  "weaknesses":       "...",
  "risk_level":       "...",
  "improvement_plan": "..."
}}
"""
            # ── Call Groq (Qwen) for analysis ──
            groq_key = os.getenv("GROQ_API_KEY4", "")
            if not groq_key:
                return HttpResponse("❌ GROQ_API_KEY4 missing in .env")

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key.strip()}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model": "qwen/qwen3-32b",
                    "messages": [
                        {"role": "system", "content": "Return ONLY valid JSON. No text outside JSON."},
                        {"role": "user",   "content": prompt}
                    ],
                    "temperature": 0.2
                }
            )

            if res.status_code != 200:
                return HttpResponse(f"❌ Groq API error: {res.text}")

            content = res.json()["choices"][0]["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()

            try:
                analysis = json.loads(content)
            except Exception:
                analysis = {
                    "strengths":        "Could not parse analysis.",
                    "weaknesses":       "LLM returned invalid format.",
                    "risk_level":       "Unknown",
                    "improvement_plan": content[:300]
                }

            # ── Generate PDF ──
            styles   = getSampleStyleSheet()
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            sid       = request.session["parent_student_id"]
            file_path = os.path.join(settings.MEDIA_ROOT, f"report_{sid}.pdf")
            doc       = SimpleDocTemplate(file_path)
            elements  = []

            elements.append(Paragraph("<b>📊 Student Performance Report</b>", styles["Title"]))
            elements.append(Spacer(1, 15))

            # Student details table
            student_table_data = [["Field", "Value"]]
            for k, v in student_data.items():
                student_table_data.append([str(k), str(v)])

            st = Table(student_table_data, colWidths=[180, 320])
            st.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("GRID",       (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("WORDWRAP",   (1, 1), (1, -1), True),
            ]))
            elements.append(Paragraph("<b>Student Details</b>", styles["Heading2"]))
            elements.append(st)
            elements.append(Spacer(1, 20))

            # AI analysis table
            elements.append(Paragraph("<b>AI Performance Analysis</b>", styles["Heading2"]))
            elements.append(Spacer(1, 10))

            at = Table([
                ["Metric",           "Analysis"],
                ["Strengths",        analysis.get("strengths",        "N/A")],
                ["Weaknesses",       analysis.get("weaknesses",       "N/A")],
                ["Risk Level",       analysis.get("risk_level",       "N/A")],
                ["Improvement Plan", analysis.get("improvement_plan", "N/A")],
            ], colWidths=[150, 350])
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("GRID",       (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("WORDWRAP",   (1, 1), (1, -1), True),
            ]))
            elements.append(at)
            doc.build(elements)

            # ── Email PDF ──
            email_msg = EmailMessage(
                subject="📊 Student Performance Report",
                body="""
<h2>📊 Student Performance Report</h2>
<p>Dear Parent,</p>
<p>Your child's AI-analysed performance report is attached.</p>
<ul>
  <li>✔ Strength &amp; weakness insights</li>
  <li>✔ Risk level assessment</li>
  <li>✔ Improvement recommendations</li>
</ul>
<p>Regards,<br><b>Smart Academic System</b></p>
""",
                from_email=settings.EMAIL_HOST_USER,
                to=[email],
            )
            email_msg.content_subtype = "html"
            email_msg.attach_file(file_path)
            email_msg.send()

            return HttpResponse("✅ Report generated and sent successfully!")

        except Exception as e:
            return HttpResponse(f"❌ Error: {str(e)}")

    return render(request, "parent_report_generate.html", {
        "student_name": request.session.get("parent_student_name", "Student"),
        "student_id":   request.session.get("parent_student_id",   ""),
    })


@csrf_exempt
@csrf_exempt
def parent_analyze_student(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    if "parent_student_id" not in request.session:
        return JsonResponse({"error": "Session expired"}, status=401)

    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()

        if not email:
            return JsonResponse({"error": "Email required"}, status=400)

        student_id   = request.session["parent_student_id"]
        student_name = request.session["parent_student_name"]
        aishe_code   = request.session["parent_aishe_code"]
        student_data = request.session.get("parent_student_data")

        if not student_data:
            return JsonResponse({"error": "Session data missing"}, status=400)

        prompt = f"Analyze: {student_data}"

        analysis = analyze_with_llm(prompt)

        pdf_buffer = generate_student_report_pdf(
            analysis,
            student_name,
            student_id,
            aishe_code
        )

        email_sent = send_report_email(
            email,
            pdf_buffer,
            student_name,
            student_id,
            aishe_code,
            analysis
        )

        if not email_sent:
            return JsonResponse({"error": "Email failed"}, status=500)

        return JsonResponse({
            "success": True,
            "analysis": analysis
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def analyze_student_with_qwen(context, student_name):
    """
    Use Qwen 3-32B to analyze student performance
    Returns structured JSON with strengths, weaknesses, risks, recommendations
    """
    if not GROQ_KEY_QWEN:
        print("⚠️  GROQ_API_KEY4 not configured")
        return None
    
    prompt = f"""You are an expert educational analyst. Analyze the following student data and provide a comprehensive performance report.

Student Name: {student_name}

Student Data:
{context}

Provide a detailed analysis in STRICT JSON format with the following structure:
{{
  "overall_status": "Excellent/Good/Average/Below Average/At Risk",
  "risk_level": "Low/Medium/High/Critical",
  "attendance": {{
    "percentage": "XX%",
    "status": "Good/Average/Poor",
    "concern": "Brief concern if any"
  }},
  "academic_performance": {{
    "overall_grade": "A/B/C/D/F or percentage",
    "strong_subjects": ["subject1", "subject2"],
    "weak_subjects": ["subject1", "subject2"],
    "detailed_analysis": "Brief analysis of academic standing"
  }},
  "strengths": [
    "Strength point 1",
    "Strength point 2",
    "Strength point 3"
  ],
  "weaknesses": [
    "Weakness point 1",
    "Weakness point 2",
    "Weakness point 3"
  ],
  "improvement_plan": [
    "Actionable recommendation 1",
    "Actionable recommendation 2",
    "Actionable recommendation 3",
    "Actionable recommendation 4"
  ],
  "parent_guidance": "Specific advice for parents on how to support the student",
  "summary": "A 2-3 sentence executive summary of the student's overall situation"
}}

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no explanations. Just the JSON object."""

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_KEY_QWEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen/qwen-2.5-32b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON response
            analysis = json.loads(content)
            return analysis
        else:
            print(f"⚠️  Qwen API error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"⚠️  Qwen analysis error: {e}")
        return None


def generate_student_report_pdf(analysis, student_name, student_id, aishe_code):
    """
    Generate a professional PDF report from the analysis JSON
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#14532d'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#15803d'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        spaceAfter=6
    )
    
    # Header
    story.append(Paragraph("🎓 Student Performance Analysis Report", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Student Info Table
    info_data = [
        ['Student Name:', student_name],
        ['Student ID:', student_id],
        ['AISHE Code:', aishe_code],
        ['Report Date:', datetime.now().strftime('%B %d, %Y')]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#dcfce7')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#14532d')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbf7d0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Overall Status
    status_color = {
        'Excellent': '#22c55e',
        'Good': '#16a34a',
        'Average': '#eab308',
        'Below Average': '#f97316',
        'At Risk': '#dc2626',
        'Critical': '#991b1b'
    }.get(analysis.get('overall_status', 'Average'), '#64748b')
    
    status_data = [
        ['Overall Status:', analysis.get('overall_status', 'N/A')],
        ['Risk Level:', analysis.get('risk_level', 'N/A')]
    ]
    
    status_table = Table(status_data, colWidths=[2*inch, 4*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor(status_color)),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bbf7d0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(status_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Summary
    if analysis.get('summary'):
        story.append(Paragraph("📝 Executive Summary", heading_style))
        story.append(Paragraph(analysis['summary'], body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Attendance
    if analysis.get('attendance'):
        att = analysis['attendance']
        story.append(Paragraph("📅 Attendance Analysis", heading_style))
        story.append(Paragraph(f"<b>Percentage:</b> {att.get('percentage', 'N/A')}", body_style))
        story.append(Paragraph(f"<b>Status:</b> {att.get('status', 'N/A')}", body_style))
        if att.get('concern'):
            story.append(Paragraph(f"<b>Concern:</b> {att['concern']}", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Academic Performance
    if analysis.get('academic_performance'):
        ap = analysis['academic_performance']
        story.append(Paragraph("📊 Academic Performance", heading_style))
        story.append(Paragraph(f"<b>Overall Grade:</b> {ap.get('overall_grade', 'N/A')}", body_style))
        
        if ap.get('strong_subjects'):
            story.append(Paragraph(f"<b>Strong Subjects:</b> {', '.join(ap['strong_subjects'])}", body_style))
        
        if ap.get('weak_subjects'):
            story.append(Paragraph(f"<b>Weak Subjects:</b> {', '.join(ap['weak_subjects'])}", body_style))
        
        if ap.get('detailed_analysis'):
            story.append(Paragraph(ap['detailed_analysis'], body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Strengths
    if analysis.get('strengths'):
        story.append(Paragraph("💪 Key Strengths", heading_style))
        for strength in analysis['strengths']:
            story.append(Paragraph(f"• {strength}", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Weaknesses
    if analysis.get('weaknesses'):
        story.append(Paragraph("⚠️ Areas for Improvement", heading_style))
        for weakness in analysis['weaknesses']:
            story.append(Paragraph(f"• {weakness}", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Improvement Plan
    if analysis.get('improvement_plan'):
        story.append(Paragraph("🎯 Improvement Action Plan", heading_style))
        for i, plan in enumerate(analysis['improvement_plan'], 1):
            story.append(Paragraph(f"{i}. {plan}", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Parent Guidance
    if analysis.get('parent_guidance'):
        story.append(Paragraph("👨‍👩‍👧 Guidance for Parents", heading_style))
        story.append(Paragraph(analysis['parent_guidance'], body_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

from django.template.loader import render_to_string

def send_report_email(to_email, pdf_buffer, student_name, student_id, aishe_code, analysis):
    try:
        subject = f"📊 Student Report - {student_name}"

        html_content = render_to_string(
            "emails/student_report.html",
            {
                "student_name": student_name,
                "student_id": student_id,
                "aishe_code": aishe_code,
                "summary": analysis.get("summary", ""),
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", []),
                "improvement_plan": analysis.get("improvement_plan", []),
            }
        )

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )

        email.content_subtype = "html"

        email.attach(
            f"Student_Report_{student_name}.pdf",
            pdf_buffer.getvalue(),
            "application/pdf"
        )

        email.send()
        return True

    except Exception as e:
        print("❌ Email error:", e)
        return False

def parent_chat_logout(request):
    """Parent logout view"""
    for k in ["parent_student_id", "parent_aishe_code", "parent_relation", "parent_student_name"]:
        request.session.pop(k, None)
    return redirect("parent_data_chat")

import os
import re
import json
import requests
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ✅ LOAD ENV
GROQ_API_KEY4 = os.getenv("GROQ_API_KEY4")

# 📁 PATH
PASSWORD_FILES_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "student_and_parent_logins"
)

LOGGED_PARENT_DATA = {"student_row": None}


# -----------------------------
# 🔍 DYNAMIC SUBJECT EXTRACTOR
# -----------------------------
def extract_subjects(student_data):
    """
    Dynamically extracts unique subject names from student_data keys
    that follow the pattern: mid1_<Subject>, mid2_<Subject>, final_<Subject>.
    Returns a sorted list of subject name strings (e.g. "Heat_Mass_Transfer").
    Works for ANY department — Mechanical, ECE, CSE, Civil, etc.
    """
    subjects = set()
    for key in student_data.keys():
        for prefix in ("mid1_", "mid2_", "final_"):
            if key.startswith(prefix):
                subj = key[len(prefix):]
                if subj:
                    subjects.add(subj)
    return sorted(subjects)


# -----------------------------
# 📊 ROBUST PROMPT
# -----------------------------
def build_prompt_from_student_data(student_data):
    return f"""You are an expert academic counselor. Analyze the following student data and provide a detailed, meaningful performance report.

STUDENT DATA:
{json.dumps(student_data, indent=2)}

Return ONLY a valid JSON object (no markdown, no extra text, no explanation outside JSON).
The JSON must follow this exact structure:

{{
  "strengths": [
    "Detailed strength point 1 with specific subject references",
    "Detailed strength point 2",
    "Detailed strength point 3"
  ],
  "weaknesses": [
    "Specific weakness with subject name and score context",
    "Another weakness area that needs attention",
    "Another concern"
  ],
  "risk_level": "Low",
  "improvement_plan": [
    "Concrete actionable step 1 with timeline",
    "Concrete actionable step 2",
    "Concrete actionable step 3",
    "Concrete actionable step 4"
  ],
  "overall_summary": "A 3-4 sentence paragraph summarizing the student's overall academic profile, noting their grade, attendance, key patterns in performance, and general standing.",
  "subject_insights": [
    "Subject-specific insight 1 (e.g., 'Excelled in VLSI Design in finals showing growth')",
    "Subject-specific insight 2"
  ],
  "parent_message": "A warm, encouraging 2-3 sentence message starting with 'Dear Parent,' (do NOT use the guardian's name) about the student's progress and what support would help most."
}}

Rules:
- risk_level must be exactly one of: "Low", "Medium", "High"
- Each list must have at least 3 items
- Be specific — reference actual subject names, scores, attendance, internship score, project score etc. from the data
- Do NOT return empty strings or placeholder text
- Return ONLY the JSON object, nothing else
"""


# -----------------------------
# 🤖 GROQ LLM CALL — ROBUST
# -----------------------------
def _call_groq(headers, payload, timeout=90):
    import time
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = "https://api.groq.com/openai/v1/chat/completions"
    last_exc = None

    for attempt, verify in enumerate([True, False, False], start=1):
        try:
            if attempt == 3:
                time.sleep(2)
            res = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
                verify=verify,
            )
            return res
        except requests.exceptions.SSLError as e:
            print(f"⚠️ SSL error on attempt {attempt}: {e}")
            last_exc = e
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ Connection error on attempt {attempt}: {e}")
            last_exc = e
        except requests.exceptions.Timeout as e:
            print(f"⚠️ Timeout on attempt {attempt}: {e}")
            last_exc = e

    raise Exception(f"❌ All Groq request attempts failed. Last error: {last_exc}")


def analyze_with_llm(student_data):
    api_key = os.getenv("GROQ_API_KEY4")
    if not api_key:
        raise Exception("❌ GROQ_API_KEY4 missing in .env")

    prompt = build_prompt_from_student_data(student_data)

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen/qwen3-32b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an academic data analyst. "
                    "You ALWAYS respond with ONLY a valid JSON object. "
                    "Never add any text, explanation, or markdown outside the JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 1500
    }

    res = _call_groq(headers, payload)

    print("STATUS:", res.status_code)
    print("RAW RESPONSE:", res.text[:500])

    if res.status_code != 200:
        raise Exception(f"❌ Groq Error {res.status_code}: {res.text}")

    data = res.json()

    if "choices" not in data or len(data["choices"]) == 0:
        raise Exception(f"❌ Invalid API Response structure: {data}")

    content = data["choices"][0]["message"]["content"]

    if not content or content.strip() == "":
        raise Exception("❌ Empty response from LLM")

    # ✅ CLEAN: strip markdown fences
    content = content.strip()
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"```\s*", "", content)
    content = content.strip()

    # ✅ EXTRACT JSON block (in case model added preamble)
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        content = json_match.group(0)

    # ✅ PARSE
    try:
        parsed = json.loads(content)

        required_keys = ["strengths", "weaknesses", "risk_level", "improvement_plan"]
        for key in required_keys:
            if key not in parsed:
                raise ValueError(f"Missing key: {key}")
            if isinstance(parsed[key], list) and len(parsed[key]) == 0:
                raise ValueError(f"Empty list for: {key}")

        risk = parsed.get("risk_level", "Medium")
        if risk not in ["Low", "Medium", "High"]:
            rl = risk.lower()
            if "low" in rl:
                parsed["risk_level"] = "Low"
            elif "high" in rl:
                parsed["risk_level"] = "High"
            else:
                parsed["risk_level"] = "Medium"

        if "overall_summary" not in parsed or not parsed["overall_summary"]:
            parsed["overall_summary"] = generate_fallback_summary(student_data)
        if "subject_insights" not in parsed:
            parsed["subject_insights"] = []
        if "parent_message" not in parsed:
            parsed["parent_message"] = ""

        return parsed

    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️ JSON parse failed: {e}")
        print("⚠️ RAW CONTENT:", content[:500])
        return build_smart_fallback(student_data)


# -----------------------------
# 🔁 SMART FALLBACK (uses real data)
# -----------------------------
def generate_fallback_summary(student_data):
    name       = student_data.get("Name", "The student")
    grade      = student_data.get("Grade", "N/A")
    overall    = student_data.get("Overall_Average", "N/A")
    attendance = student_data.get("Attendance", "N/A")
    status     = student_data.get("Academic_Status", "Pass")
    return (
        f"{name} has an overall average of {overall} and holds a grade of {grade} "
        f"with {attendance} attendance. Academic status: {status}. "
        f"This report highlights key areas of strength and growth opportunities."
    )


def build_smart_fallback(student_data):
    name       = student_data.get("Name", "Student")
    overall    = float(student_data.get("Overall_Average", 0) or 0)
    attendance = student_data.get("Attendance", "N/A")
    internship = student_data.get("Internship_Score", "N/A")
    project    = student_data.get("Project_Score", "N/A")
    grade      = student_data.get("Grade", "N/A")

    if overall >= 75:
        risk = "Low"
    elif overall >= 50:
        risk = "Medium"
    else:
        risk = "High"

    subject_scores = {}
    for key, val in student_data.items():
        if key.startswith("final_") and val:
            subj = key.replace("final_", "").replace("_", " ")
            try:
                subject_scores[subj] = float(val)
            except:
                pass

    best_subj  = max(subject_scores, key=subject_scores.get) if subject_scores else "core subjects"
    worst_subj = min(subject_scores, key=subject_scores.get) if subject_scores else "some subjects"

    return {
        "overall_summary": generate_fallback_summary(student_data),
        "strengths": [
            f"Strong attendance record of {attendance}, demonstrating consistent commitment to academics.",
            f"Achieved a commendable Internship Score of {internship}, reflecting real-world application ability.",
            f"Project Score of {project} indicates good practical and problem-solving skills.",
            f"Performed well in {best_subj} in final examinations.",
            f"Awarded Grade {grade}, reflecting overall satisfactory academic performance."
        ],
        "weaknesses": [
            f"Overall average of {overall:.1f} leaves room for improvement toward distinction-level performance.",
            f"Scored lower in {worst_subj} — targeted revision in this subject is recommended.",
            "Mid-semester and final examination scores show inconsistency across subjects.",
            "Advanced concept mastery in technical subjects needs focused attention."
        ],
        "risk_level": risk,
        "improvement_plan": [
            f"Dedicate 1 hour daily to revising {worst_subj} concepts using practice papers.",
            "Form or join a study group for peer learning on difficult topics.",
            "Schedule monthly meetings with subject faculty to clarify doubts early.",
            "Use online resources (NPTEL, Coursera) to strengthen weak subject foundations.",
            "Track progress weekly with a study planner to ensure consistent improvement."
        ],
        "subject_insights": [
            f"Best performance seen in {best_subj} during finals.",
            f"Needs focused effort in {worst_subj} to boost overall scores."
        ],
        "parent_message": (
            f"Dear Parent, your child {name} is making consistent efforts with a {attendance} attendance rate "
            f"and a grade of {grade}. Encouraging regular study habits and periodic academic reviews "
            f"will help them achieve their full potential."
        )
    }


# -----------------------------
# 📄 BEAUTIFUL PDF — DYNAMIC SUBJECTS
# -----------------------------
def generate_pdf(file_path, student_row, analysis):
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#1e3a5f'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#5a7fa8'),
        alignment=TA_CENTER,
        spaceAfter=16
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1e3a5f'),
        fontName='Helvetica-Bold',
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leading=15,
        spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2d4a6e'),
        leading=15,
        spaceAfter=5,
        leftIndent=12,
        bulletIndent=0
    )
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        leading=16,
        spaceAfter=8,
        leftIndent=8,
        rightIndent=8
    )

    story = []

    # ─── HEADER ───
    story.append(Paragraph("Student Performance Report", title_style))
    story.append(Paragraph("AI-Powered Academic Analysis", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1e3a5f'), spaceAfter=12))

    # ─── STUDENT DETAILS TABLE ───
    story.append(Paragraph("Student Information", heading_style))

    def fmt(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "—"
        return str(v)

    details = [
        ["Name",            fmt(student_row.get("Name")),           "Student ID",      fmt(student_row.get("StudentID"))],
        ["Department",      fmt(student_row.get("Department")),      "Program",         fmt(student_row.get("Program"))],
        ["Year / Semester", f"Year {fmt(student_row.get('Year'))} / Sem {fmt(student_row.get('Semester'))}", "Gender", fmt(student_row.get("Gender"))],
        ["Grade",           fmt(student_row.get("Grade")),           "Academic Status", fmt(student_row.get("Academic_Status"))],
        ["Overall Average", fmt(student_row.get("Overall_Average")), "Attendance",      fmt(student_row.get("Attendance"))],
        ["Internship Score",fmt(student_row.get("Internship_Score")),"Project Score",   fmt(student_row.get("Project_Score"))],
    ]

    tbl = Table(details, colWidths=[42 * mm, 55 * mm, 42 * mm, 35 * mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e8f0f8')),
        ('TEXTCOLOR',  (0, 0), (0, -1), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR',  (2, 0), (2, -1), colors.HexColor('#1e3a5f')),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#c5d5e8')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f9ff')]),
        ('PADDING',    (0, 0), (-1, -1), 6),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    # ─── OVERALL SUMMARY ───
    if analysis.get("overall_summary"):
        story.append(Paragraph("Overall Summary", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#c5d5e8'), spaceAfter=6))
        story.append(Paragraph(analysis["overall_summary"], summary_style))
        story.append(Spacer(1, 6))

    # ─── RISK LEVEL BADGE ───
    risk = analysis.get("risk_level", "Medium")
    risk_color_map = {
        "Low":    colors.HexColor('#166534'),
        "Medium": colors.HexColor('#92400e'),
        "High":   colors.HexColor('#991b1b')
    }
    risk_bg_map = {
        "Low":    colors.HexColor('#dcfce7'),
        "Medium": colors.HexColor('#fef3c7'),
        "High":   colors.HexColor('#fee2e2')
    }
    risk_data = [[f"Academic Risk Level:   {risk}"]]
    risk_tbl = Table(risk_data, colWidths=[174 * mm])
    risk_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_bg_map.get(risk, colors.HexColor('#fef3c7'))),
        ('TEXTCOLOR',  (0, 0), (-1, -1), risk_color_map.get(risk, colors.HexColor('#92400e'))),
        ('FONTNAME',   (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 11),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('PADDING',    (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(risk_tbl)
    story.append(Spacer(1, 10))

    def render_section(title, emoji, items, color_hex):
        story.append(Paragraph(f"{emoji}  {title}", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(color_hex), spaceAfter=5))
        if isinstance(items, list):
            for item in items:
                story.append(Paragraph(f"• &nbsp; {item}", bullet_style))
        else:
            story.append(Paragraph(str(items), body_style))
        story.append(Spacer(1, 6))

    render_section("Key Strengths",            "✅", analysis.get("strengths",       []), "#22c55e")
    render_section("Areas for Improvement",    "⚠",  analysis.get("weaknesses",      []), "#f59e0b")
    render_section("Recommended Action Plan",  "📈", analysis.get("improvement_plan",[]), "#3b82f6")

    if analysis.get("subject_insights"):
        render_section("Subject-Level Insights", "📚", analysis.get("subject_insights", []), "#8b5cf6")

    # ─── PARENT MESSAGE ───
    if analysis.get("parent_message"):
        story.append(Paragraph("Message to Parent / Guardian", heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#c5d5e8'), spaceAfter=6))
        msg_data = [[Paragraph(analysis["parent_message"], summary_style)]]
        msg_tbl = Table(msg_data, colWidths=[174 * mm])
        msg_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4ff')),
            ('BOX',        (0, 0), (-1, -1), 1, colors.HexColor('#a5b4fc')),
            ('PADDING',    (0, 0), (-1, -1), 10),
        ]))
        story.append(msg_tbl)
        story.append(Spacer(1, 10))

    # ─── SUBJECT SCORE TABLE — DYNAMIC ───
    story.append(Paragraph("Detailed Subject Scores", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#c5d5e8'), spaceAfter=6))

    # ✅ Dynamically detect subjects from student_row keys
    student_dict = dict(student_row)
    subjects = extract_subjects(student_dict)

    score_headers = [["Subject", "Mid 1", "Mid 2", "Final"]]
    score_rows = []

    for subj in subjects:
        label = subj.replace("_", " ")
        m1    = fmt(student_dict.get(f"mid1_{subj}"))
        m2    = fmt(student_dict.get(f"mid2_{subj}"))
        fn    = fmt(student_dict.get(f"final_{subj}"))
        # Only include row if at least one score is not "—"
        if m1 != "—" or m2 != "—" or fn != "—":
            score_rows.append([label, m1, m2, fn])

    if score_rows:
        score_data = score_headers + score_rows
        score_tbl  = Table(score_data, colWidths=[80 * mm, 30 * mm, 30 * mm, 34 * mm])
        score_tbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1, 0),  colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, -1), 9),
            ('ALIGN',          (1, 0), (-1, -1), 'CENTER'),
            ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#c5d5e8')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f9ff')]),
            ('PADDING',        (0, 0), (-1, -1), 6),
        ]))
        story.append(score_tbl)
    else:
        story.append(Paragraph("No subject score data available.", body_style))

    story.append(Spacer(1, 16))

    # ─── FOOTER ───
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1e3a5f'), spaceAfter=6))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#888888'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        "This report is AI-assisted and generated for guidance purposes only. "
        "Please consult academic advisors and teachers for comprehensive planning.",
        footer_style
    ))

    doc.build(story)


# -----------------------------
# 🔐 LOGIN
# -----------------------------
def parent_login(request):
    files = []
    if os.path.exists(PASSWORD_FILES_DIR):
        for f in os.listdir(PASSWORD_FILES_DIR):
            if f.endswith(".xlsx"):
                files.append({"name": f, "file": f})

    error = None

    if request.method == "POST":
        file     = request.POST.get("college_file", "").strip()
        sid      = request.POST.get("student_id",   "").strip()
        aishe    = request.POST.get("aishe_code",   "").strip()
        pwd      = request.POST.get("password",     "").strip()
        relation = request.POST.get("relation",     "Parent").strip()

        df = pd.read_excel(os.path.join(PASSWORD_FILES_DIR, file))
        df.columns = df.columns.str.strip()

        match = df[
            (df["StudentID"].astype(str).str.strip()        == sid)   &
            (df["AISHE_Code"].astype(str).str.strip()       == aishe) &
            (df["student_password"].astype(str).str.strip() == pwd)
        ]

        if not match.empty:
            request.session.flush()

            student_row  = match.iloc[0]
            student_dict = student_row.to_dict()

            student_data = get_student_full_data(sid, aishe)
            if student_data is None:
                student_data = {
                    str(k): ("" if pd.isna(v) else (v.item() if hasattr(v, "item") else str(v)))
                    for k, v in student_dict.items()
                }

            build_parent_context(sid, aishe, student_data, relation)

            student_name = str(
                student_data.get("Name")         or
                student_data.get("name")         or
                student_data.get("StudentName")  or
                student_data.get("student_name") or
                sid
            )

            request.session["parent_student_id"]   = sid
            request.session["parent_aishe_code"]   = aishe
            request.session["parent_relation"]     = relation
            request.session["parent_student_name"] = student_name
            request.session["parent_student_data"] = student_data

            return redirect("parent_chat_room")

        error = "Invalid Student ID, AISHE Code, or Password."

    return render(request, "parent_login.html", {
        "college_files": files,
        "error":         error,
    })


# -----------------------------
# 🚀 REPORT GENERATION
# -----------------------------
def parent_report_generate(request):
    if "parent_student_id" not in request.session:
        return redirect("parent_login")

    if request.method == "POST":
        try:
            email        = request.POST.get("parent_email", "").strip()
            student_data = request.session.get("parent_student_data")

            if not student_data:
                return HttpResponse("❌ Session expired. Please login again.")

            if not email:
                return render(request, "parent_report_generate.html", {
                    "error":        "Please provide a valid email address.",
                    "student_name": request.session.get("parent_student_name"),
                    "student_id":   request.session.get("parent_student_id"),
                })

            student_row = pd.Series(student_data)

            # 🔹 LLM Analysis (robust)
            analysis = analyze_with_llm(student_data)

            # 🔹 Generate PDF
            file_path = os.path.join(
                settings.MEDIA_ROOT,
                f"report_{request.session['parent_student_id']}.pdf"
            )
            generate_pdf(file_path, student_row, analysis)

            # ✅ Build dynamic subject scores list for email template
            subjects      = extract_subjects(student_data)
            subject_scores = []
            for subj in subjects:
                m1 = student_data.get(f"mid1_{subj}", "")
                m2 = student_data.get(f"mid2_{subj}", "")
                fn = student_data.get(f"final_{subj}", "")

                def safe(v):
                    if v is None or v == "" or (isinstance(v, float) and pd.isna(v)):
                        return "—"
                    return str(v)

                m1, m2, fn = safe(m1), safe(m2), safe(fn)
                # Only include if at least one score present
                if m1 != "—" or m2 != "—" or fn != "—":
                    subject_scores.append({
                        "subject": subj.replace("_", " "),
                        "mid1":    m1,
                        "mid2":    m2,
                        "final":   fn,
                    })

            # 🔹 HTML Email
            html_content = render_to_string(
                "emails/student_report.html",
                {
                    "student_name":    request.session["parent_student_name"],
                    "student_id":      request.session["parent_student_id"],
                    "aishe_code":      request.session["parent_aishe_code"],
                    "overall_summary": analysis.get("overall_summary", ""),
                    "strengths":       analysis.get("strengths", []),
                    "weaknesses":      analysis.get("weaknesses", []),
                    "improvement_plan":analysis.get("improvement_plan", []),
                    "subject_insights":analysis.get("subject_insights", []),
                    "risk_level":      analysis.get("risk_level", "Medium"),
                    "parent_message":  analysis.get("parent_message", ""),
                    "grade":           student_data.get("Grade", "N/A"),
                    "department":      student_data.get("Department", "N/A"),
                    "attendance":      student_data.get("Attendance", "N/A"),
                    "overall_average": student_data.get("Overall_Average", "N/A"),
                    # ✅ Dynamic subject scores — works for ALL departments
                    "subject_scores":  subject_scores,
                }
            )

            email_msg = EmailMessage(
                subject=f"📊 Student Performance Report — {request.session['parent_student_name']}",
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_msg.content_subtype = "html"
            email_msg.attach_file(file_path)
            email_msg.send()

            return render(request, "parent_report_generate.html", {
                "success":      True,
                "student_name": request.session.get("parent_student_name"),
                "student_id":   request.session.get("parent_student_id"),
                "email_sent_to": email,
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return render(request, "parent_report_generate.html", {
                "error":        f"Something went wrong: {str(e)}",
                "student_name": request.session.get("parent_student_name"),
                "student_id":   request.session.get("parent_student_id"),
            })

    return render(request, "parent_report_generate.html", {
        "student_name": request.session.get("parent_student_name"),
        "student_id":   request.session.get("parent_student_id"),
    })
# -----------------------------
# 🚪 PARENT LOGOUT
# -----------------------------
def parent_logout(request):
    request.session.flush()
    return redirect("/indexs")