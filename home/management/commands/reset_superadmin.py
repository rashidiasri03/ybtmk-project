from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Recreate or reset the superadmin account (emergency recovery)'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Superadmin username (default: admin)')
        parser.add_argument('--password', default='admin123', help='Superadmin password (default: admin123)')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Superadmin "{username}" berjaya dicipta. Password: {password}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Superadmin "{username}" berjaya direset. Password: {password}'
            ))
