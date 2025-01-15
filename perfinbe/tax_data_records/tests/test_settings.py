# tax_data_records/tests/test_settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'personal_finance_portfolio',
    'tax_data_records',
]

SECRET_KEY = 'test-key-not-for-production'

USE_TZ = True