import os

from secret_keys import CSRF_SECRET_KEY, SESSION_KEY
# Set secret keys for CSRF protection
SECRET_KEY = CSRF_SECRET_KEY
CSRF_SESSION_KEY = SESSION_KEY
CSRF_ENABLED = True

DEBUG_MODE = False
# Auto-set debug mode based on App Engine dev environ
if 'SERVER_SOFTWARE' in os.environ and os.environ['SERVER_SOFTWARE'].startswith('Dev'):
    DEBUG = True
    SERVER_NAME = '127.0.0.1'
else:
    SERVER_NAME = 'yourapp.com'

DEBUG = DEBUG_MODE

# Shopify Settings

SHOPIFY_SHARED_SECRET = ''
SHOPIFY_API_KEY = ''
SHOPIFY_APP_SITE = ''

SHOPIFY_TEST_SITE = ''
SHOPIFY_TEST_API_KEY = ''
SHOPIFY_TEST_PASSWORD = ''

