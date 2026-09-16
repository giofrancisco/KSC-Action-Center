from django import forms
from django.contrib.auth import get_user_model

from .models import Problem


User = get_user_model()


class ProblemQuickEditForm(forms.ModelForm):
    due_at = forms.DateTimeField(
        required=False,
        label="Data fim da atividade",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            },
        ),
    )

    class Meta:
        model = Problem
        fields = [
            "assigned_to",
            "priority",
            "workflow_status",
            "due_at",
        ]
        labels = {
            "assigned_to": "Responsável",
            "priority": "Criticidade",
            "workflow_status": "Status",
            "due_at": "Data fim da atividade",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["assigned_to"].queryset = (
            User.objects
            .filter(is_active=True)
            .order_by("first_name", "username")
        )
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].empty_label = "Não atribuído"

        self.fields["priority"].choices = [
            ("P0", "P0 - Crítica"),
            ("P1", "P1 - Alta"),
            ("P2", "P2 - Operacional"),
        ]
