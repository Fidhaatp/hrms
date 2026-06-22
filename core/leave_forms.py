from django import forms

from core.leave_utils import (
    count_leave_days,
    get_active_leave_categories,
    get_active_leave_types,
    leave_balance,
)
from core.models import LeaveCategory, LeaveRequest, LeaveType

FORM_CONTROL = {"class": "form-control"}


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ("leave_category", "leave_type", "start_date", "end_date", "reason")
        widgets = {
            "leave_category": forms.Select(attrs={**FORM_CONTROL}),
            "leave_type": forms.Select(attrs={**FORM_CONTROL}),
            "start_date": forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
            "end_date": forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
            "reason": forms.Textarea(attrs={**FORM_CONTROL, "rows": 3, "placeholder": "Reason for leave"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["leave_category"].queryset = get_active_leave_categories()
        self.fields["leave_type"].queryset = get_active_leave_types()
        self.fields["leave_category"].empty_label = None
        self.fields["leave_type"].empty_label = None
        self.fields["leave_category"].label = "Leave category"
        self.fields["leave_type"].label = "Leave type"

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        leave_category = cleaned.get("leave_category")
        if start and end:
            if end < start:
                raise forms.ValidationError("End date must be on or after start date.")
            requested = count_leave_days(start, end)
            if requested < 1:
                raise forms.ValidationError("Leave must be at least one day.")
            if self.user and leave_category:
                remaining = leave_balance(self.user, leave_category, start.year)
                if requested > remaining:
                    raise forms.ValidationError(
                        f"You only have {remaining} day(s) of {leave_category.name} remaining for {start.year}."
                    )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.status = LeaveRequest.Status.PENDING
        staff = getattr(self.user, "staff_profile", None)
        if staff and staff.branch_id:
            instance.workflow_stage = LeaveRequest.WorkflowStage.PENDING_MANAGER
        else:
            instance.workflow_stage = LeaveRequest.WorkflowStage.PENDING_HR
        if commit:
            instance.save()
        return instance


class LeaveCategoryForm(forms.ModelForm):
    """HR: entitlement buckets (yearly leave with day counts)."""

    class Meta:
        model = LeaveCategory
        fields = ("name", "code", "description", "days_per_year", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. Yearly Leave"}),
            "code": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. yearly"}),
            "description": forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
            "days_per_year": forms.NumberInput(attrs={**FORM_CONTROL, "min": 1}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().lower()
        if not code:
            name = self.cleaned_data.get("name", "")
            code = name.lower().replace(" ", "-")[:50]
        qs = LeaveCategory.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This code is already used by another leave category.")
        return code


class LeaveTypeForm(forms.ModelForm):
    """HR: leave kinds — sick, casual, etc."""

    class Meta:
        model = LeaveType
        fields = ("name", "code", "description", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. Sick Leave"}),
            "code": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. sick"}),
            "description": forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().lower()
        if not code:
            name = self.cleaned_data.get("name", "")
            code = name.lower().replace(" ", "-")[:50]
        qs = LeaveType.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This code is already used by another leave type.")
        return code
