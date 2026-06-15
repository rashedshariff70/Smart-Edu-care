# ============================================================
# PASTE THIS BLOCK AT THE BOTTOM OF student_app/views.py
# ============================================================

import os
import json
import requests
import pandas as pd
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

# -------------------------------------------------
# PATHS
# -------------------------------------------------
AISHE_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "AISHE_CODE"
)

PASSWORD_FILES_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "password_generated_files"
)

STUDENT_CONTEXT_DIR = os.path.join(
    settings.BASE_DIR,
    "static", "data", "uploads", "student_chat_contexts"
)


# -------------------------------------------------
# HELPER: Read full student row from password_generated_files
# -------------------------------------------------
def get_student_full_data(student_id, aishe_code):
    if not os.path.exists(PASSWORD_FILES_DIR):
        return None

    for filename in os.listdir(PASSWORD_FILES_DIR):
        filepath = os.path.join(PASSWORD_FILES_DIR, filename)
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(filepath, dtype=str).fillna("")
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(filepath, dtype=str).fillna("")
            else:
                continue

            df.columns       = [c.strip() for c in df.columns]
            if "StudentID" not in df.columns or "AISHE_Code" not in df.columns:
                continue

            df["StudentID"]  = df["StudentID"].str.strip()
            df["AISHE_Code"] = df["AISHE_Code"].str.strip()

            match = df[
                (df["StudentID"]  == student_id.strip()) &
                (df["AISHE_Code"] == aishe_code.strip())
            ]
            if not match.empty:
                return match.iloc[0].to_dict()

        except Exception as e:
            print(f"⚠️  Error reading {filename}: {e}")

    return None


# -------------------------------------------------
# HELPER: Build student context text file
# -------------------------------------------------
def build_student_context(student_id, aishe_code, student_data):
    os.makedirs(STUDENT_CONTEXT_DIR, exist_ok=True)
    context_path = os.path.join(STUDENT_CONTEXT_DIR, f"{aishe_code}_{student_id}.txt")
    with open(context_path, "w", encoding="utf-8") as f:
        f.write("=== STUDENT INFORMATION ===\n")
        for key, value in student_data.items():
            f.write(f"{key}: {value}\n")
    return context_path


# -------------------------------------------------
# HELPER: Read student context
# -------------------------------------------------
def read_student_context(student_id, aishe_code):
    context_path = os.path.join(STUDENT_CONTEXT_DIR, f"{aishe_code}_{student_id}.txt")
    if os.path.exists(context_path):
        with open(context_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


# -------------------------------------------------
# HELPER: Call HuggingFace LLM
# -------------------------------------------------
def call_llm(question, context):
    prompt = f"""You are a helpful college academic assistant.
Answer in the SAME language the student uses.
Be concise, friendly, and accurate.

=== STUDENT DATA ===
{context}

=== STUDENT QUESTION ===
{question}

Answer clearly based on the student data above.
"""
    try:
        url     = "https://router.huggingface.co/v1/chat/completions"
        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "model": "meta-llama/Llama-3.1-70B-Instruct",
            "messages": [
                {"role": "system", "content": "You are a helpful academic assistant."},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.4
        }
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code != 200:
            return f"LLM Error: {res.text}"
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error calling LLM: {str(e)}"


# -------------------------------------------------
# HELPER: Transcribe audio via HuggingFace Whisper API
# -------------------------------------------------
def transcribe_audio(audio_path):
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        url     = "https://api-inference.huggingface.co/models/openai/whisper-base"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        res     = requests.post(url, headers=headers, data=audio_bytes, timeout=30)
        if res.status_code == 200:
            return res.json().get("text", "").strip()
        print(f"⚠️  Whisper API error: {res.text}")
        return ""
    except Exception as e:
        print(f"⚠️  Transcription error: {e}")
        return ""


# =============================================================================
# VIEW 1: student_data_chat — login page
# =============================================================================
def student_data_chat(request):
    error = None

    if request.method == "POST":
        aishe_code = request.POST.get("aishe_code", "").strip()
        student_id = request.POST.get("student_id", "").strip()

        if not aishe_code or not student_id:
            error = "Both AISHE Code and Student ID are required."
        else:
            excel_path = os.path.join(AISHE_DIR, f"{aishe_code}.xlsx")
            if not os.path.exists(excel_path):
                error = f"No data found for AISHE Code: {aishe_code}"
            else:
                df = pd.read_excel(excel_path, dtype=str).fillna("")
                df["StudentID"]  = df["StudentID"].str.strip()
                df["AISHE_Code"] = df["AISHE_Code"].str.strip()

                match = df[
                    (df["StudentID"]  == student_id) &
                    (df["AISHE_Code"] == aishe_code)
                ]

                if match.empty:
                    error = "Student ID not found for this AISHE Code."
                else:
                    student_data = get_student_full_data(student_id, aishe_code)
                    if student_data is None:
                        error = "Student details not found. Please contact admin."
                    else:
                        build_student_context(student_id, aishe_code, student_data)
                        request.session["chat_student_id"]   = student_id
                        request.session["chat_aishe_code"]   = aishe_code
                        request.session["chat_student_name"] = student_data.get("name", student_id)
                        return redirect("student_chat_room")

    return render(request, "student_data_chat.html", {"error": error})


# =============================================================================
# VIEW 2: student_chat_room — chat UI
# =============================================================================
def student_chat_room(request):
    if "chat_student_id" not in request.session:
        return redirect("student_data_chat")

    return render(request, "student_chat_room.html", {
        "student_name": request.session.get("chat_student_name", "Student"),
        "student_id":   request.session.get("chat_student_id", ""),
        "aishe_code":   request.session.get("chat_aishe_code", ""),
    })


# =============================================================================
# VIEW 3: student_chat_ask — AJAX text endpoint
# =============================================================================
@csrf_exempt
def student_chat_ask(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Invalid method"}, status=405)
    if "chat_student_id" not in request.session:
        return JsonResponse({"answer": "Session expired. Please login again."})
    try:
        data       = json.loads(request.body)
        question   = data.get("question", "").strip()
        student_id = request.session["chat_student_id"]
        aishe_code = request.session["chat_aishe_code"]
        if not question:
            return JsonResponse({"answer": "Please type a question."})
        context = read_student_context(student_id, aishe_code)
        answer  = call_llm(question, context)
        return JsonResponse({"answer": answer})
    except Exception as e:
        return JsonResponse({"answer": f"Error: {str(e)}"})


# =============================================================================
# VIEW 4: student_chat_voice — AJAX voice endpoint
# =============================================================================
@csrf_exempt
def student_chat_voice(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Invalid method"}, status=405)
    if "chat_student_id" not in request.session:
        return JsonResponse({"answer": "Session expired. Please login again."})
    try:
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return JsonResponse({"answer": "No audio received."})

        student_id = request.session["chat_student_id"]
        aishe_code = request.session["chat_aishe_code"]

        temp_path  = os.path.join(settings.BASE_DIR, "temp_voice.webm")
        with open(temp_path, "wb") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        transcript = transcribe_audio(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not transcript:
            return JsonResponse({"answer": "Could not understand audio.", "transcript": ""})

        context = read_student_context(student_id, aishe_code)
        answer  = call_llm(transcript, context)
        return JsonResponse({"answer": answer, "transcript": transcript})
    except Exception as e:
        return JsonResponse({"answer": f"Error: {str(e)}", "transcript": ""})


# =============================================================================
# VIEW 5: student_chat_logout
# =============================================================================
def student_chat_logout(request):
    request.session.pop("chat_student_id",   None)
    request.session.pop("chat_aishe_code",   None)
    request.session.pop("chat_student_name", None)
    return redirect("student_data_chat")