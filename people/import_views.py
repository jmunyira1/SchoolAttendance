# people/import_views.py

import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Form, Stream, Student
from accounts.decorators import admin_required


def _clean(value):
    if value is None:
        return ''
    s = str(value).strip()
    return '' if s.lower() in ('nan', 'none', '') else s


def _parse_gender(value):
    v = _clean(value).lower()
    if v in ('m', 'male', 'boy'):
        return 'male'
    if v in ('f', 'female', 'girl'):
        return 'female'
    if v:
        return 'other'
    return ''


def _resolve_stream(selected_form, stream_raw, stream_cache):
    key = (selected_form.pk, stream_raw.strip().lower())
    if key in stream_cache:
        return stream_cache[key]

    # try existing first
    stream = Stream.objects.filter(
        form=selected_form,
        name__iexact=stream_raw.strip()
    ).first()

    # not found — create it automatically
    if not stream:
        stream = Stream.objects.create(
            form=selected_form,
            name=stream_raw.strip(),
        )

    stream_cache[key] = stream
    return stream

@login_required
@admin_required
def import_students(request):
    # NOTE: context key is 'school_forms' not 'forms' to avoid
    # conflict with Django's built-in 'form' template variable
    school_forms = Form.objects.all().order_by('order', 'name')

    if request.method == 'GET':
        return render(request, 'people/import_students.html', {
            'school_forms': school_forms,
        })

    # --- POST ---
    form_id       = request.POST.get('form')
    uploaded_file = request.FILES.get('excel_file')

    if not form_id:
        messages.error(request, 'Please select a form before uploading.')
        return render(request, 'people/import_students.html', {
            'school_forms': school_forms,
        })

    selected_form = get_object_or_404(Form, pk=form_id)

    if not uploaded_file:
        messages.error(request, 'Please select a file to upload.')
        return render(request, 'people/import_students.html', {
            'school_forms': school_forms,
        })

    fname = uploaded_file.name.lower()
    if not (fname.endswith('.xlsx') or fname.endswith('.xls') or fname.endswith('.csv')):
        messages.error(request, 'Invalid file type. Please upload .xlsx, .xls or .csv.')
        return render(request, 'people/import_students.html', {
            'school_forms': school_forms,
        })

    # read file
    try:
        if fname.endswith('.csv'):
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)
    except Exception as e:
        messages.error(request, f'Could not read file: {e}')
        return render(request, 'people/import_students.html', {
            'school_forms': school_forms,
        })

    # normalise column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # check required columns
    required = ['admission number', 'name', 'stream']
    missing  = [c for c in required if c not in df.columns]
    if missing:
        messages.error(request,
            f'Missing required columns: {", ".join(missing)}. '
            f'Columns found: {", ".join(df.columns.tolist())}')
        return render(request, 'people/import_students.html', {
            'school_forms': school_forms,
        })

    # streams available under selected form — used in error messages
    available_streams = list(
        Stream.objects.filter(form=selected_form).values_list('name', flat=True)
    )

    # process rows
    results       = []
    stream_cache  = {}
    created_count = 0
    updated_count = 0
    error_count   = 0
    skipped_count = 0

    for idx, row in df.iterrows():
        row_num    = idx + 2
        adm        = _clean(row.get('admission number', ''))
        fullname   = _clean(row.get('name', ''))
        stream_raw = _clean(row.get('stream', ''))
        gender     = _parse_gender(row.get('gender', ''))

        if not adm:
            results.append({'row': row_num, 'adm': '-', 'name': fullname,
                            'stream': stream_raw, 'status': 'skipped',
                            'message': 'Missing admission number'})
            skipped_count += 1
            continue

        if not fullname:
            results.append({'row': row_num, 'adm': adm, 'name': '-',
                            'stream': stream_raw, 'status': 'skipped',
                            'message': 'Missing name'})
            skipped_count += 1
            continue

        if not stream_raw:
            results.append({'row': row_num, 'adm': adm, 'name': fullname,
                            'stream': '-', 'status': 'skipped',
                            'message': 'Missing stream value in row'})
            skipped_count += 1
            continue

        stream = _resolve_stream(selected_form, stream_raw, stream_cache)
        if not stream:
            results.append({'row': row_num, 'adm': adm, 'name': fullname,
                            'stream': stream_raw, 'status': 'error',
                            'message': (
                                f'Stream "{stream_raw}" not found under {selected_form}. '
                                f'Available: {", ".join(available_streams) or "none configured"}'
                            )})
            error_count += 1
            continue

        try:
            student, created = Student.objects.update_or_create(
                admission_number=adm,
                defaults={
                    'full_name' : fullname,
                    'stream'    : stream,
                    'gender'    : gender,
                    'is_active' : True,
                }
            )

            if created:
                created_count += 1
                status  = 'created'
                message = f'Added to {stream.full_name}'
            else:
                updated_count += 1
                status  = 'updated'
                message = f'Updated — stream: {stream.full_name}'

            results.append({
                'row'    : row_num,
                'adm'    : adm,
                'name'   : fullname,
                'stream' : stream.full_name,
                'status' : status,
                'message': message,
            })

        except Exception as e:
            error_count += 1
            results.append({
                'row'    : row_num,
                'adm'    : adm,
                'name'   : fullname,
                'stream' : stream_raw,
                'status' : 'error',
                'message': str(e),
            })

    return render(request, 'people/import_students.html', {
        'school_forms'  : school_forms,
        'results'       : results,
        'selected_form' : selected_form,
        'created_count' : created_count,
        'updated_count' : updated_count,
        'error_count'   : error_count,
        'skipped_count' : skipped_count,
        'total'         : len(results),
    })