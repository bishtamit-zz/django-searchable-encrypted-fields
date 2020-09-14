import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        """We delete migrations created from any previous test run, so we can test
        'makemigrations' in each 'tox' environment."""

        dir_path = os.path.dirname(os.path.realpath(__file__))
        print(f"dir_path: {dir_path}")
        pg_dir = dir_path.replace("management/commands", "test_pg_migrations")
        sqlite_dir = dir_path.replace("management/commands", "test_sqlite_migrations")
        folders = [pg_dir, sqlite_dir]
        print(f"folders: {folders}")
        for folder in folders:
            for filename in os.listdir(folder):
                if "__init__" not in filename:
                    file_path = os.path.join(folder, filename)
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        print("Failed to delete %s. Reason: %s" % (file_path, e))
