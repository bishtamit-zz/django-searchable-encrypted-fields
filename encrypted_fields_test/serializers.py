from rest_framework import serializers

from .models import DemoModel


class DemoModelSerializer(serializers.ModelSerializer):
    # Unaccompanied EncryptedFields do not need to be declared.
    # They work just as expected. Eg 'date_2', 'info'
    #
    # SearchFields should be declared with the appropriate serializer Field, otherwise
    # they will be a 'serializer.CharField(max_length=66)' and validation will not be
    # as expected.
    # Note: don't include a SearchField's accompanying EncryptedField in the serializer.
    name = serializers.CharField(required=False, max_length=10)
    email = serializers.EmailField(required=True)
    date = serializers.DateField(required=True)
    number = serializers.IntegerField(required=True)
    text = serializers.CharField(required=True)

    # Let's add some read-only fields that are SearchFields.
    # We declare them here instead of in `Meta.read_only_fields` to give them the
    # correct type of serializer Field.
    default_date = serializers.DateField(read_only=True)
    default_number = serializers.IntegerField(read_only=True)
    default_char = serializers.CharField(read_only=True)

    class Meta:
        model = DemoModel
        fields = [
            "id",
            "name",
            "email",
            "date",
            "date_2",
            "number",
            "text",
            "info",
            "default_date",
            "default_number",
            "default_char",
        ]
