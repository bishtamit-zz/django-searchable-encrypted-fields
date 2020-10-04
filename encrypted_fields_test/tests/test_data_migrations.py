import pytest
from django.core.management.commands.migrate import Command as migrate_command

from ..models import DemoMigrationModel


pytestmark = pytest.mark.django_db


def test_data_migrations(settings):
    DemoMigrationModel.objects.create(data="bar")
    kwargs = {
        "app_label": "encrypted_fields_test",
        "verbosity": 0,
        "interactive": False,
        "database": "default",
        "run_syncdb": False,
        "fake": False,
        "fake_initial": False,
    }
    back_migrate = migrate_command()
    # undo all migrations
    back_migrate.handle(migration_name="zero", **kwargs)
    # make sure we are using our prebuilt migrations
    settings.MIGRATION_MODULES = {
        "encrypted_fields_test": "encrypted_fields_test.migrations"
    }
    migrate = migrate_command()
    # migrate to initial state that we want (first data migration)
    migrate.handle(migration_name="0003_data_migration_example", **kwargs)

    obj = DemoMigrationModel.objects.first()
    assert obj.data == "bye"
    assert obj.encrypted_data == "bye"
    assert obj.info == "foo"
    assert obj.encrypted_info == "foo"
    assert obj.searchable_encrypted_info == "foo"
    # We haven't migrated this yet, so it will still have the default value
    assert obj.searchable_encrypted_data == "hi"
    assert obj._encrypted_data == "hi"

    # Do next data migration
    migrate.handle(migration_name="0004_data_migration_example_2", **kwargs)

    obj = DemoMigrationModel.objects.first()
    assert obj.searchable_encrypted_data == "bye"
    assert obj._encrypted_data == "bye"

    # Test rotating to new encryption key.
    new_key = "d244ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b"
    settings.FIELD_ENCRYPTION_KEYS = [new_key] + settings.FIELD_ENCRYPTION_KEYS
    migrate.handle(migration_name="0005_rotate_keys_migration", **kwargs)

    # We must remove the 'keys' cached property of encrypted fields, so they can
    # repopulate 'keys' with the new 'settings.FIELD_ENCRYPTION_KEYS'.
    # This is just for this test and is not relevant in reality.
    enc_fields = ["encrypted_data", "encrypted_info", "_encrypted_data"]
    for enc_field in enc_fields:
        f = DemoMigrationModel._meta.get_field(enc_field)
        del f.keys

    obj = DemoMigrationModel.objects.first()
    # Field values have not changed and can still be decrypted
    assert obj.data == "bye"
    assert obj.encrypted_data == "bye"
    assert obj.info == "foo"
    assert obj.encrypted_info == "foo"
    assert obj.searchable_encrypted_info == "foo"
    assert obj.searchable_encrypted_data == "bye"
    assert obj._encrypted_data == "bye"
