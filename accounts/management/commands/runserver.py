from django.core.management.commands.runserver import Command as DjangoRunserverCommand
from django.core.management import call_command
import os


class Command(DjangoRunserverCommand):
    help = "Run HTTPS dev server when ssl.crt/ssl.key are present, otherwise use Django's runserver"

    def inner_run(self, *args, **options):
        cert = os.path.join(os.getcwd(), 'ssl.crt')
        key = os.path.join(os.getcwd(), 'ssl.key')

        if os.path.exists(cert) and os.path.exists(key):
            self.stdout.write(self.style.NOTICE('ssl.crt and ssl.key found — starting HTTPS dev server'))
            call_command('runsslserver', options.get('addrport', '127.0.0.1:8000'), certificate=cert, key=key)
            return

        self.stdout.write(self.style.NOTICE('ssl.crt/ssl.key not found — starting plain HTTP dev server'))
        return super().inner_run(*args, **options)
