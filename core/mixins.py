from django.contrib.auth.mixins import AccessMixin

class TeamLeadOrCoordinatorRequiredMixin(AccessMixin):
    """Verify that the current user is a team lead or a coordinator."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or (not request.user.is_team_lead and not request.user.is_coordinator):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

class ExpenseManagementMixin(AccessMixin):
    """Verify that the current user is a team lead, a coordinator or a field team user."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or (not request.user.is_team_lead and not request.user.is_coordinator and not request.user.is_field_team):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
