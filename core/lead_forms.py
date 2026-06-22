from django import forms
from django.core.exceptions import ValidationError

from branch.models import Branch
from core.lead_service_utils import LEAD_SERVICE_ZIP_FIELD, validate_lead_service_zip
from core.phone_validation import LEAD_PHONE_COUNTRY_CHOICES, normalize_lead_phone
from core.lead_utils import (
    get_active_lead_services,
    get_active_lead_sources,
    get_active_lead_statuses,
    get_active_lost_reason_types,
    get_default_lead_status,
    get_followup_lead_statuses,
    get_staff_lead_statuses,
    is_staff_lost_status,
    staff_status_to_stage,
)
from core.models import Lead, LeadProcedureStep, LeadService, LeadServiceProcedure, LeadSource, LeadStatus

FORM_CONTROL = {"class": "form-control"}
PAYMENT_SCREENSHOT_FIELD = "payment_screenshot"
PAYMENT_IMAGE_ACCEPT = ".jpg,.jpeg,.png,.webp,.gif,image/jpeg,image/png,image/webp,image/gif"


class DisabledPlaceholderSelect(forms.Select):
    """Render empty placeholder option as disabled/non-selectable."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value in ("", None):
            option["attrs"]["disabled"] = True
        return option


def validate_payment_screenshot_upload(uploaded):
    if not uploaded:
        return uploaded
    content_type = getattr(uploaded, "content_type", "") or ""
    if content_type and not content_type.startswith("image/"):
        raise ValidationError("Payment proof must be an image screenshot.")
    name = (getattr(uploaded, "name", "") or "").lower()
    if name and not name.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        raise ValidationError("Payment proof must be a JPG, PNG, WEBP, or GIF image.")
    return uploaded


def add_payment_screenshot_field(form):
    form.fields[PAYMENT_SCREENSHOT_FIELD] = forms.ImageField(
        required=False,
        label="Payment screenshot",
        widget=forms.ClearableFileInput(
            attrs={**FORM_CONTROL, "accept": PAYMENT_IMAGE_ACCEPT}
        ),
        help_text="Upload a screenshot of the payment (image only).",
    )


class StaffLeadAddForm(forms.ModelForm):
    """Quick add — name, phone, and service only."""

    phone_country = forms.ChoiceField(
        choices=LEAD_PHONE_COUNTRY_CHOICES,
        initial="+971",
        label="Country",
        widget=forms.Select(attrs=FORM_CONTROL),
    )

    class Meta:
        model = Lead
        fields = ("name", "phone", "service")
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Contact name"}),
            "phone": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "501234567"}),
            "service": DisabledPlaceholderSelect(attrs={**FORM_CONTROL, "class": "form-control lead-service-select"}),
        }

    def __init__(self, *args, staff_branch=None, **kwargs):
        self.staff_branch = staff_branch
        super().__init__(*args, **kwargs)
        if not staff_branch:
            self.fields["branch"] = forms.ModelChoiceField(
                queryset=Branch.active.all().order_by("name"),
                required=True,
                label="Branch",
                empty_label="Select your branch",
                widget=forms.Select(attrs=FORM_CONTROL),
            )
        self.fields["service"].queryset = get_active_lead_services()
        self.fields["service"].empty_label = "Select service"
        self.fields["service"].required = True
        self.fields["phone"].label = "Mobile number"
        self.fields["phone"].widget.attrs.update({
            "inputmode": "numeric",
            "autocomplete": "tel-national",
            "pattern": "[0-9]*",
            "maxlength": "15",
        })

    def clean(self):
        cleaned = super().clean()
        country = cleaned.get("phone_country") or "+971"
        national = cleaned.get("phone") or ""
        phone, error = normalize_lead_phone(country, national)
        if error:
            self.add_error("phone", error)
            return cleaned
        if Lead.objects.filter(phone=phone).exists():
            self.add_error("phone", "A lead with this phone number already exists.")
            return cleaned
        cleaned["phone"] = phone
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.company = Lead.ClientType.COMPANY
        instance.staff_status = get_default_lead_status()
        instance.followup_status = None
        if commit:
            instance.save()
        return instance


class StaffLeadEditForm(forms.ModelForm):
    """Edit core lead fields — name, phone, and service."""

    phone_country = forms.ChoiceField(
        choices=LEAD_PHONE_COUNTRY_CHOICES,
        initial="+971",
        label="Country",
        widget=forms.Select(attrs=FORM_CONTROL),
    )

    class Meta:
        model = Lead
        fields = ("name", "phone", "service")
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Contact name"}),
            "phone": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "501234567"}),
            "service": DisabledPlaceholderSelect(attrs={**FORM_CONTROL, "class": "form-control lead-service-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.phone_validation import split_stored_lead_phone

        self.fields["service"].queryset = get_active_lead_services()
        self.fields["service"].empty_label = "Select service"
        self.fields["service"].required = True
        self.fields["phone"].label = "Mobile number"
        self.fields["phone"].widget.attrs.update({
            "inputmode": "numeric",
            "autocomplete": "tel-national",
            "pattern": "[0-9]*",
            "maxlength": "15",
        })
        if self.instance.pk:
            country, national = split_stored_lead_phone(self.instance.phone)
            self.fields["phone_country"].initial = country
            if not self.is_bound:
                self.fields["phone"].initial = national

    def clean(self):
        cleaned = super().clean()
        country = cleaned.get("phone_country") or "+971"
        national = cleaned.get("phone") or ""
        phone, error = normalize_lead_phone(country, national)
        if error:
            self.add_error("phone", error)
            return cleaned
        qs = Lead.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            self.add_error("phone", "A lead with this phone number already exists.")
            return cleaned
        cleaned["phone"] = phone
        return cleaned


class StaffLeadUpdateForm(forms.ModelForm):
    """Complete lead details — email, type, source, ZIP, payment, notes."""

    class Meta:
        model = Lead
        fields = ("email", "company", "source", "notes", "payment_verified")
        widgets = {
            "email": forms.EmailInput(attrs={**FORM_CONTROL, "placeholder": "email@company.com"}),
            "company": forms.Select(attrs=FORM_CONTROL),
            "source": forms.Select(attrs=FORM_CONTROL),
            "notes": forms.Textarea(attrs={**FORM_CONTROL, "rows": 3, "placeholder": "Lead details"}),
            "payment_verified": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].label = "Type"
        self.fields["company"].required = True
        self.fields["company"].empty_label = "Select type"
        self.fields["source"].queryset = get_active_lead_sources()
        self.fields["source"].empty_label = "Select source"
        self.fields["source"].required = False
        self.fields["payment_verified"].label = "Payment received"
        self.fields["payment_verified"].required = False
        zip_required = not (self.instance.pk and self.instance.service_documents_zip)
        self.fields[LEAD_SERVICE_ZIP_FIELD] = forms.FileField(
            required=zip_required,
            label="Service documents (ZIP)",
            widget=forms.ClearableFileInput(
                attrs={**FORM_CONTROL, "accept": ".zip,application/zip,application/x-zip-compressed"}
            ),
            help_text="Upload all documents for this service in one ZIP file.",
        )
        add_payment_screenshot_field(self)

    def clean_payment_screenshot(self):
        return validate_payment_screenshot_upload(self.cleaned_data.get(PAYMENT_SCREENSHOT_FIELD))

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            return None
        qs = Lead.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A lead with this email already exists.")
        return email.lower()

    def clean(self):
        cleaned = super().clean()
        uploaded = self.files.get(LEAD_SERVICE_ZIP_FIELD) if self.files is not None else None
        has_zip = bool(self.instance.pk and self.instance.service_documents_zip)
        if not uploaded and not has_zip:
            self.add_error(LEAD_SERVICE_ZIP_FIELD, "Service documents ZIP file is required.")
        elif uploaded:
            try:
                validate_lead_service_zip(self.files)
            except ValidationError as exc:
                if hasattr(exc, "error_list"):
                    for message in exc.error_list:
                        self.add_error(LEAD_SERVICE_ZIP_FIELD, message)
                else:
                    for messages in exc.error_dict.values():
                        for message in messages:
                            self.add_error(LEAD_SERVICE_ZIP_FIELD, message)
        payment_verified = cleaned.get("payment_verified")
        uploaded = cleaned.get(PAYMENT_SCREENSHOT_FIELD)
        has_screenshot = bool(self.instance.payment_screenshot) or bool(uploaded)
        if payment_verified and not has_screenshot:
            self.add_error(
                PAYMENT_SCREENSHOT_FIELD,
                "Upload a payment screenshot when payment is confirmed.",
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded = self.cleaned_data.get(PAYMENT_SCREENSHOT_FIELD)
        if uploaded:
            instance.payment_screenshot = uploaded
        if commit:
            instance.save()
        return instance


class StaffLeadStatusForm(forms.ModelForm):
    status_change_note = forms.CharField(
        required=False,
        label="Note",
        widget=forms.Textarea(
            attrs={**FORM_CONTROL, "rows": 2, "placeholder": "Optional note for this status change"}
        ),
    )
    class Meta:
        model = Lead
        fields = ("staff_status", "lost_reason_type")
        widgets = {
            "staff_status": forms.Select(attrs=FORM_CONTROL),
            "lost_reason_type": forms.Select(attrs=FORM_CONTROL),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["staff_status"].queryset = get_staff_lead_statuses()
        self.fields["staff_status"].empty_label = None
        self.fields["staff_status"].label = "Status"
        self.fields["lost_reason_type"].queryset = get_active_lost_reason_types()
        self.fields["lost_reason_type"].empty_label = "Select lost reason"
        self.fields["lost_reason_type"].label = "Lost reason"
        self.fields["lost_reason_type"].required = False

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("staff_status")
        lost_reason = cleaned.get("lost_reason_type")
        if status and status.sends_to_followup and not self.instance.service_documents_zip:
            raise ValidationError(
                "Upload service documents (ZIP) using Update before sending this lead to follow-up."
            )
        if status and status.sends_to_followup:
            if not self.instance.payment_verified:
                self.add_error(
                    "staff_status",
                    "Confirm payment received before setting status to Converted.",
                )
            if not self.instance.payment_screenshot:
                self.add_error(
                    "staff_status",
                    "Upload a payment screenshot before setting status to Converted.",
                )
        if is_staff_lost_status(status) and not lost_reason:
            self.add_error("lost_reason_type", "Select a reason when marking the lead as Lost.")
        if status and not is_staff_lost_status(status):
            cleaned["lost_reason_type"] = None
        return cleaned


class BackofficeCheckForm(forms.Form):
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2, "placeholder": "Optional note"}),
    )


class FollowupZipCheckForm(forms.Form):
    """Check each file extracted from the staff ZIP."""

    def __init__(self, lead, *args, **kwargs):
        self.lead = lead
        super().__init__(*args, **kwargs)
        self.extracted_docs = list(lead.extracted_documents.all())
        for doc in self.extracted_docs:
            field_name = f"file_{doc.pk}"
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=doc.original_name,
                initial=doc.followup_checked,
            )
        if not self.extracted_docs and lead.service_documents_zip:
            self.fields["zip_verified"] = forms.BooleanField(
                required=False,
                label="Staff ZIP verified",
                initial=lead.service_zip_verified,
            )

    def clean(self):
        cleaned = super().clean()
        if not self.lead.service_documents_zip:
            raise ValidationError("No staff ZIP uploaded for this lead.")
        if self.extracted_docs:
            missing = [
                doc.original_name
                for doc in self.extracted_docs
                if not cleaned.get(f"file_{doc.pk}")
            ]
            if missing:
                raise ValidationError("Check every file from the staff ZIP before saving.")
        elif not cleaned.get("zip_verified"):
            raise ValidationError("Confirm the staff ZIP before saving.")
        return cleaned

    def save_checks(self):
        for doc in self.extracted_docs:
            checked = bool(self.cleaned_data.get(f"file_{doc.pk}"))
            if doc.followup_checked != checked:
                doc.followup_checked = checked
                doc.save(update_fields=["followup_checked"])
        if not self.extracted_docs and self.lead.service_documents_zip:
            verified = bool(self.cleaned_data.get("zip_verified"))
            if self.lead.service_zip_verified != verified:
                self.lead.service_zip_verified = verified
                self.lead.save(update_fields=["service_zip_verified", "updated_at"])


class FollowupLeadStatusForm(forms.ModelForm):
    roadmap_note = forms.CharField(
        required=False,
        label="Roadmap note",
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2, "placeholder": "Optional note"}),
    )

    class Meta:
        model = Lead
        fields = ("followup_status",)
        widgets = {
            "followup_status": forms.Select(attrs=FORM_CONTROL),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["followup_status"].queryset = get_followup_lead_statuses()
        self.fields["followup_status"].empty_label = None
        self.fields["followup_status"].label = "Status"

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("followup_status")
        if status and status.sends_to_backoffice:
            if not self.instance.staff_zip_documents_checked:
                raise ValidationError("Check all staff ZIP files before setting status to Approved.")
        return cleaned


class FollowupServiceExpireForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ("service_expire_date",)
        widgets = {
            "service_expire_date": forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service_expire_date"].label = "Service expire date"
        self.fields["service_expire_date"].required = False


class FollowupLeadForm(forms.ModelForm):
    roadmap_note = forms.CharField(
        required=False,
        label="Roadmap note",
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2, "placeholder": "What happened in this step?"}),
    )

    class Meta:
        model = Lead
        fields = (
            "followup_status",
            "next_followup_date",
            "service_expire_date",
            "doc_passport_collected",
            "doc_certificates_collected",
            "doc_photos_collected",
            "doc_collection_notes",
        )
        widgets = {
            "followup_status": forms.Select(attrs={**FORM_CONTROL}),
            "next_followup_date": forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
            "service_expire_date": forms.DateInput(attrs={**FORM_CONTROL, "type": "date"}),
            "doc_collection_notes": forms.Textarea(
                attrs={**FORM_CONTROL, "rows": 2, "placeholder": "Missing items or collection notes"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["followup_status"].queryset = get_followup_lead_statuses()
        self.fields["followup_status"].empty_label = None
        self.fields["service_expire_date"].label = "Service expire date"
        self.fields["service_expire_date"].required = False


class FollowupProcedureStepForm(forms.Form):
    procedure_id = forms.IntegerField(widget=forms.HiddenInput())
    document = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={**FORM_CONTROL}),
        label="Procedure document",
    )
    followup_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2, "placeholder": "Optional note"}),
        label="Follow-up note",
    )

    def __init__(self, lead, *args, **kwargs):
        self.lead = lead
        super().__init__(*args, **kwargs)

    def clean_document(self):
        doc = self.cleaned_data.get("document")
        if not doc:
            raise ValidationError("Upload a document for this procedure step.")
        return doc

    def clean(self):
        cleaned = super().clean()
        procedure_id = cleaned.get("procedure_id")
        if not procedure_id:
            return cleaned
        try:
            procedure = LeadServiceProcedure.objects.get(
                pk=procedure_id,
                service_id=self.lead.service_id,
                is_active=True,
            )
        except LeadServiceProcedure.DoesNotExist:
            raise ValidationError("Invalid procedure for this lead service.")

        templates = list(
            LeadServiceProcedure.objects.filter(service_id=self.lead.service_id, is_active=True).order_by("sort_order", "name")
        )
        steps = {
            step.procedure_id: step
            for step in LeadProcedureStep.objects.filter(lead=self.lead).select_related("procedure")
        }
        next_procedure = None
        for template in templates:
            step = steps.get(template.pk)
            if not step or step.status != LeadProcedureStep.Status.APPROVED:
                next_procedure = template
                break
        if not next_procedure:
            raise ValidationError("All procedure steps are already approved for this lead.")
        if procedure.pk != next_procedure.pk:
            raise ValidationError(f"Submit the next pending step first: {next_procedure.name}.")
        existing = steps.get(procedure.pk)
        if existing and existing.status == LeadProcedureStep.Status.PENDING:
            raise ValidationError("This step is pending back office review. Wait for approval/rejection.")
        cleaned["procedure"] = procedure
        cleaned["existing_step"] = existing
        return cleaned


class BackofficeProcedureReviewForm(forms.Form):
    action = forms.ChoiceField(choices=(("approve", "Approve"), ("reject", "Reject")))
    review_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**FORM_CONTROL, "rows": 2, "placeholder": "Optional review note"}),
        label="Review note",
    )


class LeadServiceForm(forms.ModelForm):
    class Meta:
        model = LeadService
        fields = ("name", "code", "description", "sort_order", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. Visa renewal"}),
            "code": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. visa-renewal"}),
            "description": forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
            "sort_order": forms.NumberInput(attrs={**FORM_CONTROL, "min": 0}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().lower()
        if not code:
            name = self.cleaned_data.get("name", "")
            code = name.lower().replace(" ", "-")[:50]
        qs = LeadService.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This code is already used by another service.")
        return code


class LeadSourceForm(forms.ModelForm):
    class Meta:
        model = LeadSource
        fields = ("name", "code", "description", "sort_order", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. Website"}),
            "code": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. website"}),
            "description": forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
            "sort_order": forms.NumberInput(attrs={**FORM_CONTROL, "min": 0}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().lower()
        if not code:
            name = self.cleaned_data.get("name", "")
            code = name.lower().replace(" ", "-")[:50]
        qs = LeadSource.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This code is already used by another lead source.")
        return code


class LeadStatusForm(forms.ModelForm):
    class Meta:
        model = LeadStatus
        fields = (
            "name",
            "code",
            "description",
            "badge_style",
            "sort_order",
            "is_default",
            "counts_as_converted",
            "sends_to_followup",
            "sends_to_backoffice",
            "is_active",
        )
        widgets = {
            "name": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. Contacted"}),
            "code": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "e.g. contacted"}),
            "description": forms.Textarea(attrs={**FORM_CONTROL, "rows": 2}),
            "badge_style": forms.Select(attrs=FORM_CONTROL),
            "sort_order": forms.NumberInput(attrs={**FORM_CONTROL, "min": 0}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "counts_as_converted": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sends_to_followup": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "sends_to_backoffice": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().lower()
        if not code:
            name = self.cleaned_data.get("name", "")
            code = name.lower().replace(" ", "-")[:50]
        qs = LeadStatus.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This code is already used by another lead status.")
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.is_default:
            LeadStatus.objects.exclude(pk=instance.pk).update(is_default=False)
        if commit:
            instance.save()
        return instance
