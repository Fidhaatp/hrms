"""Team member onboarding document fields and persistence."""

from django import forms

from core.branch_utils import is_india_branch, is_india_nationality
from core.models import TeamMemberDocuments

DOC_ACCEPT = "image/*,.pdf"
DOC_FILE = {"class": "form-control", "accept": DOC_ACCEPT}
DOC_DATE = {"class": "form-control", "type": "date"}

INDIA_REQUIRED_FIELDS = ("aadhaar_card", "offer_letter")

GULF_FILE_FIELDS = (
    "passport_image",
    "emirates_id_image",
    "insurance_image",
    "labour_card_image",
    "labour_contract_image",
    "offer_letter",
)

GULF_DATE_FIELDS = (
    ("passport_expiry", "Passport expiry date"),
    ("emirates_id_expiry", "Emirates ID expiry date"),
    ("insurance_expiry", "Insurance expiry date"),
    ("labour_card_expiry", "Labour card expiry date"),
    ("labour_contract_expiry", "Labour contract expiry date"),
)


class BranchSelectWithNationality(forms.Select):
    """Branch dropdown with data-nationality on each option."""

    def __init__(self, *args, nationalities=None, **kwargs):
        self._nationalities = nationalities or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value:
            nationality = self._nationalities.get(str(value), "")
            if nationality:
                option.setdefault("attrs", {})
                option["attrs"]["data-nationality"] = nationality
        return option


def branch_nationality_map():
    from branch.models import Branch

    return {str(pk): nationality for pk, nationality in Branch.active.values_list("pk", "nationality")}


def team_branch_field(required=True):
    nationalities = branch_nationality_map()
    return forms.ModelChoiceField(
        queryset=__import__("branch.models", fromlist=["Branch"]).Branch.active.all().order_by("name"),
        required=required,
        label="Branch",
        empty_label="Select branch" if required else "— Optional —",
        widget=BranchSelectWithNationality(
            attrs={"class": "form-control team-branch-select"},
            nationalities=nationalities,
        ),
    )


def add_document_fields(form_class):
    """Attach document upload fields to a form class."""
    form_class.base_fields["aadhaar_card"] = forms.FileField(
        label="Aadhaar card",
        required=False,
        widget=forms.FileInput(attrs=DOC_FILE),
    )
    form_class.base_fields["offer_letter"] = forms.FileField(
        label="Offer letter",
        required=False,
        widget=forms.FileInput(attrs=DOC_FILE),
    )
    form_class.base_fields["passport_image"] = forms.FileField(
        label="Passport copy",
        required=False,
        widget=forms.FileInput(attrs=DOC_FILE),
    )
    form_class.base_fields["passport_expiry"] = forms.DateField(
        label="Passport expiry date",
        required=False,
        widget=forms.DateInput(attrs=DOC_DATE),
    )
    form_class.base_fields["emirates_id_image"] = forms.FileField(
        label="Emirates ID copy",
        required=False,
        widget=forms.FileInput(attrs=DOC_FILE),
    )
    form_class.base_fields["emirates_id_expiry"] = forms.DateField(
        label="Emirates ID expiry date",
        required=False,
        widget=forms.DateInput(attrs=DOC_DATE),
    )
    form_class.base_fields["insurance_image"] = forms.FileField(
        label="Insurance copy",
        required=False,
        widget=forms.FileInput(attrs=DOC_FILE),
    )
    form_class.base_fields["insurance_expiry"] = forms.DateField(
        label="Insurance expiry date",
        required=False,
        widget=forms.DateInput(attrs=DOC_DATE),
    )
    form_class.base_fields["labour_card_image"] = forms.FileField(
        label="Labour card copy",
        required=False,
        widget=forms.FileInput(attrs=DOC_FILE),
    )
    form_class.base_fields["labour_card_expiry"] = forms.DateField(
        label="Labour card expiry date",
        required=False,
        widget=forms.DateInput(attrs=DOC_DATE),
    )
    form_class.base_fields["labour_contract_image"] = forms.FileField(
        label="Labour contract copy",
        required=False,
        widget=forms.FileInput(attrs=DOC_FILE),
    )
    form_class.base_fields["labour_contract_expiry"] = forms.DateField(
        label="Labour contract expiry date",
        required=False,
        widget=forms.DateInput(attrs=DOC_DATE),
    )


class TeamDocumentFormMixin:
    """Validate and save onboarding documents based on branch nationality."""

    nationality_field_name = "nationality"

    def _resolve_document_region(self, cleaned):
        branch = cleaned.get("branch")
        if branch is not None:
            return is_india_branch(branch)
        nationality = (self.data.get(self.nationality_field_name) or "").strip()
        if nationality:
            return is_india_nationality(nationality)
        return None

    def clean(self):
        cleaned = super().clean()
        is_india = self._resolve_document_region(cleaned)
        if is_india is None:
            return cleaned

        if is_india:
            for field_name in INDIA_REQUIRED_FIELDS:
                if not cleaned.get(field_name):
                    self.add_error(field_name, "This field is required for Indian branches.")
        else:
            for field_name in GULF_FILE_FIELDS:
                if not cleaned.get(field_name):
                    label = self.fields[field_name].label
                    self.add_error(field_name, f"{label} is required for non-Indian branches.")
            for field_name, label in GULF_DATE_FIELDS:
                if not cleaned.get(field_name):
                    self.add_error(field_name, f"{label} is required for non-Indian branches.")
        return cleaned

    def save_team_documents(self, user, branch=None):
        branch = branch or self.cleaned_data.get("branch")
        nationality = None
        if branch is None:
            nationality = (self.data.get(self.nationality_field_name) or "").strip()
        is_india = is_india_branch(branch) if branch else is_india_nationality(nationality)

        docs, _ = TeamMemberDocuments.objects.get_or_create(user=user)
        docs.offer_letter = self.cleaned_data["offer_letter"]

        if is_india:
            docs.aadhaar_card = self.cleaned_data["aadhaar_card"]
            docs.passport_image = None
            docs.passport_expiry = None
            docs.emirates_id_image = None
            docs.emirates_id_expiry = None
            docs.insurance_image = None
            docs.insurance_expiry = None
            docs.labour_card_image = None
            docs.labour_card_expiry = None
            docs.labour_contract_image = None
            docs.labour_contract_expiry = None
        else:
            docs.aadhaar_card = None
            docs.passport_image = self.cleaned_data["passport_image"]
            docs.passport_expiry = self.cleaned_data["passport_expiry"]
            docs.emirates_id_image = self.cleaned_data["emirates_id_image"]
            docs.emirates_id_expiry = self.cleaned_data["emirates_id_expiry"]
            docs.insurance_image = self.cleaned_data["insurance_image"]
            docs.insurance_expiry = self.cleaned_data["insurance_expiry"]
            docs.labour_card_image = self.cleaned_data["labour_card_image"]
            docs.labour_card_expiry = self.cleaned_data["labour_card_expiry"]
            docs.labour_contract_image = self.cleaned_data["labour_contract_image"]
            docs.labour_contract_expiry = self.cleaned_data["labour_contract_expiry"]

        docs.save()
        return docs


def get_team_documents(user):
    if not user:
        return None
    try:
        return user.team_documents
    except TeamMemberDocuments.DoesNotExist:
        return None


def team_document_view_items(user, branch=None):
    """Build view-modal payload for uploaded onboarding documents."""
    docs = get_team_documents(user)
    if not docs:
        return []

    is_india = is_india_branch(branch) if branch is not None else bool(docs.aadhaar_card)
    items = []

    def add_item(label, file_field, expiry=None):
        if not file_field:
            return
        entry = {"label": label, "url": file_field.url}
        if expiry:
            entry["expiry"] = expiry.strftime("%d %b %Y")
        items.append(entry)

    if is_india:
        add_item("Aadhaar card", docs.aadhaar_card)
    else:
        add_item("Passport", docs.passport_image, docs.passport_expiry)
        add_item("Emirates ID", docs.emirates_id_image, docs.emirates_id_expiry)
        add_item("Insurance", docs.insurance_image, docs.insurance_expiry)
        add_item("Labour card", docs.labour_card_image, docs.labour_card_expiry)
        add_item("Labour contract", docs.labour_contract_image, docs.labour_contract_expiry)

    add_item("Offer letter", docs.offer_letter)
    return items
