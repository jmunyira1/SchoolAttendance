# devices/sync.py

import logging
from django.utils import timezone
from django.db import IntegrityError

from .models import Device, PunchLog

logger = logging.getLogger(__name__)


def get_device_users(device: Device) -> dict:
    """
    Connect to a ZKTeco device and retrieve all enrolled users.
    Returns a list of dicts with uid, user_id, name, privilege.
    """
    result = {
        'success'   : False,
        'users'     : [],
        'error'     : None,
    }

    try:
        from zk import ZK
        zk = ZK(
            device.ip_address,
            port=device.port,
            timeout=10,
            password=0,
            force_udp=False,
            ommit_ping=False
        )

        conn = zk.connect()
        conn.disable_device()

        try:
            users = conn.get_users()
        finally:
            conn.enable_device()
            conn.disconnect()

        cleaned_users = []
        for user in users:
            # strip any non-digit characters from user_id
            # some ZKTeco firmware versions return trailing backticks or spaces
            raw_id = str(user.user_id).strip()
            clean_id = ''.join(c for c in raw_id if c.isdigit())
            if not clean_id:
                logger.warning(f'[get_users] Skipping user with unparseable ID: {repr(raw_id)}')
                continue
            cleaned_users.append({
                'uid'       : user.uid,
                'user_id'   : int(clean_id),
                'name'      : user.name.strip(),
                'privilege' : user.privilege,
            })
        result['users'] = cleaned_users
        result['success'] = True
        logger.info(f'[get_users] {device.name}: {len(result["users"])} users retrieved')

    except Exception as e:
        result['error'] = str(e)
        logger.error(f'[get_users] {device.name} failed: {e}')

    return result


def sync_device(device: Device) -> dict:
    """
    Connect to a single ZKTeco device, pull all attendance logs,
    save new PunchLog records, and return a result summary.
    """
    result = {
        'device'            : device.name,
        'success'           : False,
        'new_punches'       : 0,
        'duplicate_punches' : 0,
        'error'             : None,
    }

    try:
        from zk import ZK
        zk = ZK(
            device.ip_address,
            port=device.port,
            timeout=10,
            password=0,
            force_udp=False,
            ommit_ping=False
        )

        conn = zk.connect()
        conn.disable_device()

        try:
            attendances = conn.get_attendance()
        finally:
            conn.enable_device()
            conn.disconnect()

        new_count   = 0
        dupe_count  = 0

        for record in attendances:
            punch_time = record.timestamp


            # clean user_id — strip non-digit chars from firmware quirks
            raw_id   = str(record.user_id).strip()
            clean_id = ''.join(c for c in raw_id if c.isdigit())
            if not clean_id:
                logger.warning(f'[sync] Skipping punch with unparseable user_id: {repr(raw_id)}')
                continue

            try:
                PunchLog.objects.create(
                    device      = device,
                    zk_user_id  = int(clean_id),
                    punch_time  = punch_time,
                )
                new_count += 1

            except IntegrityError:
                dupe_count += 1

        device.last_sync = timezone.now()
        device.save(update_fields=['last_sync'])

        result['success']           = True
        result['new_punches']       = new_count
        result['duplicate_punches'] = dupe_count

        logger.info(f'[sync] {device.name}: {new_count} new, {dupe_count} duplicates')

    except Exception as e:
        result['error'] = str(e)
        logger.error(f'[sync] {device.name} failed: {e}')

    return result


def sync_all_devices() -> list:
    devices = Device.objects.filter(is_active=True)
    return [sync_device(device) for device in devices]


def background_sync_and_process() -> dict:
    sync_results    = sync_all_devices()
    process_result  = process_punch_logs()
    absent_result   = fill_absent_records()
    return {
        'sync_results'  : sync_results,
        'process_result': process_result,
        'absent_result' : absent_result,
    }



def process_punch_logs() -> dict:
    from attendance.models import AttendanceRecord
    from people.models import Student, StaffMember
    from core.models import Term, SchoolWeek, LateThreshold, NonSchoolDay

    result = {
        'processed' : 0,
        'skipped'   : 0,
        'errors'    : [],
    }

    unprocessed = PunchLog.objects.filter(is_processed=False).order_by('punch_time')

    if not unprocessed.exists():
        return result

    groups = {}
    for punch in unprocessed:
        date = punch.punch_time.date()
        key  = (punch.zk_user_id, date)
        if key not in groups:
            groups[key] = []
        groups[key].append(punch)

    try:
        current_term = Term.objects.get(is_current=True)
        current_year = current_term.academic_year
    except Term.DoesNotExist:
        result['errors'].append('No current term set.')
        return result

    non_school_dates = set(NonSchoolDay.objects.values_list('date', flat=True))

    for (zk_user_id, date), punches in groups.items():

        if date in non_school_dates:
            PunchLog.objects.filter(
                zk_user_id=zk_user_id,
                punch_time__date=date,
                is_processed=False
            ).update(is_processed=True)
            result['skipped'] += 1
            continue

        student         = None
        staff_member    = None
        person_type     = None

        try:
            student     = Student.objects.get(zk_user_id=zk_user_id, is_active=True)
            person_type = AttendanceRecord.STUDENT
        except Student.DoesNotExist:
            try:
                staff_member = StaffMember.objects.get(zk_user_id=zk_user_id, is_active=True)
                person_type  = AttendanceRecord.STAFF
            except StaffMember.DoesNotExist:
                result['errors'].append(f'ZK user ID {zk_user_id} not matched to any person.')
                result['skipped'] += 1
                continue

        times       = sorted([p.punch_time for p in punches])
        check_in    = times[0].time()
        check_out   = times[-1].time() if len(times) > 1 else None

        school_week = SchoolWeek.objects.filter(
            term            = current_term,
            start_date__lte = date,
            end_date__gte   = date
        ).first()

        is_saturday = date.weekday() == 5
        day_type    = LateThreshold.SATURDAY if is_saturday else LateThreshold.WEEKDAY
        stream      = student.stream if student else None

        threshold = (
            LateThreshold.objects.filter(day_type=day_type, applies_to=stream).first()
            or LateThreshold.objects.filter(day_type=day_type, applies_to=None).first()
        )

        status = (
            AttendanceRecord.LATE
            if (threshold and check_in > threshold.cutoff_time)
            else AttendanceRecord.PRESENT
        )

        try:
            AttendanceRecord.objects.update_or_create(
                **({'student': student} if student else {'staff_member': staff_member}),
                date=date,
                defaults={
                    'person_type'   : person_type,
                    'academic_year' : current_year,
                    'term'          : current_term,
                    'school_week'   : school_week,
                    'check_in'      : check_in,
                    'check_out'     : check_out,
                    'status'        : status,
                }
            )

            PunchLog.objects.filter(
                zk_user_id      = zk_user_id,
                punch_time__date = date,
                is_processed    = False
            ).update(is_processed=True)

            result['processed'] += 1

        except Exception as e:
            result['errors'].append(f'ZK#{zk_user_id} {date}: {str(e)}')
            result['skipped'] += 1

    return result


def backup_fingerprints(device: Device) -> dict:
    """
    Pull all fingerprint templates from a ZKTeco device
    and save them to the FingerprintTemplate table.
    Existing templates for the same zk_user_id + finger_id are overwritten.
    """
    from .models import FingerprintTemplate

    result = {
        'success'  : False,
        'saved'    : 0,
        'skipped'  : 0,
        'error'    : None,
    }

    try:
        from zk import ZK
        zk   = ZK(device.ip_address, port=device.port, timeout=15,
                  password=0, force_udp=False, ommit_ping=False)
        conn = zk.connect()
        conn.disable_device()

        try:
            templates = conn.get_templates()
        finally:
            conn.enable_device()
            conn.disconnect()

        for tmpl in templates:
            raw_id   = str(tmpl.uid).strip()
            clean_id = ''.join(c for c in raw_id if c.isdigit())
            if not clean_id:
                result['skipped'] += 1
                continue

            try:
                FingerprintTemplate.objects.update_or_create(
                    zk_user_id = int(clean_id),
                    finger_id  = int(tmpl.fid),
                    defaults   = {
                        'template'      : bytes(tmpl.template),
                        'quality'       : getattr(tmpl, 'quality', 0) or 0,
                        'backed_up_from': device,
                    }
                )
                result['saved'] += 1
            except Exception as e:
                logger.warning(f'[backup_fp] ZK#{clean_id} finger {tmpl.fid}: {e}')
                result['skipped'] += 1

        result['success'] = True
        logger.info(f'[backup_fp] {device.name}: {result["saved"]} templates saved')

    except Exception as e:
        result['error'] = str(e)
        logger.error(f'[backup_fp] {device.name} failed: {e}')

    return result


def push_fingerprints(device: Device, zk_user_ids: list = None) -> dict:
    """
    Push stored fingerprint templates to a ZKTeco device.
    If zk_user_ids is provided, only push templates for those IDs.
    Otherwise push all stored templates.
    """
    from .models import FingerprintTemplate
    from zk.user import User
    from zk.finger import Finger

    result = {
        'success'  : False,
        'pushed'   : 0,
        'skipped'  : 0,
        'error'    : None,
    }

    try:
        from zk import ZK
        zk   = ZK(device.ip_address, port=device.port, timeout=15,
                  password=0, force_udp=False, ommit_ping=False)
        conn = zk.connect()
        conn.disable_device()

        try:
            # get existing users on the device so we can match uid
            device_users = {int(u.user_id): u for u in conn.get_users()
                           if str(u.user_id).strip().isdigit()}

            templates_qs = FingerprintTemplate.objects.all()
            if zk_user_ids:
                templates_qs = templates_qs.filter(zk_user_id__in=zk_user_ids)

            # group by user
            by_user = {}
            for tmpl in templates_qs:
                uid = tmpl.zk_user_id
                if uid not in by_user:
                    by_user[uid] = []
                by_user[uid].append(tmpl)

            for zk_uid, tmpls in by_user.items():
                if zk_uid not in device_users:
                    logger.warning(f'[push_fp] ZK#{zk_uid} not enrolled on {device.name} — skipping')
                    result['skipped'] += len(tmpls)
                    continue

                fingers = []
                for tmpl in tmpls:
                    try:
                        finger = Finger(
                            fid      = tmpl.finger_id,
                            template = bytes(tmpl.template),
                            quality  = tmpl.quality,
                        )
                        fingers.append(finger)
                    except Exception as e:
                        logger.warning(f'[push_fp] ZK#{zk_uid} finger {tmpl.finger_id}: {e}')
                        result['skipped'] += 1

                if fingers:
                    try:
                        conn.save_user_template(device_users[zk_uid], fingers)
                        result['pushed'] += len(fingers)
                    except Exception as e:
                        logger.warning(f'[push_fp] ZK#{zk_uid} save failed: {e}')
                        result['skipped'] += len(fingers)

        finally:
            conn.enable_device()
            conn.disconnect()

        result['success'] = True
        logger.info(f'[push_fp] {device.name}: {result["pushed"]} templates pushed')

    except Exception as e:
        result['error'] = str(e)
        logger.error(f'[push_fp] {device.name} failed: {e}')

    return result
def fill_absent_records():
    """
    For every past school day in the current term, create ABSENT
    AttendanceRecords for any active enrolled person who has no record.
    Runs up to yesterday — today may still have pending punches.
    Uses bulk_create for performance.
    """
    from datetime import date, timedelta
    from attendance.models import AttendanceRecord
    from people.models import Student, StaffMember
    from core.models import Term, SchoolWeek, NonSchoolDay, SchoolDayConfig

    result = {'created': 0, 'errors': []}

    try:
        current_term = Term.objects.get(is_current=True)
        current_year = current_term.academic_year
    except Term.DoesNotExist:
        return result

    today      = date.today()
    yesterday  = today - timedelta(days=1)
    non_school = set(NonSchoolDay.objects.values_list('date', flat=True))

    # school-wide active days — fallback Mon-Fri if none configured
    global_days = set(
        SchoolDayConfig.objects.filter(stream__isnull=True)
        .values_list('day_of_week', flat=True)
    )
    if not global_days:
        global_days = {0, 1, 2, 3, 4}

    # build list of past school days in term up to yesterday
    school_days = []
    cursor = current_term.start_date
    while cursor <= min(yesterday, current_term.end_date):
        if cursor not in non_school and cursor.weekday() in global_days:
            school_days.append(cursor)
        cursor += timedelta(days=1)

    if not school_days:
        return result

    # school week lookup map
    week_map = {}
    for week in current_term.weeks.all():
        d = week.start_date
        while d <= week.end_date:
            week_map[d] = week
            d += timedelta(days=1)

    # enrolled people
    students = list(Student.objects.filter(is_active=True, zk_user_id__isnull=False))
    staff    = list(StaffMember.objects.filter(is_active=True, zk_user_id__isnull=False))

    if not students and not staff:
        return result

    # get ALL existing attendance records for this term in one query
    existing_student = set(
        AttendanceRecord.objects.filter(
            term=current_term,
            person_type=AttendanceRecord.STUDENT
        ).values_list('student_id', 'date')
    )
    existing_staff = set(
        AttendanceRecord.objects.filter(
            term=current_term,
            person_type=AttendanceRecord.STAFF
        ).values_list('staff_member_id', 'date')
    )

    # build records to create in bulk
    to_create = []

    for school_day in school_days:
        school_week = week_map.get(school_day)

        for student in students:
            if (student.pk, school_day) not in existing_student:
                to_create.append(AttendanceRecord(
                    person_type   = AttendanceRecord.STUDENT,
                    student       = student,
                    date          = school_day,
                    academic_year = current_year,
                    term          = current_term,
                    school_week   = school_week,
                    status        = AttendanceRecord.ABSENT,
                ))

        for member in staff:
            if (member.pk, school_day) not in existing_staff:
                to_create.append(AttendanceRecord(
                    person_type   = AttendanceRecord.STAFF,
                    staff_member  = member,
                    date          = school_day,
                    academic_year = current_year,
                    term          = current_term,
                    school_week   = school_week,
                    status        = AttendanceRecord.ABSENT,
                ))

    # bulk insert in batches of 500
    batch_size = 500
    for i in range(0, len(to_create), batch_size):
        try:
            created = AttendanceRecord.objects.bulk_create(
                to_create[i:i + batch_size],
                ignore_conflicts=True
            )
            result['created'] += len(created)
        except Exception as e:
            result['errors'].append(str(e))

    return result