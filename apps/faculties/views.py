from rest_framework.permissions import IsAuthenticated

from apps.common.viewsets import BaseViewSet
from apps.faculties.models import Faculty
from apps.faculties.serializers import FacultySerializer
from apps.users.permissions import IsAdmin


class FacultyViewSet(BaseViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdmin()]
