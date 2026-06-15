from django.shortcuts import render, HttpResponse, redirect
import pandas as pd 
from django.contrib import messages
from django.conf import settings  
import os
import csv
import re
from io import TextIOWrapper
from django.http import HttpResponseRedirect, JsonResponse

def admin_dash(request):
    selected_uni = request.GET.get('university')
    roll_no = request.GET.get('roll_no', '').strip()
    show_all = request.GET.get('show_all', '') == '1'

    headers = []
    student_data = []
    all_headers = []
    all_data = []
    search_done = False

    if selected_uni:
        file_path = os.path.join(settings.BASE_DIR, 'static', 'data', f"{selected_uni}_Students.csv")

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                all_rows = list(reader)

            if all_rows:
                headers = all_rows[0]
                data_rows = all_rows[1:]
                
                # --- PASSWORD LOGIC START ---
                # Ensure 'student_password' column exists in headers
                if 'student_password' not in headers:
                    headers.append('student_password')
                    pass_idx = len(headers) - 1
                    # Update all existing rows with the new password
                    for row in data_rows:
                        student_id = row[0]
                        numeric_part = "".join(re.findall(r'\d+', student_id))
                        row.append(f"Smartedu_{numeric_part}")
                else:
                    pass_idx = headers.index('student_password')
                    # Fill missing passwords if any
                    for row in data_rows:
                        if len(row) <= pass_idx or not row[pass_idx]:
                            student_id = row[0]
                            numeric_part = "".join(re.findall(r'\d+', student_id))
                            new_pass = f"Smartedu_{numeric_part}"
                            if len(row) <= pass_idx:
                                row.append(new_pass)
                            else:
                                row[pass_idx] = new_pass
                # --- PASSWORD LOGIC END ---

                search_done = True

                if request.method == 'POST':
                    form_data = request.POST.dict()
                    updated_roll = form_data.get('roll_no')
                    new_email = form_data.get('new_email', '').strip()
                    new_attendance = form_data.get('new_attendance', '').strip()

                    # Update specific student row
                    for i, row in enumerate(data_rows):
                        if row[0] == updated_roll:
                            if 'Email' in headers and new_email:
                                row[headers.index('Email')] = new_email
                            if 'Attendance' in headers and new_attendance:
                                row[headers.index('Attendance')] = new_attendance
                            break

                    try:
                        with open(file_path, 'w', encoding='utf-8', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(headers)
                            writer.writerows(data_rows)
                        messages.success(request, f"Record for {updated_roll} updated with password generated.")
                    except PermissionError:
                        messages.error(request, "Permission denied: Close the CSV file and try again.")
                    
                    return HttpResponseRedirect(request.path + f"?university={selected_uni}&roll_no={updated_roll}")

                # Filtering Logic
                if roll_no:
                    student_data = [row for row in data_rows if roll_no.lower() in row[0].lower()]
                else:
                    student_data = data_rows[:10]

                if show_all:
                    all_headers = headers
                    all_data = data_rows

        else:
            messages.error(request, "Student data file not found.")
            search_done = True

    return render(request, 'admin_dash.html', {
        'headers': headers,
        'student_data': student_data,
        'selected_uni': selected_uni,
        'roll_no': roll_no,
        'search_done': search_done,
        'show_all': show_all,
        'all_headers': all_headers,
        'all_data': all_data,
    })

def student_dataset_view(request):
    # Note: Updated to handle CSV with potential new password column
    file_path = 'data/KLUniversity_Students_Batchwise.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        
        # Ensure password exists for Batchwise view too
        if 'student_password' not in df.columns:
            df['student_password'] = 'Smartedu_' + df['StudentID'].astype(str).str.extract(r'(\d+)', expand=False)

        departments = sorted(df['Department'].dropna().unique())
        programs = sorted(df['Program'].dropna().unique())
        roll_numbers = sorted(df['StudentID'].dropna().unique())

        context = {
            'data': df.to_dict(orient='records'),
            'departments': departments,
            'programs': programs,
            'roll_numbers': roll_numbers,
        }
        return render(request, 'student_dataset.html', context)
    else:
        return HttpResponse("File not found")