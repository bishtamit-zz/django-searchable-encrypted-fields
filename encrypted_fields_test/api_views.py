from rest_framework import viewsets

from .models import DemoModel
from .serializers import DemoModelSerializer


class DemoModelViewset(viewsets.ModelViewSet):
    queryset = DemoModel.objects.all()
    serializer_class = DemoModelSerializer
