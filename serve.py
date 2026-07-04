import os
from waitress import serve
from whitenoise import WhiteNoise
from SchoolAttendance.wsgi import application

# 1. Ensure the environment knows where settings are
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SchoolAttendance.settings')

# 2. Point to the folder where collectstatic just put your files
# This matches: C:\SchoolAttendance\staticfiles
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 3. Wrap the Django app with WhiteNoise
# This allows Waitress to serve the static files
application = WhiteNoise(application, root=STATIC_ROOT)

if __name__ == '__main__':
    print("SchoolAttendance is running!")
    print("Static files served from: " + STATIC_ROOT)
    print("Access the site at: http://0.0.0.0:8000")
    
    serve(
        application,
        host='0.0.0.0',
        port=8000,
        threads=8,
    )