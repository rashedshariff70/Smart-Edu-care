from django.shortcuts import render,HttpResponse,redirect
import pandas as pd 
from django.contrib import messages
from django.conf import settings  
import os
import csv
from io import TextIOWrapper
from django.http import HttpResponseRedirect




def student_ml_home(request):
    return render(request,'student_ml_homedltml')

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


def student_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            college_id = form.cleaned_data['college_id']
            college_name = form.cleaned_data['college_name']
            password = form.cleaned_data['password']

            try:
                login_record = StudentLogin.objects.get(
                    college_id=college_id,
                    college_name__iexact=college_name.strip()
                )

                if login_record.check_password(password):
                    messages.success(request, "Login successful!")
                    # Here you would normally set session/login user
                    return redirect('home')  # or your dashboard
                else:
                    messages.error(request, "Incorrect password")
            except StudentLogin.DoesNotExist:
                messages.error(request, "Invalid College ID or College Name")
    else:
        form = LoginForm()

    return render(request, 'student_login.html', {'form': form})

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



