from django.core.management.base import BaseCommand
from Crypto.Random import get_random_bytes


class Command(BaseCommand):
    """Command that generates a suitable encryption key for EncryptedFieldMixin.
    """

    help = "Generates (and prints) a 256 bit, hex encoded random encryption key."

    def handle(self, *args, **options):
        key = get_random_bytes(32)
        print(key.hex())
