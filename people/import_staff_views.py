# people/import_staff_views.py

import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import StaffMember
from accounts.decorators import admin_required


STAFF_TYPE_CHOICES = {
    'teaching'    : ['teaching', 'teacher', 't'],
    'non_teaching': ['non_teaching', 'non-teaching', 'nonteaching', 'support', 'non teaching', 'nt'],
}


def _clean(value):
    if value is None:
        return ''
    s = str(value).strip()
    return '' if s.lower() in ('nan', 'none', '') else s


def _parse_staff_type(value, selected_type):
    """Use the selected type from the form unless the file overrides it clearly."""
    if selected_type:
        return selected_type
    v = _clean(value).lower()
    for key, aliases in STAFF_TYPE_CHOICES.items():
        if v in aliases:
            return key
    return 'teaching'  # default


@login_required
@admin_required
def import_staff(request):
    if request.method == 'GET':
        return render(request, 'people/import_staff.html', {})

    # --- POST ---
    staff_type    = request.POST.get('staff_type')
    uploaded_file = request.FILES.get('excel_file')

    if not staff_type:
        messages.error(request, 'Please select a staff type before uploading.')
        return render(request, 'people/import_staff.html', {})

    if not uploaded_file:
        messages.error(request, 'Please select a file to upload.')
        return render(request, 'people/import_staff.html', {})

    fname = uploaded_file.name.lower()
    if not (fname.endswith('.xlsx') or fname.endswith('.xls') or fname.endswith('.csv')):
        messages.error(request, 'Invalid file type. Please upload .xlsx, .xls or .csv.')
        return render(request, 'people/import_staff.html', {})

    try:
        if fname.endswith('.csv'):
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)
    except Exception as e:
        messages.error(request, f'Could not read file: {e}')
        return render(request, 'people/import_staff.html', {})

    # normalise column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # determine required columns based on staff type
    # teaching staff → staff_id is TSC number
    # non-teaching   → staff_id is National ID
    required = ['name']
    if staff_type == 'teaching':
        required.append('tsc number')
    else:
        required.append('national id')

    # also accept generic 'staff id' column
    has_staff_id   = 'staff id' in df.columns
    has_tsc        = 'tsc number' in df.columns
    has_national   = 'national id' in df.columns

    id_column = None
    if staff_type == 'teaching':
        if has_tsc:
            id_column = 'tsc number'
        elif has_staff_id:
            id_column = 'staff id'
    else:
        if has_national:
            id_column = 'national id'
        elif has_staff_id:
            id_column = 'staff id'

    if not id_column:
        expected = 'TSC Number' if staff_type == 'teaching' else 'National ID'
        messages.error(request,
                       f'Missing ID column. Expected "{expected}" or "Staff ID". '
                       f'Columns found: {", ".join(df.columns.tolist())}')
        return render(request, 'people/import_staff.html', {})

    if 'name' not in df.columns:
        messages.error(request,
                       f'Missing "Name" column. Columns found: {", ".join(df.columns.tolist())}')
        return render(request, 'people/import_staff.html', {})

    # process rows
    results       = []
    created_count = 0
    updated_count = 0
    error_count   = 0
    skipped_count = 0

    for idx, row in df.iterrows():
        row_num     = idx + 2
        staff_id    = _clean(row.get(id_column, ''))
        fullname    = _clean(row.get('name', ''))
        designation = _clean(row.get('designation', '') or row.get('role', '') or row.get('subject', ''))

        if not staff_id:
            results.append({'row': row_num, 'staff_id': '-', 'name': fullname,
                            'status': 'skipped', 'message': f'Missing {id_column}'})
            skipped_count += 1
            continue

        if not fullname:
            results.append({'row': row_num, 'staff_id': staff_id, 'name': '-',
                            'status': 'skipped', 'message': 'Missing name'})
            skipped_count += 1
            continue

        try:
            member, created = StaffMember.objects.update_or_create(
                staff_id=staff_id,
                defaults={
                    'full_name'  : fullname,
                    'staff_type' : staff_type,
                    'designation': designation,
                    'is_active'  : True,
                }
            )

            if created:
                created_count += 1
                status  = 'created'
                message = f'Added as {member.get_staff_type_display()}'
            else:
                updated_count += 1
                status  = 'updated'
                message = 'Record updated'

            results.append({
                'row'    : row_num,
                'staff_id': staff_id,
                'name'   : fullname,
                'status' : status,
                'message': message,
            })

        except Exception as e:
            error_count += 1
            results.append({
                'row'    : row_num,
                'staff_id': staff_id,
                'name'   : fullname,
                'status' : 'error',
                'message': str(e),
            })

    return render(request, 'people/import_staff.html', {
        'results'       : results,
        'staff_type'    : staff_type,
        'created_count' : created_count,
        'updated_count' : updated_count,
        'error_count'   : error_count,
        'skipped_count' : skipped_count,
        'total'         : len(results),
    })