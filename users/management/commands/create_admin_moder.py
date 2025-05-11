from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from users.models import User

class Command(BaseCommand):
    help = 'Creates admin and moderator accounts'

    def handle(self, *args, **kwargs):
        try:
            # Create Admin
            admin = User.objects.create_user(
                username='Admin',
                email='admin@example.com',
                password='123',
                first_name='Администратор',
                last_name='Системы',
                is_staff=True,  # Staff status
                is_superuser=True,  # Superuser status
                is_active=True,
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user created: {admin.username}'))
            
            # Create Moderator
            moderator = User.objects.create_user(
                username='Moder',
                email='moderator@example.com',
                password='123',
                first_name='Модератор',
                last_name='Платформы',
                is_staff=True,  # Staff status 
                is_superuser=False,  # Not a superuser
                is_active=True,
                role='moderator'
            )
            self.stdout.write(self.style.SUCCESS(f'Moderator user created: {moderator.username}'))
            
        except IntegrityError:
            self.stdout.write(self.style.WARNING('Users already exist. Please delete them first if you want to recreate.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating users: {e}'))