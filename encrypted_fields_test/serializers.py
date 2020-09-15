from rest_framework import serializers

from .models import DemoModel


class DemoModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoModel
        fields = ["id", "name", "email", "date", "date_2", "number", "text"]
