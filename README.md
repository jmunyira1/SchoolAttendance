---
title: 'School Attendance System'
summary: 'A biometric attendance management system for secondary schools using ZKTeco fingerprint devices.'
description: 'Secondary schools struggle to track attendance accurately across multiple entry points and staff categories. This system connects directly to ZKTeco K40 Pro fingerprint devices over the school LAN, automatically captures every check-in and check-out, and presents the data through a role-based web dashboard. Administrators, principals, and storekeepers each see exactly the information they need without manual data entry.'
tech:
  - 'Python 3.13'
  - 'Django 6.0.3'
  - 'MariaDB'
  - 'pyzk'
  - 'pandas'
  - 'openpyxl'
  - 'Jinja2 / Django Templates'
  - 'Bootstrap 5'
  - 'Remix Icons'
  - 'jQuery'
  - 'JavaScript'
  - 'HTML & CSS'
  - 'python-decouple'
  - 'Pillow'
live_url: 'https://your-live-url.com'
github_url: 'https://github.com/jmunyira1/SchoolAttendance'
featured: true
active: true
---

School Attendance System

A comprehensive biometric attendance management system built for secondary schools. It connects directly to ZKTeco K40 Pro fingerprint devices installed at school gates, automatically recording every arrival and departure for students and staff without any manual intervention. Designed for schools with multiple entry points, mixed grade structures, and diverse staff categories.

The system is entirely web-based and works on any device connected to the school's local network — no software installation required for administrators, teachers, or management.

✨ Key Features

Biometric Device Integration
The system connects in real-time to multiple ZKTeco K40 Pro fingerprint devices across the school premises. Every time a student or staff member places their finger on any device, the punch is automatically captured, processed, and reflected in the dashboard the next time any attendance page is loaded. No manual syncing or USB transfers are needed.

Fingerprint Backup and Cross-Device Sync
Administrators can back up all enrolled fingerprints from any device into the system's database with a single click. These stored fingerprints can then be pushed to any other device on the network, meaning a person enrolled at the main gate is automatically recognised at the staff entrance or any other gate — without anyone needing to re-enrol physically.

User Mapping and Enrolment Management
When users are enrolled on a ZKTeco device, the system retrieves their records and presents a mapping interface. Administrators assign each fingerprint ID to the correct student or staff member in the system, linking biometric identity to school records. This mapping only needs to be done once per person.

Student Import from Excel
Administrators can upload the school's existing student register directly from an Excel or CSV file. They select the form or grade level, upload the file, and the system automatically creates or updates each student record — matching by admission number so re-uploads only update what has changed, never duplicate.

Role-Based Access
Different users see different parts of the system based on their role. The principal and deputy principal have full visibility across all reports and can configure term dates. The admin manages devices, users, and system settings. The storekeeper sees only a daily headcount per class for catering purposes. All access is enforced automatically — no user can view pages outside their role.

Student Attendance Reports
The daily student register shows every student's check-in time, check-out time, and status — present, late, absent, or excused — filterable by date, stream, and student type. The absentee report shows at a glance who did not show up on any given day. The term summary gives a full attendance percentage for every student across the current term, with colour-coded indicators flagging anyone below acceptable thresholds.

Staff Attendance Reports
Staff attendance is tracked with the same biometric precision as students. The daily staff register shows every staff member's arrival and departure, and highlights enrolled staff with no punch record for the day. The term summary breaks down attendance by individual staff member with percentage indicators. The late arrivals report covers any date range and ranks staff by how frequently they have arrived after the configured threshold time.

Configurable Academic Calendar
Principals and deputy principals define the school's academic structure directly in the system — academic years, terms with start and end dates, and school weeks which are generated automatically. Public holidays and ad-hoc school closure days are marked so they are excluded from attendance calculations. Late arrival thresholds can be set school-wide or per stream, and active school days can be configured per class to accommodate Saturday timetables.

Attendance Overrides and Audit Trail
Any attendance record can be manually corrected by an authorised user — for example to mark a student as excused after a medical certificate is received. Every change is logged with the name of the person who made it, the timestamp, and the reason given, creating a complete and tamper-evident audit trail.

Storekeeper Headcount View
The storekeeper has a dedicated, simplified view showing today's student headcount per form and stream alongside the total number of staff present. This gives the catering team exactly what they need to plan meals without exposing any personal attendance details.

Flexible Stream and Class Structure
The system supports any combination of forms, grades, and named streams. Schools can configure Form 3 East, Form 4 Beta, Grade 10 Champion, or any naming convention they use. Each stream can have its own school day schedule and late arrival threshold, accommodating schools where different classes operate on different timetables.