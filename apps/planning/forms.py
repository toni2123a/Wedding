from django import forms

from apps.tenancy.models import Membership


class TaskForm(forms.Form):
    title = forms.CharField(label="Aufgabe", max_length=160)
    description = forms.CharField(
        label="Notizen",
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    due_date = forms.DateField(
        label="Fällig am",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d", "%d.%m.%Y"],
    )
    assigned_to = forms.ModelChoiceField(
        label="Verantwortlich",
        queryset=Membership.objects.none(),
        required=False,
        empty_label="Noch nicht zugewiesen",
    )

    def __init__(self, *args, wedding_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = (
            Membership.objects.filter(
                wedding_id=wedding_id, is_active=True, role__in=["owner", "planner", "witness"]
            )
            .select_related("user")
            .order_by("user__first_name", "id")
        )
        self.fields["assigned_to"].label_from_instance = lambda member: (
            f"{member.user.first_name or member.user.email} · {member.get_role_display()}"
        )


class TaskStatusForm(forms.Form):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    is_done = forms.TypedChoiceField(
        choices=[("true", "Erledigt"), ("false", "Offen")], coerce=lambda value: value == "true"
    )
