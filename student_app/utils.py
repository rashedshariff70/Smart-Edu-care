# ════════════════════════════════════════════════════════════════
# SmartEduCare - UTILS (FINAL STABLE VERSION)
# ════════════════════════════════════════════════════════════════

import os
import pandas as pd
import requests
import google.generativeai as genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✅ CORRECT ENV KEYS
GROQ_API_KEY3 = os.getenv("GROQ_API_KEY3")
GROQ_API_KEY4 = os.getenv("GROQ_API_KEY4")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_API_Key")

# ════════════════════════════════════════════════════════════════
# 1. LOAD STUDENT DATA (FIXED)
# ════════════════════════════════════════════════════════════════

def get_student_full_data(student_id, aishe_code):
    folder_path = os.path.join(
        BASE_DIR,
        "static", "data", "uploads", "password_generated_files"
    )

    if not os.path.exists(folder_path):
        print("❌ Folder not found:", folder_path)
        return None

    student_id = str(student_id).strip().lower()
    aishe_code = str(aishe_code).strip().lower()

    for file in os.listdir(folder_path):
        if file.endswith(".xlsx"):
            try:
                df = pd.read_excel(os.path.join(folder_path, file))
                df.columns = df.columns.str.strip()

                df["StudentID"] = df["StudentID"].astype(str).str.strip().str.lower()
                df["AISHE_Code"] = df["AISHE_Code"].astype(str).str.strip().str.lower()

                row = df[
                    (df["StudentID"] == student_id) &
                    (df["AISHE_Code"] == aishe_code)
                ]

                if not row.empty:
                    print("✅ Student found in:", file)
                    return row.iloc[0].to_dict()

            except Exception as e:
                print("⚠️ Excel error:", e)

    print("❌ Student NOT FOUND")
    return None


# ════════════════════════════════════════════════════════════════
# 2. CONTEXT
# ════════════════════════════════════════════════════════════════

def build_parent_context(student_id, aishe_code, data, relation):
    folder = os.path.join(BASE_DIR, "static/data/student_chat_contexts")
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, f"{aishe_code}_{student_id}.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Relation: {relation}\n\n")
        for k, v in data.items():
            f.write(f"{k}: {v}\n")

    return path


def read_parent_context(student_id, aishe_code):
    path = os.path.join(
        BASE_DIR,
        "static/data/student_chat_contexts",
        f"{aishe_code}_{student_id}.txt"
    )

    if not os.path.exists(path):
        return ""

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ════════════════════════════════════════════════════════════════
# 3. GEMINI CONFIG
# ════════════════════════════════════════════════════════════════

def _configure_gemini():
    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY missing")
    genai.configure(api_key=GEMINI_API_KEY)


# ════════════════════════════════════════════════════════════════
# 4. CHAT (GEMINI + FALLBACK QWEN)
# ════════════════════════════════════════════════════════════════

def call_gemini_parent(question, context, relation):
    try:
        _configure_gemini()

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
You are helping a {relation} understand student performance.

{context}

Question: {question}
"""

        res = model.generate_content(prompt)
        return res.text.strip()

    except Exception as e:
        print("⚠️ Gemini failed:", e)

        # 🔥 FALLBACK TO QWEN
        return call_qwen_fallback(question, context)


def call_qwen_fallback(question, context):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY4}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen/qwen-2.5-32b-instruct",
            "messages": [
                {"role": "user", "content": f"{context}\n\nQ: {question}"}
            ],
            "temperature": 0.3
        }

        res = requests.post(url, headers=headers, json=payload)

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]

        return "AI service temporarily unavailable."

    except Exception as e:
        print("⚠️ Qwen fallback error:", e)
        return "AI service temporarily unavailable."


# ════════════════════════════════════════════════════════════════
# 5. WHISPER (VOICE → TEXT)
# ════════════════════════════════════════════════════════════════

def transcribe_parent_audio(file_path):
    if not GROQ_API_KEY3:
        print("❌ GROQ_API_KEY3 missing")
        return ""

    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY3}"
    }

    with open(file_path, "rb") as f:
        files = {
            "file": f,
            "model": (None, "whisper-large-v3")
        }

        res = requests.post(url, headers=headers, files=files)

    if res.status_code == 200:
        return res.json().get("text", "")

    print("⚠️ Whisper error:", res.text)
    return ""