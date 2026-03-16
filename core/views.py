from django.shortcuts import render

# Create your views here.
# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta

from .models import AcademicYear, Term, SchoolWeek, NonSchoolDay, SchoolDayConfig, LateThreshold
from .forms import AcademicYearForm, TermForm, NonSchoolDayForm, LateThresholdForm, SchoolDayConfigForm
from accounts.decorators import admin_required, admin_or_principal_required


@login_required
@admin_or_principal_required
def academic_year_list(request):
    years = AcademicYear.objects.all()
    return render(request, 'core/academic_year_list.html', {'years': years})


@login_required
@admin_or_principal_required
def academic_year_create(request):
    form = AcademicYearForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Academic year created.')
        return redirect('core:academic_year_list')
    return render(request, 'core/generic_form.html', {'form': form, 'title': 'Add Academic Year'})


@login_required
@admin_or_principal_required
def term_list(request):
    terms = Term.objects.select_related('academic_year').all()
    return render(request, 'core/term_list.html', {'terms': terms})


@login_required
@admin_or_principal_required
def term_create(request):
    form = TermForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Term created.')
        return redirect('core:term_list')
    return render(request, 'core/generic_form.html', {'form': form, 'title': 'Add Term'})


@login_required
@admin_or_principal_required
def term_edit(request, pk):
    term    = get_object_or_404(Term, pk=pk)
    form    = TermForm(request.POST or None, instance=term)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Term updated.')
        return redirect('core:term_list')
    return render(request, 'core/generic_form.html', {'form': form, 'title': 'Edit Term'})


@login_required
@admin_or_principal_required
def generate_weeks(request, pk):
    """
    Auto-generate SchoolWeek records for a term based on its start/end dates.
    Each week starts on Monday and ends on Sunday (or term end if sooner).
    """
    term = get_object_or_404(Term, pk=pk)

    # delete existing weeks first
    term.weeks.all().delete()

    current     = term.start_date
    # move to the Monday of the start week
    current     = current - timedelta(days=current.weekday())
    week_number = 1

    while current <= term.end_date:
        week_end = min(current + timedelta(days=6), term.end_date)
        SchoolWeek.objects.create(
            term        = term,
            week_number = week_number,
            start_date  = max(current, term.start_date),
            end_date    = week_end,
        )
        current     += timedelta(weeks=1)
        week_number += 1

    messages.success(request, f'{week_number - 1} weeks generated for {term}.')
    return redirect('core:term_list')


@login_required
@admin_required
def non_school_day_list(request):
    days = NonSchoolDay.objects.all()
    return render(request, 'core/non_school_day_list.html', {'days': days})


@login_required
@admin_required
def non_school_day_create(request):
    form = NonSchoolDayForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Non-school day added.')
        return redirect('core:non_school_day_list')
    return render(request, 'core/generic_form.html', {'form': form, 'title': 'Add Non-School Day'})


@login_required
@admin_required
def non_school_day_delete(request, pk):
    day = get_object_or_404(NonSchoolDay, pk=pk)
    if request.method == 'POST':
        day.delete()
        messages.success(request, 'Non-school day removed.')
        return redirect('core:non_school_day_list')
    return render(request, 'core/generic_form.html', {'form': None, 'title': 'Delete Non-School Day', 'object': day})


@login_required
@admin_required
def late_threshold_list(request):
    thresholds = LateThreshold.objects.select_related('applies_to').all()
    return render(request, 'core/late_threshold_list.html', {'thresholds': thresholds})


@login_required
@admin_required
def late_threshold_create(request):
    form = LateThresholdForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Late threshold set.')
        return redirect('core:late_threshold_list')
    return render(request, 'core/generic_form.html', {'form': form, 'title': 'Set Late Threshold'})


@login_required
@admin_required
def late_threshold_edit(request, pk):
    threshold   = get_object_or_404(LateThreshold, pk=pk)
    form        = LateThresholdForm(request.POST or None, instance=threshold)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Late threshold updated.')
        return redirect('core:late_threshold_list')
    return render(request, 'core/generic_form.html', {'form': form, 'title': 'Edit Late Threshold'})


@login_required
@admin_required
def school_day_config_list(request):
    configs = SchoolDayConfig.objects.select_related('stream').all()
    return render(request, 'core/school_day_config_list.html', {'configs': configs})


@login_required
@admin_required
def school_day_config_create(request):
    form = SchoolDayConfigForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'School day config saved.')
        return redirect('core:school_day_config_list')
    return render(request, 'core/generic_form.html', {'form': form, 'title': 'Add School Day Config'})


@login_required
@admin_required
def school_day_config_delete(request, pk):
    config = get_object_or_404(SchoolDayConfig, pk=pk)
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Config removed.')
        return redirect('core:school_day_config_list')
    return render(request, 'core/generic_form.html', {'form': None, 'title': 'Delete Config', 'object': config})