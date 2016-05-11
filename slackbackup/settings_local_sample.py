import os
DOMAIN = "http://localhost:8000"
SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID', '...')
SLACK_CLIENT_SECRET =  os.getenv('SLACK_CLIENT_SECRET', '...')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'