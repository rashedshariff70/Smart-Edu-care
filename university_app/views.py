from django.shortcuts import render, redirect
from django.contrib import messages
from university_app.models import UniversityRequest


def register_view(request):
    return render(request, "university_register.html")


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UniversityRequest

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

        if UniversityRequest.objects.filter(college_id=college_id).exists():
            messages.warning(
                request,
                f"College ID '{college_id}' already exists. Please use a different ID."
            )
            return render(request, "university_register.html")

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
        # ✅ Fix: use named URL, not a string path
        return redirect("university_reg_save")

    return render(request, "university_register.html")


def university_reg_show(request):
    universities = UniversityRequest.objects.all()
    return render(request, "university_reg_show.html", {"universities": universities})

import os
import pandas as pd
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages


def university_login(request):
    """
    Login using College/University ID + Password
    Validated against Excel file: static/data/uploads/univesity_logins/university_logins.xlsx

    Actual Excel columns (written by _save_credentials_to_excel):
        S.No | College ID / Username | Official Email | Password | University Name | Approved On

    After normalisation (strip + lower + spaces→_):
        s.no | college_id_/_username | official_email | password | university_name | approved_on
    """

    if request.method == "POST":
        college_id = request.POST.get("college_id", "").strip()
        password   = request.POST.get("password", "").strip()

        if not college_id or not password:
            messages.error(request, "Both fields are required.")
            return redirect("university_login")

        # ── Locate Excel file ─────────────────────────────────────────────
        excel_folder = os.path.join(
            settings.BASE_DIR, "static", "data", "uploads", "univesity_logins"
        )

        excel_file = None
        if os.path.isdir(excel_folder):
            preferred = os.path.join(excel_folder, "university_logins.xlsx")
            if os.path.isfile(preferred):
                excel_file = preferred
            else:
                for fname in sorted(os.listdir(excel_folder)):
                    if fname.lower().endswith((".xlsx", ".xls", ".xlsm")):
                        excel_file = os.path.join(excel_folder, fname)
                        break

        if not excel_file:
            messages.error(request, "Credential store not found. Please contact admin.")
            return redirect("university_login")

        # ── Read & normalise column names ─────────────────────────────────
        try:
            df = pd.read_excel(excel_file, dtype=str)

            # Normalise: strip whitespace + lowercase + spaces → underscore
            # "College ID / Username" → "college_id_/_username"
            # "Official Email"        → "official_email"
            # "University Name"       → "university_name"
            # "Password"              → "password"
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
                .str.replace(r"\s+", "_", regex=True)
            )

            # ── Resolve College ID column ─────────────────────────────────
            # Exact normalised name from the Excel header written by _save_credentials_to_excel
            id_col = None
            for candidate in (
                "college_id_/_username",   # ← exact match from your Excel
                "college_id",
                "collegeid",
                "university_id",
                "id",
            ):
                if candidate in df.columns:
                    id_col = candidate
                    break

            # ── Resolve Password column ───────────────────────────────────
            pass_col = None
            for candidate in ("password", "pass", "passwd", "pwd"):
                if candidate in df.columns:
                    pass_col = candidate
                    break

            # ── Resolve Name column ───────────────────────────────────────
            name_col = None
            for candidate in ("university_name", "name", "college_name"):
                if candidate in df.columns:
                    name_col = candidate
                    break

            if not id_col or not pass_col:
                found = ", ".join(df.columns.tolist()) or "none"
                messages.error(
                    request,
                    f"Credential file format is incorrect (found columns: {found}). "
                    f"Contact admin."
                )
                return redirect("university_login")

            # ── Strip whitespace from cell values ─────────────────────────
            df[id_col]   = df[id_col].str.strip()
            df[pass_col] = df[pass_col].str.strip()

            # ── Match credentials ─────────────────────────────────────────
            match = df[
                (df[id_col]   == college_id) &
                (df[pass_col] == password)
            ]

            if not match.empty:
                request.session["college_id"] = college_id

                # Store university name in session if available
                if name_col:
                    name_val = match.iloc[0][name_col]
                    if pd.notna(name_val):
                        request.session["university_name"] = str(name_val).strip()

                messages.success(request, "Login successful. Welcome!")
                return redirect("student_data_upload")

            else:
                messages.error(request, "Invalid College ID or Password.")
                return redirect("university_login")

        except Exception as e:
            messages.error(request, f"Login error: {str(e)}")
            return redirect("university_login")

    return render(request, "university_login.html")

import os
import re

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_folder(value: str) -> str:
    safe = value.strip().replace(" ", "_")
    safe = re.sub(r"[^\w\-]", "", safe)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:120]


def _read_file(file_obj, ext: str) -> pd.DataFrame:
    file_obj.seek(0)
    try:
        if ext == ".csv":
            try:
                df = pd.read_csv(file_obj, dtype=str, encoding="utf-8")
            except UnicodeDecodeError:
                file_obj.seek(0)
                df = pd.read_csv(file_obj, dtype=str, encoding="latin-1")
        else:
            df = pd.read_excel(file_obj, dtype=str)
    except Exception as e:
        print(f"[DEBUG] _read_file error: {e}")
        return pd.DataFrame()
    finally:
        file_obj.seek(0)
    return df


def _extract_aishe_code(file_obj, ext: str) -> str | None:
    """
    Find any column whose name starts with 'aishe' (case-insensitive,
    ignoring spaces / underscores / dashes).
    Return the first non-empty cell value from that column.
    """
    df = _read_file(file_obj, ext)
    if df.empty:
        print("[DEBUG] DataFrame is empty — could not read file.")
        return None

    print(f"[DEBUG] Columns found in file: {df.columns.tolist()}")

    aishe_col = None
    for col in df.columns:
        normalised = re.sub(r"[\s_\-\.]+", "", col).lower()
        print(f"[DEBUG] Checking column '{col}' → normalised: '{normalised}'")
        if normalised.startswith("aishe"):
            aishe_col = col
            print(f"[DEBUG] Matched AISHE column: '{col}'")
            break

    if not aishe_col:
        print("[DEBUG] No AISHE column found.")
        return None

    for val in df[aishe_col].dropna():
        v = str(val).strip()
        if v and v.lower() not in ("nan", "none", ""):
            print(f"[DEBUG] AISHE code value: '{v}'")
            return v

    print("[DEBUG] AISHE column found but all values are empty.")
    return None


# ── View ─────────────────────────────────────────────────────────────────────
import os
import re
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def _safe_folder(value: str) -> str:
    """Convert any string to a safe folder name."""
    safe = value.strip().replace(" ", "_")
    safe = re.sub(r"[^\w\-]", "", safe)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:120]


def _get_repeated_value(file_obj, ext: str) -> str | None:
    """
    Logic:
      1. Read file with no header to find the real header row
         (row with the most non-empty cells).
      2. Re-read using that row as header.
      3. For every column count how many rows share the same value.
      4. Pick the column whose header contains 'aishe' with highest repeat %.
         If no aishe column found, pick column with highest repeat % overall
         (excluding pure numbers and blanks).
      5. Return that most-repeated value → used as folder name suffix.
    """
    # ── Step 1: Read raw ──────────────────────────────────────────────────
    file_obj.seek(0)
    try:
        if ext == ".csv":
            try:
                raw = pd.read_csv(file_obj, dtype=str, header=None, encoding="utf-8")
            except UnicodeDecodeError:
                file_obj.seek(0)
                raw = pd.read_csv(file_obj, dtype=str, header=None, encoding="latin-1")
        else:
            raw = pd.read_excel(file_obj, dtype=str, header=None)
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return None
    finally:
        file_obj.seek(0)

    if raw.empty:
        return None

    # ── Step 2: Find real header row (row with most filled cells) ─────────
    filled = raw.apply(
        lambda row: row.dropna()
                       .apply(lambda c: str(c).strip() not in ("", "nan"))
                       .sum(),
        axis=1
    )
    hdr_idx = int(filled.idxmax())

    # ── Step 3: Re-read with correct header ───────────────────────────────
    file_obj.seek(0)
    try:
        if ext == ".csv":
            try:
                df = pd.read_csv(file_obj, dtype=str, header=hdr_idx, encoding="utf-8")
            except UnicodeDecodeError:
                file_obj.seek(0)
                df = pd.read_csv(file_obj, dtype=str, header=hdr_idx, encoding="latin-1")
        else:
            df = pd.read_excel(file_obj, dtype=str, header=hdr_idx)
    except Exception as e:
        print(f"[ERROR] Re-read failed: {e}")
        return None
    finally:
        file_obj.seek(0)

    if df.empty or len(df) == 0:
        return None

    total = len(df)

    # ── Step 4: Score every column by repeat % ────────────────────────────
    # col_scores = { col_name: (most_repeated_value, repeat_percentage) }
    col_scores = {}
    for col in df.columns:
        clean = df[col].dropna().apply(lambda x: str(x).strip())
        clean = clean[clean.apply(lambda v: v not in ("", "nan", "none"))]
        if len(clean) == 0:
            continue
        top_val = clean.value_counts().idxmax()
        top_pct = clean.value_counts().max() / total
        col_scores[col] = (top_val, top_pct)

    if not col_scores:
        return None

    # ── Step 5: Pick best column ──────────────────────────────────────────
    # Priority 1 → column whose header contains "aishe" with pct >= 50%
    aishe_candidates = {
        col: (val, pct)
        for col, (val, pct) in col_scores.items()
        if "aishe" in str(col).lower().replace(" ", "").replace("_", "")
        and pct >= 0.50
    }
    if aishe_candidates:
        best = max(aishe_candidates, key=lambda c: aishe_candidates[c][1])
        print(f"[FOLDER] AISHE column '{best}' → value='{aishe_candidates[best][0]}'")
        return aishe_candidates[best][0]

    # Priority 2 → highest repeat % where value is not a plain number
    non_numeric = {
        col: (val, pct)
        for col, (val, pct) in col_scores.items()
        if not str(val).replace(".", "").replace("-", "").isdigit()
        and len(str(val)) > 2
        and pct >= 0.70
    }
    if non_numeric:
        best = max(non_numeric, key=lambda c: non_numeric[c][1])
        print(f"[FOLDER] Best repeat column '{best}' → value='{non_numeric[best][0]}'")
        return non_numeric[best][0]

    # Priority 3 → absolute fallback
    best = max(col_scores, key=lambda c: col_scores[c][1])
    print(f"[FOLDER] Fallback column '{best}' → value='{col_scores[best][0]}'")
    return col_scores[best][0]


def student_data_upload(request):
    if request.method == "POST":
        university_name = request.POST.get("university_name", "").strip()
        student_files   = request.FILES.getlist("student_files")

        if not university_name:
            messages.error(request, "Please enter the university name. ❌")
            return redirect("student_data_upload")

        if not student_files:
            messages.error(request, "Please select at least one file. ❌")
            return redirect("student_data_upload")

        # Destination root → static/data/uploads/received/
        base_dir = os.path.join(
            settings.BASE_DIR, "static", "data", "uploads", "university_data"
        )
        os.makedirs(base_dir, exist_ok=True)

        uni_part = _safe_folder(university_name)   # e.g. Sri_Venkateswara_University

        saved    = []
        no_value = []
        skipped  = []

        for student_file in student_files:
            fname = student_file.name
            _, ext = os.path.splitext(fname)
            ext = ext.lower()

            if ext not in ALLOWED_EXTENSIONS:
                skipped.append(fname)
                continue

            # Get the most-repeated AISHE/identifier value from the file
            repeated_value = _get_repeated_value(student_file, ext)

            if not repeated_value:
                no_value.append(fname)
                continue

            # ── Folder = university name input + repeated value ───────────
            # e.g.  Sri_Venkateswara_University_U-0423
            folder_name = f"{uni_part}_{_safe_folder(repeated_value)}"
            dest_dir    = os.path.join(base_dir, folder_name)

            # Reuse existing folder, don't create duplicate
            os.makedirs(dest_dir, exist_ok=True)

            # Save file — overwrites if same filename already present
            save_path = os.path.join(dest_dir, fname)
            student_file.seek(0)
            with open(save_path, "wb+") as out:
                for chunk in student_file.chunks():
                    out.write(chunk)

            print(f"[UPLOAD] ✅ Saved '{fname}' → {folder_name}")
            saved.append((fname, folder_name))

        # ── Messages ──────────────────────────────────────────────────────
        if saved:
            folder_groups: dict[str, list[str]] = {}
            for fname, folder in saved:
                folder_groups.setdefault(folder, []).append(fname)

            for folder, files in folder_groups.items():
                if len(files) == 1:
                    messages.success(request,
                        f"✅ '{files[0]}' saved → {folder}")
                else:
                    messages.success(request,
                        f"✅ {len(files)} files saved → {folder}")

        if no_value:
            messages.warning(request,
                f"⚠️ Could not detect identifier value in: {', '.join(no_value)}.")

        if skipped:
            messages.error(request,
                f"❌ Skipped unsupported file(s): {', '.join(skipped)}.")

        return redirect("student_data_upload")

    return render(request, "university_stu_data_upload.html")