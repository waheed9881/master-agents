"""Generate a Fernet key for CREDENTIALS_ENCRYPTION_KEY."""
from django.core.management.base import BaseCommand

from apps.integrations.services.credential_encryption import generate_key


class Command(BaseCommand):
    help = "Generate a Fernet encryption key for channel credentials"

    def handle(self, *args, **options):
        key = generate_key()
        self.stdout.write("AI Agent OS - Credential Encryption Key")
        self.stdout.write("=" * 45)
        self.stdout.write("")
        self.stdout.write("Generated Fernet key (add to your .env file):")
        self.stdout.write("")
        self.stdout.write(f"CREDENTIALS_ENCRYPTION_KEY={key}")
        self.stdout.write("")
        self.stdout.write("Instructions:")
        self.stdout.write("1. Copy the line above into your .env file")
        self.stdout.write("2. Restart the Django server")
        self.stdout.write("3. Re-save integration credentials to encrypt existing plain values")
        self.stdout.write("4. Never commit this key to version control")
        self.stdout.write("")
        self.stdout.write("Existing plain: prefixed values continue to work in local dev.")
        self.stdout.write("New credentials are encrypted automatically when the key is set.")
