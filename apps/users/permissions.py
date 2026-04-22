from apps.common.permissions import make_role_permission
from apps.users.models import Role


IsAdmin = make_role_permission(Role.ADMIN)
IsRector = make_role_permission(Role.RECTOR, Role.ADMIN)
IsViceRector = make_role_permission(Role.VICE_RECTOR, Role.ADMIN)
IsDean = make_role_permission(Role.DEAN, Role.ADMIN)
IsHeadOfDept = make_role_permission(Role.HEAD_OF_DEPT, Role.ADMIN)
IsTeacher = make_role_permission(Role.TEACHER)
IsManagement = make_role_permission(Role.RECTOR, Role.VICE_RECTOR, Role.ADMIN)
