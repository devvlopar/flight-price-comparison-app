# tokens.py
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
import time

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk) + six.text_type(timestamp)

# Instantiate the token generator
token_generator = CustomPasswordResetTokenGenerator()

def generate_reset_token(user):
    timestamp = int(time.time())
    return token_generator.make_token(user)
