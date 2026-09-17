from django import forms
from django.contrib.auth import get_user_model

from .models import WsusMaintenanceTask


User = get_user_model()


class WsusTaskForm(forms.ModelForm):
    planned_start_at = forms.DateTimeField(
        required=False,
        label="Início previsto",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            },
        ),
    )

    planned_end_at = forms.DateTimeField(
        required=False,
        label="Fim previsto",
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
        model = WsusMaintenanceTask
        fields = [
            "assigned_to",
            "priority",
            "status",
            "planned_start_at",
            "planned_end_at",
            "allow_reboot",
            "notes",
        ]
        widgets = {
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Informe janela, dependências, "
                        "orientações ou observações da atividade..."
                    ),
                }
            ),
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

    def clean(self):
        cleaned_data = super().clean()

        planned_start_at = cleaned_data.get("planned_start_at")
        planned_end_at = cleaned_data.get("planned_end_at")

        if (
            planned_start_at
            and planned_end_at
            and planned_end_at < planned_start_at
        ):
            self.add_error(
                "planned_end_at",
                (
                    "O fim previsto não pode ser "
                    "anterior ao início previsto."
                ),
            )

        return cleaned_data
