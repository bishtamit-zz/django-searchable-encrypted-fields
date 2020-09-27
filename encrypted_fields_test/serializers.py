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

    class Meta:
        model = DemoModel
        fields = ["id", "name", "email", "date", "date_2", "number", "text", "info"]
