from django.core.management.base import BaseCommand
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = "Run HTTPS dev server automatically if ssl.crt/ssl.key exist, else HTTP runserver"

    def add_arguments(self, parser):
        parser.add_argument('addrport', nargs='?', help=' Optional port/addr to bind', default='127.0.0.1:8000')

    def handle(self, *args, **options):
        addrport = options.get('addrport')
        cert = os.path.join(os.getcwd(), 'ssl.crt')
        key = os.path.join(os.getcwd(), 'ssl.key')

        if os.path.exists(cert) and os.path.exists(key):
            self.stdout.write(self.style.NOTICE('Found ssl.crt and ssl.key — starting HTTPS dev server'))
            call_command('runsslserver', addrport, certificate=cert, key=key)
        else:
            self.stdout.write(self.style.NOTICE('ssl.crt/ssl.key not found — starting plain HTTP dev server'))
            call_command('runserver', addrport)
