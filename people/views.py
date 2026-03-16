from django.shortcuts import render

# Create your views here.
# people/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Form, Stream, Student, StaffMember
from .forms import FormForm, StreamForm, StudentForm, StaffMemberForm
from accounts.decorators import admin_required, admin_or_principal_required


# --- Forms ---

@login_required
@admin_required
def form_list(request):
    forms = Form.objects.all()
    return render(request, 'people/form_list.html', {'forms': forms})


@login_required
@admin_required
def form_create(request):
    form = FormForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Form added.')
        return redirect('people:form_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Add Form'})


@login_required
@admin_required
def form_edit(request, pk):
    obj     = get_object_or_404(Form, pk=pk)
    form    = FormForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Form updated.')
        return redirect('people:form_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Edit Form'})


# --- Streams ---

@login_required
@admin_required
def stream_list(request):
    streams = Stream.objects.select_related('form').all()
    return render(request, 'people/stream_list.html', {'streams': streams})


@login_required
@admin_required
def stream_create(request):
    form = StreamForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Stream added.')
        return redirect('people:stream_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Add Stream'})


@login_required
@admin_required
def stream_edit(request, pk):
    obj     = get_object_or_404(Stream, pk=pk)
    form    = StreamForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Stream updated.')
        return redirect('people:stream_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Edit Stream'})


# --- Students ---

@login_required
@admin_or_principal_required
def student_list(request):
    selected_stream = request.GET.get('stream', '')
    students        = Student.objects.select_related('stream', 'stream__form').filter(is_active=True)
    if selected_stream:
        students = students.filter(stream_id=selected_stream)
    streams = Stream.objects.select_related('form').all()
    return render(request, 'people/student_list.html', {
        'students'          : students,
        'streams'           : streams,
        'selected_stream'   : selected_stream,
    })


@login_required
@admin_required
def student_create(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Student added.')
        return redirect('people:student_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Add Student'})


@login_required
@admin_or_principal_required
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related('stream', 'stream__form'), pk=pk)
    return render(request, 'people/student_detail.html', {'student': student})


@login_required
@admin_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form    = StudentForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Student updated.')
        return redirect('people:student_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Edit Student'})


@login_required
@admin_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.is_active = False
        student.save()
        messages.success(request, 'Student deactivated.')
        return redirect('people:student_list')
    return render(request, 'confirm_delete.html', {'object': student, 'title': 'Deactivate Student'})


# --- Staff ---

@login_required
@admin_or_principal_required
def staff_list(request):
    staff = StaffMember.objects.filter(is_active=True)
    return render(request, 'people/staff_list.html', {'staff': staff})


@login_required
@admin_required
def staff_create(request):
    form = StaffMemberForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Staff member added.')
        return redirect('people:staff_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Add Staff Member'})


@login_required
@admin_or_principal_required
def staff_detail(request, pk):
    member = get_object_or_404(StaffMember, pk=pk)
    return render(request, 'people/staff_detail.html', {'member': member})


@login_required
@admin_required
def staff_edit(request, pk):
    member  = get_object_or_404(StaffMember, pk=pk)
    form    = StaffMemberForm(request.POST or None, request.FILES or None, instance=member)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Staff member updated.')
        return redirect('people:staff_list')
    return render(request, 'people/generic_form.html', {'form': form, 'title': 'Edit Staff Member'})


@login_required
@admin_required
def staff_delete(request, pk):
    member = get_object_or_404(StaffMember, pk=pk)
    if request.method == 'POST':
        member.is_active = False
        member.save()
        messages.success(request, 'Staff member deactivated.')
        return redirect('people:staff_list')
    return render(request, 'confirm_delete.html', {'object': member, 'title': 'Deactivate Staff Member'})