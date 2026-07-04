# devices/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Device, PunchLog, FingerprintTemplate
from .forms import DeviceForm
from .sync import (sync_device, sync_all_devices,
                   get_device_users, backup_fingerprints, push_fingerprints)
from accounts.decorators import admin_required
from people.models import Student, StaffMember


def _auto_match(zk_user_id):
    """
    Try to resolve a ZK user ID to a Student or StaffMember automatically.

    Enrollment convention:
      - Students      → ZK user ID = admission number (integer)
      - Teaching staff → ZK user ID = TSC number (integer)
      - Non-teaching  → ZK user ID = National ID (integer)

    All three are stored as strings in staff_id / admission_number,
    so we compare str(zk_user_id) against them.
    """
    uid_str = str(zk_user_id)

    # try student first
    try:
        student = Student.objects.get(admission_number=uid_str, is_active=True)
        return 'student', student
    except Student.DoesNotExist:
        pass

    # try staff (TSC no. or National ID stored in staff_id)
    try:
        member = StaffMember.objects.get(staff_id=uid_str, is_active=True)
        return 'staff', member
    except StaffMember.DoesNotExist:
        pass

    return None, None


@login_required
@admin_required
def device_list(request):
    sync_results = sync_all_devices()
    devices      = Device.objects.all()
    fp_count     = FingerprintTemplate.objects.count()
    return render(request, 'devices/device_list.html', {
        'devices'     : devices,
        'sync_results': sync_results,
        'fp_count'    : fp_count,
    })


@login_required
@admin_required
def device_create(request):
    form = DeviceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Device added successfully.')
        return redirect('devices:device_list')
    return render(request, 'devices/device_form.html', {'form': form, 'title': 'Add Device'})


@login_required
@admin_required
def device_edit(request, pk):
    device = get_object_or_404(Device, pk=pk)
    form   = DeviceForm(request.POST or None, instance=device)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Device updated.')
        return redirect('devices:device_list')
    return render(request, 'devices/device_form.html', {'form': form, 'title': 'Edit Device'})


@login_required
@admin_required
def device_delete(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == 'POST':
        device.delete()
        messages.success(request, 'Device deleted.')
        return redirect('devices:device_list')
    return render(request, 'confirm_delete.html', {
        'object': device, 'title': 'Delete Device'
    })


@login_required
@admin_required
def device_sync(request, pk):
    device = get_object_or_404(Device, pk=pk)
    result = sync_device(device)
    if result['success']:
        messages.success(request, f"Synced {device.name}: {result['new_punches']} new punches.")
    else:
        messages.error(request, f"Sync failed for {device.name}: {result['error']}")
    return redirect('devices:device_list')


@login_required
@admin_required
def sync_all(request):
    results = sync_all_devices()
    total   = sum(r['new_punches'] for r in results)
    messages.success(request, f'Sync complete. {total} new punches across all devices.')
    return redirect('devices:device_list')


@login_required
@admin_required
def punch_log_list(request):
    logs = PunchLog.objects.select_related('device').order_by('-punch_time')[:500]
    return render(request, 'devices/punch_log_list.html', {'logs': logs})


@login_required
@admin_required
def import_users(request, pk):
    """
    Pull enrolled users from the device.
    Auto-match each ZK user ID to a Student or StaffMember using
    admission number / TSC number / National ID.
    Show results and allow manual override for unmatched users.
    """
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        # handle manual mapping form submission
        return map_user(request, pk)

    result = get_device_users(device)

    if not result['success']:
        messages.error(request, f"Could not retrieve users from {device.name}: {result['error']}")
        return redirect('devices:device_list')

    zk_users     = result['users']
    auto_mapped  = 0
    unmatched    = []

    for user in zk_users:
        uid             = user['user_id']
        person_type, person = _auto_match(uid)

        if person:
            # auto-save the zk_user_id if not already set
            if person_type == 'student':
                if person.zk_user_id != uid:
                    person.zk_user_id = uid
                    person.save(update_fields=['zk_user_id'])
                user['matched_to']   = person.full_name
                user['matched_id']   = str(person.admission_number)
                user['matched_type'] = 'Student'
                user['matched_pk']   = person.pk
                auto_mapped += 1
            else:
                if person.zk_user_id != uid:
                    person.zk_user_id = uid
                    person.save(update_fields=['zk_user_id'])
                user['matched_to']   = person.full_name
                user['matched_id']   = person.staff_id
                user['matched_type'] = person.get_staff_type_display()
                user['matched_pk']   = person.pk
                auto_mapped += 1
        else:
            user['matched_to']   = None
            user['matched_type'] = None
            user['matched_pk']   = None
            unmatched.append(user)

    # for manual mapping of unmatched users
    students = Student.objects.filter(is_active=True).select_related('stream', 'stream__form')
    staff    = StaffMember.objects.filter(is_active=True)

    if auto_mapped:
        messages.success(request,
                         f'{auto_mapped} user(s) automatically matched and saved. '
                         f'{len(unmatched)} unmatched.')

    return render(request, 'devices/import_users.html', {
        'device'      : device,
        'zk_users'    : zk_users,
        'unmatched'   : unmatched,
        'auto_mapped' : auto_mapped,
        'students'    : students,
        'staff'       : staff,
    })


@login_required
@admin_required
def map_user(request, pk):
    """Manual mapping for ZK users that could not be auto-matched."""
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        zk_user_id  = request.POST.get('zk_user_id')
        person_type = request.POST.get('person_type')
        person_id   = request.POST.get('person_id')

        if not all([zk_user_id, person_type, person_id]):
            messages.error(request, 'Invalid mapping data.')
            return redirect('devices:import_users', pk=pk)

        try:
            zk_user_id = int(zk_user_id)
            # clear any existing mapping for this zk_user_id
            Student.objects.filter(zk_user_id=zk_user_id).update(zk_user_id=None)
            StaffMember.objects.filter(zk_user_id=zk_user_id).update(zk_user_id=None)

            if person_type == 'student':
                obj = get_object_or_404(Student, pk=person_id)
                obj.zk_user_id = zk_user_id
                obj.save(update_fields=['zk_user_id'])
                messages.success(request,
                                 f'ZK ID {zk_user_id} manually mapped to student {obj.full_name}.')
            elif person_type == 'staff':
                obj = get_object_or_404(StaffMember, pk=person_id)
                obj.zk_user_id = zk_user_id
                obj.save(update_fields=['zk_user_id'])
                messages.success(request,
                                 f'ZK ID {zk_user_id} manually mapped to {obj.full_name}.')

        except Exception as e:
            messages.error(request, f'Mapping failed: {e}')

    return redirect('devices:import_users', pk=pk)


@login_required
@admin_required
def backup_fingerprints_view(request, pk):
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        result = backup_fingerprints(device)
        if result['success']:
            messages.success(request,
                             f'Backup complete from {device.name}: '
                             f'{result["saved"]} templates saved, {result["skipped"]} skipped.')
        else:
            messages.error(request, f'Backup failed: {result["error"]}')
        return redirect('devices:fingerprint_list')

    existing_count = FingerprintTemplate.objects.filter(backed_up_from=device).count()
    return render(request, 'devices/backup_fingerprints.html', {
        'device'        : device,
        'existing_count': existing_count,
    })


@login_required
@admin_required
def push_fingerprints_view(request, pk):
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('zk_user_ids')
        zk_ids = [int(i) for i in selected_ids if i.isdigit()] if selected_ids else None

        result = push_fingerprints(device, zk_user_ids=zk_ids)
        if result['success']:
            messages.success(request,
                             f'Push complete to {device.name}: '
                             f'{result["pushed"]} templates pushed, {result["skipped"]} skipped.')
        else:
            messages.error(request, f'Push failed: {result["error"]}')
        return redirect('devices:fingerprint_list')

    templates = FingerprintTemplate.objects.all().order_by('zk_user_id', 'finger_id')
    student_map = {str(s.zk_user_id): s for s in Student.objects.filter(zk_user_id__isnull=False)}
    staff_map   = {str(s.zk_user_id): s for s in StaffMember.objects.filter(zk_user_id__isnull=False)}

    grouped = {}
    for tmpl in templates:
        uid = tmpl.zk_user_id
        if uid not in grouped:
            person = student_map.get(str(uid)) or staff_map.get(str(uid))
            grouped[uid] = {'uid': uid, 'person': person, 'fingers': []}
        grouped[uid]['fingers'].append(tmpl.finger_id)

    return render(request, 'devices/push_fingerprints.html', {
        'device' : device,
        'grouped': grouped.values(),
        'total'  : templates.count(),
    })


@login_required
@admin_required
def fingerprint_list(request):
    templates   = FingerprintTemplate.objects.select_related('backed_up_from').order_by('zk_user_id', 'finger_id')
    devices     = Device.objects.filter(is_active=True)
    student_map = {str(s.zk_user_id): s for s in Student.objects.filter(zk_user_id__isnull=False)}
    staff_map   = {str(s.zk_user_id): s for s in StaffMember.objects.filter(zk_user_id__isnull=False)}

    grouped = {}
    for tmpl in templates:
        uid = tmpl.zk_user_id
        if uid not in grouped:
            person = student_map.get(str(uid)) or staff_map.get(str(uid))
            grouped[uid] = {
                'uid'    : uid,
                'person' : person,
                'fingers': [],
                'source' : tmpl.backed_up_from,
            }
        grouped[uid]['fingers'].append(tmpl.finger_id)

    return render(request, 'devices/fingerprint_list.html', {
        'grouped'         : grouped.values(),
        'total_templates' : templates.count(),
        'total_people'    : len(grouped),
        'devices'         : devices,
    })