web: DJANGO_SETTINGS_MODULE=hotel_management.settings_production gunicorn hotel_management.wsgi:application --bind 0.0.0.0:$PORT --workers 2
release: DJANGO_SETTINGS_MODULE=hotel_management.settings_production python manage.py migrate --no-input && DJANGO_SETTINGS_MODULE=hotel_management.settings_production python manage.py collectstatic --no-input
