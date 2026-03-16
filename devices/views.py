# devices/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Device, PunchLog, FingerprintTemplate
from .forms import DeviceForm
from .sync import (sync_device, sync_all_devices, sync_and_process,
                   get_device_users, backup_fingerprints, push_fingerprints)
from accounts.decorators import admin_required
from people.models import Student, StaffMember


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
    return render(request, 'devices/confirm_delete.html', {
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
    device = get_object_or_404(Device, pk=pk)
    result = get_device_users(device)

    if not result['success']:
        messages.error(request, f"Could not retrieve users: {result['error']}")
        return redirect('devices:device_list')

    zk_users        = result['users']
    all_student_ids = set(Student.objects.filter(zk_user_id__isnull=False).values_list('zk_user_id', flat=True))
    all_staff_ids   = set(StaffMember.objects.filter(zk_user_id__isnull=False).values_list('zk_user_id', flat=True))

    for user in zk_users:
        uid = user['user_id']
        if uid in all_student_ids:
            try:
                user['mapped_to']   = str(Student.objects.get(zk_user_id=uid))
                user['mapped_type'] = 'student'
            except Student.DoesNotExist:
                user['mapped_to'] = user['mapped_type'] = None
        elif uid in all_staff_ids:
            try:
                user['mapped_to']   = str(StaffMember.objects.get(zk_user_id=uid))
                user['mapped_type'] = 'staff'
            except StaffMember.DoesNotExist:
                user['mapped_to'] = user['mapped_type'] = None
        else:
            user['mapped_to'] = user['mapped_type'] = None

    students = Student.objects.filter(is_active=True).select_related('stream', 'stream__form')
    staff    = StaffMember.objects.filter(is_active=True)

    return render(request, 'devices/import_users.html', {
        'device'  : device,
        'zk_users': zk_users,
        'students': students,
        'staff'   : staff,
    })


@login_required
@admin_required
def map_user(request, pk):
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
            Student.objects.filter(zk_user_id=zk_user_id).update(zk_user_id=None)
            StaffMember.objects.filter(zk_user_id=zk_user_id).update(zk_user_id=None)

            if person_type == 'student':
                obj = get_object_or_404(Student, pk=person_id)
                obj.zk_user_id = zk_user_id
                obj.save(update_fields=['zk_user_id'])
                messages.success(request, f'ZK ID {zk_user_id} mapped to student {obj.full_name}.')
            elif person_type == 'staff':
                obj = get_object_or_404(StaffMember, pk=person_id)
                obj.zk_user_id = zk_user_id
                obj.save(update_fields=['zk_user_id'])
                messages.success(request, f'ZK ID {zk_user_id} mapped to staff {obj.full_name}.')

        except Exception as e:
            messages.error(request, f'Mapping failed: {e}')

    return redirect('devices:import_users', pk=pk)


@login_required
@admin_required
def backup_fingerprints_view(request, pk):
    """Pull all fingerprint templates from device and store in database."""
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

    # GET — show confirmation page
    existing_count = FingerprintTemplate.objects.filter(backed_up_from=device).count()
    return render(request, 'devices/backup_fingerprints.html', {
        'device'        : device,
        'existing_count': existing_count,
    })


@login_required
@admin_required
def push_fingerprints_view(request, pk):
    """Push stored fingerprint templates to a device."""
    device = get_object_or_404(Device, pk=pk)

    if request.method == 'POST':
        # optional: push only selected zk_user_ids
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

    # GET — show available templates grouped by person
    templates = FingerprintTemplate.objects.all().order_by('zk_user_id', 'finger_id')

    # resolve person names
    student_map = {s.zk_user_id: s for s in Student.objects.filter(zk_user_id__isnull=False)}
    staff_map   = {s.zk_user_id: s for s in StaffMember.objects.filter(zk_user_id__isnull=False)}

    grouped = {}
    for tmpl in templates:
        uid = tmpl.zk_user_id
        if uid not in grouped:
            person = student_map.get(uid) or staff_map.get(uid)
            grouped[uid] = {
                'uid'       : uid,
                'person'    : person,
                'fingers'   : [],
            }
        grouped[uid]['fingers'].append(tmpl.finger_id)

    return render(request, 'devices/push_fingerprints.html', {
        'device' : device,
        'grouped': grouped.values(),
        'total'  : templates.count(),
    })


@login_required
@admin_required
def fingerprint_list(request):
    """Overview of all stored fingerprint templates."""
    templates = FingerprintTemplate.objects.select_related('backed_up_from').order_by('zk_user_id', 'finger_id')
    devices   = Device.objects.filter(is_active=True)

    student_map = {s.zk_user_id: s for s in Student.objects.filter(zk_user_id__isnull=False)}
    staff_map   = {s.zk_user_id: s for s in StaffMember.objects.filter(zk_user_id__isnull=False)}

    grouped = {}
    for tmpl in templates:
        uid = tmpl.zk_user_id
        if uid not in grouped:
            person = student_map.get(uid) or staff_map.get(uid)
            grouped[uid] = {
                'uid'    : uid,
                'person' : person,
                'fingers': [],
                'source' : tmpl.backed_up_from,
            }
        grouped[uid]['fingers'].append(tmpl.finger_id)

    return render(request, 'devices/fingerprint_list.html', {
        'grouped'       : grouped.values(),
        'total_templates': templates.count(),
        'total_people'  : len(grouped),
        'devices'       : devices,
    })