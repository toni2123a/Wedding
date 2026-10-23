from django.core.exceptions import PermissionDenied

from .models import Membership

PLANNING_ROLES = {Membership.Role.OWNER, Membership.Role.PLANNER}
TASK_ROLES = PLANNING_ROLES | {Membership.Role.WITNESS}


def require_role(membership, roles):
    if membership is None or not membership.is_active or membership.role not in roles:
        raise PermissionDenied("Für diesen Bereich fehlt die Freigabe.")
