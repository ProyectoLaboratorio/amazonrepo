from django.core.exceptions import ImproperlyConfigured
import json
import os

with open(os.path.join('secrets.json')) as secrets_file:
    secrets = json.load(secrets_file)

def get_secret(setting, secrets=secrets):
    """Get secret setting or fail with ImproperlyConfigured"""
    try:
        return secrets[setting]
    except KeyError:
        raise ImproperlyConfigured('Set the {} setting'.format(setting))