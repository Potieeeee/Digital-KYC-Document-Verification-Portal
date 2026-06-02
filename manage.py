#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    cert_path = os.path.join(os.path.dirname(__file__), 'ssl.crt')
    key_path = os.path.join(os.path.dirname(__file__), 'ssl.key')

    if len(sys.argv) > 1 and sys.argv[1] == 'runserver' and os.path.exists(cert_path) and os.path.exists(key_path):
        sys.argv[1] = 'runsslserver'
        if '--certificate' not in sys.argv:
            sys.argv.extend(['--certificate', cert_path])
        if '--key' not in sys.argv:
            sys.argv.extend(['--key', key_path])
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
