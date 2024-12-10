# tokens.py
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import time
from django.conf import settings

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp)

# Instantiate the token generator
token_generator = CustomPasswordResetTokenGenerator()

def generate_reset_token(user):
    timestamp = int(time.time())
    return token_generator.make_token(user), timestamp

def is_token_expired(timestamp):
    """
    Check if the token is expired based on the configured timeout in settings.
    """
    expiration_time = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 1800)  # Default to 30 minutes
    current_time = int(time.time())
    return current_time > (timestamp + expiration_time)
