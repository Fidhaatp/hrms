"""Lead document uploads (follow-up) and viewing (back office)."""

from django import forms
from django.contrib import messages
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from core.backoffice_utils import backoffice_accessible_leads_queryset
from core.lead_utils import followup_active_leads_queryset
from core.models import Lead, LeadDocument, UserProfile
from core.portal import portal_role_required, render_portal_page

FORM_CONTROL = {"class": "form-control"}

FOLLOWUP_LEAD_LIST = "followup:lead_list"
BACKOFFICE_PENDING_LIST = "backoffice:pending_verifications"


class LeadDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = LeadDocument
        fields = ("doc_type", "file", "title")
        widgets = {
            "doc_type": forms.Select(attrs=FORM_CONTROL),
            "file": forms.FileInput(attrs={**FORM_CONTROL, "accept": ".pdf,.jpg,.jpeg,.png,.webp"}),
            "title": forms.TextInput(attrs={**FORM_CONTROL, "placeholder": "Optional label"}),
        }


def documents_prefetch():
    return Prefetch(
        "documents",
        queryset=LeadDocument.objects.select_related("uploaded_by").order_by("-created_at"),
    )


def followup_lead_document_upload_view():
    @portal_role_required(UserProfile.UserType.FOLLOWUP)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(followup_active_leads_queryset(), pk=pk)
        form = LeadDocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.lead = lead
            doc.uploaded_by = request.user
            doc.save()
            lead.sync_document_collection_flags()
            messages.success(
                request,
                f"Uploaded {doc.get_doc_type_display()} for {lead.name}.",
            )
        else:
            messages.error(request, "Could not upload document. Check file and type.")
        return redirect(FOLLOWUP_LEAD_LIST)

    return view


def backoffice_open_case_view():
    @portal_role_required(UserProfile.UserType.BACKOFFICE)
    @require_http_methods(["POST"])
    def view(request, pk):
        lead = get_object_or_404(
            backoffice_accessible_leads_queryset(request.user),
            pk=pk,
            backoffice_status=Lead.BackofficeStatus.VERIFIED,
        )
        case, created = ensure_client_case(lead, request.user)
        if created:
            messages.success(request, f"Case {case.case_ref} opened for {lead.name}.")
        return redirect("backoffice:case_detail", pk=case.pk)

    return view


def _case_processing_leads_queryset():
    return (
        Lead.objects.filter(
            backoffice_status=Lead.BackofficeStatus.VERIFIED,
            sent_to_backoffice_at__isnull=False,
        )
        .annotate(
            doc_count=Count("documents", distinct=True),
            extracted_doc_count=Count("extracted_documents", distinct=True),
            case_count=Count("cases", distinct=True),
        )
        .filter(
            Q(doc_count__gt=0)
            | Q(extracted_doc_count__gt=0)
            | Q(service_documents_zip__gt="")
            | Q(case_count__gt=0)
            | Q(followup_status__counts_as_converted=True)
            | Q(sent_to_backoffice_at__isnull=False)
        )
        .select_related("branch", "created_by", "followup_status", "service")
        .prefetch_related(documents_prefetch(), "cases")
        .distinct()
        .order_by("-updated_at")[:100]
    )