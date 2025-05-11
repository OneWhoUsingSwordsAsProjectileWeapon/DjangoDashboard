"""
Authentication utilities for the users app
"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class TokenGenerator(PasswordResetTokenGenerator):
    """
    Generate token for email verification
    """
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )

account_activation_token = TokenGenerator()

def get_user_by_email(email):
    """
    Get user by email (case-insensitive)
    """
    from users.models import User
    
    try:
        return User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return None

def generate_verification_code():
    """
    Generate 6-digit verification code
    """
    import random
    return str(random.randint(100000, 999999))
